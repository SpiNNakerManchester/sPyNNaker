from spynnaker.pyNN.models.abstract_models.abstract_master_pop_table_factory\
    import AbstractMasterPopTableFactory
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN import exceptions

#pacman constants
from pacman.utilities import constants as pacman_constants

#dsg imports
from data_specification.enums.data_type import DataType

import logging
import math
logger = logging.getLogger(__name__)


class MasterPopTableAs2dArray(AbstractMasterPopTableFactory):

    def __init__(self):
        AbstractMasterPopTableFactory.__init__(self)

    def extract_synaptic_matrix_data_location(
            self, incoming_key, master_pop_base_mem_address, txrx, chip_x,
            chip_y):
        # locate address of the synaptic block
        pre_x = packet_conversions.get_x_from_key(incoming_key)
        pre_y = packet_conversions.get_y_from_key(incoming_key)
        pre_p = packet_conversions.get_p_from_key(incoming_key)
        table_slot_addr = packet_conversions.\
            get_mpt_sb_mem_addrs_from_coords(pre_x, pre_y, pre_p)
        master_table_pop_entry_address = (table_slot_addr +
                                          master_pop_base_mem_address)
        #read in entry
        master_pop_entry = \
            self.read_and_convert(
                chip_x, chip_y, master_table_pop_entry_address, 2, "<H",
                txrx)

        synaptic_block_base_address = master_pop_entry >> 3  # in kilobytes
        #convert synaptic_block_base_address into bytes from kilobytes
        synaptic_block_base_address_offset = synaptic_block_base_address << 10
        max_row_length_index = master_pop_entry & 0x7
        #retrieve the max row length
        maxed_row_length = constants.ROW_LEN_TABLE_ENTRIES[max_row_length_index]
        return maxed_row_length, synaptic_block_base_address_offset

    def update_master_population_table(self, spec, block_start_addr, row_index,
                                       key, master_pop_table_region,
                                       mask=pacman_constants.DEFAULT_MASK):
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
        assert (block_start_addr < math.pow(2, 32))
        #moves by 7 to tack on at the end the row_length information
        # which resides in the last 3 bits
        entry_addr_field = block_start_addr >> 7
        # Assembly entry:
        new_entry = entry_addr_field | row_index

        # Write entry:
        spec.switch_write_focus(region=master_pop_table_region)
        spec.set_write_pointer(address=table_slot_addr)
        spec.write_value(data=new_entry, data_type=DataType.INT16)

    def finish_master_pop_table(self, spec, master_pop_table_region):
        pass