
# pacman imports
from pacman.model.abstract_classes import AbstractHasGlobalMaxAtoms
from pacman.model.constraints.key_allocator_constraints \
    import ContiguousKeyRangeContraint
from pacman.model.decorators import overrides
from pacman.executor.injection_decorator import inject_items
from pacman.model.graphs.common import Slice
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.resources import CPUCyclesPerTickResource, DTCMResource
from pacman.model.resources import ResourceContainer, SDRAMResource

# front end common imports
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spinn_front_end_common.abstract_models import \
    AbstractProvidesIncomingPartitionConstraints
from spinn_front_end_common.abstract_models import \
    AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.abstract_models\
    import AbstractRewritesDataSpecification
from spinn_front_end_common.abstract_models \
    import AbstractGeneratesDataSpecification
from spinn_front_end_common.abstract_models import AbstractHasAssociatedBinary
from spinn_front_end_common.abstract_models.impl\
    import ProvidesKeyToAtomMappingImpl
from spinn_front_end_common.utilities import constants as common_constants
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.interface.buffer_management\
    import recording_utilities
from spinn_front_end_common.interface.profiling import profile_utils

# spynnaker imports
from spynnaker.pyNN.models.neuron.synaptic_manager import SynapticManager
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.common import AbstractSpikeRecordable
from spynnaker.pyNN.models.common import AbstractNeuronRecordable
from spynnaker.pyNN.models.common import NeuronRecorder
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.neuron.population_machine_vertex \
    import PopulationMachineVertex
from spynnaker.pyNN.models.abstract_models \
    import AbstractPopulationInitializable, AbstractAcceptsIncomingSynapses
from spynnaker.pyNN.models.abstract_models \
    import AbstractPopulationSettable, AbstractReadParametersBeforeSet
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits

import logging
import os
import random

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


class AbstractPopulationVertex(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary, AbstractContainsUnits,
        AbstractSpikeRecordable,  AbstractNeuronRecordable,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractProvidesIncomingPartitionConstraints,
        AbstractPopulationInitializable, AbstractPopulationSettable,
        AbstractChangableAfterRun, AbstractHasGlobalMaxAtoms,
        AbstractRewritesDataSpecification, AbstractReadParametersBeforeSet,
        AbstractAcceptsIncomingSynapses, ProvidesKeyToAtomMappingImpl):
    """ Underlying vertex model for Neural Populations.
    """

    BASIC_MALLOC_USAGE = 2

    # recording region ids
    SPIKE_RECORDING_REGION = 0
    V_RECORDING_REGION = 1
    GSYN_EXCITATORY_RECORDING_REGION = 2
    GSYN_INHIBITORY_RECORDING_REGION = 3

    RECORDING_REGION = {"spikes": 0, "v": 1, "gsyn_exc": 2, "gsyn_inh": 3}

    VARIABLE_LONG = {"spikes": "spikes",
                     "v": "membrane voltage",
                     "gsyn_exc": "gsyn_excitatory",
                     "gsyn_inh": "gsyn_inhibitory"}

    N_RECORDING_REGIONS = 4

    # the size of the runtime SDP port data region
    RUNTIME_SDP_PORT_SIZE = 4

    # 6 elements before the start of global parameters
    BYTES_TILL_START_OF_GLOBAL_PARAMETERS = 24

    _n_vertices = 0

    none_pynn_default_parameters = {
        'spikes_per_second': None, 'ring_buffer_sigma': None,
        'incoming_spike_buffer_size': None, 'constraints': None,
        'label': None}

    def __init__(
            self, n_neurons, binary, label, max_atoms_per_core,
            spikes_per_second, ring_buffer_sigma, incoming_spike_buffer_size,
            model_name, neuron_model, input_type, synapse_type, threshold_type,
            additional_input=None, constraints=None, max_feasible_atoms_per_core=255):

        ApplicationVertex.__init__(
            self, label, constraints, max_atoms_per_core)
        AbstractSpikeRecordable.__init__(self)
        AbstractNeuronRecordable.__init__(self)
        AbstractProvidesOutgoingPartitionConstraints.__init__(self)
        AbstractProvidesIncomingPartitionConstraints.__init__(self)
        AbstractPopulationInitializable.__init__(self)
        AbstractChangableAfterRun.__init__(self)
        AbstractHasGlobalMaxAtoms.__init__(self)
        AbstractAcceptsIncomingSynapses.__init__(self)
        ProvidesKeyToAtomMappingImpl.__init__(self)
        AbstractContainsUnits.__init__(self)

        self._units = {
            'spikes': 'spikes',
            'v': 'mV',
            'gsyn_exc': "uS",
            'gsyn_inh': "uS"}

        self._binary = binary
        self._n_atoms = n_neurons
        self._max_feasible_atoms_per_core = max_feasible_atoms_per_core


        # buffer data
        self._incoming_spike_buffer_size = incoming_spike_buffer_size

        # get config from simulator
        config = globals_variables.get_simulator().config

        if incoming_spike_buffer_size is None:
            self._incoming_spike_buffer_size = config.getint(
                "Simulation", "incoming_spike_buffer_size")

        self._model_name = model_name
        self._neuron_model = neuron_model
        self._input_type = input_type
        self._threshold_type = threshold_type
        self._additional_input = additional_input

        # Set up for recording
        self._neuron_recorder = NeuronRecorder(
            ["spikes", "v", "gsyn_exc", "gsyn_inh"], n_neurons)

        self._time_between_requests = config.getint(
            "Buffers", "time_between_requests")
        self._minimum_buffer_sdram = config.getint(
            "Buffers", "minimum_buffer_sdram")
        self._using_auto_pause_and_resume = config.getboolean(
            "Buffers", "use_auto_pause_and_resume")
        self._receive_buffer_host = config.get(
            "Buffers", "receive_buffer_host")
        self._receive_buffer_port = helpful_functions.read_config_int(
            config, "Buffers", "receive_buffer_port")

        # If live buffering is enabled, set a maximum on the buffer sizes
        spike_buffer_max_size = 0
        v_buffer_max_size = 0
        gsyn_buffer_max_size = 0
        self._buffer_size_before_receive = None
        if config.getboolean("Buffers", "enable_buffered_recording"):
            spike_buffer_max_size = config.getint(
                "Buffers", "spike_buffer_size")
            v_buffer_max_size = config.getint(
                "Buffers", "v_buffer_size")
            gsyn_buffer_max_size = config.getint(
                "Buffers", "gsyn_buffer_size")
            self._buffer_size_before_receive = config.getint(
                "Buffers", "buffer_size_before_receive")

        self._maximum_sdram_for_buffering = [
            spike_buffer_max_size, v_buffer_max_size, gsyn_buffer_max_size,
            gsyn_buffer_max_size
        ]

        # Set up synapse handling
        self._synapse_manager = SynapticManager(
            synapse_type, ring_buffer_sigma, spikes_per_second, config)

        # bool for if state has changed.
        self._change_requires_mapping = True
        self._change_requires_neuron_parameters_reload = False

        # Set up for profiling
        self._n_profile_samples = helpful_functions.read_config_int(
            config, "Reports", "n_profile_samples")

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        return self._n_atoms

    @inject_items({
        "graph": "MemoryApplicationGraph",
        "n_machine_time_steps": "TotalMachineTimeSteps",
        "machine_time_step": "MachineTimeStep"
    })
    @overrides(
        ApplicationVertex.get_resources_used_by_atoms,
        additional_arguments={
            "graph", "n_machine_time_steps", "machine_time_step"
        }
    )
    def get_resources_used_by_atoms(
            self, vertex_slice, graph, n_machine_time_steps,
            machine_time_step):

        # set resources required from this object
        container = ResourceContainer(
            sdram=SDRAMResource(
                self.get_sdram_usage_for_atoms(
                    vertex_slice, graph, machine_time_step)),
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms(vertex_slice)),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms(vertex_slice)))

        recording_sizes = recording_utilities.get_recording_region_sizes(
            self._get_buffered_sdram(vertex_slice, n_machine_time_steps),
            self._minimum_buffer_sdram, self._maximum_sdram_for_buffering,
            self._using_auto_pause_and_resume)
        container.extend(recording_utilities.get_recording_resources(
            recording_sizes, self._receive_buffer_host,
            self._receive_buffer_port))

        # return the total resources.
        return container

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self._change_requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        self._change_requires_mapping = False

    def _get_buffered_sdram_per_timestep(self, vertex_slice):
        return [
            self._neuron_recorder.get_buffered_sdram_per_timestep(
                "spikes", vertex_slice),
            self._neuron_recorder.get_buffered_sdram_per_timestep(
                "v", vertex_slice),
            self._neuron_recorder.get_buffered_sdram_per_timestep(
                "gsyn_exc", vertex_slice),
            self._neuron_recorder.get_buffered_sdram_per_timestep(
                "gsyn_inh", vertex_slice)
        ]

    def _get_buffered_sdram(self, vertex_slice, n_machine_time_steps):
        return [
            self._neuron_recorder.get_buffered_sdram(
                "spikes", vertex_slice, n_machine_time_steps),
            self._neuron_recorder.get_buffered_sdram(
                "v", vertex_slice, n_machine_time_steps),
            self._neuron_recorder.get_buffered_sdram(
                "gsyn_exc", vertex_slice, n_machine_time_steps),
            self._neuron_recorder.get_buffered_sdram(
                "gsyn_inh", vertex_slice, n_machine_time_steps)
        ]

    @inject_items({"n_machine_time_steps": "TotalMachineTimeSteps"})
    @overrides(
        ApplicationVertex.create_machine_vertex,
        additional_arguments={"n_machine_time_steps"})
    def create_machine_vertex(
            self, vertex_slice, resources_required, n_machine_time_steps,
            label=None, constraints=None):

        is_recording = len(self._neuron_recorder.recording_variables) > 0
        buffered_sdram_per_timestep = self._get_buffered_sdram_per_timestep(
            vertex_slice)
        buffered_sdram = self._get_buffered_sdram(
            vertex_slice, n_machine_time_steps)
        minimum_buffer_sdram = recording_utilities.get_minimum_buffer_sdram(
            buffered_sdram, self._minimum_buffer_sdram)
        overflow_sdram = self._neuron_recorder.get_sampling_overflow_sdram(
            vertex_slice)
        vertex = PopulationMachineVertex(
            resources_required, is_recording, minimum_buffer_sdram,
            buffered_sdram_per_timestep, label, constraints, overflow_sdram)

        self._n_vertices += 1

        # return machine vertex
        return vertex

    def get_cpu_usage_for_atoms(self, vertex_slice):
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
                self._neuron_recorder.get_n_cpu_cycles(vertex_slice.n_atoms) +
                self._synapse_manager.get_n_cpu_cycles())

    def get_dtcm_usage_for_atoms(self, vertex_slice):
        per_neuron_usage = (
            self._neuron_model.get_dtcm_usage_per_neuron_in_bytes() +
            self._input_type.get_dtcm_usage_per_neuron_in_bytes() +
            self._threshold_type.get_dtcm_usage_per_neuron_in_bytes())
        if self._additional_input is not None:
            per_neuron_usage += \
                self._additional_input.get_dtcm_usage_per_neuron_in_bytes()
        return (_NEURON_BASE_DTCM_USAGE_IN_BYTES +
                (per_neuron_usage * vertex_slice.n_atoms) +
                self._neuron_recorder.get_dtcm_usage_in_bytes(vertex_slice) +
                self._synapse_manager.get_dtcm_usage_in_bytes())

    def _get_sdram_usage_for_neuron_params_per_neuron(self):
        per_neuron_usage = (
            self._input_type.get_sdram_usage_per_neuron_in_bytes() +
            self._threshold_type.get_sdram_usage_per_neuron_in_bytes() +
            self._neuron_recorder.get_sdram_usage_per_neuron_in_bytes() +
            self._neuron_model.get_sdram_usage_per_neuron_in_bytes())
        if self._additional_input is not None:
            per_neuron_usage += \
                self._additional_input.get_sdram_usage_per_neuron_in_bytes()
        return per_neuron_usage

    def _get_sdram_usage_for_neuron_params(self, vertex_slice):
        """ calculates the sdram usage for just the neuron parameters region

        :param vertex_slice: the slice of atoms.
        :return:  The sdram required for the neuron region
        """
        per_neuron_usage = \
            self._get_sdram_usage_for_neuron_params_per_neuron()
        return (self.BYTES_TILL_START_OF_GLOBAL_PARAMETERS +
                self._neuron_model
                    .get_sdram_usage_for_global_parameters_in_bytes() +
                self._neuron_recorder
                    .get_sdram_usage_for_global_parameters_in_bytes() +
                (per_neuron_usage * vertex_slice.n_atoms))

    def get_sdram_usage_for_atoms(
            self, vertex_slice, graph, machine_time_step):
        sdram_requirement = (
            common_constants.SYSTEM_BYTES_REQUIREMENT +
            self._get_sdram_usage_for_neuron_params(vertex_slice) +
            recording_utilities.get_recording_header_size(
                self.N_RECORDING_REGIONS) +
            PopulationMachineVertex.get_provenance_data_size(
                PopulationMachineVertex.N_ADDITIONAL_PROVENANCE_DATA_ITEMS) +
            self._synapse_manager.get_sdram_usage_in_bytes(
                vertex_slice, graph.get_edges_ending_at_vertex(self),
                machine_time_step) +
            (self._get_number_of_mallocs_used_by_dsg() *
             common_constants.SARK_PER_MALLOC_SDRAM_USAGE) +
            profile_utils.get_profile_region_size(
                self._n_profile_samples))

        return sdram_requirement

    def _get_number_of_mallocs_used_by_dsg(self):
        extra_mallocs = len(self._neuron_recorder.recording_variables)
        return (
            self.BASIC_MALLOC_USAGE +
            self._synapse_manager.get_number_of_mallocs_used_by_dsg() +
            extra_mallocs)

    def _reserve_memory_regions(self, spec, vertex_slice, vertex):

        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.SYSTEM.value,
            size=common_constants.SYSTEM_BYTES_REQUIREMENT,
            label='System')

        self._reserve_neuron_params_data_region(spec, vertex_slice)

        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.RECORDING.value,
            size=recording_utilities.get_recording_header_size(
                self.N_RECORDING_REGIONS))

        profile_utils.reserve_profile_region(
            spec, constants.POPULATION_BASED_REGIONS.PROFILING.value,
            self._n_profile_samples)

        vertex.reserve_provenance_data_region(spec)

    def _reserve_neuron_params_data_region(self, spec, vertex_slice):
        """ reserve the neuron parameter data region

        :param spec: the spec to write the dsg region to
        :param vertex_slice: the slice of atoms from the application vertex
        :return: None
        """
        params_size = self._get_sdram_usage_for_neuron_params(vertex_slice)
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value,
            size=params_size,
            label='NeuronParams')

    def _write_neuron_parameters(
            self, spec, key, vertex_slice, machine_time_step,
            time_scale_factor):

        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        spec.comment("\nWriting Neuron Parameters for {} Neurons:\n".format(
            n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value)

        # Write the random back off value
        spec.write_value(random.randint(0, self._n_vertices))

        # Write the number of microseconds between sending spikes
        time_between_spikes = (
            (machine_time_step * time_scale_factor) /
            (n_atoms * 2.0))
        spec.write_value(data=int(time_between_spikes))

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

        # Write the recording rates and sizes
        record_globals = self._neuron_recorder.get_global_parameters(
            vertex_slice)
        for param in record_globals:
            spec.write_value(data=param.get_value(),
                             data_type=param.get_dataspec_datatype())

        # Write the index parameters
        indexes = self._neuron_recorder.get_index_parameters(vertex_slice)
        utility_calls.write_parameters_per_neuron(
            spec, vertex_slice, indexes, slice_paramaters=True)

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

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "routing_info": "MemoryRoutingInfos"})
    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "routing_info"})
    def regenerate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, routing_info):

        vertex_slice = graph_mapper.get_slice(placement.vertex)

        # reserve the neuron parameters data region
        self._reserve_neuron_params_data_region(
            spec, graph_mapper.get_slice(placement.vertex))

        # write the neuron params into the new dsg region
        self._write_neuron_parameters(
            key=routing_info.get_first_key_from_pre_vertex(
                placement.vertex, constants.SPIKE_PARTITION_ID),
            machine_time_step=machine_time_step, spec=spec,
            time_scale_factor=time_scale_factor,
            vertex_slice=vertex_slice)

        self._synapse_manager.regenerate_data_specification(
            spec, placement, machine_time_step, time_scale_factor,
            vertex_slice)

        # close spec
        spec.end_specification()

    @overrides(AbstractRewritesDataSpecification
               .requires_memory_regions_to_be_reloaded)
    def requires_memory_regions_to_be_reloaded(self):
        return self._change_requires_neuron_parameters_reload

    @overrides(AbstractRewritesDataSpecification.mark_regions_reloaded)
    def mark_regions_reloaded(self):
        self._change_requires_neuron_parameters_reload = False

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "application_graph": "MemoryApplicationGraph",
        "machine_graph": "MemoryMachineGraph",
        "routing_info": "MemoryRoutingInfos",
        "tags": "MemoryTags",
        "n_machine_time_steps": "TotalMachineTimeSteps"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "application_graph", "machine_graph", "routing_info", "tags",
            "n_machine_time_steps"
        })
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, application_graph, machine_graph, routing_info,
            tags, n_machine_time_steps):
        vertex = placement.vertex

        spec.comment("\n*** Spec for block of {} neurons ***\n".format(
            self._model_name))
        vertex_slice = graph_mapper.get_slice(vertex)

        # Reserve memory regions
        self._reserve_memory_regions(spec, vertex_slice, vertex)

        # Declare random number generators and distributions:
        # TODO add random distribution stuff
        # self.write_random_distribution_declarations(spec)

        # Get the key
        key = routing_info.get_first_key_from_pre_vertex(
            vertex, constants.SPIKE_PARTITION_ID)

        # Write the setup region
        spec.switch_write_focus(
            constants.POPULATION_BASED_REGIONS.SYSTEM.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name(), machine_time_step,
            time_scale_factor))

        # Write the recording region
        spec.switch_write_focus(
            constants.POPULATION_BASED_REGIONS.RECORDING.value)
        ip_tags = tags.get_ip_tags_for_vertex(vertex)
        recorded_region_sizes = recording_utilities.get_recorded_region_sizes(
            self._get_buffered_sdram(vertex_slice, n_machine_time_steps),
            self._maximum_sdram_for_buffering)
        spec.write_array(recording_utilities.get_recording_header_array(
            recorded_region_sizes, self._time_between_requests,
            self._buffer_size_before_receive, ip_tags))

        # Write the neuron parameters
        self._write_neuron_parameters(
            spec, key, vertex_slice, machine_time_step, time_scale_factor)

        # write profile data
        profile_utils.write_profile_region_data(
            spec, constants.POPULATION_BASED_REGIONS.PROFILING.value,
            self._n_profile_samples)

        # allow the synaptic matrix to write its data spec-able data
        self._synapse_manager.write_data_spec(
            spec, self, vertex_slice, vertex, placement, machine_graph,
            application_graph, routing_info, graph_mapper,
            self._input_type, machine_time_step, self._max_feasible_atoms_per_core)

        # End the writing of this specification:
        spec.end_specification()

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):

        # Split binary name into title and extension
        binary_title, binary_extension = os.path.splitext(self._binary)

        # Reunite title and extension and return
        return (binary_title + self._synapse_manager.vertex_executable_suffix +
                binary_extension)

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self._neuron_recorder.is_recording("spikes")

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        self.set_recording("spikes", new_state, sampling_interval, indexes)

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(
            self, placements, graph_mapper, buffer_manager, machine_time_step):
        return self._neuron_recorder.get_spikes(
            self.label, buffer_manager, self.SPIKE_RECORDING_REGION,
            placements, graph_mapper, self, machine_time_step)

    @overrides(AbstractNeuronRecordable.get_recordable_variables)
    def get_recordable_variables(self):
        return self._neuron_recorder.get_recordable_variables()

    @overrides(AbstractNeuronRecordable.is_recording)
    def is_recording(self, variable):
        return self._neuron_recorder.is_recording(variable)

    @overrides(AbstractNeuronRecordable.set_recording)
    def set_recording(self, variable, new_state=True, sampling_interval=None,
                      indexes=None):
        self._change_requires_mapping = not self.is_recording(variable)
        self._neuron_recorder.set_recording(
            variable, new_state, sampling_interval, indexes)

    @overrides(AbstractNeuronRecordable.get_data)
    def get_data(self, variable, n_machine_time_steps, placements,
                 graph_mapper, buffer_manager, machine_time_step):
        return self._neuron_recorder.get_matrix_data(
            self.label, buffer_manager, self.RECORDING_REGION[variable],
            placements, graph_mapper, self, variable, n_machine_time_steps)

    @overrides(AbstractNeuronRecordable.get_neuron_sampling_interval)
    def get_neuron_sampling_interval(self, variable):
        return self._neuron_recorder.get_neuron_sampling_interval(variable)

    @overrides(AbstractSpikeRecordable.get_spikes_sampling_interval)
    def get_spikes_sampling_interval(self):
        return self._neuron_recorder.get_neuron_sampling_interval("spikes")

    @overrides(AbstractPopulationInitializable.initialize)
    def initialize(self, variable, value):
        initialize_attr = getattr(
            self._neuron_model, "initialize_%s" % variable, None)
        if initialize_attr is None or not callable(initialize_attr):
            raise Exception("Vertex does not support initialisation of"
                            " parameter {}".format(variable))
        initialize_attr(value)
        self._change_requires_neuron_parameters_reload = True

    @property
    def input_type(self):
        return self._input_type

    @overrides(AbstractPopulationSettable.get_value)
    def get_value(self, key):
        """ Get a property of the overall model
        """
        for obj in [self._neuron_model, self._input_type,
                    self._threshold_type, self._synapse_manager.synapse_type,
                    self._additional_input, self]:
            if hasattr(obj, key):
                return getattr(obj, key)
        raise Exception("Population {} does not have parameter {}".format(
            self._model_name, key))

    @overrides(AbstractPopulationSettable.set_value)
    def set_value(self, key, value):
        """ Set a property of the overall model
        """
        for obj in [self._neuron_model, self._input_type,
                    self._threshold_type, self._synapse_manager.synapse_type,
                    self._additional_input]:
            if hasattr(obj, key):
                setattr(obj, key, value)
                self._change_requires_neuron_parameters_reload = True
                return
        raise InvalidParameterType(
            "Type {} does not have parameter {}".format(type(self), key))

    @overrides(AbstractReadParametersBeforeSet.read_parameters_from_machine)
    def read_parameters_from_machine(
            self, transceiver, placement, vertex_slice):

        # locate sdram address to where the neuron parameters are stored
        neuron_region_sdram_address = \
            helpful_functions.locate_memory_region_for_placement(
                placement,
                constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value,
                transceiver)

        # shift past the extra stuff before neuron parameters that we don't
        # need to read
        neuron_parameters_sdram_address = (
            neuron_region_sdram_address +
            self.BYTES_TILL_START_OF_GLOBAL_PARAMETERS)

        # get size of neuron params
        size_of_region = self._get_sdram_usage_for_neuron_params(vertex_slice)
        size_of_region -= self.BYTES_TILL_START_OF_GLOBAL_PARAMETERS

        # get data from the machine
        byte_array = transceiver.read_memory(
            placement.x, placement.y, neuron_parameters_sdram_address,
            size_of_region)

        # update python neuron parameters with the data
        offset = 0

        # handle global params (only once, so given a slice of 0 to 0)
        global_params, offset = utility_calls.translate_parameters(
            self._neuron_model.get_global_parameter_types(),
            byte_array, offset, Slice(0, 0))
        self._neuron_model.set_global_parameters(global_params)

        # handle state params for a neuron
        neuron_params, offset = utility_calls.translate_parameters(
            self._neuron_model.get_neural_parameter_types(),
            byte_array, offset, vertex_slice)
        self._neuron_model.set_neural_parameters(neuron_params, vertex_slice)

        # handle input params
        input_params, offset = utility_calls.translate_parameters(
            self._input_type.get_input_type_parameter_types(),
            byte_array, offset, vertex_slice)
        self._input_type.set_input_type_parameters(input_params, vertex_slice)

        # handle additional input params, if they exist
        if self._additional_input is not None:
            additional_params, offset = utility_calls.translate_parameters(
                self._additional_input.get_parameter_types(),
                byte_array, offset, vertex_slice)
            self._additional_input.set_parameters(
                additional_params, vertex_slice)

        # handle threshold type params
        threshold_params, offset = utility_calls.translate_parameters(
            self._threshold_type.get_threshold_parameter_types(),
            byte_array, offset, vertex_slice)
        self._threshold_type.set_threshold_parameters(
            threshold_params, vertex_slice)

        # Read synapse parameters
        self._synapse_manager.read_parameters_from_machine(
            transceiver, placement, vertex_slice)

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

    def set_synapse_dynamics(self, synapse_dynamics):
        self._synapse_manager.synapse_dynamics = synapse_dynamics

    def add_pre_run_connection_holder(
            self, connection_holder, edge, synapse_info):
        self._synapse_manager.add_pre_run_connection_holder(
            connection_holder, edge, synapse_info)

    @overrides(AbstractAcceptsIncomingSynapses.get_connections_from_machine)
    def get_connections_from_machine(
            self, transceiver, placement, edge, graph_mapper, routing_infos,
            synapse_information, machine_time_step, using_extra_monitor_cores,
            placements=None, data_receiver=None,
            sender_extra_monitor_core_placement=None,
            extra_monitor_cores_for_router_timeout=None,
            handle_time_out_configuration=True):
        return self._synapse_manager.get_connections_from_machine(
            transceiver, placement, edge, graph_mapper,
            routing_infos, synapse_information, machine_time_step, self._max_feasible_atoms_per_core,
            using_extra_monitor_cores, placements, data_receiver,
            sender_extra_monitor_core_placement,
            extra_monitor_cores_for_router_timeout,
            handle_time_out_configuration)

    def clear_connection_cache(self):
        self._synapse_manager.clear_connection_cache()

    @property
    def synapse_type(self):
        return self._synapse_manager.synapse_type

    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        return self._synapse_manager.get_maximum_delay_supported_in_ms(
            machine_time_step)

    @overrides(AbstractProvidesIncomingPartitionConstraints.
               get_incoming_partition_constraints)
    def get_incoming_partition_constraints(self, partition):
        """ Gets the constraints for partitions going into this vertex

        :param partition: partition that goes into this vertex
        :return: list of constraints
        """
        return self._synapse_manager.get_incoming_partition_constraints()

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        """ Gets the constraints for partitions going out of this vertex

        :param partition: the partition that leaves this vertex
        :return: list of constraints
        """
        return [ContiguousKeyRangeContraint()]

    @overrides(
        AbstractNeuronRecordable.clear_recording)
    def clear_recording(
            self, variable, buffer_manager, placements, graph_mapper):
        self._clear_recording_region(
            buffer_manager, placements, graph_mapper,
            self.RECORDING_REGION[variable])

    @overrides(AbstractSpikeRecordable.clear_spike_recording)
    def clear_spike_recording(self, buffer_manager, placements, graph_mapper):
        self._clear_recording_region(
            buffer_manager, placements, graph_mapper,
            AbstractPopulationVertex.SPIKE_RECORDING_REGION)

    def _clear_recording_region(
            self, buffer_manager, placements, graph_mapper,
            recording_region_id):
        """ clears a recorded data region from the buffer manager

        :param buffer_manager: the buffer manager object
        :param placements: the placements object
        :param graph_mapper: the graph mapper object
        :param recording_region_id: the recorded region id for clearing
        :rtype: None
        """
        machine_vertices = graph_mapper.get_machine_vertices(self)
        for machine_vertex in machine_vertices:
            placement = placements.get_placement_of_vertex(machine_vertex)
            buffer_manager.clear_recorded_data(
                placement.x, placement.y, placement.p, recording_region_id)

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        # search the model components for the variable
        for obj in [self._neuron_model, self._input_type,
                    self._threshold_type, self._synapse_manager.synapse_type,
                    self._additional_input]:
            if (hasattr(obj, variable) and
                    isinstance(obj, AbstractContainsUnits)):
                return obj.unit(variable)
        # if not in the components, must be within myself, so call my own units
        if variable in self._units:
            return self._units[variable]
        else:
            raise InvalidParameterType(
                "The parameter {} does not exist in this input "
                "conductance component".format(variable))

    def describe(self):
        """
        Returns a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template
        together with an associated template engine
        (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template context
        will be returned.
        """
        parameters = dict()
        for parameter_name in self.default_parameters:
            parameters[parameter_name] = self.get_value(parameter_name)

        context = {
            "name": self._model_name,
            "default_parameters": self.default_parameters,
            "default_initial_values": self.default_parameters,
            "parameters": parameters,
        }
        return context

    def __str__(self):
        return "{} with {} atoms".format(self.label, self.n_atoms)

    def __repr__(self):
        return self.__str__()
