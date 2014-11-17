from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
import logging

#spinnman imports
from spinnman import exceptions as spinnman_exceptions
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities.utility_calls \
    import get_region_base_address_offset

import struct

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
        :param incoming_key: the source key which the synaptic matrix needs to \
        be mapped to
        :param incoming_mask: the mask being used to create a key combo
        :return: a synaptic matrix memory position.
        """

    @abstractmethod
    def update_master_population_table(self, spec, block_start_addr, row_index,
                                       key, master_pop_table_region, mask):
        """ updates a spec with a master pop entry in some form

        :param spec: the spec to write the master pop entry to
        :param block_start_addr: the start address of the master pop table
        :param row_index: the row length index for the row_length table for \
        this entry
        :param key: the key being recieved to be stored in the master pop table,
        :param master_pop_table_region: the region to which the master pop table\
        is being stored
        :param mask: the mask being used to create a key combo
        :return:
        """

    @abstractmethod
    def finish_master_pop_table(self, spec, master_pop_table_region):
        """ completes the master pop table in the spec

        :param spec: the spec to write the master pop entry to
        :param master_pop_table_region: the region to which the master pop table\
        is being stored
        :return:
        """

    @staticmethod
    def read_and_convert(x, y, address, length, data_format, transceiver):
        """
        tries to read and convert a piece of memory. If it fails, it tries again
        up to for 4 times, and then if still fails, throws an error.
        """
        try:
            #turn byte array into str for unpack to work.
            data = \
                str(list(transceiver.read_memory(
                    x, y, address, length))[0])
            result = struct.unpack(data_format, data)[0]
            return result
        except spinnman_exceptions.SpinnmanIOException:
            raise exceptions.SynapticBlockReadException(
                "failed to read and translate a piece of memory due to a "
                "spinnman io exception.")
        except spinnman_exceptions.SpinnmanInvalidPacketException:
            raise exceptions.SynapticBlockReadException(
                "failed to read and translate a piece of memory due to a "
                "invalid packet exception in spinnman.")
        except spinnman_exceptions.SpinnmanInvalidParameterException:
            raise exceptions.SynapticBlockReadException(
                "failed to read and translate a piece of memory due to a "
                "invalid parameter exception in spinnman.")
        except spinnman_exceptions.SpinnmanUnexpectedResponseCodeException:
            raise exceptions.SynapticBlockReadException(
                "failed to read and translate a piece of memory due to a "
                "unexpected response code exception in spinnman.")

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
        :type spinnman.transciever.Transciever object
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