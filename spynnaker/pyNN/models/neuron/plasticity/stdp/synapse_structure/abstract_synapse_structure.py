from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractSynapseStructure(object):

    __slots__ = ()

    @abstractmethod
    def get_n_bytes_per_connection(self):
        """ Get the number of bytes for each connection
        """

    @abstractmethod
    def get_synaptic_data(self, connections):
        """ Get the plastic synaptic data for this connection
        """

    @abstractmethod
    def read_synaptic_data(self, fp_size, pp_data):
        """ Read the plastic synaptic data for this connection from\
            the data
        """
