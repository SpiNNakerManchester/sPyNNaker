from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractWeightUpdatable(object):
    """ An object the weight of which can be updated
    """

    @abstractmethod
    def update_weight(self, graph_mapper):
        """ Update the weight
        """
