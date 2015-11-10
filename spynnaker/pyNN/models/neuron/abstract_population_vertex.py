from abc import ABCMeta
from six import add_metaclass
import logging
import os

from spinn_front_end_common.utility_models.\
    outgoing_edge_same_contiguous_keys_restrictor import \
    OutgoingEdgeSameContiguousKeysRestrictor
from spinn_front_end_common.abstract_models.\
    abstract_provides_incoming_edge_constraints import \
    AbstractProvidesIncomingEdgeConstraints
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_edge_constraints import \
    AbstractProvidesOutgoingEdgeConstraints
from spynnaker.pyNN.models.neuron.synaptic_manager import SynapticManager
from spynnaker.pyNN.utilities import utility_calls
from data_specification.data_specification_generator \
    import DataSpecificationGenerator
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
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

import tempfile

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
        AbstractPartitionableVertex, AbstractDataSpecableVertex,
        AbstractSpikeRecordable, AbstractVRecordable, AbstractGSynRecordable,
        AbstractProvidesOutgoingEdgeConstraints,
        AbstractProvidesIncomingEdgeConstraints):
    """ Underlying vertex model for Neural Populations.
    """

    def __init__(self, n_neurons, binary, label, max_atoms_per_core,
                 machine_time_step, timescale_factor, spikes_per_second,
                 ring_buffer_sigma, model_name, neuron_model, input_type,
                 synapse_type, threshold_type, additional_input=None,
                 constraints=None):

        AbstractPartitionableVertex.__init__(
            self, n_neurons, label, max_atoms_per_core, constraints)
        AbstractDataSpecableVertex.__init__(
            self, machine_time_step, timescale_factor)
        AbstractSpikeRecordable.__init__(self)
        AbstractVRecordable.__init__(self)
        AbstractGSynRecordable.__init__(self)

        self._binary = binary
        self._label = label
        self._machine_time_step = machine_time_step
        self._timescale_factor = timescale_factor

        self._model_name = model_name
        self._neuron_model = neuron_model
        self._input_type = input_type
        self._threshold_type = threshold_type
        self._additional_input = additional_input

        # Set up for recording
        self._spike_recorder = SpikeRecorder(machine_time_step)
        self._v_recorder = VRecorder(machine_time_step)
        self._gsyn_recorder = GsynRecorder(machine_time_step)

        # Set up synapse handling
        self._synapse_manager = SynapticManager(
            synapse_type, machine_time_step, ring_buffer_sigma,
            spikes_per_second)

        # set up continious restrictor
        self._outgoing_edge_key_restrictor = \
            OutgoingEdgeSameContiguousKeysRestrictor()

        # bool for if state has changed.
        self._change_requires_mapping = True

    @property
    def change_requires_mapping(self):
        """
        property for checking if someting has changed
        :return:
        """
        return self._change_requires_mapping

    @change_requires_mapping.setter
    def change_requires_mapping(self, new_value):
        """
        setter for the changed property
        :param new_value: the new state to change it to
        :return:
        """
        self._change_requires_mapping = new_value

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
        return (_NEURON_BASE_SDRAM_USAGE_IN_BYTES +
                (per_neuron_usage * vertex_slice.n_atoms) +
                self._neuron_model.get_sdram_usage_in_bytes(
                    vertex_slice.n_atoms))

    # @implements AbstractPopulationVertex.get_sdram_usage_for_atoms
    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        return (self._get_sdram_usage_for_neuron_params(vertex_slice) +
                self._spike_recorder.get_sdram_usage_in_bytes(
                    vertex_slice.n_atoms, self._no_machine_time_steps) +
                self._v_recorder.get_sdram_usage_in_bytes(
                    vertex_slice.n_atoms, self._no_machine_time_steps) +
                self._gsyn_recorder.get_sdram_usage_in_bytes(
                    vertex_slice.n_atoms, self._no_machine_time_steps) +
                self._synapse_manager.get_sdram_usage_in_bytes(
                    vertex_slice, graph.incoming_edges_to_vertex(self)))

    # @implements AbstractPopulationVertex.model_name
    def model_name(self):
        return self._model_name

    def _reserve_memory_regions(
            self, spec, vertex_slice, spike_history_region_sz,
            v_history_region_sz, gsyn_history_region_sz):

        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.SYSTEM.value,
            size=constants.POPULATION_SYSTEM_REGION_BYTES, label='System')

        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value,
            size=self._get_sdram_usage_for_neuron_params(vertex_slice),
            label='NeuronParams')

        if self._spike_recorder.record:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.SPIKE_HISTORY.value,
                size=spike_history_region_sz, label='spikeHistBuffer',
                empty=True)
        if self._v_recorder.record_v:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.POTENTIAL_HISTORY
                                                         .value,
                size=v_history_region_sz, label='vHistBuffer',
                empty=True)
        if self._gsyn_recorder.record_gsyn:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.GSYN_HISTORY.value,
                size=gsyn_history_region_sz, label='gsynHistBuffer',
                empty=True)

    def _write_setup_info(self, spec, spike_history_region_sz,
                          neuron_potential_region_sz, gsyn_region_sz):
        """ Write information used to control the simulation and gathering of\
            results.

        The format of the information is as follows:
        Word 0: Flags selecting data to be gathered during simulation.
            Bit 0: Record spike history
            Bit 1: Record neuron potential
            Bit 2: Record gsyn values
            Bit 3: Reserved
        """
        # What recording commands were set for the parent pynn_population.py?
        recording_info = 0
        if spike_history_region_sz > 0 and self._spike_recorder.record:
            recording_info |= constants.RECORD_SPIKE_BIT
        if neuron_potential_region_sz > 0 and self._v_recorder.record_v:
            recording_info |= constants.RECORD_STATE_BIT
        if gsyn_region_sz > 0 and self._gsyn_recorder.record_gsyn:
            recording_info |= constants.RECORD_GSYN_BIT
        recording_info |= 0xBEEF0000

        # Write this to the system region (to be picked up by the simulation):
        self._write_basic_setup_info(
            spec, constants.POPULATION_BASED_REGIONS.SYSTEM.value)
        spec.write_value(data=recording_info)
        spec.write_value(data=spike_history_region_sz)
        spec.write_value(data=neuron_potential_region_sz)
        spec.write_value(data=gsyn_region_sz)

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

        # Write the global parameters
        global_params = self._neuron_model.get_global_parameters()
        for param in global_params:
            spec.write_value(data=param.get_value(),
                             data_type=param.get_dataspec_datatype())

        # Write the neuron paramters
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
            self, subvertex, placement, subgraph, graph, routing_info,
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

        # Get recording sizes
        spike_history_sz = self._spike_recorder.get_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self._no_machine_time_steps)
        v_history_sz = self._v_recorder.get_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self._no_machine_time_steps)
        gsyn_history_sz = self._gsyn_recorder.get_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self._no_machine_time_steps)

        # Reserve memory regions
        self._reserve_memory_regions(
            spec, vertex_slice, spike_history_sz, v_history_sz,
            gsyn_history_sz)

        # Declare random number generators and distributions:
        # TODO add random distrubtion stuff
        # self.write_random_distribution_declarations(spec)

        # Get the key - use only the first edge
        key = None
        if len(subgraph.outgoing_subedges_from_subvertex(subvertex)) > 0:
            keys_and_masks = routing_info.get_keys_and_masks_from_subedge(
                subgraph.outgoing_subedges_from_subvertex(subvertex)[0])

            # NOTE: using the first key assigned as the key.  Should in future
            # get the list of keys and use one per neuron, to allow arbitrary
            # key and mask assignments
            key = keys_and_masks[0].key

        # Write the regions
        self._write_setup_info(
            spec, spike_history_sz, v_history_sz, gsyn_history_sz)
        self._write_neuron_parameters(spec, key, vertex_slice)

        # allow the synaptic matrix to write its data specable data
        self._synapse_manager.write_data_spec(
            spec, self, vertex_slice, subvertex, placement, subgraph, graph,
            routing_info, hostname, graph_mapper)

        # End the writing of this specification:
        spec.end_specification()
        data_writer.close()

        return [data_writer.filename]

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
        self._spike_recorder.record = True

    # @implements AbstractSpikeRecordable.reset
    def reset(self):
        self._spike_recorder.reset()
        self._v_recorder.reset()
        self._gsyn_recorder.reset()

    # @implements AbstractSpikeRecordable.get_spikes
    def get_spikes(self, transceiver, n_machine_time_steps, placements,
                   graph_mapper, return_data=True):
        return self._spike_recorder.get_spikes(
            self._label, transceiver,
            constants.POPULATION_BASED_REGIONS.SPIKE_HISTORY.value,
            n_machine_time_steps, placements, graph_mapper, self, return_data)

    # @implements AbstractVRecordable.is_recording_v
    def is_recording_v(self):
        return self._v_recorder.record_v

    # @implements AbstractVRecordable.set_recording_v
    def set_recording_v(self):
        self._v_recorder.record_v = True

    # @implements AbstractVRecordable.get_v
    def get_v(self, transceiver, n_machine_time_steps, placements,
              graph_mapper, return_data=True):
        return self._v_recorder.get_v(
            self._label, self.n_atoms, transceiver,
            constants.POPULATION_BASED_REGIONS.POTENTIAL_HISTORY.value,
            n_machine_time_steps, placements, graph_mapper, self, return_data)

    # @implements AbstractGSynRecordable.is_recording_gsyn
    def is_recording_gsyn(self):
        return self._gsyn_recorder.record_gsyn

    # @implements AbstractGSynRecordable.set_recording_gsyn
    def set_recording_gsyn(self):
        self._gsyn_recorder.record_gsyn = True

    # @implements AbstractGSynRecordable.get_gsyn
    def get_gsyn(self, transceiver, n_machine_time_steps, placements,
                 graph_mapper, return_data=True):
        return self._gsyn_recorder.get_gsyn(
            self._label, self.n_atoms, transceiver,
            constants.POPULATION_BASED_REGIONS.GSYN_HISTORY.value,
            n_machine_time_steps, placements, graph_mapper, self, return_data)

    def initialize(self, variable, value):
        initialize_attr = getattr(
            self._neuron_model, "initialize_%s" % variable, None)
        if initialize_attr is None or not callable(initialize_attr):
            raise Exception("Vertex does not support initialization of"
                            " parameter {}".format(variable))
        initialize_attr(value)

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

    def get_synaptic_list_from_machine(
            self, placements, transceiver, pre_subvertex, pre_n_atoms,
            post_subvertex, synapse_io, subgraph, routing_infos,
            weight_scales):
        return self._synapse_manager.get_synaptic_list_from_machine(
            placements, transceiver, pre_subvertex, pre_n_atoms,
            post_subvertex, synapse_io, subgraph, routing_infos, weight_scales)

    def is_data_specable(self):
        return True

    def get_incoming_edge_constraints(self, partitioned_edge, graph_mapper):
        """
        gets the constraints for edges going into this vertex
        :param partitioned_edge: partitioned edge that goes into this vertex
        :param graph_mapper: the graph mapper object
        :return: list of constraints
        """
        return self._synapse_manager.get_incoming_edge_constraints()

    def get_outgoing_edge_constraints(self, partitioned_edge, graph_mapper):
        """
        gets the constraints for edges going out of this vertex
        :param partitioned_edge: the parittioned edge that leaves this vertex
        :param graph_mapper: the graph mapper object
        :return: list of constraints
        """
        return self._outgoing_edge_key_restrictor.\
            get_outgoing_edge_constraints()

    def __str__(self):
        return "{} with {} atoms".format(self._label, self.n_atoms)

    def __repr__(self):
        return self.__str__()
