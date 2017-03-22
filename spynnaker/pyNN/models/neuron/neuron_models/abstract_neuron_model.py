from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractNeuronModel(object):
    """ Represents a neuron model
    """

    __slots__ = ()

    @abstractmethod
    def get_n_neural_parameters(self):
        """ Get the number of neural parameters

        :return: The number of parameters
        :rtype: int
        """

    @abstractmethod
    def get_neural_parameters(self):
        """ Get the neural parameters

        :return: an array of parameters
        :rtype: array of\
                :py:class:`spynnaker.pyNN.models.neural_properties.neural_parameter.NeuronParameter`
        """

    @abstractmethod
    def get_n_global_parameters(self):
        """ Get the number of global parameters

        :return: The number of global parameters
        :rtype: int
        """

    @abstractmethod
    def get_global_parameters(self):
        """ Get the global parameters

        :return: an array of parameters
        :rtype: array of\
                :py:class:`spynnaker.pyNN.models.neural_properties.neural_parameter.NeuronParameter`
        """

    @abstractmethod
    def get_n_cpu_cycles_per_neuron(self):
        """ Get the total number of CPU cycles executed by \
            neuron_model_state_update and neuron_model_has_spiked, per neuron

        :return: The number of CPU cycles executed
        :rtype: int
        """

    def get_sdram_usage_in_bytes(self, n_neurons):
        """ Get the total sdram usage in bytes

        :return: The SDRAM usage
        :rtype: int
        """
        return ((self.get_n_neural_parameters() * 4 * n_neurons) +
                self.get_n_global_parameters() * 4)

    def get_dtcm_usage_per_neuron_in_bytes(self):
        """ Get the DTCM usage of this neuron model in bytes

        :return: The DTCM usage
        :rtype: int
        """
        return self.get_n_neural_parameters() * 4
