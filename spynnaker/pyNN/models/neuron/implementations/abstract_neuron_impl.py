from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod,\
    abstractproperty


@add_metaclass(AbstractBase)
class AbstractNeuronImpl(object):
    """ An abstraction of a whole neuron model including all parts
    """

    @abstractproperty
    @staticmethod
    def default_parameters():
        """ The default parameters of the model

        :rtype: dict of str->value
        """

    @abstractproperty
    def model_name(self):
        """ The name of the model

        :rtype: str
        """

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
    def get_global_weight_scale(self):
        """ Get the weight scaling required by this model

        :rtype: int
        """

    @abstractmethod
    def get_n_synapse_types(self):
        """ Get the number of synapse types supported by the model

        :rtype: int
        """

    @abstractmethod
    def get_synapse_id_by_target(self, target):
        """ Get the id of a synapse given the name

        :param target: The name of the synapse
        :type target: str
        :rtype: int
        """

    @abstractmethod
    def get_synapse_targets(self):
        """ Get the target names of the synapse type

        :rtype: array of str
        """

    @abstractmethod
    def get_recordable_variables(self):
        """ Get the names of the variables that can be recorded in this model

        :rtype: list of str
        """

    def get_recordable_units(self, variable):
        """ Get the units of the given variable that can be recorded

        :param variable: The name of the variable
        :type variable: str
        """

    @abstractmethod
    def is_recordable(self, variable):
        """ Determine if the given variable can be recorded

        :param variable: The name of the variable being requested
        :type variable: str
        :rtype: bool
        """

    @abstractmethod
    def get_recordable_variable_index(self, variable):
        """ Get the index of the variable in the list of variables that can be\
            recorded

        :param variable: The name of the variable
        :type variable: str
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
        """

    @abstractmethod
    def get_units(self, variable):
        """ Get the units of the given variable

        :param variable: The name of the variable
        :type variable: str
        """

    @abstractproperty
    def is_conductance_based(self):
        """ Determine if the model uses conductance

        :rtype: bool
        """
