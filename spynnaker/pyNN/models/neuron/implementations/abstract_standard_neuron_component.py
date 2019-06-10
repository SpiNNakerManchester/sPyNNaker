from six import with_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from .struct import Struct
from .ranged_dict_vertex_slice import RangedDictVertexSlice


class AbstractStandardNeuronComponent(with_metaclass(AbstractBase, object)):
    """ Represents a component of a standard neural model
    """

    __slots__ = ["__struct"]

    def __init__(self, data_types):
        """
        :param data_types:\
            A list of data types in the component structure, in the order that\
            they appear
        """
        self.__struct = Struct(data_types)

    @property
    def struct(self):
        """ The structure of the component

        :rtype:\
            :py:class:'spynnaker.pyNN.models.neuron.implementations.struct.Struct'
        """
        return self.__struct

    @abstractmethod
    def get_n_cpu_cycles(self, n_neurons):
        """ Get the number of CPU cycles required to update the state

        :param n_neurons: The number of neurons to get the cycles for
        :type n_neurons: int
        :rtype: int
        """

    def get_dtcm_usage_in_bytes(self, n_neurons):
        """ Get the DTCM memory usage required

        :param n_neurons: The number of neurons to get the usage for
        :type n_neurons: int
        :rtype: int
        """
        return self.struct.get_size_in_whole_words(n_neurons) * 4

    def get_sdram_usage_in_bytes(self, n_neurons):
        """ Get the SDRAM memory usage required

        :param n_neurons: The number of neurons to get the usage for
        :type n_neurons: int
        :rtype: int
        """
        return self.struct.get_size_in_whole_words(n_neurons) * 4

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
    def get_values(self, parameters, state_variables, vertex_slice):
        """ Get the values to be written to the machine for this model

        :param parameters: The holder of the parameters
        :type parameters:\
            :py:class:`spinn_utilities.ranged.range_dictionary.RangeDictionary`
        :param state_variables: The holder of the state variables
        :type state_variables:\
            :py:class:`spinn_utilities.ranged.range_dictionary.RangeDictionary`
        :param vertex_slice: The slice of variables being retrieved
        :return: A list with the same length as self.struct.field_types
        :rtype: A list of (single value or list of values or RangedList)
        """

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
        values = self.get_values(parameters, state_variables, vertex_slice)
        return self.struct.get_data(
            values, vertex_slice.lo_atom, vertex_slice.n_atoms)

    @abstractmethod
    def update_values(self, values, parameters, state_variables):
        """ Update the parameters and state variables with the given struct\
            values that have been read from the machine

        :param values:\
            The values read from the machine, one for each struct element
        :type value: A list of lists
        :param parameters: The holder of the parameters to update
        :param state_variables: The holder of the state variables to update
        """

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
        values = self.struct.read_data(data, offset, vertex_slice.n_atoms)
        new_offset = offset + (self.struct.get_size_in_whole_words(
            vertex_slice.n_atoms) * 4)
        params = RangedDictVertexSlice(parameters, vertex_slice)
        variables = RangedDictVertexSlice(state_variables, vertex_slice)
        self.update_values(values, params, variables)
        return new_offset

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
