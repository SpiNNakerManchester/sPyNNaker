from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSendsBuffersFromHostPartitionableVertex(object):
    """ Interface for partitionable vertices that want to control the\
        buffers to be sent for their partitioned vertices.  This might be\
        done to save memory for example, as the data can be loaded dynamically\
        as requested
    """

    @abstractmethod
    def get_regions(self):
        """ Get the set of regions for which there are keys to be sent

        :return: Iterable of region ids
        :rtype: iterable of int
        """

    @abstractmethod
    def get_region_buffer_size(self, region, vertex_slice):
        """ Get the size of the buffer to be used in SDRAM on the machine\
            for the region in bytes

        :param region: The region to get the buffer size of
        :type region: int
        :param vertex_slice: The slice to get the buffer size of
        :type: vertex_slice: :py:class:`pacman.model.graph_mapper.slice.Slice`
        :return: The size of the buffer space in bytes
        :rtype: int
        """

    @abstractmethod
    def is_next_timestamp(self, region, vertex_slice):
        """ Determine if there is another timestamp with data to be sent

        :param region: The region to determine if there is more data for
        :type region: int
        :param vertex_slice: The slice to determine if there is more data for
        :type: vertex_slice: :py:class:`pacman.model.graph_mapper.slice.Slice`
        :return: True if there is more data, False otherwise
        :rtype: int
        """

    @abstractmethod
    def get_next_timestamp(self, region, vertex_slice):
        """ Get the next timestamp at which there are still keys to be sent\
            for the given region

        :param region: The region to get the timestamp for
        :type region: int
        :param vertex_slice: The vertex slice to get the keys for
        :type: vertex_slice: :py:class:`pacman.model.graph_mapper.slice.Slice`
        :return: The timestamp of the next available keys
        :rtype: int
        """

    @abstractmethod
    def is_next_key(self, region, vertex_slice, timestamp):
        """ Determine if there are still keys to be sent at the given\
            timestamp for the given region

        :param region: The region to determine if there are keys for
        :type region: int
        :param vertex_slice: The vertex slice to determine if there are keys\
                    for
        :type: vertex_slice: :py:class:`pacman.model.graph_mapper.slice.Slice`
        :param timestamp: The timestamp to determine if there are more keys for
        :type timestamp: int
        :return: True if there are more keys to send for the parameters, False\
                    otherwise
        :rtype: bool
        """

    @abstractmethod
    def get_next_key(self, region, vertex_slice):
        """ Get the next key in the given region for the given slice

        :param region: The region to get the next key from
        :type region: int
        :param vertex_slice: The vertex slice to key the next key from
        :type: vertex_slice: :py:class:`pacman.model.graph_mapper.slice.Slice`
        :return: The next key, or None if there are no more keys
        :rtype: int
        """
