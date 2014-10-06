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
    def read_in_master_pop_table(self, x, y, p, transceiver,
                                 master_pop_table_region):
        """

        :param x: x coord for the chip to whcih this master pop table is \
        being read
        :type x: int
        :param y: y coord for the chip to whcih this master pop table is \
        being read
        :type y: int
        :param p: p coord for the processor to whcih this master pop table is \
        being read
        :type p: int
        :param transceiver: the transciever object
        :type spinnman.transciever.Transciever object
        :param master_pop_table_region: the region to which the master pop\
         resides
         :type master_pop_table_region: int


        :return: the master pop table in some form
        """

    @abstractmethod
    def extract_synaptic_matrix_data_location(self, incoming_key):
        """
        :param incoming_key: the source key which the synaptic matrix needs to \
        be mapped to
        :return: a synaptic matrix memory position.
        """

    @abstractmethod
    def update_master_population_table(self, spec, block_start_addr, row_index,
                                       key, master_pop_table_region):
        """ updates a spec with a master pop entry in some form

        :param spec: the spec to write the master pop entry to
        :param block_start_addr: the start address of the master pop table
        :param row_index: the row length index for the row_length table for \
        this entry
        :param key: the key being recieved to be stored in the master pop table,
        :param master_pop_table_region: the region to which the master pop table\
        is being stored
        :return:
        """