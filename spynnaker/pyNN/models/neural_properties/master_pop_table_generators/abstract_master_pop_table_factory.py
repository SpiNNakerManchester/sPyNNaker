
from spinn_front_end_common.utilities import helpful_functions

# dsg imports
from data_specification import utility_calls as dsg_utility

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
        :param txrx: the transciever object from spinnman
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
            master_pop_table_region):
        """ updates a spec with a master pop entry in some form

        :param spec: the spec to write the master pop entry to
        :param block_start_addr: the start address of the master pop table
        :param row_length: the row length of this entry
        :param keys_and_masks: list of key_and_mask objects containing the\
                    keys and masks for a given edge that will require being\
                    received to be stored in the master pop table
        :type keys_and_masks: list of\
                    :py:class:`pacman.model.routing_info.key_and_mask.KeyAndMask`
        :param master_pop_table_region: the region to which the master pop\
                    table is being stored
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

    def locate_master_pop_table_base_address(self, x, y, p, transceiver,
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
        :type transceiver: spinnman.transciever.Transciever object
        :param master_pop_table_region: the region to which the master pop\
         resides
         :type master_pop_table_region: int


        :return: the master pop table in some form
        """
        # Get the App Data base address for the core
        # (location where this cores memory starts in
        # sdram and region table)
        app_data_base_address = \
            transceiver.get_cpu_information_from_core(x, y, p).user[0]

        # Get the memory address of the master pop table region
        master_pop_region = master_pop_table_region

        master_region_base_address_address = \
            dsg_utility.get_region_base_address_offset(
                app_data_base_address, master_pop_region)

        master_region_base_address_offset = helpful_functions.read_data(
            x, y, master_region_base_address_address, 4, "<I", transceiver)

        master_region_base_address =\
            master_region_base_address_offset + app_data_base_address

        return master_region_base_address, app_data_base_address

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
