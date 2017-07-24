from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.abstract_base import abstractmethod


@add_metaclass(AbstractBase)
class AbstractEthernetController(object):
    """ A controller that can send multicast packets which can be received\
        over Ethernet and translated to control an external device
    """

    @abstractmethod
    def get_message_translator(self):
        """ Get the translator of messages

        :rtype:\
            :py:class:`spynnaker_external_devices_plugin.pyNN.external_devices_models.abstract_ethernet_translator.AbstractEthernetTranslator`
        """

    @abstractmethod
    def get_external_devices(self):
        """ Get the external devices that are to be controlled by the\
            controller
        """

    @abstractmethod
    def get_outgoing_partition_ids(self):
        """ Get the partition ids of messages coming out of the controller

        :rtype: list of str
        """
