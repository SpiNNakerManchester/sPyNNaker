from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod
from spynnaker.pyNN.utilities import utility_calls


@add_metaclass(ABCMeta)
class AbstractAdditionalInput(object):
    """ Represents a possible additional independent input for a model
    """

    @abstractmethod
    def get_n_parameters(self):
        """ Get the number of parameters for the additional input

        :return: The number of parameters
        :rtype: int
        """

    @abstractmethod
    def get_parameters(self):
        """ Get the parameters for the additional input

        :return: An array of parameters
        :rtype: array of\
                :py:class:`spynnaker.pyNN.models.neural_properties.neural_parameter.NeuronParameter`
        """

    @abstractmethod
    def get_n_cpu_cycles_per_neuron(self):
        """ Get the number of CPU cycles executed by\
            additional_input_get_input_value_as_current and\
            additional_input_has_spiked
        """

    def get_sdram_usage_per_neuron_in_bytes(self):
        """ Get the SDRAM usage of this additional input in bytes

        :return: The SDRAM usage
        :rtype: int
        """
        return self.get_n_parameters() * 4

    def get_dtcm_usage_per_neuron_in_bytes(self):
        """ Get the DTCM usage of this additional input in bytes

        :return: The DTCM usage
        :rtype: int
        """
        return self.get_n_parameters() * 4

    def translate_into_parameters(self, byte_array, position_in_byte_array):
        """

        :param byte_array:
        :param position_in_byte_array:
        :return:
        """
        parameters = self.get_parameters()
        return utility_calls.translate_parameters(
            parameters, byte_array, position_in_byte_array)

    def params_memory_size_in_bytes(self):
        """

        :return:
        """
        parameters = self.get_parameters()
        return utility_calls.get_parameters_size_in_bytes(parameters)
