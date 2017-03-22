from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractWeightUpdatable(object):
    """ An object the weight of which can be updated
    """

    __slots__ = ()

    @abstractmethod
    def update_weight(self, graph_mapper):
        """ Update the weight
        """
