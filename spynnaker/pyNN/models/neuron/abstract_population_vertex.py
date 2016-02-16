
# pacman imports
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint

# front end common imports
from spinn_front_end_common.abstract_models.\
    abstract_provides_incoming_partition_constraints import \
    AbstractProvidesIncomingPartitionConstraints
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_partition_constraints import \
    AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.utilities import constants as \
    common_constants
from spinn_front_end_common.interface.buffer_management\
    .buffer_models.receives_buffers_to_host_basic_impl \
    import ReceiveBuffersToHostBasicImpl
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex

# spynnaker imports
from spynnaker.pyNN.models.neuron.synaptic_manager import SynapticManager
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.common import recording_utils
from spynnaker.pyNN.models.abstract_models.abstract_population_initializable \
    import AbstractPopulationInitializable
from spynnaker.pyNN.models.abstract_models.abstract_population_settable \
    import AbstractPopulationSettable
from spynnaker.pyNN.models.abstract_models.abstract_mappable \
    import AbstractMappable
from spynnaker.pyNN.models.common.abstract_spike_recordable \
    import AbstractSpikeRecordable
from spynnaker.pyNN.models.common.abstract_v_recordable \
    import AbstractVRecordable
from spynnaker.pyNN.models.common.abstract_gsyn_recordable \
    import AbstractGSynRecordable
from spynnaker.pyNN.models.common.spike_recorder import SpikeRecorder
from spynnaker.pyNN.models.common.v_recorder import VRecorder
from spynnaker.pyNN.models.common.gsyn_recorder import GsynRecorder
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN.models.neuron.population_partitioned_vertex \
    import PopulationPartitionedVertex

# dsg imports
from data_specification.data_specification_generator \
    import DataSpecificationGenerator
from data_specification.utility_calls \
    import get_region_base_address_offset

from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint

from abc import ABCMeta
from six import add_metaclass
import logging
import os
import numpy
import struct

logger = logging.getLogger(__name__)

# TODO: Make sure these values are correct (particularly CPU cycles)
_NEURON_BASE_DTCM_USAGE_IN_BYTES = 36
_NEURON_BASE_SDRAM_USAGE_IN_BYTES = 12
_NEURON_BASE_N_CPU_CYCLES_PER_NEURON = 22
_NEURON_BASE_N_CPU_CYCLES = 10

# TODO: Make sure these values are correct (particularly CPU cycles)
_C_MAIN_BASE_DTCM_USAGE_IN_BYTES = 12
_C_MAIN_BASE_SDRAM_USAGE_IN_BYTES = 72
_C_MAIN_BASE_N_CPU_CYCLES = 0

# Define profiler time scale
MS_SCALE = (1.0 / 200032.4)


@add_metaclass(ABCMeta)
class AbstractPopulationVertex(
        AbstractPartitionableVertex, AbstractDataSpecableVertex,
        AbstractSpikeRecordable, AbstractVRecordable, AbstractGSynRecordable,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractProvidesIncomingPartitionConstraints,
        AbstractPopulationInitializable, AbstractPopulationSettable,
        AbstractMappable):
    """ Underlying vertex model for Neural Populations.
    """

    def __init__(
            self, n_neurons, binary, label, max_atoms_per_core,
            machine_time_step, timescale_factor, spikes_per_second,
            ring_buffer_sigma, incoming_spike_buffer_size, model_name,
            neuron_model, input_type, synapse_type, threshold_type,
            additional_input=None, constraints=None):

        AbstractPartitionableVertex.__init__(
            self, n_neurons, label, max_atoms_per_core, constraints)
        AbstractDataSpecableVertex.__init__(
            self, machine_time_step, timescale_factor)
        AbstractSpikeRecordable.__init__(self)
        AbstractVRecordable.__init__(self)
        AbstractGSynRecordable.__init__(self)
        AbstractProvidesOutgoingPartitionConstraints.__init__(self)
        AbstractProvidesIncomingPartitionConstraints.__init__(self)
        AbstractPopulationInitializable.__init__(self)
        AbstractPopulationSettable.__init__(self)
        AbstractMappable.__init__(self)

        self._binary = binary
        self._label = label
        self._machine_time_step = machine_time_step
        self._timescale_factor = timescale_factor
        self._incoming_spike_buffer_size = incoming_spike_buffer_size
        if incoming_spike_buffer_size is None:
            self._incoming_spike_buffer_size = config.getint(
                "Simulation", "incoming_spike_buffer_size")

        self._model_name = model_name
        self._neuron_model = neuron_model
        self._input_type = input_type
        self._threshold_type = threshold_type
        self._additional_input = additional_input

        # Set up for recording
        self._spike_recorder = SpikeRecorder(machine_time_step)
        self._v_recorder = VRecorder(machine_time_step)
        self._gsyn_recorder = GsynRecorder(machine_time_step)
        self._spike_buffer_max_size = config.getint(
            "Buffers", "spike_buffer_size")
        self._v_buffer_max_size = config.getint(
            "Buffers", "v_buffer_size")
        self._gsyn_buffer_max_size = config.getint(
            "Buffers", "gsyn_buffer_size")
        self._buffer_size_before_receive = config.getint(
            "Buffers", "buffer_size_before_receive")
        self._time_between_requests = config.getint(
            "Buffers", "time_between_requests")
        self._minimum_buffer_sdram = config.getint(
            "Buffers", "minimum_buffer_sdram")
        self._using_auto_pause_and_resume = config.getboolean(
            "Buffers", "use_auto_pause_and_resume")
        self._receive_buffer_host = config.get(
            "Buffers", "receive_buffer_host")
        self._receive_buffer_port = config.getint(
            "Buffers", "receive_buffer_port")
        self._enable_buffered_recording = config.getboolean(
            "Buffers", "enable_buffered_recording")

        # Set up synapse handling
        self._synapse_manager = SynapticManager(
            synapse_type, machine_time_step, ring_buffer_sigma,
            spikes_per_second)

        # bool for if state has changed.
        self._change_requires_mapping = True

        # By default, profiling is disabled
        self.profiler_num_samples = 500

    @property
    def requires_mapping(self):
        return self._change_requires_mapping

    def mark_no_changes(self):
        self._change_requires_mapping = False

    def create_subvertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):

        subvertex = PopulationPartitionedVertex(
            resources_required, label, constraints)
        if not self._using_auto_pause_and_resume:
            spike_buffer_size = self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._no_machine_time_steps)
            v_buffer_size = self._v_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._no_machine_time_steps)
            gsyn_buffer_size = self._gsyn_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._no_machine_time_steps)
            spike_buffering_needed = recording_utils.needs_buffering(
                self._spike_buffer_max_size, spike_buffer_size,
                self._enable_buffered_recording)
            v_buffering_needed = recording_utils.needs_buffering(
                self._v_buffer_max_size, v_buffer_size,
                self._enable_buffered_recording)
            gsyn_buffering_needed = recording_utils.needs_buffering(
                self._gsyn_buffer_max_size, gsyn_buffer_size,
                self._enable_buffered_recording)
            if (spike_buffering_needed or v_buffering_needed or
                    gsyn_buffering_needed):
                subvertex.activate_buffering_output(
                    buffering_ip_address=self._receive_buffer_host,
                    buffering_port=self._receive_buffer_port)
        else:
            sdram_per_ts = 0
            sdram_per_ts += self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, 1)
            sdram_per_ts += self._v_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, 1)
            sdram_per_ts += self._gsyn_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, 1)
            subvertex.activate_buffering_output(
                minimum_sdram_for_buffering=self._minimum_buffer_sdram,
                buffered_sdram_per_timestep=sdram_per_ts)
        return subvertex

    @property
    def maximum_delay_supported_in_ms(self):
        return self._synapse_manager.maximum_delay_supported_in_ms

    # @implements AbstractPopulationVertex.get_cpu_usage_for_atoms
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        per_neuron_cycles = (
            _NEURON_BASE_N_CPU_CYCLES_PER_NEURON +
            self._neuron_model.get_n_cpu_cycles_per_neuron() +
            self._input_type.get_n_cpu_cycles_per_neuron(
                self._synapse_manager.synapse_type.get_n_synapse_types()) +
            self._threshold_type.get_n_cpu_cycles_per_neuron())
        if self._additional_input is not None:
            per_neuron_cycles += \
                self._additional_input.get_n_cpu_cycles_per_neuron()
        return (_NEURON_BASE_N_CPU_CYCLES +
                _C_MAIN_BASE_N_CPU_CYCLES +
                (per_neuron_cycles * vertex_slice.n_atoms) +
                self._spike_recorder.get_n_cpu_cycles(vertex_slice.n_atoms) +
                self._v_recorder.get_n_cpu_cycles(vertex_slice.n_atoms) +
                self._gsyn_recorder.get_n_cpu_cycles(vertex_slice.n_atoms) +
                self._synapse_manager.get_n_cpu_cycles(vertex_slice, graph))

    # @implements AbstractPopulationVertex.get_dtcm_usage_for_atoms
    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        per_neuron_usage = (
            self._neuron_model.get_dtcm_usage_per_neuron_in_bytes() +
            self._input_type.get_dtcm_usage_per_neuron_in_bytes() +
            self._threshold_type.get_dtcm_usage_per_neuron_in_bytes())
        if self._additional_input is not None:
            per_neuron_usage += \
                self._additional_input.get_dtcm_usage_per_neuron_in_bytes()
        return (_NEURON_BASE_DTCM_USAGE_IN_BYTES +
                (per_neuron_usage * vertex_slice.n_atoms) +
                self._spike_recorder.get_dtcm_usage_in_bytes() +
                self._v_recorder.get_dtcm_usage_in_bytes() +
                self._gsyn_recorder.get_dtcm_usage_in_bytes() +
                self._synapse_manager.get_dtcm_usage_in_bytes(
                    vertex_slice, graph))

    def _get_sdram_usage_for_neuron_params(self, vertex_slice):
        per_neuron_usage = (
            self._input_type.get_sdram_usage_per_neuron_in_bytes() +
            self._threshold_type.get_sdram_usage_per_neuron_in_bytes())
        if self._additional_input is not None:
            per_neuron_usage += \
                self._additional_input.get_sdram_usage_per_neuron_in_bytes()
        return ((common_constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS * 4) +
                ReceiveBuffersToHostBasicImpl.get_recording_data_size(3) +
                (per_neuron_usage * vertex_slice.n_atoms) +
                self._neuron_model.get_sdram_usage_in_bytes(
                    vertex_slice.n_atoms))

    # @implements AbstractPartitionableVertex.get_sdram_usage_for_atoms
    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        sdram_requirement = (
            self._get_sdram_usage_for_neuron_params(vertex_slice) +
            ReceiveBuffersToHostBasicImpl.get_buffer_state_region_size(3) +
            PopulationPartitionedVertex.get_provenance_data_size(
                PopulationPartitionedVertex
                .N_ADDITIONAL_PROVENANCE_DATA_ITEMS) +
            self._synapse_manager.get_sdram_usage_in_bytes(
                vertex_slice, graph.incoming_edges_to_vertex(self)) +
            (self._get_number_of_mallocs_used_by_dsg(
                vertex_slice, graph.incoming_edges_to_vertex(self)) *
             common_constants.SARK_PER_MALLOC_SDRAM_USAGE))

        # add recording SDRAM if not automatically calculated
        if not self._using_auto_pause_and_resume:
            spike_buffer_size = self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._no_machine_time_steps)
            v_buffer_size = self._v_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._no_machine_time_steps)
            gsyn_buffer_size = self._gsyn_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._no_machine_time_steps)
            sdram_requirement += recording_utils.get_buffer_sizes(
                self._spike_buffer_max_size, spike_buffer_size,
                self._enable_buffered_recording)
            sdram_requirement += recording_utils.get_buffer_sizes(
                self._v_buffer_max_size, v_buffer_size,
                self._enable_buffered_recording)
            sdram_requirement += recording_utils.get_buffer_sizes(
                self._gsyn_buffer_max_size, gsyn_buffer_size,
                self._enable_buffered_recording)
        else:
            sdram_requirement += self._minimum_buffer_sdram

        return sdram_requirement

    # @implements AbstractPopulationVertex.model_name
    def model_name(self):
        return self._model_name

    def _get_number_of_mallocs_used_by_dsg(self, vertex_slice, in_edges):
        extra_mallocs = 0
        if self._gsyn_recorder.record_gsyn:
            extra_mallocs += 1
        if self._v_recorder.record_v:
            extra_mallocs += 1
        if self._spike_recorder.record:
            extra_mallocs += 1
        return (
            2 + self._synapse_manager.get_number_of_mallocs_used_by_dsg() +
            extra_mallocs)

    def _get_number_of_mallocs_from_basic_model(self):

        # one for system, one for neuron params
        return 2

    def _reserve_memory_regions(
            self, spec, vertex_slice, spike_history_region_sz,
            v_history_region_sz, gsyn_history_region_sz, subvertex):

        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.SYSTEM.value,
            size=((
                common_constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS * 4) +
                subvertex.get_recording_data_size(3)), label='System')

        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value,
            size=self._get_sdram_usage_for_neuron_params(vertex_slice),
            label='NeuronParams')

        subvertex.reserve_buffer_regions(
            spec,
            constants.POPULATION_BASED_REGIONS.BUFFERING_OUT_STATE.value,
            [constants.POPULATION_BASED_REGIONS.SPIKE_HISTORY.value,
             constants.POPULATION_BASED_REGIONS.POTENTIAL_HISTORY.value,
             constants.POPULATION_BASED_REGIONS.GSYN_HISTORY.value],
            [spike_history_region_sz, v_history_region_sz,
             gsyn_history_region_sz])

        subvertex.reserve_provenance_data_region(spec)

        if self.profiler_num_samples != 0:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.PROFILING.value,
                size=(8 + (self.profiler_num_samples * 8)), label="profilerRegion")
        else:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.PROFILING.value,
                size=4, label="profilerRegion")

        
    def get_profiling_data(self, txrx, placements, graph_mapper):
        # Create a dictionary to hold each sub-vertex's profiling data
        profile_data = {}
        
        subvertices = graph_mapper.get_subvertices_from_vertex(self)
        for subvertex in subvertices:
            placement = placements.get_placement_of_subvertex(subvertex)
            (x, y, p) = placement.x, placement.y, placement.p
            subvertex_slice = graph_mapper.get_subvertex_slice(subvertex)
            lo_atom = subvertex_slice.lo_atom
            logger.debug("Reading spikes from chip {}, {}, core {}, "
                         "lo_atom {}".format(x, y, p, lo_atom))

            # Get the App Data for the core
            app_data_base_address = \
                txrx.get_cpu_information_from_core(x, y, p).user[0]
            # Get the position of the value buffer
            profiling_region_base_address_offset = \
                get_region_base_address_offset(app_data_base_address, 
                                               constants.POPULATION_BASED_REGIONS.PROFILING.value)
            profiling_region_base_address_buf = buffer(txrx.read_memory(
                x, y, profiling_region_base_address_offset, 4))
            profiling_region_base_address = \
                struct.unpack_from("<I", profiling_region_base_address_buf)[0]
            profiling_region_base_address += app_data_base_address
            
            # Read the profiling data size
            words_written_data =\
                buffer(txrx.read_memory(
                    x, y, profiling_region_base_address + 4, 4))
            words_written = \
                struct.unpack_from("<I", words_written_data)[0]
            
            # Read the profiling data
            profiling_data = txrx.read_memory(
                x, y, profiling_region_base_address + 8, words_written * 4)

            # Finally read into numpyi
            profiling_samples = numpy.asarray(profiling_data, dtype="uint8").view(dtype="<u4")

        # If there's no data, return an empty dictionary
        if len(profiling_samples) == 0:
	    print("No samples recorded")
	    return {}

        # Slice data to seperate times, tags and flags
        sample_times = profiling_samples[::2]
        sample_tags_and_flags = profiling_samples[1::2]

        # Further split the tags and flags word into seperate arrays of tags and flags
        sample_tags = numpy.bitwise_and(sample_tags_and_flags, 0x7FFFFFFF)
        sample_flags = numpy.right_shift(sample_tags_and_flags, 31)

        # Find indices of samples relating to entries and exits
        sample_entry_indices = numpy.where(sample_flags == 1)
        sample_exit_indices = numpy.where(sample_flags == 0)

        # Convert count-down times to count up times from 1st sample
        sample_times = numpy.subtract(sample_times[0], sample_times)
        sample_times_ms = numpy.multiply(sample_times, MS_SCALE, dtype=numpy.float)

        # Slice tags and times into entry and exits
        entry_tags = sample_tags[sample_entry_indices]
        entry_times_ms = sample_times_ms[sample_entry_indices]
        exit_tags = sample_tags[sample_exit_indices]
        exit_times_ms = sample_times_ms[sample_exit_indices]

        # Loop through unique tags
        tag_dictionary = {}
        unique_tags = numpy.unique(sample_tags)
        for tag in unique_tags:
	    # Get indices where these tags occur
	    tag_entry_indices = numpy.where(entry_tags == tag)
	    tag_exit_indices = numpy.where(exit_tags == tag)

	    # Use these to get subset for this tag
	    tag_entry_times_ms = entry_times_ms[tag_entry_indices]
	    tag_exit_times_ms = exit_times_ms[tag_exit_indices]

	    # If the first exit is before the first
	    # Entry, add a dummy entry at beginning
	    if tag_exit_times_ms[0] < tag_entry_times_ms[0]:
		print "WARNING: profile starts mid-tag"
		tag_entry_times_ms = numpy.append(0.0, tag_entry_times_ms)

	    if len(tag_entry_times_ms) > len(tag_exit_times_ms):
		print "WARNING: profile finishes mid-tag"
		tag_entry_times_ms = tag_entry_times_ms[:len(tag_exit_times_ms)-len(tag_entry_times_ms)]

	    # Subtract entry times from exit times to get durations of each call
	    tag_durations_ms = numpy.subtract(tag_exit_times_ms, tag_entry_times_ms)

	    # Add entry times and durations to dictionary
	    tag_dictionary[tag] = (tag_entry_times_ms, tag_durations_ms)

	return tag_dictionary

        
    def _write_setup_info(
            self, spec, spike_history_region_sz, neuron_potential_region_sz,
            gsyn_region_sz, ip_tags, buffer_size_before_receive,
            time_between_requests, subvertex):
        """ Write information used to control the simulation and gathering of\
            results.
        """

        # Write this to the system region (to be picked up by the simulation):
        self._write_basic_setup_info(
            spec, constants.POPULATION_BASED_REGIONS.SYSTEM.value)
        subvertex.write_recording_data(
            spec, ip_tags,
            [spike_history_region_sz, neuron_potential_region_sz,
             gsyn_region_sz], buffer_size_before_receive,
            time_between_requests)
        
        # Write profiler setting.
        spec.switch_write_focus(region=constants.POPULATION_BASED_REGIONS.PROFILING.value)
        spec.write_value(data=self.profiler_num_samples)


    def _write_neuron_parameters(
            self, spec, key, vertex_slice):

        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        spec.comment("\nWriting Neuron Parameters for {} Neurons:\n".format(
            n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value)

        # Write whether the key is to be used, and then the key, or 0 if it
        # isn't to be used
        if key is None:
            spec.write_value(data=0)
            spec.write_value(data=0)
        else:
            spec.write_value(data=1)
            spec.write_value(data=key)

        # Write the number of neurons in the block:
        spec.write_value(data=n_atoms)

        # Write the size of the incoming spike buffer
        spec.write_value(data=self._incoming_spike_buffer_size)

        # Write the global parameters
        global_params = self._neuron_model.get_global_parameters()
        for param in global_params:
            spec.write_value(data=param.get_value(),
                             data_type=param.get_dataspec_datatype())

        # Write the neuron parameters
        utility_calls.write_parameters_per_neuron(
            spec, vertex_slice, self._neuron_model.get_neural_parameters())

        # Write the input type parameters
        utility_calls.write_parameters_per_neuron(
            spec, vertex_slice, self._input_type.get_input_type_parameters())

        # Write the additional input parameters
        if self._additional_input is not None:
            utility_calls.write_parameters_per_neuron(
                spec, vertex_slice, self._additional_input.get_parameters())

        # Write the threshold type parameters
        utility_calls.write_parameters_per_neuron(
            spec, vertex_slice,
            self._threshold_type.get_threshold_parameters())

    # @implements AbstractDataSpecableVertex.generate_data_spec
    def generate_data_spec(
            self, subvertex, placement, partitioned_graph, graph, routing_info,
            hostname, graph_mapper, report_folder, ip_tags,
            reverse_ip_tags, write_text_specs, application_run_time_folder):

        # Create new DataSpec for this processor:
        data_writer, report_writer = self.get_data_spec_file_writers(
            placement.x, placement.y, placement.p, hostname, report_folder,
            write_text_specs, application_run_time_folder)
        spec = DataSpecificationGenerator(data_writer, report_writer)
        spec.comment("\n*** Spec for block of {} neurons ***\n".format(
            self.model_name))
        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)

        # Get recording sizes - the order is important here as spikes will
        # require less space than voltage and voltage less than gsyn.  This
        # order ensures that the buffer size before receive is optimum for
        # all recording channels
        # TODO: Maybe split the buffer size before receive by channel?
        spike_buffer_size = self._spike_recorder.get_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self._no_machine_time_steps)
        v_buffer_size = self._v_recorder.get_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self._no_machine_time_steps)
        gsyn_buffer_size = self._gsyn_recorder.get_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self._no_machine_time_steps)
        spike_history_sz = recording_utils.get_buffer_sizes(
            self._spike_buffer_max_size, spike_buffer_size,
            self._enable_buffered_recording)
        v_history_sz = recording_utils.get_buffer_sizes(
            self._v_buffer_max_size, v_buffer_size,
            self._enable_buffered_recording)
        gsyn_history_sz = recording_utils.get_buffer_sizes(
            self._gsyn_buffer_max_size, gsyn_buffer_size,
            self._enable_buffered_recording)
        spike_buffering_needed = recording_utils.needs_buffering(
            self._spike_buffer_max_size, spike_buffer_size,
            self._enable_buffered_recording)
        v_buffering_needed = recording_utils.needs_buffering(
            self._v_buffer_max_size, v_buffer_size,
            self._enable_buffered_recording)
        gsyn_buffering_needed = recording_utils.needs_buffering(
            self._gsyn_buffer_max_size, gsyn_buffer_size,
            self._enable_buffered_recording)
        buffer_size_before_receive = self._buffer_size_before_receive
        if (not spike_buffering_needed and not v_buffering_needed and
                not gsyn_buffering_needed):
            buffer_size_before_receive = max((
                spike_history_sz, v_history_sz, gsyn_history_sz)) + 256

        # Reserve memory regions
        self._reserve_memory_regions(
            spec, vertex_slice, spike_history_sz, v_history_sz,
            gsyn_history_sz, subvertex)

        # Declare random number generators and distributions:
        # TODO add random distribution stuff
        # self.write_random_distribution_declarations(spec)

        # Get the key - use only the first edge
        key = None

        for partition in partitioned_graph.\
                outgoing_edges_partitions_from_vertex(subvertex).values():

            keys_and_masks = \
                routing_info.get_keys_and_masks_from_partition(partition)

            # NOTE: using the first key assigned as the key.  Should in future
            # get the list of keys and use one per neuron, to allow arbitrary
            # key and mask assignments
            key = keys_and_masks[0].key

        # Write the regions
        self._write_setup_info(
            spec, spike_history_sz, v_history_sz, gsyn_history_sz, ip_tags,
            buffer_size_before_receive, self._time_between_requests, subvertex)
        self._write_neuron_parameters(spec, key, vertex_slice)

        # allow the synaptic matrix to write its data spec-able data
        self._synapse_manager.write_data_spec(
            spec, self, vertex_slice, subvertex, placement, partitioned_graph,
            graph, routing_info, graph_mapper, self._input_type)

        # End the writing of this specification:
        spec.end_specification()
        data_writer.close()

        return data_writer.filename

    # @implements AbstractDataSpecableVertex.get_binary_file_name
    def get_binary_file_name(self):

        # Split binary name into title and extension
        binary_title, binary_extension = os.path.splitext(self._binary)

        # Reunite title and extension and return
        return (binary_title + self._synapse_manager.vertex_executable_suffix +
                binary_extension)

    # @implements AbstractSpikeRecordable.is_recording_spikes
    def is_recording_spikes(self):
        return self._spike_recorder.record

    # @implements AbstractSpikeRecordable.set_recording_spikes
    def set_recording_spikes(self):
        self._change_requires_mapping = not self._spike_recorder.record
        self._spike_recorder.record = True

    # @implements AbstractSpikeRecordable.get_spikes
    def get_spikes(self, placements, graph_mapper, buffer_manager):
        return self._spike_recorder.get_spikes(
            self._label, buffer_manager,
            constants.POPULATION_BASED_REGIONS.SPIKE_HISTORY.value,
            constants.POPULATION_BASED_REGIONS.BUFFERING_OUT_STATE.value,
            placements, graph_mapper, self)

    # @implements AbstractVRecordable.is_recording_v
    def is_recording_v(self):
        return self._v_recorder.record_v

    # @implements AbstractVRecordable.set_recording_v
    def set_recording_v(self):
        self._change_requires_mapping = not self._v_recorder.record_v
        self._v_recorder.record_v = True

    # @implements AbstractVRecordable.get_v
    def get_v(self, n_machine_time_steps, placements, graph_mapper,
              buffer_manager):
        return self._v_recorder.get_v(
            self._label, buffer_manager,
            constants.POPULATION_BASED_REGIONS.POTENTIAL_HISTORY.value,
            constants.POPULATION_BASED_REGIONS.BUFFERING_OUT_STATE.value,
            placements, graph_mapper, self)

    # @implements AbstractGSynRecordable.is_recording_gsyn
    def is_recording_gsyn(self):
        return self._gsyn_recorder.record_gsyn

    # @implements AbstractGSynRecordable.set_recording_gsyn
    def set_recording_gsyn(self):
        self._change_requires_mapping = not self._gsyn_recorder.record_gsyn
        self._gsyn_recorder.record_gsyn = True

    # @implements AbstractGSynRecordable.get_gsyn
    def get_gsyn(self, n_machine_time_steps, placements, graph_mapper,
                 buffer_manager):
        return self._gsyn_recorder.get_gsyn(
            self._label, buffer_manager,
            constants.POPULATION_BASED_REGIONS.GSYN_HISTORY.value,
            constants.POPULATION_BASED_REGIONS.BUFFERING_OUT_STATE.value,
            placements, graph_mapper, self)

    def initialize(self, variable, value):
        initialize_attr = getattr(
            self._neuron_model, "initialize_%s" % variable, None)
        if initialize_attr is None or not callable(initialize_attr):
            raise Exception("Vertex does not support initialisation of"
                            " parameter {}".format(variable))
        initialize_attr(value)
        self._change_requires_mapping = True

    @property
    def synapse_type(self):
        return self._synapse_manager.synapse_type

    @property
    def input_type(self):
        return self._input_type

    def get_value(self, key):
        """ Get a property of the overall model
        """
        for obj in [self._neuron_model, self._input_type,
                    self._threshold_type, self._synapse_manager.synapse_type,
                    self._additional_input]:
            if hasattr(obj, key):
                return getattr(obj, key)
        raise Exception("Population {} does not have parameter {}".format(
            self.vertex, key))

    def set_value(self, key, value):
        """ Set a property of the overall model
        """
        for obj in [self._neuron_model, self._input_type,
                    self._threshold_type, self._synapse_manager.synapse_type,
                    self._additional_input]:
            if hasattr(obj, key):
                setattr(obj, key, value)
                self._change_requires_mapping = True
                return
        raise Exception("Type {} does not have parameter {}".format(
            self._model_name, key))

    @property
    def weight_scale(self):
        return self._input_type.get_global_weight_scale()

    @property
    def ring_buffer_sigma(self):
        return self._synapse_manager.ring_buffer_sigma

    @ring_buffer_sigma.setter
    def ring_buffer_sigma(self, ring_buffer_sigma):
        self._synapse_manager.ring_buffer_sigma = ring_buffer_sigma

    @property
    def spikes_per_second(self):
        return self._synapse_manager.spikes_per_second

    @spikes_per_second.setter
    def spikes_per_second(self, spikes_per_second):
        self._synapse_manager.spikes_per_second = spikes_per_second

    @property
    def synapse_dynamics(self):
        return self._synapse_manager.synapse_dynamics

    @synapse_dynamics.setter
    def synapse_dynamics(self, synapse_dynamics):
        self._synapse_manager.synapse_dynamics = synapse_dynamics

    def add_pre_run_connection_holder(
            self, connection_holder, edge, synapse_info):
        self._synapse_manager.add_pre_run_connection_holder(
            connection_holder, edge, synapse_info)

    def get_connections_from_machine(
            self, transceiver, placement, subedge, graph_mapper,
            routing_infos, synapse_info, partitioned_graph):
        return self._synapse_manager.get_connections_from_machine(
            transceiver, placement, subedge, graph_mapper,
            routing_infos, synapse_info, partitioned_graph)

    def is_data_specable(self):
        return True

    def get_incoming_partition_constraints(self, partition, graph_mapper):
        """ Gets the constraints for partitions going into this vertex

        :param partition: partition that goes into this vertex
        :param graph_mapper: the graph mapper object
        :return: list of constraints
        """
        return self._synapse_manager.get_incoming_partition_constraints()

    def get_outgoing_partition_constraints(self, partition, graph_mapper):
        """ Gets the constraints for partitions going out of this vertex
        :param partition: the partition that leaves this vertex
        :param graph_mapper: the graph mapper object
        :return: list of constraints
        """
        return [KeyAllocatorContiguousRangeContraint()]

    def __str__(self):
        return "{} with {} atoms".format(self._label, self.n_atoms)

    def __repr__(self):
        return self.__str__()
