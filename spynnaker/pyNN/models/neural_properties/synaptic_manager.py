__author__ = 'stokesa6'
import numpy, math, logging, struct
from pacman103.front.common.projection_edge import ProjectionEdge
from pacman103.front.common.projection_subedge import ProjectionSubedge
from pacman103.front.common.synaptic_list import SynapticList
from pacman103.front.common.fixed_synapse_row_io import FixedSynapseRowIO
from pacman103.front.pynn.synapse_dynamics.\
    weight_based_plastic_synapse_row_io import WeightBasedPlasticSynapseRowIo
from pacman103.core.utilities import packet_conversions
from pacman103.core import exceptions
from pacman103.core.spinnman.scp import scamp
from pacman103.core.utilities.memory_utils import getAppDataBaseAddressOffset,\
                                                  getRegionBaseAddressOffset

logger = logging.getLogger(__name__)

class SynapticManager(object):

    SYNAPTIC_ROW_HEADER_WORDS = 2 + 1   # Words - 2 for row lenth and number of rows and
                                    # 1 for plastic region size (which might be 0)

    ROW_LEN_TABLE_ENTRIES = [0, 1, 8, 16, 32, 64, 128, 256]
    ROW_LEN_TABLE_SIZE    = 4 * len(ROW_LEN_TABLE_ENTRIES)

    X_CHIPS = 8
    Y_CHIPS = 8
    CORES_PER_CHIP = 18
    MASTER_POPULATION_ENTRIES = (X_CHIPS * Y_CHIPS * CORES_PER_CHIP)
    MASTER_POPULATION_TABLE_SIZE = 2 * MASTER_POPULATION_ENTRIES # 2 bytes per entry



    def __init__(self):
        self._stdp_checked = False
        self._stdp_mechanism = None

    def writeSynapseRowInfo(self, sublist, rowIO, spec, currentWritePtr,
            fixedRowLength, region, weight_scale, n_synapse_type_bits):
        """
        Write this synaptic block to the designated synaptic matrix region at
        its current write pointer.
        """

        # Switch focus to the synaptic matrix memory region:
        spec.switchWriteFocus(region)

        # Align the write pointer to the next 1Kbyte boundary using padding:
        writePtr = currentWritePtr
        if (writePtr & 0x3FF) != 0:

            # Ptr not aligned. Align it:
            writePtr = (writePtr & 0xFFFFFC00) + 0x400

            # Pad out data file with the added alignment bytes:
            numPaddingBytes = writePtr - currentWritePtr
            spec.moveToReg(destReg = 15, data = numPaddingBytes)
            spec.write(data = 0xDD, repeatReg = 15, sizeof='uint8')

        # Remember this aligned address, it's where this block will start:
        blockStartAddr = writePtr
        # Write the synaptic block, tracking the word count:
        synapticRows = sublist.get_rows()

        rowNo = 0
        for row in synapticRows:
            wordsWritten = 0
            plastic_region = rowIO.get_packed_plastic_region(row, weight_scale,
                    n_synapse_type_bits)

            # Write the size of the plastic region
            spec.comment("\nWriting plastic region for row {}".format(rowNo))
            spec.write(data = len(plastic_region), sizeof = "uint32")
            wordsWritten += 1

            # Write the plastic region
            spec.write_array(data = plastic_region)
            wordsWritten += len(plastic_region)

            fixed_fixed_region = numpy.asarray(
                    rowIO.get_packed_fixed_fixed_region(row, weight_scale,
                                                        n_synapse_type_bits),
                                                        dtype="uint32")
            fixed_plastic_region = numpy.asarray(
                    rowIO.get_packed_fixed_plastic_region(row, weight_scale,
                                                          n_synapse_type_bits),
                                                          dtype="uint16")

            # Write the size of the fixed parts
            spec.comment("\nWriting fixed region for row {}".format(rowNo))
            spec.write(data = len(fixed_fixed_region), sizeof = "uint32")
            spec.write(data = len(fixed_plastic_region), sizeof = "uint32")
            wordsWritten += 2

            # Write the fixed fixed region
            spec.write_array(data = fixed_fixed_region)
            wordsWritten += len(fixed_fixed_region)

            # As everything needs to be word aligned, add extra zero to fixed_plastic
            # Region if it has an odd number of entries and build uint32 view of it
            if (len(fixed_plastic_region) % 2) != 0:
                fixed_plastic_region = numpy.asarray(numpy.append(
                        fixed_plastic_region, 0), dtype='uint16')
            # does indeed return something (due to c fancy stuff in numpi) ABS
            fixed_plastic_region_words = fixed_plastic_region.view(dtype="uint32")

            spec.write_array(data = fixed_plastic_region_words)
            wordsWritten += len(fixed_plastic_region_words)

            writePtr += (4 * wordsWritten)

            # Write padding (if required):
            padding = ((fixedRowLength + self.SYNAPTIC_ROW_HEADER_WORDS) - wordsWritten)
            if padding != 0:
                spec.write(data=0xBBCCDDEE, repeats=padding, sizeof='uint32')
                writePtr += 4 * padding

            rowNo += 1

        # The current write pointer is where the next block could start:
        nextBlockStartAddr = writePtr
        return blockStartAddr, nextBlockStartAddr
    
    def get_exact_synaptic_block_memory_size(self, subvertex):
        memorySize = 0
        
        # Go through the subedges and add up the memory
        for subedge in subvertex.in_subedges:
            if (memorySize & 0x3FF) != 0:
                memorySize = (memorySize & 0xFFFFFC00) + 0x400
            
            sublist = subedge.get_synapse_sublist()
            max_n_words = max([subedge.edge.synapse_row_io.get_n_words(
                        synapse_row) 
                    for synapse_row in sublist.get_rows()])
            rowLength = self.selectMinimumRowLength(max_n_words)[1]
            numRows = sublist.get_n_rows()
            synBlockSz = 4 * (self.SYNAPTIC_ROW_HEADER_WORDS + rowLength)
            allSynBlockSz = synBlockSz * numRows
            memorySize += allSynBlockSz
        return memorySize    
    
    def getSynapticBlocksMemorySize(self, lo_atom, hi_atom, in_edges):
        self._check_synapse_dynamics(in_edges)
        memorySize = 0
        
        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionEdge):
                
                # Get maximum row length in this edge 
                maxRowLength = in_edge.get_max_n_words(lo_atom, hi_atom)
                numRows = in_edge.get_n_rows()
                    
                # Gets smallest possible (i.e. supported by row length 
                # Table structure) that can contain maxRowLength
                rowLength = self.selectMinimumRowLength(maxRowLength)[1]
                synBlockSz = 4 * (self.SYNAPTIC_ROW_HEADER_WORDS + rowLength)
                allSynBlockSz = synBlockSz * numRows
                
                # TODO: Fix this to be more accurate!
                # May require modification to the master abstract_population.py table
                n_atoms = in_edge.prevertex.get_maximum_atoms_per_core()
                if in_edge.prevertex.custom_max_atoms_per_core != None:
                    n_atoms = in_edge.prevertex.custom_max_atoms_per_core
                if in_edge.prevertex.atoms < n_atoms:
                    n_atoms = in_edge.prevertex.atoms
                if n_atoms > 100:
                    n_atoms = 100
                
                extraMem = math.ceil(float(numRows) / float(n_atoms)) * 1024
                if extraMem == 0:
                    extraMem = 1024
                allSynBlockSz += extraMem
                memorySize += allSynBlockSz 
                
        return memorySize

    def _check_synapse_dynamics(self, in_edges):
        if self._stdp_checked:
            return True
        self._stdp_checked = True
        for in_edge in in_edges:
            if (isinstance(in_edge, ProjectionEdge)
                    and in_edge.synapse_dynamics is not None):
                if in_edge.synapse_dynamics.fast is not None:
                    raise exceptions.PacmanException(
                            "Fast synapse dynamics are not supported")
                elif in_edge.synapse_dynamics.slow is not None:
                    if self._stdp_mechanism is None:
                        self._stdp_mechanism = in_edge.synapse_dynamics.slow
                    else:
                        if not (self._stdp_mechanism
                                == in_edge.synapse_dynamics.slow):
                            raise exceptions.PacmanException(
                                    "Different STDP mechanisms on the same"
                                    + " vertex are not supported")


    def get_n_synapse_type_bits(self):
        """
        Return the number of bits used to identify the synapse in the synaptic
        row
        """
        raise NotImplementedError()

    def write_synapse_parameters(self, spec, machineTimeStep, subvertex):
        raise NotImplementedError


    def selectMinimumRowLength(self, longestActualRow):
        """
        Given a new synaptic block the list of valid row lengths supported,
        return the index and value of the minimum valid length that can fit
        even the largest row in the synaptic block.
        """

        # Can even the largest valid entry accommodate the given synaptic row?
        if longestActualRow > SynapticManager.ROW_LEN_TABLE_ENTRIES[-1]:
            raise Exception(
                """\
                Synaptic block generation.
                Row table entry calculator: Max row length too long.
                Wanted length %d, but max length permitted is %d.
                Try adjusting table entries in row length translation table.
                """ % (longestActualRow,
                       SynapticManager.ROW_LEN_TABLE_ENTRIES[-1])
            )

        # Search up the list until we find one entry big enough:
        bestIndex = None
        minimumValidRowLength = None
        for i in range(len(SynapticManager.ROW_LEN_TABLE_ENTRIES)):
            if longestActualRow <= SynapticManager.ROW_LEN_TABLE_ENTRIES[i]:
                # This row length is big enough. Choose it and exit:
                bestIndex = i
                minimumValidRowLength = SynapticManager.ROW_LEN_TABLE_ENTRIES[i]
                break

        # Variable bestIndex now contains the table entry corresponding to the
        # smallest row that is big enough for our row of data
        return bestIndex, minimumValidRowLength

    def get_synapse_parameter_size(self, lo_atom, hi_atom):
        raise NotImplementedError

    def get_synapse_targets(self):
        """
        Gets the supported names of the synapse targets
        """
        return ("excitatory", "inhibitory")

    def get_synapse_id(self, target_name):
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

    def write_row_length_translation_table(self, spec, ROW_LEN_TRANSLATION):
        """
        Generate Row Length Translation Table (region 4):
        """
        spec.comment("\nWriting Row Length Translation Table:\n")

        # Switch focus of writes to the memory region to hold the table:
        spec.switchWriteFocus(region = ROW_LEN_TRANSLATION)

        # The table is a list of eight 32-bit words, that provide a row length
        # when given its encoding (3-bit value used as an index into the
        # table).
        # Set the focus to memory region 3 (row length translation):
        for entry in SynapticManager.ROW_LEN_TABLE_ENTRIES:
            spec.write(data = entry)

    def write_stdp_parameters(self, spec, machineTimeStep, subvertex,
                            weight_scale, STDP_PARAMS):
        if self._stdp_mechanism is not None:
            self._stdp_mechanism.write_plastic_params(spec, STDP_PARAMS,
                    machineTimeStep, subvertex, weight_scale)


    def get_weight_scale(self, ring_buffer_to_input_left_shift):
        """
        Return the amount to scale the weights by to convert them from floating
        point values to 16-bit fixed point numbers which can be shifted left by
        ring_buffer_to_input_left_shift to produce an s1615 fixed point number
        """
        return float(math.pow(2, 16 - (ring_buffer_to_input_left_shift + 1)))

    def write_synaptic_matrix_and_master_population_table(self, spec, subvertex,
                                                    allSynBlockSz,weight_scale,
                                                    MASTER_POP_TABLE,
                                                    SYNAPTIC_MATRIX):
        """
        Simultaneously generates both the master abstract_population.py table and the
        synatic matrix.

        Master Population Table (MPT):
        Table of 1152 entries (one per numbered core on a 48-node board
        arranged in an 8 x 8 grid) giving offset pointer to synapse rows
        for that source abstract_population.py.

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
        spec.switchWriteFocus(region=MASTER_POP_TABLE)
        myRepeatReg = 4
        spec.moveToReg(destReg = myRepeatReg,
                       data = SynapticManager.MASTER_POPULATION_ENTRIES)
        spec.write(data=0, repeatReg = myRepeatReg, sizeof = 'uint16')

        # Track writes inside the synaptic matrix region:
        next_block_start_addr = 0
        n_synapse_type_bits = self.get_n_synapse_type_bits()

        # For each entry in subedge into the subvertex, create a
        # sub-synaptic list
        for subedge in subvertex.in_subedges:

            # Only deal with incoming projection subedges
            if not subedge.pruneable and isinstance(subedge, ProjectionSubedge):

                x = packet_conversions.get_x_from_key(subedge.key)
                y = packet_conversions.get_y_from_key(subedge.key)
                p = packet_conversions.get_p_from_key(subedge.key)
                spec.comment("\nWriting matrix for subedge from"
                        + " {}, {}, {}\n".format(x, y, p))

                sublist = subedge.get_synapse_sublist()
                rowIO = subedge.edge.get_synapse_row_io()
                #if (logger.isEnabledFor("debug")):
                #    logger.debug("Writing subedge from {} ({}-{}) to {} ({}-{})"
                #            .format(sourceSubvertex.vertex.label,
                #                    sourceSubvertex.lo_atom,
                #                    sourceSubvertex.hi_atom,
                #                    subvertex.vertex.label, subvertex.lo_atom,
                #                    subvertex.hi_atom))
                #    rows = sublist.get_rows()
                #    for i in range(len(rows)):
                #        logger.debug("{}: {}".format(i, rows[i]))

                # Get the maximum row length in words, excluding headers
                max_row_length = max([rowIO.get_n_words(row)
                        for row in sublist.get_rows()])
                # Get an entry in the row length table for this length
                row_index, row_length = \
                    self.selectMinimumRowLength(max_row_length)
                if max_row_length == 0 or row_length == 0:
                    print ""

                # Write the synaptic block for the sublist
                (block_start_addr, next_block_start_addr) = \
                    self.writeSynapseRowInfo(sublist, rowIO, spec,
                            next_block_start_addr, row_length,
                            SYNAPTIC_MATRIX, weight_scale,
                            n_synapse_type_bits)
                if ((next_block_start_addr - 1) > allSynBlockSz):
                    raise Exception(
                            "Too much synapse memory consumed (used {} of {})!"
                            .format(next_block_start_addr - 1, allSynBlockSz))
                self.updateMasterPopulationTable(spec, block_start_addr,
                                                 row_index, subedge.key,
                                                 MASTER_POP_TABLE)


    def updateMasterPopulationTable(self, spec, blockStartAddr, rowIndex, key,
                                    MASTER_POP_TABLE):
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
        # Calculate the index into the master abstract_population.py table for
        # a projection from the given core:
        tableSlotAddr = \
            packet_conversions.get_mpt_sb_mem_addrs_from_coords(x, y, p)
        # What is the write address in the table for this index?

        spec.comment("\nUpdate entry in master abstract_population.py table for incoming"
                + " connection from {}, {}, {}:\n".format(x, y, p))

        # Process start address (align to 1K boundary then shift right by 10 and
        # left by 3 (i.e. 7) to make it the top 13-bits of the field):
        if (blockStartAddr & 0x3FF) != 0:
            raise Exception(
                "Synaptic Block start address is not aligned to a 1K boundary")
        #moves by 7 to tack on at the end the row_length information
        # which resides in the last 3 bits
        entryAddrField = blockStartAddr >> 7
        # Assembly entry:
        newEntry = entryAddrField | rowIndex

        # Write entry:
        spec.switchWriteFocus(region = MASTER_POP_TABLE)
        spec.setWritePtr(data = tableSlotAddr)
        spec.write(data = newEntry, sizeof = 'uint16')
        return

    def _get_synaptic_data(self, controller, pre_subvertex, pre_n_atoms,
                          post_subvertex, master_pop_table_region, synapse_io,
                          synaptic_matrix_region):
        '''
        Get synaptic weights for a subvertex for a given projection
        '''
        synaptic_block, max_row_length = \
            self._retrieve_synaptic_block(controller, pre_subvertex,
                                          pre_n_atoms, post_subvertex,
                                          master_pop_table_region,
                                          self.MASTER_POPULATION_TABLE_SIZE,
                                          synaptic_matrix_region)
        #translate the synaptic block into a sublist of synapse_row_infos
        synapse_list = \
            self._translate_synaptic_block_from_memory(synaptic_block,
                                                       pre_n_atoms,
                                                       max_row_length,
                                                       synapse_io,
                                                       pre_subvertex,
                                                       post_subvertex)

        return synapse_list

    def _translate_synaptic_block_from_memory(self, synaptic_block, n_atoms,
                                              max_row_length, synapse_io,
                                              pre_subvertex, post_subvertex):
        '''
        translates a collection of memory into synaptic rows
        '''
        synaptic_list = list()
        for atom in range(n_atoms):
            #extract the 3 elements of a row (PP, FF, FP)
            p_p_entries, f_f_entries, f_p_entries, = \
                self._extract_row_data_from_memory_block(atom, synaptic_block,
                                                         max_row_length,
                                                         synapse_io)
            # create a synaptic_row from the 3 entries
            ring_buffer_shift = \
                self.get_ring_buffer_to_input_left_shift(post_subvertex)
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


    def _extract_row_data_from_memory_block(self, atom, synaptic_block,
                                            max_row_length, synapse_io):

        '''
        extracts the 6 elements from a data block which is ordered
        no PP, pp, No ff, NO fp, FF fp
        '''
        #locate offset
        position_in_block = \
            atom * 4 * (max_row_length + SynapticManager.SYNAPTIC_ROW_HEADER_WORDS) # convert to bytes
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
        return plastic_plastic_entries, fixed_fixed_entries, \
               fixed_plastic_entries




    def _retrieve_synaptic_block(self, controller, pre_subvertex, pre_n_atoms,
                                 post_subvertex, master_pop_table_region,
                                 MASTER_POPULATION_TABLE_SIZE,
                                 synaptic_matrix_region):
        '''
        reads in a synaptic block from a given processor and subvertex on the
        machine.
        '''
        post_x, post_y, post_p = \
            post_subvertex.placement.processor.get_coordinates()
        controller.txrx.select(post_x, post_y)
        # either read in the master pop table or retrieve it from storage
        app_data_base_address = None
        if not post_subvertex in controller.dao.master_population_tables.keys():
            master_pop_base_mem_address,\
            app_data_base_address = \
                self._read_in_master_pop_table(post_p, controller,
                                               master_pop_table_region,
                                               MASTER_POPULATION_TABLE_SIZE)

            controller.dao.master_population_tables[post_subvertex] = list()
            controller.dao.master_population_tables[post_subvertex].append(master_pop_base_mem_address)
            controller.dao.master_population_tables[post_subvertex].append(app_data_base_address)
        else:
            master_pop_base_mem_address = \
                controller.dao.master_population_tables[post_subvertex][0]
            app_data_base_address = \
                controller.dao.master_population_tables[post_subvertex][1]


        # locate address of the synaptic block
        pre_x, pre_y, pre_p = pre_subvertex.placement.processor.get_coordinates()
        tableSlotAddr = packet_conversions.\
            get_mpt_sb_mem_addrs_from_coords(pre_x, pre_y,pre_p)
        master_table_pop_entry_address = (tableSlotAddr +
                                          master_pop_base_mem_address)
        #read in the master pop entry
        master_pop_entry = \
            self._read_and_convert(master_table_pop_entry_address,
                                   scamp.TYPE_HALF, 2, "<H", controller)


        synaptic_block_base_address = master_pop_entry >> 3 #in kilobytes
        #convert synaptic_block_base_address into bytes from kilobytes
        synaptic_block_base_address_offset = synaptic_block_base_address << 10
        max_row_length_index = master_pop_entry & 0x7
        #retrieve the max row length
        maxed_row_length =\
            SynapticManager.ROW_LEN_TABLE_ENTRIES[max_row_length_index]

        #calculate the synaptic block size in words
        synaptic_block_size = pre_n_atoms * 4 * \
            (SynapticManager.SYNAPTIC_ROW_HEADER_WORDS + maxed_row_length)

        #read in the base address of the synaptic matrix in the app region table
        synapste_region_base_address_location = \
            getRegionBaseAddressOffset(app_data_base_address,
                                       synaptic_matrix_region)

        # read in the memory address of the synaptic_region base address
        synapste_region_base_address = \
            self._read_and_convert(synapste_region_base_address_location,
                                   scamp.TYPE_WORD, 4, "<I", controller)
        # the base address of the synaptic block in absolute terms is the app
        # base, plus the synaptic matrix base plus the offset
        synaptic_block_base_address = \
            app_data_base_address + synapste_region_base_address + \
            synaptic_block_base_address_offset

        #read in and return the synaptic block
        block = controller.txrx.memory_calls.\
            read_mem(synaptic_block_base_address, scamp.TYPE_WORD,
                     synaptic_block_size), maxed_row_length
        if len(block[0]) != synaptic_block_size:
            raise exceptions.SpinnManException("Not enough data has been read (aka, something funkky)")
        return block



    def _read_in_master_pop_table(self, p, controller, master_pop_table_region,
                                  MASTER_POPULATION_TABLE_SIZE):
        '''
        reads in the master pop table from a given processor on the machine
        '''
        # Get the App Data base address for the core
        # (location where this cores memory starts in
        # sdram and region table)
        app_data_base_address_offset = getAppDataBaseAddressOffset(p)
        app_data_base_address = \
            self._read_and_convert(app_data_base_address_offset,
                                   scamp.TYPE_WORD, 4, "<I", controller)

        # Get the memory address of the master pop table region
        master_pop_region = master_pop_table_region

        master_region_base_address_address = \
            getRegionBaseAddressOffset(app_data_base_address,
                                       master_pop_region)

        master_region_base_address_offset = \
            self._read_and_convert(master_region_base_address_address,
                                   scamp.TYPE_WORD, 4, "<I", controller)

        master_region_base_address =\
            master_region_base_address_offset + app_data_base_address

        #read in the master pop table and store in ram for future use
        logger.debug("Reading {} ({}) bytes starting at {} + "
                     "4".format(MASTER_POPULATION_TABLE_SIZE,
                                hex(MASTER_POPULATION_TABLE_SIZE),
                                hex(master_region_base_address)))

        return master_region_base_address, app_data_base_address


    def _read_and_convert(self, address, type, size, format, controller,
                          attempt=0):
        '''
        tries to read and convert a piece of memory. If it fails, it tries again
        up to for 4 times, and then if still fails, throws an error.
        '''
        try:
            data = controller.txrx.memory_calls.read_mem(address, type, size)
            return struct.unpack(format, data)[0]
        except Exception as e:
            if attempt != 4:
                attempt += 1
                return self._read_and_convert(address, type, size, format,
                                              controller, attempt)
            else:
                raise exceptions.SpinnManException("failed to read and "
                                                   "translate a piece of "
                                                   "memory.")