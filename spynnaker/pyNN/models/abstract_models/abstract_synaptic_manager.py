import math
import logging
import struct
import sys
import numpy

from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from spynnaker.pyNN.models.neural_projections.projection_partitionable_edge \
    import ProjectionPartitionableEdge
from spynnaker.pyNN.models.neural_projections.projection_partitioned_edge \
    import ProjectionPartitionedEdge
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_properties import master_pop_table_generators
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities.utility_calls \
    import get_region_base_address_offset
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.utilities import conf
#pacman imports
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex

#spinnman imports
from spinnman import exceptions as spinnman_exceptions

#dsg imports
from data_specification.enums.data_type import DataType

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractSynapticManager(object):

    def __init__(self):
        self._stdp_checked = False
        self._stdp_mechanism = None
        self._master_pop_table_generator = None
        algorithum_id = \
            "MasterPopTableAs" + \
            conf.config.get("MasterPopTable", "generator")

        algorithum_list = \
            conf.get_valid_components(master_pop_table_generators,
                                      "master_pop_table_as")
        self._master_pop_table_generator = algorithum_list[algorithum_id]()

    @staticmethod
    def write_synapse_row_info(sublist, row_io, spec, current_write_ptr,
                               fixed_row_length, region, weight_scale,
                               n_synapse_type_bits):
        """
        Write this synaptic block to the designated synaptic matrix region at
        its current write pointer.
        """

        # Switch focus to the synaptic matrix memory region:
        spec.switch_write_focus(region)

        # Align the write pointer to the next 1Kbyte boundary using padding:
        write_ptr = current_write_ptr
        if (write_ptr & 0x3FF) != 0:

            # Ptr not aligned. Align it:
            write_ptr = (write_ptr & 0xFFFFFC00) + 0x400

            # Pad out data file with the added alignment bytes:
            num_padding_bytes = write_ptr - current_write_ptr
            spec.set_register_value(register_id=15, data=num_padding_bytes)
            spec.write_value(data=0xDD, repeats_register=15,
                             data_type=DataType.UINT8)

        # Remember this aligned address, it's where this block will start:
        block_start_addr = write_ptr
        # Write the synaptic block, tracking the word count:
        synaptic_rows = sublist.get_rows()

        row_no = 0
        for row in synaptic_rows:
            words_written = 0
            plastic_region = \
                row_io.get_packed_plastic_region(row, weight_scale,
                                                 n_synapse_type_bits)

            # Write the size of the plastic region
            spec.comment("\nWriting plastic region for row {}".format(row_no))
            spec.write_value(data=len(plastic_region))
            words_written += 1

            # Write the plastic region
            spec.write_array(array_values=plastic_region)
            words_written += len(plastic_region)

            fixed_fixed_region = numpy.asarray(
                row_io.get_packed_fixed_fixed_region(row, weight_scale,
                                                     n_synapse_type_bits),
                dtype="uint32")
            fixed_plastic_region = numpy.asarray(
                row_io.get_packed_fixed_plastic_region(row, weight_scale,
                                                       n_synapse_type_bits),
                dtype="uint16")

            # Write the size of the fixed parts
            spec.comment("\nWriting fixed region for row {}".format(row_no))
            #spec.write_value(data=len(fixed_plastic_region))
            #spec.write_value(data=len(fixed_fixed_region))
            spec.write_value(data=len(fixed_fixed_region))
            spec.write_value(data=len(fixed_plastic_region))
            words_written += 2

            # Write the fixed fixed region
            spec.write_array(array_values=fixed_fixed_region)
            words_written += len(fixed_fixed_region)

            # As everything needs to be word aligned, add extra zero to
            # fixed_plastic Region if it has an odd number of entries and build
            # uint32 view of it
            if (len(fixed_plastic_region) % 2) != 0:
                fixed_plastic_region = \
                    numpy.asarray(numpy.append(fixed_plastic_region, 0),
                                  dtype='uint16')
            # does indeed return something (due to c fancy stuff in numpi) ABS

            # noinspection PyNoneFunctionAssignment
            fixed_plastic_region_words = \
                fixed_plastic_region.view(dtype="uint32")

            spec.write_array(array_values=fixed_plastic_region_words)

            # noinspection PyTypeChecker
            words_written += len(fixed_plastic_region_words)

            write_ptr += (4 * words_written)

            # Write padding (if required):
            padding = ((fixed_row_length + constants.SYNAPTIC_ROW_HEADER_WORDS)
                       - words_written)
            if padding != 0:
                spec.write_value(data=0xBBCCDDEE, repeats=padding,
                                 data_type=DataType.UINT32)
                write_ptr += 4 * padding
            row_no += 1

        # The current write pointer is where the next block could start:
        next_block_start_addr = write_ptr
        return block_start_addr, next_block_start_addr
    
    def get_exact_synaptic_block_memory_size(self, graph_mapper,
                                             subvertex_in_edges):
        memory_size = 0
        
        # Go through the subedges and add up the memory
        for subedge in subvertex_in_edges:
            #pad the memory size to meet 1 k offsets
            if (memory_size & 0x3FF) != 0:
                memory_size = (memory_size & 0xFFFFFC00) + 0x400
            
            sublist = subedge.get_synapse_sublist(graph_mapper)
            max_n_words = \
                max([graph_mapper.get_partitionable_edge_from_partitioned_edge(subedge)
                    .get_synapse_row_io().get_n_words(synapse_row)
                    for synapse_row in sublist.get_rows()])
            #check that the max_n_words is greater than zero
            assert(max_n_words > 0)
            all_syn_block_sz = \
                self._calculate_all_synaptic_block_size(sublist,
                                                        max_n_words)
            memory_size += all_syn_block_sz
        return memory_size

    # TODO DOES THIS METHOD EVER GET RAN????
    def get_synaptic_blocks_memory_size(self, vertex_slice, in_edges):
        self._check_synapse_dynamics(in_edges)
        memory_size = 0
        
        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionPartitionableEdge):
                
                # Get maximum row length in this edge 
                max_n_words = in_edge.get_max_n_words(vertex_slice)
                all_syn_block_sz = \
                    self._calculate_all_synaptic_block_size(in_edge,
                                                            max_n_words)
                
                # TODO: Fix this to be more accurate!
                # May require modification to the master pynn_population.py
                # table
                n_atoms = sys.maxint
                edge_pre_vertex = in_edge.pre_vertex
                if edge_pre_vertex in \
                        AbstractPartitionableVertex.__subclasses__():
                    n_atoms = in_edge.pre_vertex.get_maximum_atoms_per_core()
                if in_edge.pre_vertex.n_atoms < n_atoms:
                    n_atoms = in_edge.pre_vertex.n_atoms

                num_rows = in_edge.get_n_rows()
                extra_mem = math.ceil(float(num_rows) / float(n_atoms)) * 1024
                if extra_mem == 0:
                    extra_mem = 1024
                all_syn_block_sz += extra_mem
                memory_size += all_syn_block_sz
                
        return memory_size

    def _calculate_all_synaptic_block_size(self, synaptic_sub_list,
                                           max_n_words):
        # Gets smallest possible (i.e. supported by row length
        # Table structure) that can contain max_row_length
        row_length = self.select_minimum_row_length(max_n_words)[1]
        num_rows = synaptic_sub_list.get_n_rows()
        syn_block_sz = \
            4 * (constants.SYNAPTIC_ROW_HEADER_WORDS + row_length)
        return syn_block_sz * num_rows

    def _check_synapse_dynamics(self, in_edges):
        if self._stdp_checked:
            return True
        self._stdp_checked = True
        for in_edge in in_edges:
            if (isinstance(in_edge, ProjectionPartitionableEdge)
                    and in_edge.synapse_dynamics is not None):
                if in_edge.synapse_dynamics.fast is not None:
                    raise exceptions.SynapticConfigurationException(
                        "Fast synapse dynamics are not supported")
                elif in_edge.synapse_dynamics.slow is not None:
                    if self._stdp_mechanism is None:
                        self._stdp_mechanism = in_edge.synapse_dynamics.slow
                    else:
                        if not (self._stdp_mechanism
                                == in_edge.synapse_dynamics.slow):
                            raise exceptions.SynapticConfigurationException(
                                "Different STDP mechanisms on the same"
                                + " vertex are not supported")

    @abstractmethod
    def get_n_synapse_type_bits(self):
        """
        Return the number of bits used to identify the synapse in the synaptic
        row
        """

    @abstractmethod
    def write_synapse_parameters(self, spec, subvertex):
        """forced method for dealing with writing synapse params

        """

    @staticmethod
    def select_minimum_row_length(longest_actual_row):
        """
        Given a new synaptic block the list of valid row lengths supported,
        return the index and value of the minimum valid length that can fit
        even the largest row in the synaptic block.
        """

        # Can even the largest valid entry accommodate the given synaptic row?
        if longest_actual_row > constants.ROW_LEN_TABLE_ENTRIES[-1]:
            raise exceptions.SynapticBlockGenerationException(
                """\
                Synaptic block generation.
                Row table entry calculator: Max row length too long.
                Wanted length %d, but max length permitted is %d.
                Try adjusting table entries in row length translation table.
                """ % (longest_actual_row,
                       constants.ROW_LEN_TABLE_ENTRIES[-1])
            )

        # Search up the list until we find one entry big enough:
        best_index = None
        minimum_valid_row_length = None
        for i in range(len(constants.ROW_LEN_TABLE_ENTRIES)):
            if longest_actual_row <= constants.ROW_LEN_TABLE_ENTRIES[i]:
                # This row length is big enough. Choose it and exit:
                best_index = i
                minimum_valid_row_length = constants.ROW_LEN_TABLE_ENTRIES[i]
                break

        # Variable best_index now contains the table entry corresponding to the
        # smallest row that is big enough for our row of data
        return best_index, minimum_valid_row_length

    def get_synapse_parameter_size(self, vertex_slice):
        raise NotImplementedError

    @staticmethod
    def get_synapse_targets():
        """
        Gets the supported names of the synapse targets
        """
        return "excitatory", "inhibitory"

    @staticmethod
    def get_synapse_id(target_name):
        """
        Returns the numeric identifier of a synapse, given its name.  This
        is used by the neuron models.
        """
        if target_name == "excitatory":
            return 0
        elif target_name == "inhibitory":
            return 1
        return None

    def get_stdp_parameter_size(self, in_edges):
        self._check_synapse_dynamics(in_edges)
        if self._stdp_mechanism is not None:
            return self._stdp_mechanism.get_params_size()
        return 0

    @staticmethod
    def write_row_length_translation_table(spec, row_length_translation_region):
        """
        Generate Row Length Translation Table (region 4):
        """
        spec.comment("\nWriting Row Length Translation Table:\n")

        # Switch focus of writes to the memory region to hold the table:
        spec.switch_write_focus(region=row_length_translation_region)

        # The table is a list of eight 32-bit words, that provide a row length
        # when given its encoding (3-bit value used as an index into the
        # table).
        # Set the focus to memory region 3 (row length translation):
        for entry in constants.ROW_LEN_TABLE_ENTRIES:
            spec.write_value(data=entry)

    def write_stdp_parameters(self, spec, machine_time_step, region, weight_scale):
        if self._stdp_mechanism is not None:
            self._stdp_mechanism.write_plastic_params(spec, region,
                                                      machine_time_step,
                                                      weight_scale)

    @staticmethod
    def get_weight_scale(ring_buffer_to_input_left_shift):
        """
        Return the amount to scale the weights by to convert them from floating
        point values to 16-bit fixed point numbers which can be shifted left by
        ring_buffer_to_input_left_shift to produce an s1615 fixed point number
        """
        return float(math.pow(2, 16 - (ring_buffer_to_input_left_shift + 1)))
    
    def get_ring_buffer_to_input_left_shift(self, subvertex, sub_graph, 
                                            graph_mapper):

        in_sub_edges = sub_graph.incoming_subedges_from_subvertex(subvertex)
        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1  # do to starting at zero
        total_exc_weights = numpy.zeros(n_atoms)
        total_inh_weights = numpy.zeros(n_atoms)
        for subedge in in_sub_edges:
            sublist = subedge.get_synapse_sublist(graph_mapper)
            sublist.sum_weights(total_exc_weights, total_inh_weights)

        max_weight = max((max(total_exc_weights), max(total_inh_weights)))
        
        # If we have an STDP mechanism, let it provide an extra max weight
        if self._stdp_mechanism is not None\
                and self._stdp_mechanism.weight_dependence is not None:
            # If weight dependence has a max weight,
            # Take this into account as well
            stdp_max_weight = self._stdp_mechanism.get_max_weight()
            max_weight = max(max_weight, stdp_max_weight)

        max_weight_log_2 = 0
        if max_weight > 0:
            max_weight_log_2 = math.log(max_weight, 2)

        # Currently, we can only cope with positive left shifts, so the minimum
        # scaling will be no shift i.e. a max weight of 0nA
        if max_weight_log_2 < 0:
            max_weight_log_2 = 0

        max_weight_power = int(math.ceil(max_weight_log_2))
        
        # If we have an STDP mechanism that uses signed weights,
        # Add another bit of shift to prevent overflows
        if self._stdp_mechanism is not None\
            and self._stdp_mechanism.are_weights_signed():
                max_weight_power = max_weight_power + 1
        
        logger.debug("Max weight is {}, Max power is {}"
                    .format(max_weight, max_weight_power))

        # Actual shift is the max_weight_power - 1 for 16-bit fixed to s1615,
        # but we ignore the "-1" to allow a bit of overhead in the above
        # calculation in case a couple of extra spikes come in
        return max_weight_power
    
    def write_synaptic_matrix_and_master_population_table(
            self, spec, subvertex, all_syn_block_sz, weight_scale,
            master_pop_table_region, synaptic_matrix_region, routing_info,
            graph_mapper, subgraph):
        """
        Simultaneously generates both the master pynn_population.py table and
        the synatic matrix.

        Master Population Table (MPT):
        Table of 1152 entries (one per numbered core on a 48-node board
        arranged in an 8 x 8 grid) giving offset pointer to synapse rows
        for that source pynn_population.py.

        Synaptic Matrix:
        One block for each projection in the network (sub_edge in the partitionable_graph).
        Blocks are always aligned to 1K boundaries (within the region).
        Each block contains one row for each arriving axon.
        Each row contains a header of two words and then one 32-bit word for
        each synapse. The row contents depend on the connector type.
        """
        spec.comment("\nWriting Synaptic Matrix and Master Population Table:\n")

        # Zero all entries in the Master Population Table so that all unused
        # entries are assumed empty:
        spec.switch_write_focus(region=master_pop_table_region)
        my_repeat_reg = 4
        spec.set_register_value(register_id=my_repeat_reg,
                                data=constants.MASTER_POPULATION_ENTRIES)
        spec.write_value(data=0, repeats_register=my_repeat_reg,
                         data_type=DataType.UINT16)

        # Track writes inside the synaptic matrix region:
        next_block_start_addr = 0
        n_synapse_type_bits = self.get_n_synapse_type_bits()

        # For each entry in subedge into the subvertex, create a
        # sub-synaptic list
        in_subedges = subgraph.incoming_subedges_from_subvertex(subvertex)
        for subedge in in_subedges:

            # Only deal with incoming projection subedges
            if isinstance(subedge, ProjectionPartitionedEdge):
                key = routing_info.get_key_from_subedge(subedge)
                x = packet_conversions.get_x_from_key(key)
                y = packet_conversions.get_y_from_key(key)
                p = packet_conversions.get_p_from_key(key)
                spec.comment("\nWriting matrix for subedge from {}, {}, {}\n"
                             .format(x, y, p))

                sublist = subedge.get_synapse_sublist(graph_mapper)
                associated_edge = \
                    graph_mapper.get_partitionable_edge_from_partitioned_edge(subedge)
                row_io = associated_edge.get_synapse_row_io()
                if logger.isEnabledFor("debug"):
                    subvertex_vertex =\
                        graph_mapper.get_vertex_from_subvertex(subvertex)
                    pre_sub_lo = \
                        graph_mapper.get_subvertex_slice(
                            subedge.pre_subvertex).lo_atom
                    pre_sub_hi = \
                        graph_mapper.get_subvertex_slice(
                            subedge.pre_subvertex).hi_atom
                    sub_lo = graph_mapper.get_subvertex_slice(subvertex).lo_atom
                    sub_hi = graph_mapper.get_subvertex_slice(subvertex).hi_atom

                    logger.debug("Writing subedge from {} ({}-{}) to {} ({}-{})"
                                 .format(subedge.pre_subvertex.label,
                                         pre_sub_lo, pre_sub_hi,
                                         subvertex_vertex.label, sub_lo,
                                         sub_hi))
                    rows = sublist.get_rows()
                    for i in range(len(rows)):
                        logger.debug("{}: {}".format(i, rows[i]))

                # Get the maximum row length in words, excluding headers
                max_row_length = \
                    max([row_io.get_n_words(row) for row in sublist.get_rows()])
                #check that the max_row_length is not zero
                assert(max_row_length > 0)
                # Get an entry in the row length table for this length
                row_index, row_length = \
                    self.select_minimum_row_length(max_row_length)
                if max_row_length == 0 or row_length == 0:
                    raise exceptions.SynapticBlockGenerationException(
                        "generated a row length of zero, this is deemed an "
                        "error and therefore the system will stop")

                # Write the synaptic block for the sublist
                (block_start_addr, next_block_start_addr) = \
                    self.write_synapse_row_info(
                        sublist, row_io, spec, next_block_start_addr,
                        row_length, synaptic_matrix_region, weight_scale,
                        n_synapse_type_bits)

                if (next_block_start_addr - 1) > all_syn_block_sz:
                    raise exceptions.SynapticBlockGenerationException(
                        "Too much synapse memory consumed (used {} of {})!"
                        .format(next_block_start_addr - 1, all_syn_block_sz))
                self._master_pop_table_generator.\
                    update_master_population_table(
                        spec, block_start_addr, row_index, key,
                        master_pop_table_region)
        self._master_pop_table_generator.finish_master_pop_table(
            spec, master_pop_table_region)

    def get_synaptic_list_from_machine(
            self, placements, transceiver, pre_subvertex, pre_n_atoms,
            post_subvertex, master_pop_table_region, synaptic_matrix_region,
            synapse_io, subgraph, graph_mapper, routing_infos, weight_scale):

        synaptic_block, max_row_length = \
            self._retrieve_synaptic_block(
                placements, transceiver, pre_subvertex, pre_n_atoms,
                post_subvertex, master_pop_table_region, synaptic_matrix_region,
                routing_infos, subgraph)
        #translate the synaptic block into a sublist of synapse_row_infos
        synapse_list = \
            self._translate_synaptic_block_from_memory(
                synaptic_block, pre_n_atoms, max_row_length, synapse_io,
                weight_scale)
        return synapse_list

    def _translate_synaptic_block_from_memory(self, synaptic_block, n_atoms,
                                              max_row_length, synapse_io,
                                              weight_scale):
        """
        translates a collection of memory into synaptic rows
        """
        synaptic_list = list()
        numpy_block = numpy.frombuffer(dtype='uint8',
                                       buffer=synaptic_block).view(dtype='<u4')
        position_in_block = 0
        for atom in range(n_atoms):
            #extract the 3 elements of a row (PP, FF, FP)
            p_p_entries, f_f_entries, f_p_entries = \
                self._extract_row_data_from_memory_block(numpy_block,
                                                         position_in_block)
            #new position in synpaptic block
            position_in_block = \
                ((atom + 1) *
                 (max_row_length + constants.SYNAPTIC_ROW_HEADER_WORDS))

            bits_reserved_for_type = self.get_n_synapse_type_bits()
            synaptic_row = \
                synapse_io.create_row_info_from_elements(p_p_entries,
                                                         f_f_entries,
                                                         f_p_entries,
                                                         bits_reserved_for_type,
                                                         weight_scale)

            synaptic_list.append(synaptic_row)
        return SynapticList(synaptic_list)

    @staticmethod
    def _extract_row_data_from_memory_block(synaptic_block, position_in_block):

        """
        extracts the 6 elements from a data block which is ordered
        no PP, pp, No ff, NO fp, FF fp
        """
        #read in number of plastic plastic entries
        no_plastic_plastic_entries = synaptic_block[position_in_block]
        position_in_block += 1
        #read inall the plastic entries
        end_point = position_in_block + no_plastic_plastic_entries
        plastic_plastic_entries = synaptic_block[position_in_block:end_point]
        ##for element in plastic_plastic_entries:
        ##    assert(element != 3150765550)
        #update position in block
        position_in_block = end_point
        #update position in block
        #read in number of both fixed fixed and fixed plastic
        no_fixed_fixed = synaptic_block[position_in_block]
        position_in_block += 1
        no_fixed_plastic = synaptic_block[position_in_block]
        position_in_block += 1
        #read in fixed fixed
        end_point = position_in_block + no_fixed_fixed
        fixed_fixed_entries = synaptic_block[position_in_block:end_point]
        ##for element in fixed_fixed_entries:
        ##    assert(element != 3150765550)
        position_in_block = end_point
        #read in fixed plastic (fixed plastic are in 16 bits, so each int is 2 entries)
        end_point = position_in_block + math.ceil(no_fixed_plastic / 2.0)
        fixed_plastic_entries = \
            synaptic_block[position_in_block:end_point].view(dtype='<u2')
        if no_fixed_plastic % 2.0 == 1:  # remove last entry if required
            fixed_plastic_entries = \
                fixed_plastic_entries[0:len(fixed_plastic_entries) - 2]
        ##for element in fixed_plastic_entries:
        ##    assert(element != 3150765550)
        #return the different entries
        return plastic_plastic_entries, fixed_fixed_entries, \
            fixed_plastic_entries

    def _retrieve_synaptic_block(self, placements, transceiver,
                                 pre_subvertex, pre_n_atoms,
                                 post_subvertex, master_pop_table_region,
                                 synaptic_matrix_region, routing_infos,
                                 subgraph):
        """
        reads in a synaptic block from a given processor and subvertex on the
        machine.
        """
        post_placement = placements.get_placement_of_subvertex(post_subvertex)
        post_x, post_y, post_p = \
            post_placement.x, post_placement.y, post_placement.p
        # either read in the master pop table or retrieve it from storage
        master_pop_base_mem_address, app_data_base_address = \
            self._master_pop_table_generator.\
            locate_master_pop_table_base_address(
                post_x, post_y, post_p, transceiver, master_pop_table_region)

        # locate address of the synaptic block
        pre_placement = placements.get_placement_of_subvertex(pre_subvertex)

        pre_x, pre_y, pre_p = pre_placement.x, pre_placement.y, pre_placement.p

        incoming_edges = \
            subgraph.incoming_subedges_from_subvertex(post_subvertex)
        incoming_key_combo = None
        for subedge in incoming_edges:
            if subedge.pre_subvertex == pre_subvertex:
                routing_info = routing_infos.get_subedge_information_from_subedge(subedge)
                incoming_key_combo = routing_info.key_mask_combo

        maxed_row_length, synaptic_block_base_address_offset = \
            self._master_pop_table_generator.\
            extract_synaptic_matrix_data_location(
                incoming_key_combo, master_pop_base_mem_address)

        #calculate the synaptic block size in words
        synaptic_block_size = pre_n_atoms * 4 * \
            (constants.SYNAPTIC_ROW_HEADER_WORDS + maxed_row_length)

        #read in the base address of the synaptic matrix in the app region table
        synapste_region_base_address_location = \
            get_region_base_address_offset(app_data_base_address,
                                           synaptic_matrix_region)

        # read in the memory address of the synaptic_region base address
        synapste_region_base_address = \
            self._master_pop_table_generator.read_and_convert(
                post_x, post_y, synapste_region_base_address_location, 4,
                "<I", transceiver)
        # the base address of the synaptic block in absolute terms is the app
        # base, plus the synaptic matrix base plus the offset
        synaptic_block_base_address = \
            app_data_base_address + synapste_region_base_address + \
            synaptic_block_base_address_offset

        #read in and return the synaptic block
        blocks = list(transceiver.read_memory(
            post_x, post_y, synaptic_block_base_address, synaptic_block_size))

        block = bytearray()
        for message_block in blocks:
            block.extend(message_block)

        if len(block) != synaptic_block_size:
            raise exceptions.SynapticBlockReadException(
                "Not enough data has been read "
                "(aka, something funkky happened)")
        return block, maxed_row_length

    def _read_in_master_pop_table(self, x, y, p, transceiver,
                                  master_pop_table_region):
        """
        reads in the master pop table from a given processor on the machine
        """
        # Get the App Data base address for the core
        # (location where this cores memory starts in
        # sdram and region table)
        app_data_base_address = \
            transceiver.get_cpu_information_from_core(x, y, p).user[0]

        # Get the memory address of the master pop table region
        master_pop_region = master_pop_table_region

        master_region_base_address_address = \
            get_region_base_address_offset(app_data_base_address,
                                           master_pop_region)

        master_region_base_address_offset = \
            self._read_and_convert(x, y, master_region_base_address_address,
                                   4, "<I", transceiver)

        master_region_base_address =\
            master_region_base_address_offset + app_data_base_address

        #read in the master pop table and store in ram for future use
        logger.debug("Reading {} ({}) bytes starting at {} + "
                     "4".format(constants.MASTER_POPULATION_TABLE_SIZE,
                                hex(constants.MASTER_POPULATION_TABLE_SIZE),
                                hex(master_region_base_address)))

        return master_region_base_address, app_data_base_address

    @staticmethod
    def _read_and_convert(x, y, address, length, data_format, transceiver):
        """
        tries to read and convert a piece of memory. If it fails, it tries again
        up to for 4 times, and then if still fails, throws an error.
        """
        try:
            #turn byte array into str for unpack to work.
            data = \
                str(list(transceiver.read_memory(
                    x, y, address, length))[0])
            result = struct.unpack(data_format, data)[0]
            return result
        except spinnman_exceptions.SpinnmanIOException:
            raise exceptions.SynapticBlockReadException(
                "failed to read and translate a piece of memory due to a "
                "spinnman io exception.")
        except spinnman_exceptions.SpinnmanInvalidPacketException:
            raise exceptions.SynapticBlockReadException(
                "failed to read and translate a piece of memory due to a "
                "invalid packet exception in spinnman.")
        except spinnman_exceptions.SpinnmanInvalidParameterException:
            raise exceptions.SynapticBlockReadException(
                "failed to read and translate a piece of memory due to a "
                "invalid parameter exception in spinnman.")
        except spinnman_exceptions.SpinnmanUnexpectedResponseCodeException:
            raise exceptions.SynapticBlockReadException(
                "failed to read and translate a piece of memory due to a "
                "unexpected response code exception in spinnman.")
