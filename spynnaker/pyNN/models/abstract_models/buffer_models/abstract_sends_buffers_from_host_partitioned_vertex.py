from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
import logging

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractSendsBuffersFromHostPartitionedVertex(object):
    """ Interface to a partitioned vertex that sends buffers of keys to be\
        transmitted at given timestamps in the simulation
    """

    @abstractmethod
    def get_regions(self):
        """ Get the set of regions for which there are keys to be sent

        :return: Iterable of region ids
        :rtype: iterable of int
        """

    @abstractmethod
    def get_region_buffer_size(self, region):
        """ Get the size of the buffer to be used in SDRAM on the machine\
            for the region in bytes

        :param region: The region to get the buffer size of
        :type region: int
        :return: The size of the buffer space in bytes
        :rtype: int
        """

    @abstractmethod
    def is_next_timestamp(self, region):
        """ Determine if there is another timestamp with data to be sent

        :param region: The region to determine if there is more data for
        :type region: int
        :return: True if there is more data, False otherwise
        :rtype: int
        """

    @abstractmethod
    def get_next_timestamp(self, region):
        """ Get the next timestamp at which there are still keys to be sent\
            for the given region

        :param region: The region to get the timestamp for
        :type region: int
        :return: The timestamp of the next available keys
        :rtype: int
        """

    @abstractmethod
    def is_next_key(self, region, timestamp):
        """ Determine if there are still keys to be sent at the given\
            timestamp for the given region

        :param region: The region to determine if there are keys for
        :type region: int
        :param timestamp: The timestamp to determine if there are more keys for
        :type timestamp: int
        :return: True if there are more keys to send for the parameters, False\
                    otherwise
        :rtype: bool
        """

    @abstractmethod
    def get_next_key(self, region):
        """ Get the next key in the given region

        :param region: The region to get the next key from
        :type region: int
        :return: The next key, or None if there are no more keys
        :rtype: int
        """
