from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
import logging

#spinnman imports
from spinnman import exceptions as spinnman_exceptions
from spynnaker.pyNN import exceptions

import struct

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
    def extract_synaptic_matrix_data_location(
            self, incoming_key, master_pop_base_mem_address):
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