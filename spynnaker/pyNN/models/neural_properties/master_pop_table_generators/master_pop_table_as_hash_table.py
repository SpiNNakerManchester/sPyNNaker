from spynnaker.pyNN.models.abstract_models.abstract_master_pop_table_factory\
    import AbstractMasterPopTableFactory

import logging
logger = logging.getLogger(__name__)


class MasterPopTableAsHashTable(AbstractMasterPopTableFactory):

    def finish_master_pop_table(self, spec, master_pop_table_region):
        raise NotImplementedError

    def update_master_population_table(self, spec, block_start_addr, row_index,
                                       key, master_pop_table_region, mask):
        raise NotImplementedError

    def extract_synaptic_matrix_data_location(self, incoming_key,
                                              master_pop_base_mem_address, txrx,
                                              chip_x, chip_y):
        raise NotImplementedError

    def __init__(self):
        AbstractMasterPopTableFactory.__init__(self)
        raise NotImplementedError