import os
import logging
from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from data_specification.data_specification_generator import \
    DataSpecificationGenerator
from spinn_front_end_common.utilities import packet_conversions

from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_synaptic_manager import \
    AbstractSynapticManager
from spynnaker.pyNN.models.abstract_models.\
    abstract_partitionable_population_vertex import \
    AbstractPartitionablePopulationVertex
from spynnaker.pyNN import model_binaries


logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPopulationDataSpec(AbstractSynapticManager,
                                 AbstractPartitionablePopulationVertex):

    def __init__(self, binary, n_neurons, label, constraints, max_atoms_per_core,
                 machine_time_step):
        AbstractSynapticManager.__init__(self)
        AbstractPartitionablePopulationVertex.__init__(
            self, n_atoms=n_neurons, label=label,
            machine_time_step=machine_time_step, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)
        self._binary = binary
        self._executable_constant = None

    @abstractmethod
    def get_parameters(self):
        """
        method to return whatever params a model has
        """

    def reserve_population_based_memory_regions(
            self, spec, setup_sz, neuron_params_sz, synapse_params_sz,
            row_len_trans_sz, master_pop_table_sz, all_syn_block_sz,
            spike_hist_buff_sz, potential_hist_buff_sz, gsyn_hist_buff_sz,
            stdp_params_sz):
        """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        2) Neuron parameter data (will be copied to DTCM by 'C'
           code at start-up)
        3) synapse parameter data (will be copied to DTCM)
        4) Synaptic row length look-up (copied to DTCM)
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
            size=setup_sz, label='setup')
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value,
            size=neuron_params_sz, label='NeuronParams')
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value,
            size=synapse_params_sz, label='SynapseParams')
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.ROW_LEN_TRANSLATION.value,
            size=row_len_trans_sz, label='RowLenTable')
        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.MASTER_POP_TABLE.value,
            size=master_pop_table_sz, label='MasterPopTable')
        if all_syn_block_sz > 0:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
                size=all_syn_block_sz, label='SynBlocks')

        if self._record:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.SPIKE_HISTORY.value,
                size=spike_hist_buff_sz, label='spikeHistBuffer',
                empty=True)
        if self._record_v:
            spec.reserve_memory_region(
                region=
                constants.POPULATION_BASED_REGIONS.POTENTIAL_HISTORY.value,
                size=potential_hist_buff_sz, label='potHistBuffer',
                empty=True)
        if self._record_gsyn:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.GSYN_HISTORY.value,
                size=gsyn_hist_buff_sz, label='gsynHistBuffer',
                empty=True)
        if stdp_params_sz != 0:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.STDP_PARAMS.value,
                size=stdp_params_sz, label='stdpParams')

    def write_setup_info(self, spec, spike_history_region_sz,
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
        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.SYSTEM.value)
        spec.write_value(data=executable_constant)
        spec.write_value(data=self._machine_time_step)
        spec.write_value(data=self._no_machine_time_steps)
        spec.write_value(data=recording_info)
        spec.write_value(data=spike_history_region_sz)
        spec.write_value(data=neuron_potential_region_sz)
        spec.write_value(data=gsyn_region_sz)

    def write_neuron_parameters(
            self, spec, processor_chip_x, processor_chip_y, processor_id,
            subvertex, ring_buffer_to_input_left_shift, vertex_slice):

        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        spec.comment("\nWriting Neuron Parameters for {} "
                     "Neurons:\n".format(n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value)

        # Write header info to the memory region:
        # Write Key info for this core:
        population_identity = \
            packet_conversions.get_key_from_coords(processor_chip_x,
                                                   processor_chip_y,
                                                   processor_id)
        spec.write_value(data=population_identity)

        # Write the number of neurons in the block:
        spec.write_value(data=n_atoms)

        # Write the number of parameters per neuron (struct size in words):
        params = self.get_parameters()

        # noinspection PyTypeChecker
        spec.write_value(data=len(params))

        # Write machine time step: (Integer, expressed in microseconds)
        spec.write_value(data=self._machine_time_step)

        # Write ring_buffer_to_input_left_shift
        spec.write_value(data=ring_buffer_to_input_left_shift)

        # TODO: NEEDS TO BE LOOKED AT PROPERLY
        # Create loop over number of neurons:
        for atom in range(0, n_atoms):
            # Process the parameters

            # noinspection PyTypeChecker
            for param in params:
                value = param.get_value()
                if hasattr(value, "__len__"):
                    if len(value) > 1:
                        value = value[atom]
                    else:
                        value = value[0]

                datatype = param.get_dataspec_datatype()

                spec.write_value(data=value, data_type=datatype)
        # End the loop over the neurons:

    def generate_data_spec(self, subvertex, placement, subgraph, graph,
                           routing_info, hostname, graph_mapper,
                           report_folder, write_text_specs,
                           application_run_time_folder):
        """
        Model-specific construction of the data blocks necessary to
        build a group of IF_curr_exp neurons resident on a single core.
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
        neuron_params_sz = self.get_neuron_params_size(vertex_slice)
        synapse_params_sz = self.get_synapse_parameter_size(vertex_slice)

        subvert_in_edges = subgraph.incoming_subedges_from_subvertex(subvertex)
        all_syn_block_sz = \
            self.get_exact_synaptic_block_memory_size(graph_mapper,
                                                      subvert_in_edges)

        spike_hist_buff_sz = self.get_spike_buffer_size(vertex_slice)
        potential_hist_buff_sz = self.get_v_buffer_size(vertex_slice)
        gsyn_hist_buff_sz = self.get_g_syn_buffer_size(vertex_slice)
        vertex_in_edges = graph.incoming_edges_to_vertex(self)
        stdp_region_sz = self.get_stdp_parameter_size(vertex_in_edges)

        # Declare random number generators and distributions:
        #TODO add random distrubtion stuff
        #self.write_random_distribution_declarations(spec)

        # Construct the data images needed for the Neuron:
        self.reserve_population_based_memory_regions(
            spec, constants.SETUP_SIZE, neuron_params_sz, synapse_params_sz,
            constants.ROW_LEN_TABLE_SIZE,
            constants.MASTER_POPULATION_TABLE_SIZE, all_syn_block_sz,
            spike_hist_buff_sz, potential_hist_buff_sz, gsyn_hist_buff_sz,
            stdp_region_sz)

        self.write_setup_info(spec, spike_hist_buff_sz, potential_hist_buff_sz,
                              gsyn_hist_buff_sz, self._executable_constant)

        ring_buffer_shift = self.get_ring_buffer_to_input_left_shift(
            subvertex, subgraph, graph_mapper)
        weight_scale = self.get_weight_scale(ring_buffer_shift)

        #update projections for future use
        in_partitioned_edges = \
            subgraph.incoming_subedges_from_subvertex(subvertex)
        for partitioned_edge in in_partitioned_edges:
            partitioned_edge.weight_scale_setter(weight_scale)
        
        logger.debug("Ring-buffer shift is {}, weight scale is {}"
                     .format(ring_buffer_shift, weight_scale))

        self.write_neuron_parameters(
            spec, placement.x, placement.y, placement.p, subvertex,
            ring_buffer_shift, vertex_slice)

        self.write_synapse_parameters(spec, subvertex, vertex_slice)

        self.write_stdp_parameters(
            spec, self._machine_time_step,
            constants.POPULATION_BASED_REGIONS.STDP_PARAMS.value, weight_scale)

        self.write_row_length_translation_table(
            spec, constants.POPULATION_BASED_REGIONS.ROW_LEN_TRANSLATION.value)

        if placement.x != 0 or placement.y != 0:
            print ""

        self.write_synaptic_matrix_and_master_population_table(
            spec, subvertex, all_syn_block_sz, weight_scale,
            constants.POPULATION_BASED_REGIONS.MASTER_POP_TABLE.value,
            constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
            routing_info, graph_mapper, subgraph)

        in_subedges = subgraph.incoming_subedges_from_subvertex(subvertex)
        for subedge in in_subedges:
            subedge.free_sublist()

        # End the writing of this specification:
        spec.end_specification()
        data_writer.close()

    #inhirrited from data specable vertex
    def get_binary_file_name(self):
         # Split binary name into title and extension
        binary_title, binary_extension = os.path.splitext(self._binary)

        # If we have an STDP mechanism, add it's executable suffic to title
        if self._stdp_mechanism is not None:
            binary_title = \
                binary_title + "_" + \
                self._stdp_mechanism.get_vertex_executable_suffix()

        # Rebuild executable name
        binary_name = os.path.join(os.path.dirname(model_binaries.__file__),
                                   binary_title + binary_extension)

        return binary_name
