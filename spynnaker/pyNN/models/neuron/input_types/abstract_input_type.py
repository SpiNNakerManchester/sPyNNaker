from spinn_utilities.abstract_base import abstractmethod
from spynnaker.pyNN.models.neuron.implementations \
    import AbstractStandardNeuronComponent


class AbstractInputType(AbstractStandardNeuronComponent):
    """ Represents a possible input type for a neuron model (e.g. current)
    """
    __slots__ = ()

    @abstractmethod
    def get_global_weight_scale(self):
        """ Get the global weight scaling value

        :return: The global weight scaling value
        :rtype: float
        """
