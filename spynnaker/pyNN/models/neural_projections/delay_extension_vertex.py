from math import ceil
import copy
import os
import math
import logging

from enum import Enum

from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex \
    import AbstractRecordableVertex
from spynnaker.pyNN.models.neural_projections.delay_projection_edge import \
    DelayProjectionEdge
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities.conf import config
from pacman.model.constraints.partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint
from data_specification.data_specification_generator import \
    DataSpecificationGenerator
from data_specification.file_data_writer import FileDataWriter


logger = logging.getLogger(__name__)

_DELAY_EXTENSION_REGIONS = Enum(
    'SYSTEM',
    'DELAY_PARAMS',
    'SPIKE_HISTORY'
)


class DelayExtensionVertex(AbstractRecordableVertex,
                           AbstractPartitionableVertex,
                           AbstractDataSpecableVertex):
    """
    Instance of this class provide delays to incoming spikes in multiples
    of the maximum delays of a neuron (typically 16 or 32)
    """

    CORE_APP_IDENTIFIER = constants.DELAY_EXTENSION_CORE_APPLICATION_ID
    
    def __init__(self, n_neurons, max_delay_per_neuron, source_vertex,
                 constraints=None, label="DelayExtension"):
        """
        Creates a new DelayExtension Object.
        """

        AbstractPartitionableVertex.__init__(self, n_atoms=n_neurons,
                                             constraints=constraints,
                                             label=label,
                                             max_atoms_per_core=256)
        AbstractRecordableVertex.__init__(self, label=label)

        self._max_delay_per_neuron = max_delay_per_neuron
        self._source_vertex = source_vertex
        joint_constrant = PartitionerSameSizeAsVertexConstraint(source_vertex)
        self.add_constraint(joint_constrant)

    @property
    def model_name(self):
        """
        Return a string representing a label for this class.
        """
        return "DelayExtension"

    # noinspection PyUnusedLocal
    @staticmethod
    def get_spikes_per_timestep(lo_atom, hi_atom, machine_time_step):
        # TODO: More accurate calculation of bounds
        return 200

    @staticmethod
    def get_spike_block_row_length(n_atoms):
        return int(math.ceil(n_atoms / constants.BITS_PER_WORD))

    @staticmethod
    def get_spike_region_bytes(spike_block_row_length, no_active_timesteps):
        return spike_block_row_length * no_active_timesteps * 4
    
    def get_spike_buffer_size(self, lo_atom, hi_atom):
        """
        Gets the size of the spike buffer for a range of neurons and time steps
        """
        if not self._record:
            return 0
        out_spikes_bytes = int(ceil((hi_atom - lo_atom + 1) / 32.0)) * 4
        return self.get_recording_region_size(out_spikes_bytes)

    @staticmethod
    def get_block_index_bytes(no_active_timesteps):
        return (constants.BLOCK_INDEX_HEADER_WORDS + (no_active_timesteps
                * constants.BLOCK_INDEX_ROW_WORDS)) * 4

    def generate_data_spec(self, processor_chip_x, processor_chip_y,
                           processor_id, subvertex, sub_graph,
                           routing_info, hostname, graph_sub_graph_mapper):
        """
        Model-specific construction of the data blocks necessary to build a
        single Delay Extension Block on one core.
        """
        binary_file_name = self.get_data_spec_file_name(
            processor_chip_x, processor_chip_y, processor_id, hostname)
        # Create new DataSpec for this processor:
        data_writer = FileDataWriter(binary_file_name)
        spec = DataSpecificationGenerator(data_writer)
        
        self.write_setup_info(spec, 0)

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")
        
        # ###################################################################
        # Reserve SDRAM space for memory areas:

        delay_params_header_words = 3
        n_atoms = subvertex.hi_atom - subvertex.lo_atom + 1
        block_len_words = int(ceil(n_atoms / 32.0))
        num_delay_blocks, delay_blocks = self.get_delay_blocks(
            subvertex, sub_graph, graph_sub_graph_mapper)
        delay_params_sz = 4 * (delay_params_header_words 
                               + (num_delay_blocks * block_len_words))
        
        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")

        spec.reserve_memory_region(region=_DELAY_EXTENSION_REGIONS.SYSTEM,
                                   size=constants.SETUP_SIZE, label='setup')

        spec.reserve_memory_region(
            region=_DELAY_EXTENSION_REGIONS.DELAY_PARAMS, 
            size=delay_params_sz, label='delay_params')

        self.write_delay_parameters(
            spec, processor_chip_x, processor_chip_y, processor_id, subvertex,
            num_delay_blocks, delay_blocks)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

    def write_setup_info(self, spec, spike_history_region_sz):
        """
        """
        recording_info = 0
        if self._record:
            recording_info |= constants.RECORD_SPIKE_BIT
        recording_info |= 0xBEEF0000

        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(region=_DELAY_EXTENSION_REGIONS.SYSTEM)
        spec.write_value(data=recording_info)
        spec.write_value(data=spike_history_region_sz)
        spec.write_value(data=0)
        spec.write_value(data=0)
        
    def get_delay_blocks(self, subvertex, sub_graph, graph_subgraph_mapper):
        # Create empty list of words to fill in with delay data:
        num_words_per_row = int(ceil(subvertex.n_atoms / 32.0))
        one_block = [0] * num_words_per_row
        delay_block = list()
        num_delay_blocks = 0
        
        for subedge in sub_graph.outgoing_subedges_from_subvertex(subvertex):
            subedge_assocated_edge = \
                graph_subgraph_mapper.get_edge_from_subedge(subedge)
            if not isinstance(subedge_assocated_edge, DelayProjectionEdge):
                raise exceptions.DelayExtensionException(
                    "One of the incoming subedges is not a subedge of a"
                    " DelayAfferentEdge")

            if subedge.pruneable:
                continue
    
            # Loop through each possible delay block
            dest = subedge.postsubvertex
            synapse_list = \
                subedge.edge.synapse_list.create_atom_sublist(
                    subvertex.lo_atom, subvertex.hi_atom, dest.lo_atom,
                    dest.hi_atom)
            for b in range(constants.MAX_DELAY_BLOCKS):
                min_delay = (b * self._max_delay_per_neuron) + 1
                max_delay = min_delay + self._max_delay_per_neuron
                delay_list = synapse_list.get_delay_sublist(min_delay,
                                                            max_delay)
                row_count = 0
                for row in delay_list:
                    if len(row.target_indices) != 0:
                        
                        # Fix the length of the list
                        num_delay_blocks = max(b + 1, num_delay_blocks)
                        while num_delay_blocks > len(delay_block):
                            delay_block.append(copy.copy(one_block))
                        
                        # This source neurons has synapses in the current delay
                        # range. So set the bit in the delay_block:
                        word_id = int(row_count / 32)
                        bit_id = row_count - (word_id * 32)
                        
                        #logger.debug("Adding delay for block {}, atom {}"
                        #        .format(b, row_count))
                        
                        delay_block[b][word_id] |= (1 << bit_id)
                    row_count += 1
        return num_delay_blocks, delay_block

    @staticmethod
    def write_delay_parameters(spec, processor_chip_x, processor_chip_y,
                               processor_id, subvertex, num_delay_blocks,
                               delay_block):
        """
        Generate Delay Parameter data (region 2):
        """

        # Write spec with commands to construct required delay region:
        spec.comment("\nWriting Delay Parameters for {%d} Neurons:\n"
                     .format(subvertex.n_atoms))

        # Set the focus to the memory region 2 (delay parameters):
        spec.switch_write_focus(region=_DELAY_EXTENSION_REGIONS.DELAY_PARAMS)

        # Write header info to the memory region:
        # Write Key info for this core:
        population_identity = \
            packet_conversions.get_key_from_coords(processor_chip_x,
                                                   processor_chip_y,
                                                   processor_id)
        spec.write_value(data=population_identity)

        # Write the number of neurons in the block:
        spec.write_value(data=subvertex.n_atoms)

        # Write the number of blocks of delays:
        spec.write_value(data=num_delay_blocks)

        # Write the actual delay blocks
        for i in range(0, num_delay_blocks):
            spec.write_array(data=delay_block[i])

    #inhirrted from partitoionable vertex
    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        n_atoms = (hi_atom - lo_atom) + 1
        return 128 * n_atoms

    def get_sdram_usage_for_atoms(self, lo_atom, hi_atom, vertex_in_edges):
         # TODO: Fill this in
        return 0

    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        n_atoms = (hi_atom - lo_atom) + 1
        return (44 + (16 * 4)) * n_atoms

    def get_binary_file_name(self):
         # Rebuild executable name
        common_binary_path = os.path.join(config.get("SpecGeneration",
                                                     "common_binary_folder"))

        binary_name = os.path.join(common_binary_path,
                                   'delay_extension.aplx')
        return binary_name