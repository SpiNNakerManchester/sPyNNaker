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

    @abstractmethod
    def get_n_cpu_cycles_per_neuron(self):
        """ Get the number of CPU cycles executed by\
            threshold_type_is_above_threshold, per neuron

        :return: The number of CPU cycles
        :rtype: int
        """

    def get_sdram_usage_per_neuron_in_bytes(self):
        """ Get the amount of SDRAM used per neuron in bytes

        :return: The number of bytes
        :rtype: int
        """
        return self.get_n_threshold_parameters() * 4

    def get_dtcm_usage_per_neuron_in_bytes(self):
        """ Get the amount of DTCM used per neuron in bytes

        :return: The number of bytes
        :rtype: int
        """
        return self.get_n_threshold_parameters() * 4
