from spinn_front_end_common.utilities import exceptions
import copy

class NeuronCell(object):
    """
    NeuronCell: the object that stores all data about a cell.
    """

    def __init__(self, default_parameters):

        # standard parameters
        self._params = copy.deepcopy(default_parameters)

        # recording data items
        self._record_spikes = False
        self._record_spike_file_path = None
        self._record_gsyn = False
        self._record_gsyn_file_path = None
        self._record_v = False
        self._record_v_file_path = None

        # synaptic link
        self._synapse_dynamics = None

        # change marker
        self._has_change_that_requires_mapping = True

    def add_param(self, key, value):
        self._params[key] = value
        self._has_change_that_requires_mapping = True

    def get_param(self, key):
        return self._params[key]

    def set_param(self, key, new_value):
        if key in self._params:
            self._params[key] = new_value
        self.add_param(key, new_value)
        self._has_change_that_requires_mapping = True

    def set_synapse_dynamics(self, new_value):
        if self._synapse_dynamics is None:
            self._synapse_dynamics = new_value
        elif self._synapse_dynamics != new_value:
            raise exceptions.ConfigurationException(
                "Currently only one type of SDTP can be supported per cell.")
        self._has_change_that_requires_mapping = True

    def set_record_spikes(self, new_value, file_path):
        self._record_spikes = new_value
        if isinstance(file_path, bool):
            self._record_spike_file_path = "spikes"
        else:
            self._record_spike_file_path = file_path
        self._has_change_that_requires_mapping = True

    def set_record_v(self, new_value, file_path):
        self._record_v = new_value
        if isinstance(file_path, bool):
            self._record_v_file_path = "v"
        else:
            self._record_v_file_path = file_path
        self._has_change_that_requires_mapping = True

    def set_record_gsyn(self, new_value, file_path):
        self._record_gsyn = new_value
        if isinstance(file_path, bool):
            self._record_gsyn_file_path = "gsyn"
        else:
            self._record_gsyn_file_path = file_path
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
        return output
