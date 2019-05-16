from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractSynapseStructure(object):

    __slots__ = ()

    @abstractmethod
    def get_n_half_words_per_connection(self):
        """ Get the number of bytes for each connection
        """

    @abstractmethod
    def get_weight_half_word(self):
        """ The index of the half-word where the weight should be written
        """
