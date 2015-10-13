from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSynapseStructure(object):

    @abstractmethod
    def get_n_words_in_row(self, n_connections):
        """ Get the size of the row given the number of connections in the row
        """

    @abstractmethod
    def write_synaptic_block(self, spec, synaptic_block):
        """ Write a synaptic block to the spec
        """
