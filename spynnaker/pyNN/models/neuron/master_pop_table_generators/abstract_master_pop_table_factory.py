
# general imports
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
    def extract_synaptic_matrix_data_location(
            self, incoming_key, master_pop_base_mem_address, txrx, chip_x,
            chip_y):
        """
        :param incoming_key: the source key which the synaptic matrix needs to\
                    be mapped to
        :param master_pop_base_mem_address: the base address of the master pop
        :param txrx: the transceiver object from spinnman
        :param chip_y: the y coordinate of the chip of this master pop
        :param chip_x: the x coordinate of the chip of this master pop
        :type incoming_key: int
        :type master_pop_base_mem_address: int
        :type chip_y: int
        :type chip_x: int
        :type txrx: spinnman.transciever.Transciever object
        :return: a synaptic matrix memory position.
        """

    @abstractmethod
    def update_master_population_table(
            self, spec, block_start_addr, row_length, keys_and_masks,
            master_pop_table_region, is_single=False):
        """ updates a spec with a master pop entry in some form

        :param spec: the spec to write the master pop entry to
        :param block_start_addr: the start address of the row in the region
        :param row_length: the row length of this entry
        :param keys_and_masks: list of key_and_mask objects containing the\
                    keys and masks for a given edge that will require being\
                    received to be stored in the master pop table
        :type keys_and_masks: list of\
                    :py:class:`pacman.model.routing_info.key_and_mask.KeyAndMask`
        :param master_pop_table_region: the region to which the master pop\
                    table is being stored
        :param is_single True if this is a single synapse, False otherwise
        :return:
        """

    @abstractmethod
    def finish_master_pop_table(self, spec, master_pop_table_region):
        """ completes the master pop table in the spec

        :param spec: the spec to write the master pop entry to
        :param master_pop_table_region: the region to which the master pop\
                    table is being stored
        :return:
        """

    @abstractmethod
    def get_edge_constraints(self):
        """ Gets the constraints for this table on edges coming in to a vertex
            that uses

        :return: a list of constraints
        :rtype: list of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :raise None: this method does not raise any known exceptions
        """

    @abstractmethod
    def get_master_population_table_size(self, vertex_slice, in_edges):
        """ Get the size of the master population table in SDRAM
        """
