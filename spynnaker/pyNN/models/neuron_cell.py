from spinn_front_end_common.abstract_models.\
    abstract_changable_after_run import \
    AbstractChangableAfterRun
from spinn_front_end_common.utilities import exceptions


class NeuronCell(object):
    """
    NeuronCell: the object that stores all data about a cell.
    """

    def __init__(self, default_parameters, state_variables,
                 original_class, structure):

        self._original_class = original_class

        # standard parameters
        self._params = dict(default_parameters)

        # state variables
        self._state_variables = dict()
        for state_variable in state_variables:
            self._state_variables[state_variable] = None

        # recording data items
        # spikes
        self._record_spikes = False
        self._record_spike_to_file_flag = None

        # gsyn
        self._record_gsyn = False
        self._record_gsyn_to_file_flag = None

        # v
        self._record_v = False
        self._record_v_to_file_flag = None

        # space related structures
        self._structure = structure
        self._positions = None

        # synaptic link
        self._synapse_dynamics = None

        # change marker (only set to a value if the vertex supports it)
        if issubclass(self._original_class, AbstractChangableAfterRun):
            self._has_change_that_requires_mapping = True
        else:
            self._has_change_that_requires_mapping = None

    @property
    def state_variables(self):
        """
        returns the state variables of the cell.
        :return: the state variable dictionary
        """
        return self._state_variables

    def initialize(self, key, new_value):
        """
        sets state variables as needed
        :param key: the state variable name needed to be set
        :param new_value: the value to set the state value to
        :return:None
        """
        if key in self._state_variables:
            self._has_change_that_requires_mapping = True
            self._state_variables[key] = new_value
        else:
            raise exceptions.ConfigurationException(
                "Trying to set a parameter which does not exist")

    @property
    def structure(self):
        """
        returns the structure object used by pynn pops
        :return: structure object
        """
        return self._structure

    @structure.setter
    def structure(self, new_structure):
        """
        setter for the structure object
        :param new_structure: the new structure object
        :return: None
        """
        self._structure = new_structure

    @property
    def position(self):
        """
        returns the positions object
        :return: the positions object
        """
        return self._positions

    @position.setter
    def position(self, new_value):
        """
        setter for the position object
        :param new_value: the new position object
        :return: None
        """
        self._positions = new_value

    @property
    def has_change_that_requires_mapping(self):
        """
        get changed require mapping flag
        :return:
        """
        return self._has_change_that_requires_mapping

    def mark_no_changes(self):
        """
        reset change flag
        :return:
        """
        self._has_change_that_requires_mapping = False

    @property
    def record_spikes(self):
        """
        bool flag for record spikes
        :return:
        """
        return self._record_spikes

    @record_spikes.setter
    def record_spikes(self, new_value):
        """
        setter for record flag
        :param new_value: new value for record flag
        :return:
        """
        if new_value != self._record_spikes:
            self._record_spikes = new_value
            self._has_change_that_requires_mapping = True

    @property
    def record_spikes_to_file_flag(self):
        """
        getter for record spikes to file flag
        :return: bool flag
        """
        return self._record_spike_to_file_flag

    @record_spikes_to_file_flag.setter
    def record_spikes_to_file_flag(self, to_file_flag):
        """
        record spikes to file flag setter.
        :param to_file_flag: bool flag
        :return: None
        """
        if isinstance(to_file_flag, bool):
            self._record_spike_to_file_flag = to_file_flag
        else:
            raise exceptions.ConfigurationException(
                "Only booleans are allowed to the to_file_flag. "
                "If you want to use a file_path, we recommend you use pop"
                " views and assemblies to filter between file paths.")

    @property
    def record_v(self):
        """
        getter for the record v flag
        :return: boolean flag
        """
        return self._record_v

    @record_v.setter
    def record_v(self, new_value):
        """
        setter for the record v bool flag
        :param new_value: new value for the flag
        :return: None
        """
        if new_value != self._record_v:
            self._record_v = new_value
            self._has_change_that_requires_mapping = True

    @property
    def record_v_to_file_flag(self):
        """
        getter for record v to_file_flag
        :return: file path
        """
        return self._record_v_to_file_flag

    @record_v_to_file_flag.setter
    def record_v_to_file_flag(self, to_file_flag):
        """
        record v file path setter.
        :param to_file_flag: the new file path for the record v
        :return: None
        """
        if isinstance(to_file_flag, bool):
            self._record_v_to_file_flag = to_file_flag
        else:
            raise exceptions.ConfigurationException(
                "Only booleans are allowed to the to_file_flag. "
                "If you want to use a file_path, we recommend you use pop"
                " views and assemblies to filter between file paths.")

    @property
    def record_gsyn(self):
        """
        property for record gsyn bool flag
        :return: the boolean flag for recording gsyn
        """
        return self._record_gsyn

    @record_gsyn.setter
    def record_gsyn(self, new_value):
        """
        setter for record gsyn bool flag
        :param new_value: the new value for recording gsyn boolean flag
        :return: None
        """
        if new_value != self._record_gsyn:
            self._record_gsyn = new_value
            self._has_change_that_requires_mapping = True

    @property
    def record_gsyn_to_file_flag(self):
        """
        getter for record gsyn to file flag
        :return: file path
        """
        return self._record_gsyn_to_file_flag

    @record_gsyn_to_file_flag.setter
    def record_gsyn_to_file_flag(self, to_file_flag):
        """
        record gsyn  to file flag setter.
        :param to_file_flag: the new flag for the record gsyn to file
        :return: None
        """
        if isinstance(to_file_flag, bool):
            self._record_gsyn_to_file_flag = "gsyn"
        else:
            raise exceptions.ConfigurationException(
                "Only booleans are allowed to the to_file_flag. "
                "If you want to use a file_path, we recommend you use pop"
                " views and assemblies to filter between file paths.")

    def get(self, key):
        """
        getter for any neuron parameter
        :param key: the name of the param to get
        :return: the parameter value for this neuron cell
        """
        return self._params[key]

    def set_param(self, key, new_value):
        """
        setter for neuron cell params.
        :param key: the name of the param
        :param new_value: the new value of the param
        :return: None
        """
        if key in self._params:
            self._has_change_that_requires_mapping = True
            self._params[key] = new_value
        else:
            raise exceptions.ConfigurationException(
                "Trying to set a parameter which does not exist")

    @property
    def synapse_dynamics(self):
        """
        synapse dynamics getter
        :return:the synapse dynamics for this cell
        """
        return self._synapse_dynamics

    @synapse_dynamics.setter
    def synapse_dynamics(self, new_value):
        """
        setter for the synapse dynamics, checks that the new dynamics
        matches currently added ones if one such exists.
        :param new_value: new synapse_dynamics
        :return: None
        """
        if self._synapse_dynamics is None:
            self._synapse_dynamics = new_value
        elif not self._synapse_dynamics.is_same_as(new_value):
            raise exceptions.ConfigurationException(
                "Currently only one type of STDP can be supported per cell.")
        self._has_change_that_requires_mapping = True

    def __repr__(self):
        output = ""
        for key in self._params:
            output += "{}:{},".format(key, self._params[key])
        output += "record_spikes:{}".format(self._record_spikes)
        output += "record_v:{}".format(self._record_v)
        output += "record_gsyn:{}".format(self._record_gsyn)
        output += "synapse_dynamics:{}".format(self._synapse_dynamics)
        output += "requires_remapping:{}".format(
            self._has_change_that_requires_mapping)
        output += "structure:{}".format(self._structure)
        output += "positions:{}".format(self._positions)

        return output
