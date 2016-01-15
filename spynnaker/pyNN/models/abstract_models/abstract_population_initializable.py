from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractPopulationInitializable(object):
    """ Indicates that this object has properties that can be initialised by a\
        PyNN Population
    """

    @abstractmethod
    def initialize(self, variable, value):
        """ Set the initial value of one of the state variables of the neurons\
            in this population.

        """
