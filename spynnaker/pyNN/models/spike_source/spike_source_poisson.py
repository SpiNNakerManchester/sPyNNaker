import struct

from enum import Enum

from data_specification.enums.data_type import DataType
from data_specification import utility_calls as dsg_utilities

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

from spinn_front_end_common.abstract_models. \
    abstract_changable_after_run import AbstractChangableAfterRun
from spinn_front_end_common.abstract_models. \
    abstract_provides_outgoing_partition_constraints import \
    AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.abstract_models. \
    abstract_requires_rewriting_data_regions_application_vertex import \
    AbstractRequiresRewriteDataRegionsApplicationVertex
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.abstract_models\
    .abstract_generates_data_specification \
    import AbstractGeneratesDataSpecification
from spinn_front_end_common.abstract_models \
    .abstract_binary_uses_simulation_run \
    import AbstractBinaryUsesSimulationRun
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.interface.buffer_management \
    import recording_utilities
from spinn_front_end_common.abstract_models.abstract_has_associated_binary \
    import AbstractHasAssociatedBinary
from spinn_front_end_common.utilities import constants as \
    front_end_common_constants

from spynnaker.pyNN.models.common.abstract_spike_recordable \
    import AbstractSpikeRecordable
from spynnaker.pyNN.models.common.complicated_population_settable import \
    ComplicatedPopulationSettable
from spynnaker.pyNN.models.common.multi_spike_recorder \
    import MultiSpikeRecorder
from spynnaker.pyNN.models.spike_source.spike_source_poisson_machine_vertex \
    import SpikeSourcePoissonMachineVertex
from spynnaker.pyNN.models.neural_properties.randomDistributions import \
    generate_parameter
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.utilities.conf import config

import logging
import math
import random
import scipy.stats
import numpy

logger = logging.getLogger(__name__)

# has key, key, random backoff, time_between_spikes, n_sources,
# seconds_per_timestep, timesteps_per_second, slow_rate_tick_cutoff
PARAMS_BASE_WORDS = 8

# start_scaled, end_scaled, is_fast_source, exp_minus_lambda, isi_val,
# time_to_spike
PARAMS_WORDS_PER_NEURON = 6

# seed1, seed2, seed3, seed4
RANDOM_SEED_WORDS = 4

# has key, key, random_back off, seed1, seed2, seed3 , seed4,
# n_sources, seconds_per_timestep, timesteps_per_second, slow_rate_tick_cutoff
START_OF_POISSON_GENERATOR_PARAMETERS = 11 * 4
MICROSECONDS_PER_SECOND = 1000000.0
MICROSECONDS_PER_MILLISECOND = 1000.0
DEFAULT_TIME_TO_SPIKE_VALUE = 0x0
SLOW_RATE_PER_TICK_CUTOFF = 1.0


class SpikeSourcePoisson(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary, AbstractSpikeRecordable,
        AbstractProvidesOutgoingPartitionConstraints,
    AbstractChangableAfterRun, ComplicatedPopulationSettable,
    AbstractBinaryUsesSimulationRun,
    AbstractRequiresRewriteDataRegionsApplicationVertex):
    """ A Poisson Spike source object
    """
    _DEFAULT_MALLOCS_USED = 2

    # data elements from the c struct
    DATA_POSITIONS_IN_STRUCT = Enum(
        value="DATA_POSITIONS_IN_STRUCT",
        names=[('START_SCALED', 0),
               ('END_SCALED', 1),
               ('IS_FAST_SOURCE', 2),
               ('EXP_MINUS_LAMDA', 3),
               ('ISI_VAL', 4),
               ('TIME_TO_SPIKE', 5)])

    # map from struct values to datatypes
    DATA_FORMATS_IN_STRUCT = {
        DATA_POSITIONS_IN_STRUCT.START_SCALED.value: DataType.UINT32,
        DATA_POSITIONS_IN_STRUCT.END_SCALED.value: DataType.UINT32,
        DATA_POSITIONS_IN_STRUCT.IS_FAST_SOURCE.value: DataType.UINT32,
        DATA_POSITIONS_IN_STRUCT.EXP_MINUS_LAMDA.value: DataType.U032,
        DATA_POSITIONS_IN_STRUCT.ISI_VAL.value: DataType.S1615,
        DATA_POSITIONS_IN_STRUCT.TIME_TO_SPIKE.value: DataType.S1615
    }

    # Technically, this is ~2900 in terms of DTCM, but is timescale dependent
    # in terms of CPU (2900 at 10 times slow down is fine, but not at
    # real-time)
    _model_based_max_atoms_per_core = 500

    # A count of the number of poisson vertices, to work out the random
    # back off range
    _n_poisson_machine_vertices = 0

    def __init__(
            self, n_neurons, constraints=None, label="SpikeSourcePoisson",
            rate=1.0, start=0.0, duration=None, seed=None):
        ApplicationVertex.__init__(
            self, label, constraints, self._model_based_max_atoms_per_core)
        AbstractSpikeRecordable.__init__(self)
        AbstractProvidesOutgoingPartitionConstraints.__init__(self)
        AbstractChangableAfterRun.__init__(self)
        ComplicatedPopulationSettable.__init__(self)
        AbstractRequiresRewriteDataRegionsApplicationVertex.__init__(self)

        # atoms params
        self._n_atoms = n_neurons
        self._seed = None

        # check for changes parameters
        self._change_requires_mapping = True
        self._change_requires_neuron_parameters_reload = False

        # Store the parameters
        self._rate = utility_calls.convert_param_to_numpy(rate, n_neurons)
        self._start = utility_calls.convert_param_to_numpy(start, n_neurons)
        self._duration = utility_calls.convert_param_to_numpy(
            duration, n_neurons)
        self._rng = numpy.random.RandomState(seed)
        self._time_to_spike = utility_calls.convert_param_to_numpy(
            DEFAULT_TIME_TO_SPIKE_VALUE, n_neurons)

        # Prepare for recording, and to get spikes
        self._spike_recorder = MultiSpikeRecorder()
        self._time_between_requests = config.getint(
            "Buffers", "time_between_requests")
        self._receive_buffer_host = config.get(
            "Buffers", "receive_buffer_host")
        self._receive_buffer_port = helpful_functions.read_config_int(
            config, "Buffers", "receive_buffer_port")
        self._minimum_buffer_sdram = config.getint(
            "Buffers", "minimum_buffer_sdram")
        self._using_auto_pause_and_resume = config.getboolean(
            "Buffers", "use_auto_pause_and_resume")

        spike_buffer_max_size = 0
        self._buffer_size_before_receive = 0
        if config.getboolean("Buffers", "enable_buffered_recording"):
            spike_buffer_max_size = config.getint(
                "Buffers", "spike_buffer_size")
            self._buffer_size_before_receive = config.getint(
                "Buffers", "buffer_size_before_receive")
        self._maximum_sdram_for_buffering = [spike_buffer_max_size]

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self._change_requires_mapping

    @overrides(AbstractRequiresRewriteDataRegionsApplicationVertex.
               mark_regions_reloaded)
    def mark_regions_reloaded(self):
        self._change_requires_neuron_parameters_reload = False

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        self._change_requires_mapping = False

    def set_value(self, key, value):
        ComplicatedPopulationSettable.set_value(self, key, value)
        self._change_requires_neuron_parameters_reload = True

    def _max_spikes_per_ts(
            self, vertex_slice, n_machine_time_steps, machine_time_step):
        max_rate = numpy.amax(
            self._rate[vertex_slice.lo_atom:vertex_slice.hi_atom + 1])
        ts_per_second = MICROSECONDS_PER_SECOND / machine_time_step
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

        # build resources as i currently know
        container = ResourceContainer(
            sdram=SDRAMResource(self.get_sdram_usage_for_atoms(vertex_slice)),
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms()),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms()))

        recording_sizes = recording_utilities.get_recording_region_sizes(
            [self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._max_spikes_per_ts(
                    vertex_slice, n_machine_time_steps, machine_time_step),
                1)],
            n_machine_time_steps, self._minimum_buffer_sdram,
            self._maximum_sdram_for_buffering,
            self._using_auto_pause_and_resume)
        container.extend(recording_utilities.get_recording_resources(
            recording_sizes, self._receive_buffer_host,
            self._receive_buffer_port))
        return container

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
        SpikeSourcePoisson._n_poisson_machine_vertices += 1
        buffered_sdram_per_timestep =\
            self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._max_spikes_per_ts(
                    vertex_slice, n_machine_time_steps, machine_time_step), 1)
        minimum_buffer_sdram = recording_utilities.get_minimum_buffer_sdram(
            [buffered_sdram_per_timestep], n_machine_time_steps,
            self._minimum_buffer_sdram)
        vertex = SpikeSourcePoissonMachineVertex(
            resources_required, self._spike_recorder.record,
            minimum_buffer_sdram[0], buffered_sdram_per_timestep,
            constraints, label)

        # return the machine vertex
        return vertex

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, rate):
        self._rate = utility_calls.convert_param_to_numpy(rate, self._n_atoms)

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = utility_calls.convert_param_to_numpy(
            start, self._n_atoms)

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, duration):
        self._duration = utility_calls.convert_param_to_numpy(
            duration, self._n_atoms)

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
                (vertex_slice.n_atoms * PARAMS_WORDS_PER_NEURON)) * 4

    def reserve_memory_regions(self, spec, placement, graph_mapper):
        """ Reserve memory regions for poisson source parameters and output\
            buffer.
        :param spec: the data specification writer
        :param placement: the location this vertex resides on in the machine
        :param graph_mapper: the mapping between app and machine graphs
        :return: None
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=(
                SpikeSourcePoissonMachineVertex.
                    POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value),
            size=front_end_common_constants.SYSTEM_BYTES_REQUIREMENT,
            label='setup')

        # reserve poisson params dsg region
        self._reserve_poisson_params_region(placement, graph_mapper, spec)

        spec.reserve_memory_region(
            region=(
                SpikeSourcePoissonMachineVertex.POISSON_SPIKE_SOURCE_REGIONS.
                    SPIKE_HISTORY_REGION.value),
            size=recording_utilities.get_recording_header_size(1),
            label="Recording")
        placement.vertex.reserve_provenance_data_region(spec)

    def _reserve_poisson_params_region(self, placement, graph_mapper, spec):
        """ does the allocation for the poisson params region itself, as
        it can be reused for setters after an initial run

        :param placement: the location on machine for this vertex
        :param graph_mapper: the mapping between machine and application graphs
        :param spec: the dsg writer
        :return:  None
        """
        spec.reserve_memory_region(
            region=(
                SpikeSourcePoissonMachineVertex.
                    POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION.value),
            size=self.get_params_bytes(graph_mapper.get_slice(
                placement.vertex)), label='PoissonParams')

    def _write_poisson_parameters(
            self, spec, key, vertex_slice, machine_time_step,
            time_scale_factor):
        """ Generate Neuron Parameter data for Poisson spike sources

        :param spec: the data specification writer
        :param key: the routing key for this vertex
        :param vertex_slice: the slice of atoms this machine vertex holds
        from its application vertex
        :param machine_time_step: the time between timer tick updates.
        :param time_scale_factor: the scaling between machine time step and
        real time
        :return: None
        """
        spec.comment("\nWriting Neuron Parameters for {} poisson sources:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            region=(
                SpikeSourcePoissonMachineVertex.
                    POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION.value))

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
        spec.write_value(random.randint(0, self._n_poisson_machine_vertices))

        # Write the number of microseconds between sending spikes
        total_mean_rate = numpy.sum(self._rate)
        max_spikes = scipy.stats.poisson.ppf(
            1.0 - (1.0 / total_mean_rate), total_mean_rate)
        spikes_per_timestep = (
            max_spikes / (MICROSECONDS_PER_SECOND / machine_time_step))
        time_between_spikes = (
            (machine_time_step * time_scale_factor) /
            (spikes_per_timestep * 2.0))
        spec.write_value(data=int(time_between_spikes))

        # Write the random seed (4 words), generated randomly!
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))

        # Write the number of sources
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the number of seconds per timestep (unsigned long fract)
        spec.write_value(
            data=float(machine_time_step) / MICROSECONDS_PER_SECOND,
            data_type=DataType.U032)

        # Write the number of timesteps per second (accum)
        spec.write_value(
            data=MICROSECONDS_PER_SECOND / float(machine_time_step),
            data_type=DataType.S1615)

        # Write the slow-rate-per-tick-cutoff (accum)
        spec.write_value(data=SLOW_RATE_PER_TICK_CUTOFF,
                         data_type=DataType.S1615)

        # For each neuron, get the rate to work out if it is a slow
        # or fast source
        for i in range(vertex_slice.n_atoms):

            atom_id = vertex_slice.lo_atom + i

            # Get the parameter values for source i:
            rate_val = generate_parameter(self._rate, atom_id)
            start_val = generate_parameter(self._start, atom_id)
            start_scaled = self._convert_ms_to_n_timesteps(
                start_val, machine_time_step)
            end_scaled = 0xFFFFFFFF
            if (self._duration[atom_id] is not None and
                    not math.isnan(self._duration[atom_id])):
                end_val = generate_parameter(
                    self._duration, atom_id) + start_val
                end_scaled = self._convert_ms_to_n_timesteps(
                    end_val, machine_time_step)

            # Decide if it is a fast or slow source and
            spikes_per_tick = \
                (float(rate_val) * (machine_time_step /
                                    MICROSECONDS_PER_SECOND))
            if spikes_per_tick == 0:
                exp_minus_lamda = 0
            else:
                exp_minus_lamda = math.exp(-1.0 * spikes_per_tick)

            is_fast_source = 1
            if spikes_per_tick <= SLOW_RATE_PER_TICK_CUTOFF:
                is_fast_source = 0

            if rate_val == 0:
                isi_val = 0
            else:
                isi_val = float(MICROSECONDS_PER_SECOND /
                                (rate_val * machine_time_step))

            spec.write_value(
                data=start_scaled,
                data_type=self.DATA_FORMATS_IN_STRUCT[
                    self.DATA_POSITIONS_IN_STRUCT.START_SCALED.value])
            spec.write_value(
                data=end_scaled,
                data_type=self.DATA_FORMATS_IN_STRUCT[
                    self.DATA_POSITIONS_IN_STRUCT.END_SCALED.value])
            spec.write_value(
                data=is_fast_source,
                data_type=self.DATA_FORMATS_IN_STRUCT[
                    self.DATA_POSITIONS_IN_STRUCT.IS_FAST_SOURCE.value])
            spec.write_value(
                data=exp_minus_lamda,
                data_type=self.DATA_FORMATS_IN_STRUCT[
                    self.DATA_POSITIONS_IN_STRUCT.EXP_MINUS_LAMDA.value])
            spec.write_value(
                data=isi_val,
                data_type=self.DATA_FORMATS_IN_STRUCT[
                    self.DATA_POSITIONS_IN_STRUCT.ISI_VAL.value])
            spec.write_value(
                data=self._time_to_spike[i],
                data_type=self.DATA_FORMATS_IN_STRUCT[
                    self.DATA_POSITIONS_IN_STRUCT.TIME_TO_SPIKE.value])

    @staticmethod
    def _convert_ms_to_n_timesteps(value, machine_time_step):
        return int(value * MICROSECONDS_PER_MILLISECOND / machine_time_step)

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self._spike_recorder.record

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(self):
        self._spike_recorder.record = True

    def get_sdram_usage_for_atoms(self, vertex_slice):
        poisson_params_sz = self.get_params_bytes(vertex_slice)
        total_size = \
            (front_end_common_constants.SYSTEM_BYTES_REQUIREMENT +
             SpikeSourcePoissonMachineVertex.get_provenance_data_size(0) +
             poisson_params_sz)
        total_size += self._get_number_of_mallocs_used_by_dsg() * \
            front_end_common_constants.SARK_PER_MALLOC_SDRAM_USAGE
        return total_size

    def _get_number_of_mallocs_used_by_dsg(self):
        standard_mallocs = self._DEFAULT_MALLOCS_USED
        if self._spike_recorder.record:
            standard_mallocs += 1
        return standard_mallocs

    @staticmethod
    def get_dtcm_usage_for_atoms():
        return 0

    @staticmethod
    def get_cpu_usage_for_atoms():
        return 0

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "routing_info": "MemoryRoutingInfos"})
    @overrides(
        AbstractRequiresRewriteDataRegionsApplicationVertex.
            regions_and_data_spec_to_rewrite,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "routing_info"})
    def regions_and_data_spec_to_rewrite(
            self, placement, hostname, report_directory, write_text_specs,
            reload_application_data_file_path, graph_mapper,
            machine_time_step, time_scale_factor, routing_info):
        """ returns the data region and its data that needs loading

        :return: dict of data region id and the byte array to load there.
        """

        # store for more regions as needed
        regions_and_data = dict()

        # if the neuron parameters need changing, generate dsg for neuron
        # params
        if self._change_requires_neuron_parameters_reload:
            # get new dsg writer
            file_path, spec = \
                dsg_utilities.get_data_spec_and_file_writer_filename(
                    placement.x, placement.y, placement.p,
                    hostname, report_directory, write_text_specs,
                    reload_application_data_file_path)

            # reserve the neuron parameters data region
            self._reserve_poisson_params_region(placement, graph_mapper, spec)

            # allocate parameters
            self._write_poisson_parameters(
                key=routing_info.get_first_key_from_pre_vertex(
                    placement.vertex, constants.SPIKE_PARTITION_ID),
                spec=spec,
                vertex_slice=graph_mapper.get_slice(placement.vertex),
                machine_time_step=machine_time_step,
                time_scale_factor=time_scale_factor)

            # end spec
            spec.end_specification()

            # store dsg region to spec data mapping
            regions_and_data[
                constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value] = \
                file_path

        # return mappings
        return regions_and_data

    def read_neuron_parameters_from_machine(
            self, transceiver, placement, vertex_slice):
        """ reads in the poisson parameters from the machine and stores them
        in the neuron components.

        :param transceiver: the spinnman interface
        :param placement: the placement of the vertex
        :param vertex_slice: the slice of a application vertex that this
        machine vertex uses.
        :return: None
        """

        # locate sdram address to where the neuron parameters are stored
        poisson_parameter_region_sdram_address = \
            helpful_functions.locate_memory_region_for_placement(
                placement,
                SpikeSourcePoissonMachineVertex.POISSON_SPIKE_SOURCE_REGIONS.
                    POISSON_PARAMS_REGION.value, transceiver)

        # shift past the extra stuff before neuron parameters that we don't
        # need to read
        poisson_parameter_parameters_sdram_address = \
            poisson_parameter_region_sdram_address + \
            START_OF_POISSON_GENERATOR_PARAMETERS

        # get size of poisson params
        size_of_region = self.get_params_bytes(vertex_slice)
        size_of_region -= START_OF_POISSON_GENERATOR_PARAMETERS

        # get data from the machine
        byte_array = transceiver.read_memory(
            placement.x, placement.y,
            poisson_parameter_parameters_sdram_address, size_of_region)

        # update python neuron parameters with the data
        for atom, position in zip(
                range(vertex_slice.lo_atom, vertex_slice.hi_atom),
                range(0, len(byte_array), PARAMS_WORDS_PER_NEURON * 4)):
            # only need to translate rate, start, duration, and time_to_spike,
            # rest are constant during a run, or calculated during next run

            # time to spike
            self._rate[atom] = self._translate_isi_value_to_rate(
                struct.unpack_from(
                    self.DATA_FORMATS_IN_STRUCT[
                        self.DATA_POSITIONS_IN_STRUCT.TIME_TO_SPIKE.value].
                        struct_encoding,
                    byte_array, position + (
                            self.DATA_POSITIONS_IN_STRUCT.isi_val.value * 4)))

    @overrides(
        AbstractRequiresRewriteDataRegionsApplicationVertex.
            requires_memory_regions_to_be_reloaded)
    def requires_memory_regions_to_be_reloaded(self):
        return self._change_requires_neuron_parameters_reload

    def _translate_isi_value_to_rate(self, isi_value):
        if isi_value == 0:
            return 0
        else:
            return ((self.MICROSECONDS_PER_MILLISECOND / isi_value) /
                    self._machine_time_step)

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

        spec.comment("\n*** Spec for SpikeSourcePoisson Instance ***\n\n")

        # Reserve SDRAM space for memory areas:
        self.reserve_memory_regions(spec, placement, graph_mapper)

        # write setup data
        spec.switch_write_focus(
            SpikeSourcePoissonMachineVertex.
                POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name(), machine_time_step,
            time_scale_factor))

        # write recording data
        ip_tags = tags.get_ip_tags_for_vertex(vertex)
        spec.switch_write_focus(
            SpikeSourcePoissonMachineVertex.POISSON_SPIKE_SOURCE_REGIONS
            .SPIKE_HISTORY_REGION.value)
        recorded_region_sizes = recording_utilities.get_recorded_region_sizes(
            n_machine_time_steps,
            [self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._max_spikes_per_ts(
                    vertex_slice, n_machine_time_steps, machine_time_step),
                1)],
            self._maximum_sdram_for_buffering)
        spec.write_array(recording_utilities.get_recording_header_array(
            recorded_region_sizes, self._time_between_requests,
            self._buffer_size_before_receive, ip_tags))

        # write parameters
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
            self._label, buffer_manager, 0,
            placements, graph_mapper, self, machine_time_step)

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [KeyAllocatorContiguousRangeContraint()]
