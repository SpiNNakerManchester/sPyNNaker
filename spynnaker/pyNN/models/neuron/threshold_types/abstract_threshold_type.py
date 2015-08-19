from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractThresholdType(object):
    """ Represents types of threshold for a neuron (e.g. stochastic)
    """

    @abstractmethod
    def get_n_threshold_parameters(self):
        """ Get the number of threshold parameters

        :return: The number of threshold parameters
        :rtype: int
        """

    @abstractmethod
    def get_threshold_parameters(self):
        """ Get the threshold parameters

        :return: An array of parameters
        :rtype: array of\
                :py:class:`spynnaker.pyNN.models.neural_properties.neural_parameter.NeuronParameter`
        """
