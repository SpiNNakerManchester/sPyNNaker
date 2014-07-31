import math
import logging
import struct
import sys

import numpy

from spynnaker.pyNN.models.neural_projections.projection_edge \
    import ProjectionEdge
from spynnaker.pyNN.models.neural_projections.projection_subedge \
    import ProjectionSubedge
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities.utility_calls \
    import get_region_base_address_offset
from spynnaker.pyNN.utilities import utility_calls
from pacman.model.graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from spinnman import exceptions as spinnman_exceptions


logger = logging.getLogger(__name__)


class SynapticManager(object):

    def __init__(self):
        self._stdp_checked = False
        self._stdp_mechanism = None

    @staticmethod
    def write_synapse_row_info(sublist, row_io, spec, current_write_ptr,
                               fixed_row_length, region, weight_scale,
                               n_synapse_type_bits):
        """
        Write this synaptic block to the designated synaptic matrix region at
        its current write pointer.
        """

        # Switch focus to the synaptic matrix memory region:
        spec.switchWriteFocus(region)

        # Align the write pointer to the next 1Kbyte boundary using padding:
        write_ptr = current_write_ptr
        if (write_ptr & 0x3FF) != 0:

            # Ptr not aligned. Align it:
            write_ptr = (write_ptr & 0xFFFFFC00) + 0x400

            # Pad out data file with the added alignment bytes:
            num_padding_bytes = write_ptr - current_write_ptr
            spec.set_register_value(register_id=15, data=num_padding_bytes)
            spec.write_value(data=0xDD, repeatReg=15, sizeof='uint8')

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
            spec.write_value(data=len(plastic_region), sizeof="uint32")
            words_written += 1

            # Write the plastic region
            spec.write_array(data=plastic_region)
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
            spec.write_value(data=len(fixed_fixed_region), sizeof="uint32")
            spec.write_value(data=len(fixed_plastic_region), sizeof="uint32")
            words_written += 2

            # Write the fixed fixed region
            spec.write_array(data=fixed_fixed_region)
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

            spec.write_array(data=fixed_plastic_region_words)

            # noinspection PyTypeChecker
            words_written += len(fixed_plastic_region_words)

            write_ptr += (4 * words_written)

            # Write padding (if required):
            padding = ((fixed_row_length + constants.SYNAPTIC_ROW_HEADER_WORDS)
                       - words_written)
            if padding != 0:
                spec.write(data=0xBBCCDDEE, repeats=padding, sizeof='uint32')
                write_ptr += 4 * padding

            row_no += 1

        # The current write pointer is where the next block could start:
        next_block_start_addr = write_ptr
        return block_start_addr, next_block_start_addr
    
    def get_exact_synaptic_block_memory_size(self, subvertex):
        memory_size = 0
        
        # Go through the subedges and add up the memory
        for subedge in subvertex.in_subedges:
            if (memory_size & 0x3FF) != 0:
                memory_size = (memory_size & 0xFFFFFC00) + 0x400
            
            sublist = subedge.get_synapse_sublist()
            max_n_words = \
                max([subedge.edge.synapse_row_io.get_n_words(synapse_row)
                    for synapse_row in sublist.get_rows()])
            all_syn_block_sz = \
                self._calculate_all_synaptic_block_size(sublist,
                                                        max_n_words)
            memory_size += all_syn_block_sz
        return memory_size
    
    def get_synaptic_blocks_memory_size(self, lo_atom, hi_atom, in_edges):
        self._check_synapse_dynamics(in_edges)
        memory_size = 0
        
        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionEdge):
                
                # Get maximum row length in this edge 
                max_n_words = in_edge.get_max_n_words(lo_atom, hi_atom)
                all_syn_block_sz = \
                    self._calculate_all_synaptic_block_size(in_edge,
                                                            max_n_words)
                
                # TODO: Fix this to be more accurate!
                # May require modification to the master pynn_population.py
                # table
                n_atoms = sys.maxint
                if issubclass(type(AbstractPartitionableVertex),
                              in_edge._pre_vertex):
                    n_atoms = in_edge._pre_vertex.get_maximum_atoms_per_core()
                if in_edge._pre_vertex.n_atoms < n_atoms:
                    n_atoms = in_edge._pre_vertex.n_atoms

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
            if (isinstance(in_edge, ProjectionEdge)
                    and in_edge.synapse_dynamics is not None):
                if in_edge._synapse_dynamics.fast is not None:
                    raise exceptions.SynapticConfigurationException(
                        "Fast synapse dynamics are not supported")
                elif in_edge._synapse_dynamics.slow is not None:
                    if self._stdp_mechanism is None:
                        self._stdp_mechanism = in_edge._synapse_dynamics.slow
                    else:
                        if not (self._stdp_mechanism
                                == in_edge._synapse_dynamics.slow):
                            raise exceptions.SynapticConfigurationException(
                                "Different STDP mechanisms on the same"
                                + " vertex are not supported")

    def get_n_synapse_type_bits(self):
        """
        Return the number of bits used to identify the synapse in the synaptic
        row
        """
        raise NotImplementedError()

    def write_synapse_parameters(self, spec, subvertex):
        raise NotImplementedError

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

    def get_synapse_parameter_size(self, lo_atom, hi_atom):
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

    def get_stdp_parameter_size(self, lo_atom, hi_atom, in_edges):
        self._check_synapse_dynamics(in_edges)
        if self._stdp_mechanism is not None:
            return self._stdp_mechanism.get_params_size(self, lo_atom, hi_atom)
        return 0

    @staticmethod
    def write_row_length_translation_table(spec, row_length_trnaslation_region):
        """
        Generate Row Length Translation Table (region 4):
        """
        spec.comment("\nWriting Row Length Translation Table:\n")

        # Switch focus of writes to the memory region to hold the table:
        spec.switch_write_focus(region=row_length_trnaslation_region)

        # The table is a list of eight 32-bit words, that provide a row length
        # when given its encoding (3-bit value used as an index into the
        # table).
        # Set the focus to memory region 3 (row length translation):
        for entry in constants.ROW_LEN_TABLE_ENTRIES:
            spec.write_value(data=entry)

    def write_stdp_parameters(self, spec, subvertex, weight_scale,
                              machine_time_step, stdp_params):
        if self._stdp_mechanism is not None:
            self._stdp_mechanism.write_plastic_params(
                spec, stdp_params, machine_time_step, subvertex, weight_scale)

    @staticmethod
    def get_weight_scale(ring_buffer_to_input_left_shift):
        """
        Return the amount to scale the weights by to convert them from floating
        point values to 16-bit fixed point numbers which can be shifted left by
        ring_buffer_to_input_left_shift to produce an s1615 fixed point number
        """
        return float(math.pow(2, 16 - (ring_buffer_to_input_left_shift + 1)))

    def write_synaptic_matrix_and_master_population_table(
            self, spec, subvertex, all_syn_block_sz, weight_scale,
            master_pop_table_region, synaptic_matrix_region, routing_info):
        """
        Simultaneously generates both the master pynn_population.py table and
        the synatic matrix.

        Master Population Table (MPT):
        Table of 1152 entries (one per numbered core on a 48-node board
        arranged in an 8 x 8 grid) giving offset pointer to synapse rows
        for that source pynn_population.py.

        Synaptic Matrix:
        One block for each projection in the network (sub_edge in the graph).
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
        spec.write_value(data=0, repeatReg=my_repeat_reg, sizeof='uint16')

        # Track writes inside the synaptic matrix region:
        next_block_start_addr = 0
        n_synapse_type_bits = self.get_n_synapse_type_bits()

        # For each entry in subedge into the subvertex, create a
        # sub-synaptic list
        for subedge in subvertex.in_subedges:

            # Only deal with incoming projection subedges
            if not subedge.pruneable and isinstance(subedge, ProjectionSubedge):
                key = routing_info.get_key_from_subedge(subedge)
                x = packet_conversions.get_x_from_key(key)
                y = packet_conversions.get_y_from_key(key)
                p = packet_conversions.get_p_from_key(key)
                spec.comment("\nWriting matrix for subedge from {}, {}, {}\n"
                             .format(x, y, p))

                sublist = subedge.get_synapse_sublist()
                row_io = subedge._associated_edge.get_synapse_row_io()
                if logger.isEnabledFor("debug"):
                    logger.debug("Writing subedge from {} ({}-{}) to {} ({}-{})"
                                 .format(subedge.pre_subvertex.label,
                                         subedge.pre_subvertex.lo_atom,
                                         subedge.pre_subvertex.hi_atom,
                                         subvertex.vertex.label,
                                         subvertex.lo_atom,
                                         subvertex.hi_atom))
                    rows = sublist.get_rows()
                    for i in range(len(rows)):
                        logger.debug("{}: {}".format(i, rows[i]))

                # Get the maximum row length in words, excluding headers
                max_row_length = \
                    max([row_io.get_n_words(row) for row in sublist.get_rows()])
                # Get an entry in the row length table for this length
                row_index, row_length = \
                    self.select_minimum_row_length(max_row_length)
                if max_row_length == 0 or row_length == 0:
                    print ""

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
                self.update_master_population_table(spec, block_start_addr,
                                                    row_index, key,
                                                    master_pop_table_region)

    @staticmethod
    def update_master_population_table(spec, block_start_addr, row_index,
                                       key, master_pop_table_region):
        """
        Writes an entry in the Master Population Table for the newly
        created synaptic block.
        An entry in the table is a 16-bit value, with the following structure:
        Bits [2:0]  Row length information. This value (from 0->7)
                    indicates the maximum number of synapses in this
                    block. It is translated in the row length translation
                    table by the executing code each time the table is
                    accessed, to calculate offsets.
        Bits [15:3] Address within the synaptic matrix region of the
                    start of the block. This is 1K bytes aligned, so
                    the true value is found by shifting left by 7 bits
                    then adding the start address of the memory region.
        """
        # Which core has this projection arrived from?
        x = packet_conversions.get_x_from_key(key)
        y = packet_conversions.get_y_from_key(key)
        # the plus one in p calc is due to the router table subtracting one off
        # its routing key for p (also due to unknown reasons). As the c code
        # compenstates for it, we also need to
        p = packet_conversions.get_p_from_key(key)
        # Calculate the index into the master pynn_population.py table for
        # a projection from the given core:
        table_slot_addr = \
            packet_conversions.get_mpt_sb_mem_addrs_from_coords(x, y, p)
        # What is the write address in the table for this index?

        spec.comment("\nUpdate entry in master pynn_population.py table for i"
                     "ncoming connection from {}, {}, {}:\n".format(x, y, p))

        # Process start address (align to 1K boundary then shift right by 10 and
        # left by 3 (i.e. 7) to make it the top 13-bits of the field):
        if (block_start_addr & 0x3FF) != 0:
            raise exceptions.SynapticBlockGenerationException(
                "Synaptic Block start address is not aligned to a 1K boundary")
        #moves by 7 to tack on at the end the row_length information
        # which resides in the last 3 bits
        entry_addr_field = block_start_addr >> 7
        # Assembly entry:
        new_entry = entry_addr_field | row_index

        # Write entry:
        spec.switch_write_focus(region=master_pop_table_region)
        spec.set_write_pointer(data=table_slot_addr)
        spec.write_value(data=new_entry, sizeof='uint16')
        return

    def _get_synaptic_data(self, spinnaker, pre_subvertex, pre_n_atoms,
                           post_subvertex, master_pop_table_region, synapse_io,
                           synaptic_matrix_region):
        """
        Get synaptic weights for a subvertex for a given projection
        """
        synaptic_block, max_row_length = \
            self._retrieve_synaptic_block(
                spinnaker, pre_subvertex, pre_n_atoms, post_subvertex,
                master_pop_table_region, synaptic_matrix_region)
        #translate the synaptic block into a sublist of synapse_row_infos
        synapse_list = \
            self._translate_synaptic_block_from_memory(
                synaptic_block, pre_n_atoms, max_row_length, synapse_io,
                post_subvertex, spinnaker.subgraph)

        return synapse_list

    def _translate_synaptic_block_from_memory(self, synaptic_block, n_atoms,
                                              max_row_length, synapse_io,
                                              post_subvertex, sub_graph):
        """
        translates a collection of memory into synaptic rows
        """
        synaptic_list = list()
        for atom in range(n_atoms):
            #extract the 3 elements of a row (PP, FF, FP)
            p_p_entries, f_f_entries, f_p_entries, = \
                self._extract_row_data_from_memory_block(atom, synaptic_block,
                                                         max_row_length)
            # create a synaptic_row from the 3 entries
            ring_buffer_shift = \
                utility_calls.get_ring_buffer_to_input_left_shift(
                    post_subvertex, sub_graph)

            weight_scale = self.get_weight_scale(ring_buffer_shift)
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
    def _extract_row_data_from_memory_block(atom, synaptic_block,
                                            max_row_length):

        """
        extracts the 6 elements from a data block which is ordered
        no PP, pp, No ff, NO fp, FF fp
        """
        #locate offset after conversion to bytes
        position_in_block = \
            atom * 4 * (max_row_length + constants.SYNAPTIC_ROW_HEADER_WORDS)
        #read in number of plastic plastic entries
        no_plastic_plastic_entries = \
            struct.unpack_from("<I", synaptic_block, position_in_block)[0]
        position_in_block += 4
        #read inall the plastic entries
        fmt = "<{}I".format(no_plastic_plastic_entries)
        plastic_plastic_entries = \
            struct.unpack_from(fmt, synaptic_block, position_in_block)
        #update position in block
        position_in_block += (no_plastic_plastic_entries * 4)
        #update position in block
        #read in number of both fixed fixed and fixed plastic
        no_fixed_fixed = \
            struct.unpack_from("<I", synaptic_block, position_in_block)[0]
        position_in_block += 4
        no_fixed_plastic = \
            struct.unpack_from("<I", synaptic_block, position_in_block)[0]
        #update position in block
        position_in_block += 4
        #read in fixed fixed
        fmt = "<{}I".format(no_fixed_fixed)
        fixed_fixed_entries = \
            struct.unpack_from(fmt, synaptic_block, position_in_block)
        #update position in block
        position_in_block += (no_fixed_fixed * 4)
        #read in fixed plastic
        fmt = "<{}H".format(no_fixed_plastic)
        fixed_plastic_entries = \
            struct.unpack_from(fmt, synaptic_block, position_in_block)
        return (plastic_plastic_entries, fixed_fixed_entries,
                fixed_plastic_entries)

    def _retrieve_synaptic_block(self, spinnaker, pre_subvertex, pre_n_atoms,
                                 post_subvertex, master_pop_table_region,
                                 synaptic_matrix_region):
        """
        reads in a synaptic block from a given processor and subvertex on the
        machine.
        """
        post_x, post_y, post_p = \
            post_subvertex.placement.processor.get_coordinates()
        spinnaker.txrx.select(post_x, post_y)
        # either read in the master pop table or retrieve it from storage
        master_pop_base_mem_address, app_data_base_address = \
            self._read_in_master_pop_table(post_x, post_y, post_p, spinnaker,
                                           master_pop_table_region)

        # locate address of the synaptic block
        pre_x, pre_y, pre_p = \
            pre_subvertex.placement.processor.get_coordinates()
        table_slot_addr = packet_conversions.\
            get_mpt_sb_mem_addrs_from_coords(pre_x, pre_y, pre_p)
        master_table_pop_entry_address = (table_slot_addr +
                                          master_pop_base_mem_address)
        #read in the master pop entry
        master_pop_entry = \
            self._read_and_convert(pre_x, pre_y, master_table_pop_entry_address,
                                   2, "<H", spinnaker)

        synaptic_block_base_address = master_pop_entry >> 3  # in kilobytes
        #convert synaptic_block_base_address into bytes from kilobytes
        synaptic_block_base_address_offset = synaptic_block_base_address << 10
        max_row_length_index = master_pop_entry & 0x7
        #retrieve the max row length
        maxed_row_length = constants.ROW_LEN_TABLE_ENTRIES[max_row_length_index]

        #calculate the synaptic block size in words
        synaptic_block_size = pre_n_atoms * 4 * \
            (constants.SYNAPTIC_ROW_HEADER_WORDS + maxed_row_length)

        #read in the base address of the synaptic matrix in the app region table
        synapste_region_base_address_location = \
            get_region_base_address_offset(app_data_base_address,
                                           synaptic_matrix_region)

        # read in the memory address of the synaptic_region base address
        synapste_region_base_address = \
            self._read_and_convert(pre_x, pre_y,
                                   synapste_region_base_address_location, 4,
                                   "<I", spinnaker)
        # the base address of the synaptic block in absolute terms is the app
        # base, plus the synaptic matrix base plus the offset
        synaptic_block_base_address = \
            app_data_base_address + synapste_region_base_address + \
            synaptic_block_base_address_offset

        #read in and return the synaptic block
        block = spinnaker.txrx.read_memory(pre_x, pre_y,
                                           synaptic_block_base_address,
                                           synaptic_block_size)
        if len(block[0]) != synaptic_block_size:
            raise exceptions.SynapticBlockReadException(
                "Not enough data has been read "
                "(aka, something funkky happened)")
        return block

    def _read_in_master_pop_table(self, x, y, p, spinnaker,
                                  master_pop_table_region):
        """
        reads in the master pop table from a given processor on the machine
        """
        # Get the App Data base address for the core
        # (location where this cores memory starts in
        # sdram and region table)
        app_data_base_address =\
            spinnaker.txrx.get_cpu_information_from_core(x, y, p).user[0]

        # Get the memory address of the master pop table region
        master_pop_region = master_pop_table_region

        master_region_base_address_address = \
            get_region_base_address_offset(app_data_base_address,
                                           master_pop_region)

        master_region_base_address_offset = \
            self._read_and_convert(x, y, master_region_base_address_address,
                                   4, "<I", spinnaker)

        master_region_base_address =\
            master_region_base_address_offset + app_data_base_address

        #read in the master pop table and store in ram for future use
        logger.debug("Reading {} ({}) bytes starting at {} + "
                     "4".format(constants.MASTER_POPULATION_TABLE_SIZE,
                                hex(constants.MASTER_POPULATION_TABLE_SIZE),
                                hex(master_region_base_address)))

        return master_region_base_address, app_data_base_address

    @staticmethod
    def _read_and_convert(x, y, address, length, data_format,
                          spinnaker):
        """
        tries to read and convert a piece of memory. If it fails, it tries again
        up to for 4 times, and then if still fails, throws an error.
        """
        try:
            data = spinnaker.txrx.read_memory(x, y, address, length)
            return struct.unpack(data_format, data)[0]
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