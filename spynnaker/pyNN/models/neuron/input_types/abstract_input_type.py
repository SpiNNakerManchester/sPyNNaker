from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod
from spynnaker.pyNN.utilities import utility_calls


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

    @abstractmethod
    def get_n_cpu_cycles_per_neuron(self, n_synapse_types):
        """ Get the number of CPU cycles executed by\
            input_type_get_input_value once per synapse, \
            input_type_convert_excitatory_input_to_current and
            input_type_convert_inhibitory_input_to_current, per neuron
        """

    def get_sdram_usage_per_neuron_in_bytes(self):
        """ Get the SDRAM usage of this input type in bytes

        :return: The SDRAM usage
        :rtype: int
        """
        return self.get_n_input_type_parameters() * 4

    def get_dtcm_usage_per_neuron_in_bytes(self):
        """ Get the DTCM usage of this input type in bytes

        :return: The DTCM usage
        :rtype: int
        """
        return self.get_n_input_type_parameters() * 4

    def translate_into_parameters(
            self, byte_array, position_in_byte_array, vertex_slice):
        """

        :param byte_array:
        :param position_in_byte_array:
        :param vertex_slice:
        :return:
        """
        parameters = self.get_input_type_parameters()
        return utility_calls.translate_parameters(
            parameters, byte_array, position_in_byte_array, vertex_slice)

    def params_memory_size_in_bytes(self):
        """

        :return:
        """
        parameters = self.get_input_type_parameters()
        return utility_calls.get_parameters_size_in_bytes(parameters)
