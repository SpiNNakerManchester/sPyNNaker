import logging
import math
import random
import scipy.stats

import numpy
from enum import Enum
from spinn_front_end_common.utilities import constants as\
    front_end_common_constants

from data_specification.enums.data_type import DataType

from pacman.executor.injection_decorator import inject_items
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint
from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.application.impl.application_vertex import \
    ApplicationVertex
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_partition_constraints import \
    AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.interface.buffer_management.buffer_models\
    .receives_buffers_to_host_basic_impl import ReceiveBuffersToHostBasicImpl
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.abstract_models\
    .abstract_generates_data_specification \
    import AbstractGeneratesDataSpecification
from spinn_front_end_common.abstract_models\
    .abstract_binary_uses_simulation_run import AbstractBinaryUsesSimulationRun
from spinn_front_end_common.abstract_models.abstract_has_associated_binary \
    import AbstractHasAssociatedBinary

from spynnaker.pyNN.models.common import recording_utils
from spynnaker.pyNN.models.common.abstract_spike_recordable \
    import AbstractSpikeRecordable
from spynnaker.pyNN.models.common.multi_spike_recorder \
    import MultiSpikeRecorder
from spynnaker.pyNN.models.common.population_settable_change_requires_mapping \
    import PopulationSettableChangeRequiresMapping
from spynnaker.pyNN.models.spike_source.spike_source_poisson_machine_vertex \
    import SpikeSourcePoissonMachineVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.utilities.conf import config

logger = logging.getLogger(__name__)

SLOW_RATE_PER_TICK_CUTOFF = 1.0
PARAMS_BASE_WORDS = 6
PARAMS_WORDS_PER_NEURON = 5
RANDOM_SEED_WORDS = 4


class SpikeSourcePoisson(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary, AbstractSpikeRecordable,
        AbstractProvidesOutgoingPartitionConstraints,
        PopulationSettableChangeRequiresMapping,
        ReceiveBuffersToHostBasicImpl, AbstractBinaryUsesSimulationRun):
    """ A Poisson Spike source object
    """

    _POISSON_SPIKE_SOURCE_REGIONS = Enum(
        value="_POISSON_SPIKE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('POISSON_PARAMS_REGION', 1),
               ('SPIKE_HISTORY_REGION', 2),
               ('BUFFERING_OUT_STATE', 3),
               ('PROVENANCE_REGION', 4)])

    _N_POPULATION_RECORDING_REGIONS = 1
    _DEFAULT_MALLOCS_USED = 2

    # Technically, this is ~2900 in terms of DTCM, but is timescale dependent
    # in terms of CPU (2900 at 10 times slow down is fine, but not at
    # real-time)
    _model_based_max_atoms_per_core = 500

    # A count of the number of poisson vertices, to work out the random
    # back off range
    _n_poisson_vertices = 0

    def __init__(
            self, n_neurons, constraints=None, label="SpikeSourcePoisson",
            rate=1.0, start=0.0, duration=None, seed=None):
        ApplicationVertex.__init__(
            self, label, constraints, self._model_based_max_atoms_per_core)
        AbstractSpikeRecordable.__init__(self)
        AbstractProvidesOutgoingPartitionConstraints.__init__(self)
        PopulationSettableChangeRequiresMapping.__init__(self)
        ReceiveBuffersToHostBasicImpl.__init__(self)

        # atoms params
        self._n_atoms = n_neurons
        self._seed = None

        # Store the parameters
        self._rate = utility_calls.convert_param_to_numpy(rate, n_neurons)
        self._start = utility_calls.convert_param_to_numpy(start, n_neurons)
        self._duration = utility_calls.convert_param_to_numpy(
            duration, n_neurons)
        self._rng = numpy.random.RandomState(seed)

        # Prepare for recording, and to get spikes
        self._spike_recorder = MultiSpikeRecorder()
        self._spike_buffer_max_size = config.getint(
            "Buffers", "spike_buffer_size")
        self._buffer_size_before_receive = config.getint(
            "Buffers", "buffer_size_before_receive")
        self._time_between_requests = config.getint(
            "Buffers", "time_between_requests")
        self._enable_buffered_recording = config.getboolean(
            "Buffers", "enable_buffered_recording")
        self._receive_buffer_host = config.get(
            "Buffers", "receive_buffer_host")
        self._receive_buffer_port = config.getint(
            "Buffers", "receive_buffer_port")
        self._minimum_buffer_sdram = config.getint(
            "Buffers", "minimum_buffer_sdram")
        self._using_auto_pause_and_resume = config.getboolean(
            "Buffers", "use_auto_pause_and_resume")

    def _max_spikes_per_ts(
            self, vertex_slice, n_machine_time_steps, machine_time_step):
        max_rate = numpy.amax(
            self._rate[vertex_slice.lo_atom:vertex_slice.hi_atom + 1])
        ts_per_second = 1000000.0 / machine_time_step
        max_spikes_per_ts = scipy.stats.poisson.ppf(
            1.0 - (1.0 / n_machine_time_steps),
            max_rate / ts_per_second)
        return int(math.ceil(max_spikes_per_ts))

    @inject_items({
        "n_machine_time_steps": "TotalMachineTimeSteps",
        "machine_time_step": "MachineTimeStep"
    })
    @overrides(
        ApplicationVertex.get_resources_used_by_atoms,
        additional_arguments={"n_machine_time_steps", "machine_time_step"}
    )
    def get_resources_used_by_atoms(
            self, vertex_slice, n_machine_time_steps, machine_time_step):

        # verify if needing the buffered out functionality
        self._check_for_activating_auto_pause_and_resume(
            vertex_slice, self, n_machine_time_steps, machine_time_step)

        # build resources as i currently know
        container = ResourceContainer(
            sdram=SDRAMResource(
                self.get_sdram_usage_for_atoms(
                    vertex_slice, n_machine_time_steps, machine_time_step)),
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms()),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms()))

        # extend resources with whatever the extra functionality requires
        container.extend(self.get_extra_resources(
            self._receive_buffer_host, self._receive_buffer_port))
        return container

    def _check_for_activating_auto_pause_and_resume(
            self, vertex_slice, object_to_set, n_machine_time_steps,
            machine_time_step):

        # verify if needing the buffered out functionality
        if not self._using_auto_pause_and_resume:
            spike_buffer_size = self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._max_spikes_per_ts(
                    vertex_slice, n_machine_time_steps, machine_time_step),
                n_machine_time_steps)
            spike_buffering_needed = recording_utils.needs_buffering(
                self._spike_buffer_max_size, spike_buffer_size,
                self._enable_buffered_recording)
            if spike_buffering_needed:
                object_to_set.activate_buffering_output(
                    buffering_ip_address=self._receive_buffer_host,
                    buffering_port=self._receive_buffer_port)
        else:
            sdram_per_ts = self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._max_spikes_per_ts(
                    vertex_slice, n_machine_time_steps, machine_time_step), 1)
            object_to_set.activate_buffering_output(
                minimum_sdram_for_buffering=self._minimum_buffer_sdram,
                buffered_sdram_per_timestep=sdram_per_ts)

    @property
    def n_atoms(self):
        return self._n_atoms

    @inject_items({
        "n_machine_time_steps": "TotalMachineTimeSteps",
        "machine_time_step": "MachineTimeStep"
    })
    @overrides(
        ApplicationVertex.create_machine_vertex,
        additional_arguments={"n_machine_time_steps", "machine_time_step"}
    )
    def create_machine_vertex(
            self, vertex_slice, resources_required, n_machine_time_steps,
            machine_time_step, label=None, constraints=None):
        SpikeSourcePoisson._n_poisson_vertices += 1
        vertex = SpikeSourcePoissonMachineVertex(
            resources_required, self._spike_recorder.record,
            constraints, label)

        # set up auto pause and resume stuff
        self._check_for_activating_auto_pause_and_resume(
            vertex_slice, vertex, n_machine_time_steps, machine_time_step)

        # return the machine vertex
        return vertex

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, rate):
        self._rate = rate

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = start

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, duration):
        self._duration = duration

    @property
    def seed(self):
        return self._seed

    @seed.setter
    def seed(self, seed):
        self._seed = seed

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        SpikeSourcePoisson._model_based_max_atoms_per_core = new_value

    @staticmethod
    def get_max_atoms_per_core():
        return SpikeSourcePoisson._model_based_max_atoms_per_core

    @staticmethod
    def get_params_bytes(vertex_slice):
        """ Gets the size of the poisson parameters in bytes
        :param vertex_slice:
        """
        return (RANDOM_SEED_WORDS + PARAMS_BASE_WORDS +
                (((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1) *
                 PARAMS_WORDS_PER_NEURON)) * 4

    @staticmethod
    def reserve_memory_regions(spec, setup_sz, poisson_params_sz,
                               spike_hist_buff_sz, vertex):
        """ Reserve memory regions for poisson source parameters and output\
            buffer.
        :param spec:
        :param setup_sz:
        :param poisson_params_sz:
        :param spike_hist_buff_sz:
        :return:
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=(
                SpikeSourcePoissonMachineVertex.
                _POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value),
            size=setup_sz, label='setup')
        spec.reserve_memory_region(
            region=(
                SpikeSourcePoissonMachineVertex.
                _POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION.value),
            size=poisson_params_sz, label='PoissonParams')
        vertex.reserve_buffer_regions(
            spec,
            (SpikeSourcePoissonMachineVertex.
                _POISSON_SPIKE_SOURCE_REGIONS.BUFFERING_OUT_STATE.value),
            [SpikeSourcePoissonMachineVertex.
                _POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value],
            [spike_hist_buff_sz])
        vertex.reserve_provenance_data_region(spec)

    def _write_setup_info(
            self, spec, spike_history_region_sz, iptags,
            buffer_size_before_receive, vertex, machine_time_step,
            time_scale_factor):
        """ Write information used to control the simulation and gathering of\
            results.

        :param spec:
        :param spike_history_region_sz:
        :param ip_rags
        :return:
        """
        # write simulation data
        spec.switch_write_focus(
            SpikeSourcePoissonMachineVertex.
            _POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name(), machine_time_step,
            time_scale_factor))

        # write recording data
        vertex.write_recording_data(
            spec, iptags, [spike_history_region_sz],
            buffer_size_before_receive, self._time_between_requests)

    def _write_poisson_parameters(
            self, spec, key, vertex_slice, machine_time_step,
            time_scale_factor):
        """ Generate Neuron Parameter data for Poisson spike sources

        :param spec:
        :param key:
        :param num_neurons:
        :return:
        """
        spec.comment("\nWriting Neuron Parameters for {} poisson sources:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            region=(
                SpikeSourcePoissonMachineVertex.
                _POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION.value))

        # Write header info to the memory region:

        # Write Key info for this core:
        if key is None:
            # if there's no key, then two false will cover it.
            spec.write_value(data=0)
            spec.write_value(data=0)
        else:
            # has a key, thus set has key to 1 and then add key
            spec.write_value(data=1)
            spec.write_value(data=key)

        # Write the random back off value
        spec.write_value(random.randint(
            0, SpikeSourcePoisson._n_poisson_vertices))

        # Write the number of microseconds between sending spikes
        total_mean_rate = numpy.sum(self._rate)
        max_spikes = scipy.stats.poisson.ppf(
            1.0 - (1.0 / total_mean_rate), total_mean_rate)
        spikes_per_timestep = (
            max_spikes / (1000000.0 / machine_time_step))
        time_between_spikes = (
            (machine_time_step * time_scale_factor) /
            (spikes_per_timestep * 2.0))
        spec.write_value(data=int(time_between_spikes))

        # Write the random seed (4 words), generated randomly!
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))

        # For each neuron, get the rate to work out if it is a slow
        # or fast source
        slow_sources = list()
        fast_sources = list()
        for i in range(vertex_slice.n_atoms):

            atom_id = vertex_slice.lo_atom + i

            # Get the parameter values for source i:
            rate_val = self._rate[atom_id]
            start_val = self._start[atom_id]
            end_val = None
            if self._duration[atom_id] is not None:
                end_val = self._duration[atom_id] + start_val

            # Decide if it is a fast or slow source and
            spikes_per_tick = \
                (float(rate_val) * (machine_time_step / 1000000.0))
            if spikes_per_tick <= SLOW_RATE_PER_TICK_CUTOFF:
                slow_sources.append([i, rate_val, start_val, end_val])
            else:
                fast_sources.append([i, spikes_per_tick, start_val, end_val])

        # Write the numbers of each type of source
        spec.write_value(data=len(slow_sources))
        spec.write_value(data=len(fast_sources))

        # Now write one struct for each slow source as follows
        #
        #   typedef struct slow_spike_source_t
        #   {
        #     uint32_t neuron_id;
        #     uint32_t start_ticks;
        #     uint32_t end_ticks;
        #
        #     accum mean_isi_ticks;
        #     accum time_to_spike_ticks;
        #   } slow_spike_source_t;
        for (neuron_id, rate_val, start_val, end_val) in slow_sources:
            if rate_val == 0:
                isi_val = 0
            else:
                isi_val = float(1000000.0 /
                                (rate_val * machine_time_step))
            start_scaled = int(start_val * 1000.0 / machine_time_step)
            end_scaled = 0xFFFFFFFF
            if end_val is not None and not math.isnan(end_val):
                end_scaled = int(end_val * 1000.0 / machine_time_step)
            spec.write_value(data=neuron_id, data_type=DataType.UINT32)
            spec.write_value(data=start_scaled, data_type=DataType.UINT32)
            spec.write_value(data=end_scaled, data_type=DataType.UINT32)
            spec.write_value(data=isi_val, data_type=DataType.S1615)
            spec.write_value(data=0x0, data_type=DataType.UINT32)

        # Now write
        #   typedef struct fast_spike_source_t
        #   {
        #     uint32_t neuron_id;
        #     uint32_t start_ticks;
        #     uint32_t end_ticks;
        #
        #     unsigned long fract exp_minus_lambda;
        #   } fast_spike_source_t;
        for (neuron_id, spikes_per_tick, start_val, end_val) in fast_sources:
            if spikes_per_tick == 0:
                exp_minus_lamda = 0
            else:
                exp_minus_lamda = math.exp(-1.0 * spikes_per_tick)
            start_scaled = int(start_val * 1000.0 / machine_time_step)
            end_scaled = 0xFFFFFFFF
            if end_val is not None and not math.isnan(end_val):
                end_scaled = int(end_val * 1000.0 / machine_time_step)
            spec.write_value(data=neuron_id, data_type=DataType.UINT32)
            spec.write_value(data=start_scaled, data_type=DataType.UINT32)
            spec.write_value(data=end_scaled, data_type=DataType.UINT32)
            spec.write_value(data=exp_minus_lamda, data_type=DataType.U032)

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self._spike_recorder.record

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(self):
        self._spike_recorder.record = True

    def get_sdram_usage_for_atoms(
            self, vertex_slice, n_machine_time_steps, machine_time_step):
        poisson_params_sz = self.get_params_bytes(vertex_slice)
        total_size = \
            (front_end_common_constants.SYSTEM_BYTES_REQUIREMENT +
             ReceiveBuffersToHostBasicImpl.get_recording_data_size(1) +
             ReceiveBuffersToHostBasicImpl.get_buffer_state_region_size(1) +
             SpikeSourcePoissonMachineVertex.get_provenance_data_size(0) +
             poisson_params_sz)
        total_size += self._get_number_of_mallocs_used_by_dsg() * \
            front_end_common_constants.SARK_PER_MALLOC_SDRAM_USAGE

        if self._using_auto_pause_and_resume:
            total_size += self._minimum_buffer_sdram
        else:
            spike_buffer_size = self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._max_spikes_per_ts(
                    vertex_slice, n_machine_time_steps, machine_time_step),
                n_machine_time_steps)
            total_size += recording_utils.get_buffer_sizes(
                self._spike_buffer_max_size, spike_buffer_size,
                self._enable_buffered_recording)

        return total_size

    def _get_number_of_mallocs_used_by_dsg(self):
        standard_mallocs = self._DEFAULT_MALLOCS_USED
        if self._spike_recorder.record:
            standard_mallocs += 1
        return standard_mallocs

    def get_dtcm_usage_for_atoms(self):
        return 0

    def get_cpu_usage_for_atoms(self):
        return 0

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "routing_info": "MemoryRoutingInfos",
        "tags": "MemoryTags",
        "n_machine_time_steps": "TotalMachineTimeSteps"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "routing_info", "tags", "n_machine_time_steps"
        }
    )
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, routing_info, tags, n_machine_time_steps):
        vertex = placement.vertex
        vertex_slice = graph_mapper.get_slice(vertex)

        spike_buffer_size = self._spike_recorder.get_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self._max_spikes_per_ts(
                vertex_slice, n_machine_time_steps, machine_time_step),
            n_machine_time_steps)
        spike_history_sz = recording_utils.get_buffer_sizes(
            self._spike_buffer_max_size, spike_buffer_size,
            self._enable_buffered_recording)
        spike_buffering_needed = recording_utils.needs_buffering(
            self._spike_buffer_max_size, spike_buffer_size,
            self._enable_buffered_recording)
        buffer_size_before_receive = self._buffer_size_before_receive
        if not spike_buffering_needed:
            buffer_size_before_receive = spike_history_sz + 256

        spec.comment("\n*** Spec for SpikeSourcePoisson Instance ***\n\n")

        # Basic setup plus 8 bytes for recording flags and recording size
        setup_sz = (front_end_common_constants.SYSTEM_BYTES_REQUIREMENT +
                    vertex.get_recording_data_size(1))

        poisson_params_sz = self.get_params_bytes(vertex_slice)

        # Reserve SDRAM space for memory areas:
        self.reserve_memory_regions(
            spec, setup_sz, poisson_params_sz, spike_history_sz, vertex)

        iptags = tags.get_ip_tags_for_vertex(vertex)
        self._write_setup_info(
            spec, spike_history_sz, iptags, buffer_size_before_receive,
            vertex, machine_time_step, time_scale_factor)

        key = routing_info.get_first_key_from_pre_vertex(
            vertex, constants.SPIKE_PARTITION_ID)

        self._write_poisson_parameters(
            spec, key, vertex_slice, machine_time_step, time_scale_factor)

        # End-of-Spec:
        spec.end_specification()

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return "spike_source_poisson.aplx"

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(
            self, placements, graph_mapper, buffer_manager, machine_time_step):
        return self._spike_recorder.get_spikes(
            self._label, buffer_manager,
            (SpikeSourcePoissonMachineVertex.
                _POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value),
            (SpikeSourcePoissonMachineVertex.
                _POISSON_SPIKE_SOURCE_REGIONS.BUFFERING_OUT_STATE.value),
            placements, graph_mapper, self, machine_time_step)

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [KeyAllocatorContiguousRangeContraint()]
