# dsg imports
import struct
from data_specification import utility_calls as dsg_utilities
from data_specification.enums.data_type import DataType

# pacman imports
from pacman.model.abstract_classes.abstract_has_global_max_atoms import \
    AbstractHasGlobalMaxAtoms
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint
from pacman.model.decorators.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from pacman.model.graphs.application.impl.application_vertex \
    import ApplicationVertex
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource

# front end common imports
from spinn_front_end_common.abstract_models \
    .abstract_binary_uses_simulation_run import \
    AbstractBinaryUsesSimulationRun
from spinn_front_end_common.abstract_models. \
    abstract_changable_after_run import AbstractChangableAfterRun
from spinn_front_end_common.abstract_models. \
    abstract_provides_incoming_partition_constraints import \
    AbstractProvidesIncomingPartitionConstraints
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_partition_constraints import \
    AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.abstract_models. \
    abstract_requires_rewriting_data_regions_application_vertex \
    import AbstractRequiresRewriteDataRegionsApplicationVertex
from spinn_front_end_common.utilities import constants as \
    common_constants
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.abstract_models\
    .abstract_generates_data_specification \
    import AbstractGeneratesDataSpecification
from spinn_front_end_common.abstract_models.abstract_has_associated_binary \
    import AbstractHasAssociatedBinary
from spinn_front_end_common.interface.buffer_management\
    import recording_utilities
from spinn_front_end_common.utilities import helpful_functions

# spynnaker imports
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neuron.synaptic_manager import SynapticManager
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.abstract_models.abstract_population_initializable \
    import AbstractPopulationInitializable
from spynnaker.pyNN.models.abstract_models.abstract_population_settable \
    import AbstractPopulationSettableApplicationVertex
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
from spynnaker.pyNN.models.neuron.population_machine_vertex \
    import PopulationMachineVertex

from abc import ABCMeta
from six import add_metaclass
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


@add_metaclass(ABCMeta)
class AbstractPopulationVertex(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary, AbstractBinaryUsesSimulationRun,
        AbstractSpikeRecordable, AbstractVRecordable, AbstractGSynRecordable,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractProvidesIncomingPartitionConstraints,
    AbstractPopulationInitializable,
    AbstractPopulationSettableApplicationVertex,
    AbstractChangableAfterRun, AbstractHasGlobalMaxAtoms,
    AbstractRequiresRewriteDataRegionsApplicationVertex):
    """ Underlying vertex model for Neural Populations.
    """

    BASIC_MALLOC_USAGE = 2
    SPIKE_RECORDING_REGION = 0
    V_RECORDING_REGION = 1
    GSYN_RECORDING_REGION = 2
    RUNTIME_SDP_PORT_SIZE = 4  # the size of the runtime sdp port data region
    BYTES_TILL_START_OF_GLOBAL_PARAMETERS = 24

    _n_vertices = 0

    def __init__(
            self, n_neurons, binary, label, max_atoms_per_core,
            spikes_per_second, ring_buffer_sigma, incoming_spike_buffer_size,
            model_name, neuron_model, input_type, synapse_type, threshold_type,
            additional_input=None, constraints=None):

        ApplicationVertex.__init__(
            self, label, constraints, max_atoms_per_core)
        AbstractSpikeRecordable.__init__(self)
        AbstractVRecordable.__init__(self)
        AbstractGSynRecordable.__init__(self)
        AbstractProvidesOutgoingPartitionConstraints.__init__(self)
        AbstractProvidesIncomingPartitionConstraints.__init__(self)
        AbstractPopulationInitializable.__init__(self)
        AbstractPopulationSettableApplicationVertex.__init__(self)
        AbstractChangableAfterRun.__init__(self)
        AbstractHasGlobalMaxAtoms.__init__(self)
        AbstractRequiresRewriteDataRegionsApplicationVertex.__init__(self)

        self._binary = binary
        self._n_atoms = n_neurons

        # buffer data
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
        self._spike_recorder = SpikeRecorder()
        self._v_recorder = VRecorder()
        self._gsyn_recorder = GsynRecorder()
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
            spike_buffer_max_size, v_buffer_max_size, gsyn_buffer_max_size
        ]

        # Set up synapse handling
        self._synapse_manager = SynapticManager(
            synapse_type, ring_buffer_sigma, spikes_per_second)

        # bool for if state has changed.
        self._change_requires_mapping = True
        self._change_requires_neuron_parameters_reload = False

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
            self._get_buffered_sdram_per_timestep(vertex_slice),
            n_machine_time_steps, self._minimum_buffer_sdram,
            self._maximum_sdram_for_buffering,
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
        self._change_requires_neuron_parameters_reload = False

    def _get_buffered_sdram_per_timestep(self, vertex_slice):
        return [
            self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, 1),
            self._v_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, 1),
            self._gsyn_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, 1)
        ]

    @inject_items({"n_machine_time_steps": "TotalMachineTimeSteps"})
    @overrides(
        ApplicationVertex.create_machine_vertex,
        additional_arguments={"n_machine_time_steps"})
    def create_machine_vertex(
            self, vertex_slice, resources_required, n_machine_time_steps,
            label=None, constraints=None):

        is_recording = (
            self._gsyn_recorder.record_gsyn or self._v_recorder.record_v or
            self._spike_recorder.record
        )
        buffered_sdram_per_timestep = self._get_buffered_sdram_per_timestep(
            vertex_slice)
        minimum_buffer_sdram = recording_utilities.get_minimum_buffer_sdram(
            buffered_sdram_per_timestep, n_machine_time_steps,
            self._minimum_buffer_sdram)
        vertex = PopulationMachineVertex(
            resources_required, is_recording, minimum_buffer_sdram,
            buffered_sdram_per_timestep, label, constraints)

        self._n_vertices += 1

        # return machine vertex
        return vertex

    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        return self._synapse_manager.get_maximum_delay_supported_in_ms(
            machine_time_step)

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
                self._spike_recorder.get_n_cpu_cycles(vertex_slice.n_atoms) +
                self._v_recorder.get_n_cpu_cycles(vertex_slice.n_atoms) +
                self._gsyn_recorder.get_n_cpu_cycles(vertex_slice.n_atoms) +
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
                self._spike_recorder.get_dtcm_usage_in_bytes() +
                self._v_recorder.get_dtcm_usage_in_bytes() +
                self._gsyn_recorder.get_dtcm_usage_in_bytes() +
                self._synapse_manager.get_dtcm_usage_in_bytes())

    def _get_sdram_usage_for_neuron_params_per_neuron(self):
        per_neuron_usage = (
            self._input_type.get_sdram_usage_per_neuron_in_bytes() +
            self._threshold_type.get_sdram_usage_per_neuron_in_bytes() +
            self._neuron_model.get_sdram_usage_per_neuron_in_bytes())
        if self._additional_input is not None:
            per_neuron_usage += \
                self._additional_input.get_sdram_usage_per_neuron_in_bytes()
        return per_neuron_usage

    def _get_sdram_usage_for_neuron_params(self, vertex_slice):
        per_neuron_usage = \
            self._get_sdram_usage_for_neuron_params_per_neuron()
        return (self.BYTES_TILL_START_OF_GLOBAL_PARAMETERS + (
            per_neuron_usage * vertex_slice.n_atoms))

    def get_sdram_usage_for_atoms(
            self, vertex_slice, graph, machine_time_step):
        sdram_requirement = (
            common_constants.SYSTEM_BYTES_REQUIREMENT +
            self._get_sdram_usage_for_neuron_params(vertex_slice) +
            recording_utilities.get_recording_header_size(3) +
            PopulationMachineVertex.get_provenance_data_size(
                PopulationMachineVertex.N_ADDITIONAL_PROVENANCE_DATA_ITEMS) +
            self._synapse_manager.get_sdram_usage_in_bytes(
                vertex_slice, graph.get_edges_ending_at_vertex(self),
                machine_time_step) +
            (self._get_number_of_mallocs_used_by_dsg() *
             common_constants.SARK_PER_MALLOC_SDRAM_USAGE))

        return sdram_requirement

    def _get_number_of_mallocs_used_by_dsg(self):
        extra_mallocs = 0
        if self._gsyn_recorder.record_gsyn:
            extra_mallocs += 1
        if self._v_recorder.record_v:
            extra_mallocs += 1
        if self._spike_recorder.record:
            extra_mallocs += 1
        return (
            self.BASIC_MALLOC_USAGE +
            self._synapse_manager.get_number_of_mallocs_used_by_dsg() +
            extra_mallocs)

    def _reserve_memory_regions(self, spec, vertex_slice, vertex):

        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.SYSTEM.value,
            size=common_constants.SYSTEM_BYTES_REQUIREMENT, label='System')

        self._reverse_neuron_params_data_region(spec, vertex_slice)

        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.RECORDING.value,
            size=recording_utilities.get_recording_header_size(3))

        # reserve runtime sdp command port region
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.RUNTIME_SDP_PORT.value,
            size=self.RUNTIME_SDP_PORT_SIZE)

        vertex.reserve_provenance_data_region(spec)

    def _reverse_neuron_params_data_region(self, spec, vertex_slice):
        """
        
        :param spec:
        :param vertex_slice:
        :return:
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

    @staticmethod
    def _write_neuron_sdp_commands_port(spec):
        """

        :param spec: the data specification spec object
        :return: None
        """
        # Set the focus to the memory region 8 (RUNTIME_SDP_PORT):
        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.RUNTIME_SDP_PORT.value)
        spec.write_value(constants.SDP_PORTS.NEURON_COMMANDS_SDP_PORT.value,
                         data_type=DataType.UINT32)

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
        """ returns the data region and its data that needs re loading

        :return: dict of data region id and the byte array to load there.
        """

        # store for more regions as needed
        regions_and_data = dict()

        # if the neuron parameters need changing, generate dsg for neuron
        # params
        if self._change_requires_neuron_parameters_reload:
            # get new dsg writer
            filepath, spec = \
                dsg_utilities.get_data_spec_and_file_writer_filename(
                    placement.x, placement.y, placement.p,
                    hostname, report_directory, write_text_specs,
                    reload_application_data_file_path)

            # reserve the neuron parmas data region
            self._reverse_neuron_params_data_region(
                spec, graph_mapper.get_slice(placement.vertex))

            # write the neuron params into the new dsg region
            self._write_neuron_parameters(
                key=routing_info.get_first_key_from_pre_vertex(
                    placement.vertex, constants.SPIKE_PARTITION_ID),
                machine_time_step=machine_time_step, spec=spec,
                time_scale_factor=time_scale_factor,
                vertex_slice=graph_mapper.get_slice(placement.vertex))

            # close spec
            spec.end_specification()

            # store dsg region to spec data mapping
            regions_and_data[
                constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value] = \
                filepath

        # return mappings
        return regions_and_data

    @overrides(AbstractRequiresRewriteDataRegionsApplicationVertex.
               requires_memory_regions_to_be_reloaded)
    def requires_memory_regions_to_be_reloaded(self):
        return self._change_requires_neuron_parameters_reload

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
            n_machine_time_steps,
            self._get_buffered_sdram_per_timestep(vertex_slice),
            self._maximum_sdram_for_buffering)
        spec.write_array(recording_utilities.get_recording_header_array(
            recorded_region_sizes, self._time_between_requests,
            self._buffer_size_before_receive, ip_tags))

        # Write the neuron parameters
        self._write_neuron_parameters(
            spec, key, vertex_slice, machine_time_step, time_scale_factor)

        # allow the synaptic matrix to write its data spec-able data
        self._synapse_manager.write_data_spec(
            spec, self, vertex_slice, vertex, placement, machine_graph,
            application_graph, routing_info, graph_mapper,
            self._input_type, machine_time_step)

        # write the sdp port number expected to be received for the neuron
        # sdp commands
        self._write_neuron_sdp_commands_port(spec)

        # End the writing of this specification:
        spec.end_specification()

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):

        # Split binary name into title and extension
        binary_title, binary_extension = os.path.splitext(self._binary)

        # Reunite title and extension and return
        return (binary_title + self._synapse_manager.vertex_executable_suffix +
                binary_extension)

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self._spike_recorder.record

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(self):
        self._change_requires_mapping = not self._spike_recorder.record
        self._spike_recorder.record = True

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(
            self, placements, graph_mapper, buffer_manager, machine_time_step):
        return self._spike_recorder.get_spikes(
            self._label, buffer_manager, self.SPIKE_RECORDING_REGION,
            placements, graph_mapper, self, machine_time_step)

    @overrides(AbstractVRecordable.is_recording_v)
    def is_recording_v(self):
        return self._v_recorder.record_v

    @overrides(AbstractVRecordable.set_recording_v)
    def set_recording_v(self):
        self._change_requires_mapping = not self._v_recorder.record_v
        self._v_recorder.record_v = True

    @overrides(AbstractVRecordable.get_v)
    def get_v(self, n_machine_time_steps, placements, graph_mapper,
              buffer_manager, machine_time_step):
        return self._v_recorder.get_v(
            self._label, buffer_manager, self.V_RECORDING_REGION,
            placements, graph_mapper, self, machine_time_step)

    @overrides(AbstractGSynRecordable.is_recording_gsyn)
    def is_recording_gsyn(self):
        return self._gsyn_recorder.record_gsyn

    @overrides(AbstractGSynRecordable.set_recording_gsyn)
    def set_recording_gsyn(self):
        self._change_requires_mapping = not self._gsyn_recorder.record_gsyn
        self._gsyn_recorder.record_gsyn = True

    @overrides(AbstractGSynRecordable.get_gsyn)
    def get_gsyn(
            self, n_machine_time_steps, placements, graph_mapper,
            buffer_manager, machine_time_step):
        return self._gsyn_recorder.get_gsyn(
            self._label, buffer_manager, self.GSYN_RECORDING_REGION,
            placements, graph_mapper, self, machine_time_step)

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
    def synapse_type(self):
        return self._synapse_manager.synapse_type

    @property
    def input_type(self):
        return self._input_type

    @overrides(AbstractPopulationSettableApplicationVertex.get_value)
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

    @overrides(AbstractPopulationSettableApplicationVertex.set_value)
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
        raise Exception("Type {} does not have parameter {}".format(
            self._model_name, key))

    @overrides(AbstractPopulationSettableApplicationVertex.
               read_neuron_parameters_from_machine)
    def read_neuron_parameters_from_machine(
            self, transceiver, placement, vertex_slice):
        """ reads in the neuron parameters from the machine and stores them
        in the neuron components.

        :param transceiver: the spinnman interface
        :param placement: the placement of the vertex
        :return: None
        """

        # locate sdram address to where the neuron parameters are stored
        neuron_region_sdram_address = \
            helpful_functions.locate_memory_region_for_placement(
                placement,
                constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value,
                transceiver)

        neuron_parameters_sdram_address = \
            (neuron_region_sdram_address +
             self.BYTES_TILL_START_OF_GLOBAL_PARAMETERS)

        size_of_region = self._get_sdram_usage_for_neuron_params(vertex_slice)
        size_of_region -= self.BYTES_TILL_START_OF_GLOBAL_PARAMETERS

        # get data from the machine
        byte_array = transceiver.read_memory(
            placement.x, placement.y, neuron_parameters_sdram_address,
            size_of_region)

        # update python neuron parameters with the data
        position_in_byte_array = 0

        for atom in range(vertex_slice.lo_atom, vertex_slice.hi_atom):
            # handle global params for a neuron
            global_params = self._neuron_model.translate_into_global_params(
                byte_array, position_in_byte_array)
            self._neuron_model.set_global_parameters(global_params, atom)
            position_in_byte_array += \
                self._neuron_model.global_param_memory_size_in_bytes()

            # handle state params for a neuron
            state_params = self._neuron_model.translate_into_neural_params(
                byte_array, position_in_byte_array)
            self._neuron_model.set_neural_parameters(state_params, atom)
            position_in_byte_array += \
                self._neuron_model.neural_param_memory_size_in_bytes()

            # handle input params
            input_params = self._input_type.translate_into_parameters(
                byte_array, position_in_byte_array)
            self._input_type.set_parameters(input_params, atom)
            position_in_byte_array += \
                self._input_type.params_memory_size_in_bytes()

            # handle additional input params
            additional_input_params = \
                self._additional_input.translate_into_parameters(
                    byte_array, position_in_byte_array)
            self._additional_input.set_parameters(
                additional_input_params, atom)
            position_in_byte_array += \
                self._additional_input.params_memory_size_in_bytes()

            # handle threshold type params
            threshold_params = self._threshold_type.translate_into_parameters(
                byte_array, position_in_byte_array)
            self._threshold_type.set_parameters(threshold_params, atom)
            position_in_byte_array += \
                self._threshold_type.params_memory_size_in_bytes()

        if len(byte_array) != position_in_byte_array:
            raise exceptions.MemReadException(
                "Ive not read enough data for translating neuron params from"
                " the machine")

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
            self, transceiver, placement, edge, graph_mapper,
            routing_infos, synapse_info, machine_time_step):
        return self._synapse_manager.get_connections_from_machine(
            transceiver, placement, edge, graph_mapper,
            routing_infos, synapse_info, machine_time_step)

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
        return [KeyAllocatorContiguousRangeContraint()]

    def __str__(self):
        return "{} with {} atoms".format(self._label, self.n_atoms)

    def __repr__(self):
        return self.__str__()
