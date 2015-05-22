"""
MasterPopTableAsHashTable
"""
from spynnaker.pyNN.models.neural_properties.master_pop_table_generators\
    .abstract_master_pop_table_factory import AbstractMasterPopTableFactory

import logging
logger = logging.getLogger(__name__)


class MasterPopTableAsHashTable(AbstractMasterPopTableFactory):
    """
    MasterPopTableAsHashTable
    """

    def finish_master_pop_table(self, spec, master_pop_table_region):
        """

        :param spec:
        :param master_pop_table_region:
        :return:
        """
        raise NotImplementedError

    def update_master_population_table(self, spec, block_start_addr, row_index,
                                       key, master_pop_table_region, mask):
        """

        :param spec:
        :param block_start_addr:
        :param row_index:
        :param key:
        :param master_pop_table_region:
        :param mask:
        :return:
        """
        raise NotImplementedError

    def extract_synaptic_matrix_data_location(
            self, incoming_key, master_pop_base_mem_address, txrx, chip_x,
            chip_y):
        """

        :param incoming_key:
        :param master_pop_base_mem_address:
        :param txrx:
        :param chip_x:
        :param chip_y:
        :return:
        """
        raise NotImplementedError

    def __init__(self):
        AbstractMasterPopTableFactory.__init__(self)
        raise NotImplementedError

    def initialise_table(self, spec, master_population_table_region):
        """

        :param spec:
        :param master_population_table_region:
        :return:
        """
        raise NotImplementedError

    def get_allowed_row_length(self, row_length):
        """

        :param row_length:
        :return:
        """
        raise NotImplementedError

    def get_master_population_table_size(self, vertex_slice, in_edges):
        """

        :param vertex_slice:
        :param in_edges:
        :return:
        """
        raise NotImplementedError

    def get_next_allowed_address(self, next_address):
        """

        :param next_address:
        :return:
        """
        raise NotImplementedError
