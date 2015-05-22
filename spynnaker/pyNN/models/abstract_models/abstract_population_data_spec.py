"""
AbstractPopulationDataSpec
"""

# data specable imports
from data_specification.data_specification_generator import \
    DataSpecificationGenerator

# spynnaker imports
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_synaptic_manager \
    import AbstractSynapticManager
from spynnaker.pyNN.models.abstract_models.\
    abstract_partitionable_population_vertex \
    import AbstractPartitionablePopulationVertex

from spinn_front_end_common.abstract_models\
    .abstract_outgoing_edge_same_contiguous_keys_restrictor\
    import AbstractOutgoingEdgeSameContiguousKeysRestrictor

# general imports
import os
import logging
from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPopulationDataSpec(
        AbstractSynapticManager, AbstractPartitionablePopulationVertex,
        AbstractOutgoingEdgeSameContiguousKeysRestrictor):
    """
    AbstractPopulationDataSpec: provides functioanlity on how neural models
    generate their data spec files
    """

    def __init__(self, binary, n_neurons, label, constraints,
                 max_atoms_per_core, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma,
                 master_pop_algorithm=None):
        AbstractSynapticManager.__init__(self, master_pop_algorithm)
        AbstractPartitionablePopulationVertex.__init__(
            self, n_atoms=n_neurons, label=label,
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)
        AbstractOutgoingEdgeSameContiguousKeysRestrictor.__init__(self)
        self._binary = binary
        self._executable_constant = None
        self._spikes_per_second = spikes_per_second
        self._ring_buffer_sigma = ring_buffer_sigma

    def _reserve_population_based_memory_regions(
            self, spec, neuron_params_sz, synapse_params_sz,
            master_pop_table_sz, all_syn_block_sz,
            spike_hist_buff_sz, potential_hist_buff_sz, gsyn_hist_buff_sz,
            synapse_dynamics_params_sz):
        """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        2) Neuron parameter data (will be copied to DTCM by 'C'
           code at start-up)
        3) synapse parameter data (will be copied to DTCM)
        5) Synaptic block look-up table. Translates the start address
           of each block of synapses (copied to DTCM)
        6) Synaptic row data (lives in SDRAM)
        7) Spike history
        8) Neuron potential history
        9) Gsyn value history
        """

        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.SYSTEM.value,
            size=constants.POPULATION_SYSTEM_REGION_BYTES, label='System')
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value,
            size=neuron_params_sz, label='NeuronParams')
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value,
            size=synapse_params_sz, label='SynapseParams')

        if master_pop_table_sz > 0:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.POPULATION_TABLE
                                                         .value,
                size=master_pop_table_sz, label='PopTable')

        if all_syn_block_sz > 0:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX
                                                         .value,
                size=all_syn_block_sz, label='SynBlocks')

        if synapse_dynamics_params_sz != 0:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS
                                                         .value,
                size=synapse_dynamics_params_sz, label='synapseDynamicsParams')

        if self._record:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.SPIKE_HISTORY.value,
                size=spike_hist_buff_sz, label='spikeHistBuffer',
                empty=True)
        if self._record_v:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.POTENTIAL_HISTORY
                                                         .value,
                size=potential_hist_buff_sz, label='potHistBuffer',
                empty=True)
        if self._record_gsyn:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.GSYN_HISTORY.value,
                size=gsyn_hist_buff_sz, label='gsynHistBuffer',
                empty=True)

    def _write_setup_info(self, spec, spike_history_region_sz,
                          neuron_potential_region_sz, gsyn_region_sz,
                          executable_constant):
        """
        Write information used to control the simulation and gathering of
        results.Currently, this means the flag word used to signal whether
        information on neuron firing and neuron potential is either stored
        locally in a buffer or passed out of the simulation for storage/display
         as the simulation proceeds.

        The format of the information is as follows:
        Word 0: Flags selecting data to be gathered during simulation.
            Bit 0: Record spike history
            Bit 1: Record neuron potential
            Bit 2: Record gsyn values
            Bit 3: Reserved
            Bit 4: Output spike history on-the-fly
            Bit 5: Output neuron potential
            Bit 6: Output spike rate
        """
        # What recording commands were set for the parent pynn_population.py?
        recording_info = 0
        if spike_history_region_sz > 0 and self._record:
            recording_info |= constants.RECORD_SPIKE_BIT
        if neuron_potential_region_sz > 0 and self._record_v:
            recording_info |= constants.RECORD_STATE_BIT
        if gsyn_region_sz > 0 and self._record_gsyn:
            recording_info |= constants.RECORD_GSYN_BIT
        recording_info |= 0xBEEF0000

        # Write this to the system region (to be picked up by the simulation):
        self._write_basic_setup_info(
            spec, executable_constant,
            constants.POPULATION_BASED_REGIONS.SYSTEM.value)
        spec.write_value(data=recording_info)
        spec.write_value(data=spike_history_region_sz)
        spec.write_value(data=neuron_potential_region_sz)
        spec.write_value(data=gsyn_region_sz)

    @abstractmethod
    def get_parameters(self):
        """
        method to return whatever params a model has
        """

    def _write_neuron_parameters(
            self, spec, key, subvertex, vertex_slice):

        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        spec.comment("\nWriting Neuron Parameters for {} "
                     "Neurons:\n".format(n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value)

        # Write header info to the memory region:

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

        # Write the number of parameters per neuron (struct size in words):
        params = self.get_parameters()

        # noinspection PyTypeChecker
        spec.write_value(data=len(params))

        # Write machine time step: (Integer, expressed in microseconds)
        spec.write_value(data=self._machine_time_step)

        # TODO: NEEDS TO BE LOOKED AT PROPERLY
        # Create loop over number of neurons:
        for atom in range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1):
            # Process the parameters

            # noinspection PyTypeChecker
            for param in params:
                value = param.get_value()
                if hasattr(value, "__len__"):
                    if len(value) > 1:
                        if len(value) <= atom:
                            raise Exception(
                                "Not enough parameters have been specified"
                                " for parameter of population {}".format(
                                    self.label))
                        value = value[atom]
                    else:
                        value = value[0]

                datatype = param.get_dataspec_datatype()

                spec.write_value(data=value, data_type=datatype)
        # End the loop over the neurons:

    def generate_data_spec(
            self, subvertex, placement, subgraph, graph, routing_info,
            hostname, graph_mapper, report_folder, ip_tags, reverse_ip_tags,
            write_text_specs, application_run_time_folder):
        """
        Model-specific construction of the data blocks necessary to
        build a group of IF_curr_exp neurons resident on a single core.
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
        # Create new DataSpec for this processor:
        data_writer, report_writer = \
            self.get_data_spec_file_writers(
                placement.x, placement.y, placement.p, hostname, report_folder,
                write_text_specs, application_run_time_folder)

        spec = DataSpecificationGenerator(data_writer, report_writer)

        spec.comment("\n*** Spec for block of {} neurons ***\n"
                     .format(self.model_name))

        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)

        # Calculate the size of the tables to be reserved in SDRAM:
        vertex_in_edges = graph.incoming_edges_to_vertex(self)
        neuron_params_sz = self.get_neuron_params_size(vertex_slice)
        synapse_params_sz = self.get_synapse_parameter_size(vertex_slice)
        master_pop_table_sz = self.get_population_table_size(vertex_slice,
                                                             vertex_in_edges)

        subvert_in_edges = subgraph.incoming_subedges_from_subvertex(subvertex)
        all_syn_block_sz = self.get_exact_synaptic_block_memory_size(
            graph_mapper, subvert_in_edges)

        spike_hist_buff_sz = self.get_spike_buffer_size(vertex_slice)
        potential_hist_buff_sz = self.get_v_buffer_size(vertex_slice)
        gsyn_hist_buff_sz = self.get_g_syn_buffer_size(vertex_slice)
        synapse_dynamics_region_sz = self.get_synapse_dynamics_parameter_size(
            vertex_in_edges)

        # Declare random number generators and distributions:
        # TODO add random distrubtion stuff
        # self.write_random_distribution_declarations(spec)

        ring_buffer_shifts = self.get_ring_buffer_to_input_left_shifts(
            subvertex, subgraph, graph_mapper, self._spikes_per_second,
            self._machine_time_step, self._ring_buffer_sigma)

        weight_scales = [self.get_weight_scale(r) for r in ring_buffer_shifts]

        if logger.isEnabledFor(logging.DEBUG):
            for t, r, w in zip(self.get_synapse_targets(), ring_buffer_shifts,
                               weight_scales):
                logger.debug(
                    "Synapse type:%s - Ring buffer shift:%d, Max weight:%f"
                    % (t, r, w))

        # update projections for future use
        in_partitioned_edges = \
            subgraph.incoming_subedges_from_subvertex(subvertex)
        for partitioned_edge in in_partitioned_edges:
            partitioned_edge.weight_scales_setter(weight_scales)

        # Construct the data images needed for the Neuron:
        self._reserve_population_based_memory_regions(
            spec, neuron_params_sz, synapse_params_sz,
            master_pop_table_sz, all_syn_block_sz,
            spike_hist_buff_sz, potential_hist_buff_sz, gsyn_hist_buff_sz,
            synapse_dynamics_region_sz)

        self._write_setup_info(spec, spike_hist_buff_sz,
                               potential_hist_buff_sz, gsyn_hist_buff_sz,
                               self._executable_constant)

        # Every outgoing edge from this vertex should have the same key
        key = None
        if len(subgraph.outgoing_subedges_from_subvertex(subvertex)) > 0:
            keys_and_masks = routing_info.get_keys_and_masks_from_subedge(
                subgraph.outgoing_subedges_from_subvertex(subvertex)[0])

            # NOTE: using the first key assigned as the key.  Should in future
            # get the list of keys and use one per neuron, to allow arbitrary
            # key and mask assignments
            key = keys_and_masks[0].key

        self._write_neuron_parameters(spec, key, subvertex, vertex_slice)

        self.write_synapse_parameters(spec, subvertex, vertex_slice)
        spec.write_array(ring_buffer_shifts)

        self.write_synaptic_matrix_and_master_population_table(
            spec, subvertex, all_syn_block_sz, weight_scales,
            constants.POPULATION_BASED_REGIONS.POPULATION_TABLE.value,
            constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
            routing_info, graph_mapper, subgraph)

        self.write_synapse_dynamics_parameters(
            spec, self._machine_time_step,
            constants.POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value,
            weight_scales)

        in_subedges = subgraph.incoming_subedges_from_subvertex(subvertex)
        for subedge in in_subedges:
            subedge.free_sublist()

        # End the writing of this specification:
        spec.end_specification()
        data_writer.close()

    # inherited from data specable vertex
    def get_binary_file_name(self):
        """

        :return:
        """

        # Split binary name into title and extension
        binary_title, binary_extension = os.path.splitext(self._binary)

        # If we have an STDP mechanism, add it's executable suffic to title
        if self._stdp_mechanism is not None:
            binary_title = \
                binary_title + "_" + \
                self._stdp_mechanism.get_vertex_executable_suffix()

        # Reunite title and extension and return
        return binary_title + binary_extension

    def is_data_specable(self):
        """
        helper method for isinstance
        :return:
        """
        return True
