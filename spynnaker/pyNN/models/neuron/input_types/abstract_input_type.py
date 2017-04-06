from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractInputType(object):
    """ Represents a possible input type for a neuron model (e.g. current)
    """
    __slots__ = ()

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
    def get_input_type_parameter_types(self):
        """ Get the types of the input type parameters

        :return: A list of DataType objects, in the order of the parameters
        :rtype: list of :py:class:`data_specification.enums.data_type.DataType`
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

    def set_input_type_parameters(self, parameters, vertex_slice):
        """ Sets the input type parameters.  Override if there are any\
            variables that change.

        :param parameters:\
            the parameter values in a list of numpy arrays, ordered the same\
            as get_input_type_parameters
        :param vertex_slice: The neurons to which the parameters apply
        """
        pass
