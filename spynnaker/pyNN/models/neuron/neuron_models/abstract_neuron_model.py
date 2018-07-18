from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod

_BYTES_PER_PARAMETER = 4


@add_metaclass(AbstractBase)
class AbstractNeuronModel(object):
    """ Represents a neuron model.

    ..note::
        Override :py:meth:`set_neural_parameters` if there are changing\
        variables in the neural parameters.

    .. note::
        Override :py:meth:`set_global_parameters` if there are changing\
        variables in the global parameters.
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
        :rtype: \
            list(:py:class:`spynnaker.pyNN.models.neural_properties.NeuronParameter`)
        """

    @abstractmethod
    def get_neural_parameter_types(self):
        """ Get the types of the neural parameters

        :return: A list of DataType objects, in the order of the parameters
        :rtype: list(:py:class:`data_specification.enums.DataType`)
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
        :rtype: list(:py:class:`data_specification.enums.DataType`)
        """

    @abstractmethod
    def get_global_parameters(self):
        """ Get the global parameters

        :return: an array of parameters
        :rtype: \
            list(:py:class:`spynnaker.pyNN.models.neural_properties.NeuronParameter`)
        """

    @abstractmethod
    def get_n_cpu_cycles_per_neuron(self):
        """ Get the total number of CPU cycles executed by \
            ``neuron_model_state_update`` and ``neuron_model_has_spiked``,\
            per neuron

        :return: The number of CPU cycles executed
        :rtype: int
        """

    def get_sdram_usage_per_neuron_in_bytes(self):
        """ Get the total SDRAM usage in bytes

        :return: The SDRAM usage
        :rtype: int
        """
        return self.get_n_neural_parameters() * _BYTES_PER_PARAMETER

    def get_dtcm_usage_per_neuron_in_bytes(self):
        """ Get the DTCM usage of this neuron model

        :return: The DTCM usage, in bytes
        :rtype: int
        """
        return self.get_n_neural_parameters() * _BYTES_PER_PARAMETER

    def get_sdram_usage_for_global_parameters_in_bytes(self):
        """ Get the SDRAM usage of the global parameters

        :return: The SDRAM usage, in bytes
        :rtype: int
        """
        return self.get_n_global_parameters() * _BYTES_PER_PARAMETER

    def set_global_parameters(self, parameters):
        """ Sets any global parameters.

        :param parameters:\
            the parameter values as a list, ordered the same as\
            :py:meth:`get_global_parameters`.
        """

    def set_neural_parameters(self, neural_parameters, vertex_slice):
        """ Sets any neural parameters.

        :param neural_parameters:\
            the parameter values in a list of numpy arrays, ordered the same\
            as :py:meth:`get_neural_parameters`.
        :param vertex_slice: The neurons to which the parameters apply
        """
