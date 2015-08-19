from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractInputType(object):
    """ Represents a possible input type for a neuron model (e.g. current)
    """

    @abstractmethod
    def get_global_weight_scale(self):
        """ Get the global weight scaling value

        :return: The global weight scaling value
        :rtype: float
        """

    @abstractmethod
    def get_n_input_type_parameters(self):
        """ Get the number of parameters for the input type

        :return: The number of parameters
        :rtype: int
        """

    @abstractmethod
    def get_input_type_parameters(self):
        """ Get the parameters for the input type

        :return: An array of parameters
        :rtype: array of\
                :py:class:`spynnaker.pyNN.models.neural_properties.neural_parameter.NeuronParameter`
        """
