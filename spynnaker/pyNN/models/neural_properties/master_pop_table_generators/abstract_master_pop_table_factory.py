from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
import logging

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractMasterPopTableFactory(object):

    def __init__(self):
        pass

    @abstractmethod
    def initialise_table(self, spec, master_population_table_region):
        """ Perform any tasks to prepare the region for the table

        :param spec: The spec to write to
        :param master_population_table_region: The region within the spec
        """

    @abstractmethod
    def extract_synaptic_matrix_data_location(
            self, incoming_key, master_pop_base_mem_address, txrx, chip_x,
            chip_y):
        """
        :param incoming_key: the source key which the synaptic matrix needs to\
                             be mapped to
        :param incoming_mask: the mask being used to create a key combo
        :return: a synaptic matrix memory position.
        """

    @abstractmethod
    def get_master_population_table_size(self, vertex_slice, in_edges):
        """ Get the size of the master population table in bytes

        :param vertex_slice: The range of atoms in the partitioned vertex
        :param in_edges: The incoming edges to the vertex
        :return: The number of bytes required by the master population table
        """

    @abstractmethod
    def get_allowed_row_length(self, row_length):
        """ Get an allowed row length from an actual row length

        :param row_length: The actual length of a row
        :return: An allowed row length
        """

    @abstractmethod
    def get_next_allowed_address(self, next_address):
        """ Get the next address from which an entry in the table can begin

        :param next_address: The actual next address that can be used
        :return: The next allowed address, aligned as required
        """

    @abstractmethod
    def update_master_population_table(self, spec, block_start_addr,
                                       row_length, key, mask,
                                       master_pop_table_region):
        """ updates a spec with a master pop entry in some form

        :param spec: the spec to write the master pop entry to
        :param block_start_addr: the start address of the master pop table
        :param row_length: the row length of this entry
        :param key: the key being recieved to be stored in the master pop table
        :param mask: the mask being used to create a key combo
        :param master_pop_table_region: the region to which the master pop\
                                        table is being stored
        :return:
        """

    @abstractmethod
    def finish_master_pop_table(self, spec, master_pop_table_region):
        """ completes the master pop table in the spec

        :param spec: the spec to write the master pop entry to
        :param master_pop_table_region: the region in which the\
                                        master pop table is being stored
        :return:
        """
