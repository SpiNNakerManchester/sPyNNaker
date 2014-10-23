from spynnaker.pyNN.models.abstract_models.abstract_master_pop_table_factory\
    import AbstractMasterPopTableFactory

from data_specification.enums.data_type import DataType

import logging
logger = logging.getLogger(__name__)

class _MasterPopEntry(object):

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
            self, incoming_key_combo, master_pop_base_mem_address,
            incoming_mask):
        pass

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
