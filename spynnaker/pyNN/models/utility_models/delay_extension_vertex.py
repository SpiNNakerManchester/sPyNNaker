from math import ceil
import copy
import math
import logging

from enum import Enum

from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN.models.neural_projections.delay_partitionable_edge import \
    DelayPartitionableEdge
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from spynnaker.pyNN import exceptions
from pacman.model.constraints.partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint
from data_specification.data_specification_generator import \
    DataSpecificationGenerator


logger = logging.getLogger(__name__)


class DelayExtensionVertex(AbstractPartitionableVertex,
                           AbstractDataSpecableVertex):
    """
    Instance of this class provide delays to incoming spikes in multiples
    of the maximum delays of a neuron (typically 16 or 32)
    """

    CORE_APP_IDENTIFIER = constants.DELAY_EXTENSION_CORE_APPLICATION_ID

    _DELAY_EXTENSION_REGIONS = Enum(
        value="DELAY_EXTENSION_REGIONS",
        names=[('SYSTEM', 0),
               ('DELAY_PARAMS', 1),
               ('SPIKE_HISTORY', 2)])

    def __init__(self, n_neurons, max_delay_per_neuron, source_vertex,
                 machine_time_step, timescale_factor, constraints=None,
                 label="DelayExtension"):
        """
        Creates a new DelayExtension Object.
        """

        AbstractPartitionableVertex.__init__(self, n_atoms=n_neurons,
                                             constraints=constraints,
                                             label=label,
                                             max_atoms_per_core=256)
        AbstractDataSpecableVertex.__init__(
            self, label=label, n_atoms=n_neurons,
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor)

        self._max_delay_per_neuron = max_delay_per_neuron
        self._max_stages = 0
        self._source_vertex = source_vertex
        joint_constrant = PartitionerSameSizeAsVertexConstraint(source_vertex)
        self.add_constraint(joint_constrant)

    @property
    def model_name(self):
        """
        Return a string representing a label for this class.
        """
        return "DelayExtension"

    @property
    def max_stages(self):
        """ The maximum number of delay stages required by any connection
            out of this delay extension vertex
        """
        return self._max_stages

    @max_stages.setter
    def max_stages(self, max_stages):
        self._max_stages = max_stages

    @property
    def max_delay_per_neuron(self):
        return self._max_delay_per_neuron

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

    def generate_data_spec(self, subvertex, placement, sub_graph, graph,
                           routing_info, hostname, graph_mapper,
                           report_folder):
        """
        Model-specific construction of the data blocks necessary to build a
        single Delay Extension Block on one core.
        """
        data_writer, report_writer = \
            self.get_data_spec_file_writers(
                placement.x, placement.y, placement.p, hostname, report_folder)

        spec = DataSpecificationGenerator(data_writer, report_writer)

        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:

        delay_params_header_words = 3

        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)

        n_atoms = vertex_slice.hi_atom - vertex_slice.lo_atom + 1
        block_len_words = int(ceil(n_atoms / 32.0))
        num_delay_blocks, delay_blocks = self.get_delay_blocks(
            subvertex, sub_graph, graph_mapper)
        delay_params_sz = 4 * (delay_params_header_words
                               + (num_delay_blocks * block_len_words))

        spec.reserve_memory_region(
            region=self._DELAY_EXTENSION_REGIONS.SYSTEM.value,
            size=constants.SETUP_SIZE, label='setup')

        spec.reserve_memory_region(
            region=self._DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value,
            size=delay_params_sz, label='delay_params')

        self.write_setup_info(spec, 0)

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        self.write_delay_parameters(spec, placement.x, placement.y,
                                    placement.p, subvertex, num_delay_blocks,
                                    delay_blocks, vertex_slice)
        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

    def write_setup_info(self, spec, spike_history_region_sz):
        """
        """
        recording_info = 0xBEEF0000

        # Write this to the system region (to be picked up by the simulation):
        self._write_basic_setup_info(spec, self.CORE_APP_IDENTIFIER)
        spec.switch_write_focus(
            region=self._DELAY_EXTENSION_REGIONS.SYSTEM.value)
        spec.write_value(data=recording_info)
        spec.write_value(data=spike_history_region_sz)
        spec.write_value(data=0)
        spec.write_value(data=0)

    def get_delay_blocks(self, subvertex, sub_graph, graph_mapper):

        # Create empty list of words to fill in with delay data:
        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1

        num_words_per_row = int(ceil(n_atoms / 32.0))
        one_block = [0] * num_words_per_row
        delay_block = list()
        num_delay_blocks = 0

        for subedge in sub_graph.outgoing_subedges_from_subvertex(subvertex):
            subedge_assocated_edge = \
                graph_mapper.get_partitionable_edge_from_partitioned_edge(
                    subedge)
            if not isinstance(subedge_assocated_edge, DelayPartitionableEdge):
                raise exceptions.DelayExtensionException(
                    "One of the incoming subedges is not a subedge of a"
                    " DelayPartitionableEdge")

            # Loop through each possible delay block
            dest = subedge.post_subvertex
            source_vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
            dest_vertex_slice = graph_mapper.get_subvertex_slice(dest)
            partitionable_edge = graph_mapper.\
                get_partitionable_edge_from_partitioned_edge(subedge)
            synapse_list = partitionable_edge.synapse_list.create_atom_sublist(
                source_vertex_slice, dest_vertex_slice)
            rows = synapse_list.get_rows()

            for (source_id, row) in zip(range(len(rows)), rows):
                for delay in row.delays:
                    stage = int(math.floor((delay - 1)
                                           / self.max_delay_per_neuron)) - 1
                    num_delay_blocks = max(stage + 1, num_delay_blocks)
                    if num_delay_blocks > self._max_stages:
                        raise Exception(
                            "Too many stages ({} of {}) have been"
                            " created for delay extension {}".format(
                                num_delay_blocks, self._max_stages,
                                self._label))
                    while num_delay_blocks > len(delay_block):
                        delay_block.append(copy.copy(one_block))

                    # This source neurons has synapses in the current delay
                    # range. So set the bit in the delay_block:
                    word_id = int(source_id / 32)
                    bit_id = source_id - (word_id * 32)
                    delay_block[stage][word_id] |= (1 << bit_id)

        return num_delay_blocks, delay_block

    def write_delay_parameters(self, spec, processor_chip_x, processor_chip_y,
                               processor_id, subvertex, num_delay_blocks,
                               delay_block, vertex_slice):
        """
        Generate Delay Parameter data (region 2):
        """

        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1

        # Write spec with commands to construct required delay region:
        spec.comment("\nWriting Delay Parameters for {} Neurons:\n"
                     .format(n_atoms))

        # Set the focus to the memory region 2 (delay parameters):
        spec.switch_write_focus(
            region=self._DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value)

        # Write header info to the memory region:
        # Write Key info for this core:
        population_identity = \
            packet_conversions.get_key_from_coords(processor_chip_x,
                                                   processor_chip_y,
                                                   processor_id)
        spec.write_value(data=population_identity)

        # Write the number of neurons in the block:
        spec.write_value(data=n_atoms)

        # Write the number of blocks of delays:
        spec.write_value(data=num_delay_blocks)

        # Write the actual delay blocks
        for i in range(0, num_delay_blocks):
            spec.write_array(array_values=delay_block[i])

    # inherited from partitionable vertex
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return 128 * n_atoms

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        # TODO: Fill this in
        return 0

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return (44 + (16 * 4)) * n_atoms

    def get_binary_file_name(self):
        return "delay_extension.aplx"