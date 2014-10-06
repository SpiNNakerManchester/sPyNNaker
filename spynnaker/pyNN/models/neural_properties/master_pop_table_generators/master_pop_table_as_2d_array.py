from spynnaker.pyNN.models.abstract_models.abstract_master_pop_table_factory\
    import AbstractMasterPopTableFactory
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities.utility_calls \
    import get_region_base_address_offset
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN import exceptions

#dsg imports
from data_specification.enums.data_type import DataType

import logging
logger = logging.getLogger(__name__)


class MasterPopTableAs2dArray(AbstractMasterPopTableFactory):

    def __init__(self):
        AbstractMasterPopTableFactory.__init__(self)

    def extract_synaptic_matrix_data_location(
            self, incoming_key, master_pop_base_mem_address):
        # locate address of the synaptic block
        pre_x = packet_conversions.get_x_from_key(incoming_key)
        pre_y = packet_conversions.get_y_from_key(incoming_key)
        pre_p = packet_conversions.get_p_from_key(incoming_key)
        table_slot_addr = packet_conversions.\
            get_mpt_sb_mem_addrs_from_coords(pre_x, pre_y, pre_p)
        master_table_pop_entry_address = (table_slot_addr +
                                          master_pop_base_mem_address)
        return master_table_pop_entry_address

    def update_master_population_table(self, spec, block_start_addr, row_index,
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
        spec.set_write_pointer(address=table_slot_addr)
        spec.write_value(data=new_entry, data_type=DataType.INT16)

    def read_in_master_pop_table(self, x, y, p, transceiver,
                                 master_pop_table_region):
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
            self.read_and_convert(x, y, master_region_base_address_address,
                                  4, "<I", transceiver)

        master_region_base_address =\
            master_region_base_address_offset + app_data_base_address

        #read in the master pop table and store in ram for future use
        logger.debug("Reading {} ({}) bytes starting at {} + "
                     "4".format(constants.MASTER_POPULATION_TABLE_SIZE,
                                hex(constants.MASTER_POPULATION_TABLE_SIZE),
                                hex(master_region_base_address)))

        return master_region_base_address, app_data_base_address