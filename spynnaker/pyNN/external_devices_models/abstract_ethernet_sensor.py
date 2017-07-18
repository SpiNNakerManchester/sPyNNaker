from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.abstract_base import abstractmethod


@add_metaclass(AbstractBase)
class AbstractEthernetSensor(object):

    @abstractmethod
    def get_n_neurons(self):
        """ Get the number of neurons that will be sent out by the device
        """

    @abstractmethod
    def get_injector_parameters(self):
        """ Get the parameters of the Spike Injector to use with this device
        """

    @abstractmethod
    def get_injector_label(self):
        """ Get the label to give to the Spike Injector
        """

    @abstractmethod
    def get_translator(self):
        """ Get a translator of multicast commands to Ethernet commands
        """

    @abstractmethod
    def get_database_connection(self):
        """ Get a Database Connection instance that this device uses\
            to inject packets
        """
