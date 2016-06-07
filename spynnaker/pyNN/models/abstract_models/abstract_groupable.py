from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractGroupable(object):

    def __init__(self):
        pass

    @abstractmethod
    def set_mapping(self, vertex_mapping):
        """
        sets the variable used to hold the mappings between atoms
        and populations
        :param vertex_mapping: the vertex mapping dictionary
        :return:
        """

    @abstractmethod
    def vertex_to_pop_mapping(self):
        """
        returns the variable used to hold the mapping between atoms and
        populations.
        :return: the vertex mapping dictionary
        """