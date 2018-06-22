from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod

_BYTES_PER_PARAMETER = 4


@add_metaclass(AbstractBase)
class AbstractStandardNeuronComponent(object):
    """ Represents a component of a standard neural model
    """

    __slots__ = ()

    @abstractmethod
    def get_n_cpu_cycles(self, n_neurons):
        """ Get the number of CPU cycles required to update the state

        :param n_neurons: The number of neurons to get the cycles for
        :type n_neurons: int
        :rtype: int
        """

    @abstractmethod
    def get_dtcm_usage_in_bytes(self, n_neurons):
        """ Get the DTCM memory usage required

        :param n_neurons: The number of neurons to get the usage for
        :type n_neurons: int
        :rtype: int
        """

    @abstractmethod
    def get_sdram_usage_in_bytes(self, n_neurons):
        """ Get the SDRAM memory usage required

        :param n_neurons: The number of neurons to get the usage for
        :type n_neurons: int
        :rtype: int
        """

    @abstractmethod
    def add_parameters(self, parameters):
        """ Add the initial values of the parameters to the parameter holder

        :param parameters: A holder of the parameters
        :type parameters:\
            :py:class:`spinn_utilities.ranged.range_dictionary.RangeDictionary`
        """

    @abstractmethod
    def add_state_variables(self, state_variables):
        """ Add the initial values of the state variables to the state\
            variables holder

        :param state_variables: A holder of the state variables
        :type state_variables:\
            :py:class:`spinn_utilities.ranged.range_dictionary.RangeDictionary`
        """

    @abstractmethod
    def get_data(self, parameters, state_variables, vertex_slice):
        """ Get the data to be written to the machine for this model

        :param parameters: The holder of the parameters
        :type parameters:\
            :py:class:`spinn_utilities.ranged.range_dictionary.RangeDictionary`
        :param state_variables: The holder of the state variables
        :type state_variables:\
            :py:class:`spinn_utilities.ranged.range_dictionary.RangeDictionary`
        :param vertex_slice: The slice of the vertex to generate parameters for
        :rtype: numpy array of uint32
        """

    @abstractmethod
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):
        """ Read the parameters and state variables of the model from the\
            given data

        :param data: The data to be read
        :param offset: The offset where the data should be read from
        :param vertex_slice: The slice of the vertex to read parameters for
        :param parameters: The holder of the parameters to update
        :type parameters:\
            :py:class:`spinn_utilities.ranged.range_dictionary.RangeDictionary`
        :param state_variables: The holder of the state variables to update
        :type state_variables:\
            :py:class:`spinn_utilities.ranged.range_dictionary.RangeDictionary`
        :return: The offset after reading the data
        """

    @abstractmethod
    def has_variable(self, variable):
        """ Determine if this component has a variable by the given name

        :param variable: The name of the variable
        :type variable: str
        :rtype: bool
        """

    @abstractmethod
    def get_units(self, variable):
        """ Get the units of the given variable

        :param variable: The name of the variable
        :type variable: str
        """
