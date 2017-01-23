from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod

from spynnaker.pyNN.utilities import utility_calls
from pacman.model.graphs.common.slice import Slice


@add_metaclass(ABCMeta)
class AbstractNeuronModel(object):
    """ Represents a neuron model
    """

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

    def get_sdram_usage_per_neuron_in_bytes(self):
        """ Get the total sdram usage in bytes

        :return: The SDRAM usage
        :rtype: int
        """
        return self.get_n_neural_parameters() * 4

    def get_dtcm_usage_per_neuron_in_bytes(self):
        """ Get the DTCM usage of this neuron model in bytes

        :return: The DTCM usage
        :rtype: int
        """
        return self.get_n_neural_parameters() * 4

    def translate_into_global_params(self, byte_array, position_in_byte_array):
        """

        :param byte_array:
        :param position_in_byte_array:
        :return:
        """
        global_parameters = self.get_global_parameters()

        # as global parameters are not per atom, make a slice of 1 atom
        # for the reader to work correctly
        return utility_calls.translate_parameters(
            global_parameters, byte_array, position_in_byte_array,
            Slice(0, 1))

    def translate_into_parameters(
            self, byte_array, position_in_byte_array, vertex_slice):
        """

        :param byte_array:
        :param position_in_byte_array:
        :param vertex_slice:
        :return:
        """
        neural_parameters = self.get_neural_parameters()
        return utility_calls.translate_parameters(
            neural_parameters, byte_array, position_in_byte_array,
            vertex_slice)

    def global_param_memory_size_in_bytes(self):
        """

        :return:
        """
        global_parameters = self.get_global_parameters()
        return utility_calls.get_parameters_size_in_bytes(global_parameters)

    def neural_param_memory_size_in_bytes(self):
        """

        :return:
        """
        neural_parameters = self.get_neural_parameters()
        return utility_calls.get_parameters_size_in_bytes(neural_parameters)

    @abstractmethod
    def set_global_parameters(self, parameters):
        """ sets any global parameters

        :param parameters: the parameters in a list.
        :return: None
        """

    @abstractmethod
    def set_neural_parameters(self, neural_parameters, vertex_slice):
        """ sets the neural parameters

        :param neural_parameters: the neural parameters in a list
        :param vertex_slice: the slice of atoms for this vertex
        :return: None
        """
