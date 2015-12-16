from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint

from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.neural_properties.randomDistributions\
    import generate_parameter
from spynnaker.pyNN.models.common.abstract_spike_recordable \
    import AbstractSpikeRecordable
from spynnaker.pyNN.models.common.simple_population_settable \
    import SimplePopulationSettable
from spynnaker.pyNN.models.common.spike_recorder import SpikeRecorder
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN.utilities import utility_calls

from spinn_front_end_common.abstract_models.abstract_data_specable_vertex\
    import AbstractDataSpecableVertex
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_edge_constraints import \
    AbstractProvidesOutgoingEdgeConstraints
from spinn_front_end_common.\
    abstract_models.abstract_uses_memory_mallocs import \
    AbstractPartitionableUsesMemoryMallocs
from spinn_front_end_common.utilities import constants as\
    front_end_common_constants
from spinn_front_end_common.interface.buffer_management\
    .buffer_models.abstract_receive_buffers_to_host \
    import AbstractReceiveBuffersToHost
from spinn_front_end_common.utilities import helpful_functions

from data_specification.data_specification_generator\
    import DataSpecificationGenerator
from data_specification.enums.data_type import DataType

from enum import Enum
import math
import numpy
import logging

logger = logging.getLogger(__name__)

SLOW_RATE_PER_TICK_CUTOFF = 1.0
PARAMS_BASE_WORDS = 4
PARAMS_WORDS_PER_NEURON = 6
RANDOM_SEED_WORDS = 4


class SpikeSourcePoisson(
        AbstractPartitionableVertex, AbstractDataSpecableVertex,
        AbstractSpikeRecordable, AbstractProvidesOutgoingEdgeConstraints,
        SimplePopulationSettable,
        AbstractPartitionableUsesMemoryMallocs,
        AbstractReceiveBuffersToHost):
    """A Poisson Spike source object
    """

    _POISSON_SPIKE_SOURCE_REGIONS = Enum(
        value="_POISSON_SPIKE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('POISSON_PARAMS_REGION', 1),
               ('SPIKE_HISTORY_REGION', 2),
               ('BUFFERING_OUT_STATE', 3)])

    _N_POPULATION_RECORDING_REGIONS = 1
    _DEFAULT_MALLOCS_USED = 2

    # Technically, this is ~2900 in terms of DTCM, but is timescale dependent
    # in terms of CPU (2900 at 10 times slow down is fine, but not at
    # real-time)
    _model_based_max_atoms_per_core = 500

    def __init__(
            self, n_neurons, machine_time_step, timescale_factor,
            constraints=None, label="SpikeSourcePoisson", rate=1.0, start=0.0,
            duration=None, seed=None):
        """
        Creates a new SpikeSourcePoisson Object.
        """
        AbstractPartitionableVertex.__init__(
            self, n_atoms=n_neurons, label=label, constraints=constraints,
            max_atoms_per_core=self._model_based_max_atoms_per_core)
        AbstractDataSpecableVertex.__init__(
            self, machine_time_step=machine_time_step,
            timescale_factor=timescale_factor)
        AbstractSpikeRecordable.__init__(self)
        AbstractReceiveBuffersToHost.__init__(self)
        AbstractProvidesOutgoingEdgeConstraints.__init__(self)
        SimplePopulationSettable.__init__(self)
        AbstractPartitionableUsesMemoryMallocs.__init__(self)

        # Store the parameters
        self._rate = rate
        self._start = start
        self._duration = duration
        self._rng = numpy.random.RandomState(seed)

        # Prepare for recording, and to get spikes
        self._spike_recorder = SpikeRecorder(machine_time_step)
        self._spike_buffer_max_size = config.getint(
            "Buffers", "spike_buffer_size")
        self._buffer_size_before_receive = config.getint(
            "Buffers", "buffer_size_before_receive")
        self._time_between_requests = config.getint(
            "Buffers", "time_between_requests")

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

    @property
    def model_name(self):
        """
        Return a string representing a label for this class.
        """
        return "SpikeSourcePoisson"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        """

        :param new_value:
        :return:
        """
        SpikeSourcePoisson._model_based_max_atoms_per_core = new_value

    @staticmethod
    def get_params_bytes(vertex_slice):
        """
        Gets the size of the poisson parameters in bytes
        :param vertex_slice:
        """
        return (RANDOM_SEED_WORDS + PARAMS_BASE_WORDS +
                (((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1) *
                 PARAMS_WORDS_PER_NEURON)) * 4

    def reserve_memory_regions(self, spec, setup_sz, poisson_params_sz,
                               spike_hist_buff_sz):
        """
        Reserve memory regions for poisson source parameters
        and output buffer.
        :param spec:
        :param setup_sz:
        :param poisson_params_sz:
        :param spike_hist_buff_sz:
        :return:
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=self._POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value,
            size=setup_sz, label='setup')
        spec.reserve_memory_region(
            region=self._POISSON_SPIKE_SOURCE_REGIONS
                       .POISSON_PARAMS_REGION.value,
            size=poisson_params_sz, label='PoissonParams')
        self.reserve_buffer_regions(
            spec, self._POISSON_SPIKE_SOURCE_REGIONS.BUFFERING_OUT_STATE.value,
            [self._POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value],
            [spike_hist_buff_sz])

    def _write_setup_info(
            self, spec, spike_history_region_sz, ip_tags,
            buffer_size_before_receive):
        """ Write information used to control the simulation and gathering of\
            results.
        :param spec:
        :param spike_history_region_sz:
        :param ip_rags
        :return:
        """

        self._write_basic_setup_info(
            spec, self._POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value)
        self.write_recording_data(
            spec, ip_tags, [spike_history_region_sz],
            buffer_size_before_receive, self._time_between_requests)

    def _write_poisson_parameters(self, spec, key, num_neurons):
        """
        Generate Neuron Parameter data for Poisson spike sources (region 2):
        :param spec:
        :param key:
        :param num_neurons:
        :return:
        """
        spec.comment("\nWriting Neuron Parameters for {} poisson sources:\n"
                     .format(num_neurons))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            region=self._POISSON_SPIKE_SOURCE_REGIONS
                       .POISSON_PARAMS_REGION.value)

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

        # Write the random seed (4 words), generated randomly!
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))

        spec.write_value(data=num_neurons)

        # For each neuron, get the rate to work out if it is a slow
        # or fast source
        for i in range(0, num_neurons):
            start_scaled, end_scaled, is_fast_source, exp_minus_lamda, isi_val = \
                self.generate_poisson_parameters(i)

            spec.write_value(data=start_scaled, data_type=DataType.UINT32)
            spec.write_value(data=end_scaled, data_type=DataType.UINT32)
            spec.write_value(data=is_fast_source, data_type=DataType.UINT32)
            spec.write_value(data=exp_minus_lamda, data_type=DataType.U032)
            spec.write_value(data=isi_val, data_type=DataType.S1615)
            spec.write_value(data=0x0, data_type=DataType.UINT32)

    def generate_poisson_parameters(self, neuron_id):
       # Get the parameter values for source neuron_id:
        rate_val = generate_parameter(self._rate, neuron_id)
        start_val = generate_parameter(self._start, neuron_id)
        start_scaled = int(start_val * 1000.0 / self._machine_time_step)
        end_val = None
        end_scaled = 0xFFFFFFF
        if self._duration is not None:
            end_val = generate_parameter(self._duration, neuron_id) + start_val
            end_scaled = int(end_val * 1000.0 / self._machine_time_step)

        # Decide if it is a fast or slow source and
        spikes_per_tick = \
            (float(rate_val) * (self._machine_time_step / 1000000.0))
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
            isi_val = float(1000000.0 /
                            (rate_val * self._machine_time_step))

        return start_scaled, end_scaled, is_fast_source, exp_minus_lamda, isi_val

    # @implements AbstractPopulationSettable.update_parameters
    def update_parameters(self, txrx, vertex_slice, placement):
        region = self._POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION.value
        address = helpful_functions.get_region_address(region, placement, txrx)

        # skip key, seed and num_neurons
        address += 28

        data = bytearray()

        for i in range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1):
            start_scaled, end_scaled, is_fast_source, exp_minus_lamda, isi_val = \
                self.generate_poisson_parameters(i)

            data += utility_calls.convert_value(start_scaled, DataType.UINT32)
            data += utility_calls.convert_value(end_scaled, DataType.UINT32)
            data += utility_calls.convert_value(is_fast_source, DataType.UINT32)
            data += utility_calls.convert_value(exp_minus_lamda, DataType.U032)
            data += utility_calls.convert_value(isi_val, DataType.S1615)
            data += utility_calls.convert_value(0x0, DataType.UINT32)

        txrx.write_memory(placement.x, placement.y, address, data)

    # @implements AbstractSpikeRecordable.is_recording_spikes
    def is_recording_spikes(self):
        return self._spike_recorder.record

    # @implements AbstractSpikeRecordable.set_recording_spikes
    def set_recording_spikes(self):
        ip_address = config.get("Buffers", "receive_buffer_host")
        port = config.getint("Buffers", "receive_buffer_port")
        self.set_buffering_output(ip_address, port)
        self._spike_recorder.record = True

    # inherited from partitionable vertex
    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """
        method for calculating SDRAM usage
        :param vertex_slice:
        :param graph:
        :return:
        """
        poisson_params_sz = self.get_params_bytes(vertex_slice)
        spike_hist_buff_sz = min((
            self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._no_machine_time_steps),
            self._spike_buffer_max_size))
        total_size = \
            ((constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS * 4) +
             self.get_recording_data_size(1) +
             self.get_buffer_state_region_size(1) +
             poisson_params_sz + spike_hist_buff_sz)
        total_size += self.get_number_of_mallocs_used_by_dsg(
            vertex_slice, graph.incoming_edges_to_vertex(self)) * \
            front_end_common_constants.SARK_PER_MALLOC_SDRAM_USAGE
        return total_size

    def get_number_of_mallocs_used_by_dsg(self, vertex_slice, in_edges):
        standard_mallocs = self._DEFAULT_MALLOCS_USED
        if self._spike_recorder.record:
            standard_mallocs += 1
        if config.getboolean("SpecExecution", "specExecOnHost"):
            return 1
        else:
            return standard_mallocs

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """
        method for calculating DTCM usage for a collection of atoms
        :param vertex_slice:
        :param graph:
        :return:
        """
        return 0

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """
        Gets the CPU requirements for a range of atoms

        :param vertex_slice:
        :param graph:
        :return:
        """
        return 0

    # inherited from dataspecable vertex
    def generate_data_spec(self, subvertex, placement, subgraph, graph,
                           routing_info, hostname, graph_mapper, report_folder,
                           ip_tags, reverse_ip_tags, write_text_specs,
                           application_run_time_folder):
        """
        Model-specific construction of the data blocks necessary to build a
        single SpikeSourcePoisson on one core.
        :param subvertex:
        :param placement:
        :param subgraph:
        :param graph:
        :param routing_info:
        :param hostname:
        :param graph_mapper:
        :param report_folder:
        :param ip_tags:
        :param reverse_ip_tags:
        :param write_text_specs:
        :param application_run_time_folder:
        :return:
        """
        data_writer, report_writer = \
            self.get_data_spec_file_writers(
                placement.x, placement.y, placement.p, hostname, report_folder,
                write_text_specs, application_run_time_folder)

        spec = DataSpecificationGenerator(data_writer, report_writer)

        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)

        spike_hist_buff_sz = self._spike_recorder.get_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self._no_machine_time_steps)
        buffer_size_before_receive = self._buffer_size_before_receive
        if config.getboolean("Buffers", "enable_buffered_recording"):
            if spike_hist_buff_sz < self._spike_buffer_max_size:
                buffer_size_before_receive = spike_hist_buff_sz + 256
            else:
                spike_hist_buff_sz = self._spike_buffer_max_size
        else:
            buffer_size_before_receive = spike_hist_buff_sz + 256

        spec.comment("\n*** Spec for SpikeSourcePoisson Instance ***\n\n")

        # Basic setup plus 8 bytes for recording flags and recording size
        setup_sz = ((constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS * 4) +
                    self.get_recording_data_size(1))

        poisson_params_sz = self.get_params_bytes(vertex_slice)

        # Reserve SDRAM space for memory areas:
        self.reserve_memory_regions(
            spec, setup_sz, poisson_params_sz, spike_hist_buff_sz)

        self._write_setup_info(
            spec, spike_hist_buff_sz, ip_tags, buffer_size_before_receive)

        # Every subedge should have the same key
        key = None
        subedges = subgraph.outgoing_subedges_from_subvertex(subvertex)
        if len(subedges) > 0:
            keys_and_masks = routing_info.get_keys_and_masks_from_subedge(
                subedges[0])
            key = keys_and_masks[0].key

        self._write_poisson_parameters(spec, key, vertex_slice.n_atoms)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

        return [data_writer.filename]

    def get_binary_file_name(self):
        """

        :return:
        """
        return "spike_source_poisson.aplx"

    def get_spikes(self, placements, graph_mapper, buffer_manager):
        return self._spike_recorder.get_spikes(
            self._label, buffer_manager,
            self._POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value,
            self._POISSON_SPIKE_SOURCE_REGIONS.BUFFERING_OUT_STATE.value,
            placements, graph_mapper, self)

    def get_outgoing_edge_constraints(self, partitioned_edge, graph_mapper):
        """
        gets the constraints for edges going out of this vertex
        :param partitioned_edge: the partitioned edge that leaves this vertex
        :param graph_mapper: the graph mapper object
        :return: list of constraints
        """
        return [KeyAllocatorContiguousRangeContraint()]

    def is_data_specable(self):
        """
        helper method for isinstance
        :return:
        """
        return True

    def is_receives_buffers_to_host(self):
        return True
