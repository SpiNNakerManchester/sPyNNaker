from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod

from spynnaker.pyNN.utilities import utility_calls


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
    def get_neural_parameter_types(self):
        """ Get the types of the neural parameters

        :return: A list of DataType objects, in the order of the parameters
        :rtype: list of :py:class:`data_specification.enums.data_type.DataType`
        """

    @abstractmethod
    def get_n_global_parameters(self):
        """ Get the number of global parameters

        :return: The number of global parameters
        :rtype: int
        """

    @abstractmethod
    def get_global_parameter_types(self):
        """ Get the types of the global parameters

        :return: A list of DataType objects, in the order of the parameters
        :rtype: list of :py:class:`data_specification.enums.data_type.DataType`
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

    def get_sdram_usage_for_global_parameters_in_bytes(self):
        """ Get the SDRAM usage of the global parameters in bytes

        :return: The SDRAM usage
        :rtype: int
        """
        global_parameters = self.get_global_parameters()
        return utility_calls.get_parameters_size_in_bytes(global_parameters)

    def set_global_parameters(self, parameters):
        """ Sets any global parameters.  Override if there are changing\
            variables in the global parameters

        :param parameters:\
            the parameter values as a list, ordered the same as\
            get_global_parameters
        """
        pass

    def set_neural_parameters(self, neural_parameters, vertex_slice):
        """ Sets any neural parameters.  Override if there are changing\
            variables in the neural parameters

        :param neural_parameters:\
            the parameter values in a list of numpy arrays, ordered the same\
            as get_neural_parameters
        :param vertex_slice: The neurons to which the parameters apply
        """
        pass
