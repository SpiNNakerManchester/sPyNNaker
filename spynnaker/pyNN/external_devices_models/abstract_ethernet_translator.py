from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractEthernetTranslator(object):
    """ A module that can translate packets received over Ethernet into\
        control of an external device
    """

    __slots__ = []

    @abstractmethod
    def translate_control_packet(self, multicast_packet):
        """ Translate a multicast packet received over Ethernet and send\
            appropriate messages to the external device

        :param multicast_packet: A received multicast packet
        :type multicast_packet:\
            :py:class:`spinnman.messages.eieio.data_messages.AbstractEIEIODataElement`
        """
