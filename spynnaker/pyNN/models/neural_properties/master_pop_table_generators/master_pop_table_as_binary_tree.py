from spynnaker.pyNN.models.abstract_models.abstract_master_pop_table_factory\
    import AbstractMasterPopTableFactory
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN import exceptions

import logging
import math
import numpy
logger = logging.getLogger(__name__)


class _MasterPopEntry(object):

    MASTER_POP_ENTRY_SIZE_BYTES = 12
    MASTER_POP_ENTRY_SIZE_INTS = 3

    def __init__(self, key_combo, mask, address, row_index):
        self._key_combo = key_combo
        self._mask = mask
        self._address = address
        self._row_index = row_index

    @property
    def key_combo(self):
        return self._key_combo

    @property
    def mask(self):
        return self._mask

    @property
    def address(self):
        return self._address

    @property
    def row_index(self):
        return self._row_index


class MasterPopTableAsBinaryTree(AbstractMasterPopTableFactory):

    def __init__(self):
        AbstractMasterPopTableFactory.__init__(self)
        self.entries = list()

    def extract_synaptic_matrix_data_location(
            self, incoming_key_combo, master_pop_base_mem_address, txrx, chip_x,
            chip_y):

        #get no_entries in master pop
        no_entries = txrx.read_memory(chip_x, chip_y,
                                      master_pop_base_mem_address, 4)
        top_position = (no_entries * _MasterPopEntry.MASTER_POP_ENTRY_SIZE_BYTES)
        #read in master pop structure
        master_pop_structure = \
            txrx.read_memory(chip_x, chip_y, master_pop_base_mem_address + 4,
                             top_position)
        #convert into a numpy array
        master_pop_structure = \
            numpy.frombuffer(dtype='uint8',
                             buffer=master_pop_structure).view(dtype='<u4')

        top_position = no_entries * _MasterPopEntry.MASTER_POP_ENTRY_SIZE_INTS

        entry = self._locate_entry(incoming_key_combo, master_pop_structure,
                                   top_position, bottom_position=0)

        max_row_size = constants.ROW_LEN_TABLE_ENTRIES[entry.row_index]
        return max_row_size, entry.address

    def _locate_entry(self, incoming_key_combo, master_pop_structure,
                      top_position, bottom_position):
        """ searches the binary tree strucutre for the correct entry.

        :param incoming_key_combo:
        :param master_pop_structure:
        :return: the entry of the binary tree associated with the incoming keycombo
        :rtype: a _masterpopEntry object
        """
        middle_offset = (top_position - bottom_position) / 2
        # if in middle of two elements, floor it to the bottom element
        if middle_offset % 3 != 0:
            middle_offset -= middle_offset % 3

        middle_position = bottom_position + middle_offset
        #retrieve entry
        entry = master_pop_structure[middle_position - 1:middle_position + 2]
        #check if correct entry, or move to new section of binary search
        if (incoming_key_combo & entry[1]) == entry[0]:
            return _MasterPopEntry(mask=entry[1], key_combo=entry[0],
                                   address=(entry[2] >> 8),
                                   row_index=entry[2] & 0x7)
        elif (incoming_key_combo & entry[1]) > entry[0]:
            return self._locate_entry(incoming_key_combo, master_pop_structure,
                                      top_position, middle_position)
        elif (incoming_key_combo & entry[1]) < entry[0]:
            return self._locate_entry(incoming_key_combo, master_pop_structure,
                                      middle_position, bottom_position)
        else:
            raise exceptions.MemReadException(
                "a entry inside the master pop structure is corrupt."
                " Please restart and try again")

    def update_master_population_table(
            self, spec, block_start_addr, row_index, key,
            master_pop_table_region, incoming_mask):
        self.entries.append(_MasterPopEntry(key & incoming_mask, incoming_mask,
                                            block_start_addr, row_index))

    def finish_master_pop_table(self, spec, master_pop_table_region):
        #locate the number of entries to be written to the master pop
        no_entries = len(self.entries)
        spec.switch_write_focus(region=master_pop_table_region)
        #write no entries first so that the tree can be read in easily.
        spec.write_value(no_entries)
        #sort out entries based off key_combo
        sorted(self.entries,
               key=lambda pop_table_entry: pop_table_entry.key_combo)
        #add each entry
        for pop_entry in self.entries:
            spec.write_value(pop_entry.key_combo)
            spec.write_value(pop_entry.mask)
            spec.write_value((pop_entry.address << 8) | pop_entry.row_index)
