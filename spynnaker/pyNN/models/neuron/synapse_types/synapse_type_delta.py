from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.synapse_types import AbstractSynapseType
from spynnaker.pyNN.utilities import utility_calls

ISYN_EXC = "isyn_exc"
ISYN_INH = "isyn_inh"

UNITS = {
    ISYN_EXC: "",
    ISYN_EXC: ""
}


class SynapseTypeDelta(AbstractSynapseType):
    """ This represents a synapse type with two delta synapses
    """
    __slots__ = [
        "_isyn_exc",
        "_isyn_inh"]

    def __init__(self, isyn_exc, isyn_inh):
        self._isyn_exc = isyn_exc
        self._isyn_inh = isyn_inh

    @overrides(AbstractSynapseType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 1 * n_neurons

    @overrides(AbstractSynapseType.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        # 1 parameter per neuron per synapse type (4 bytes each)
        return (2 * 1 * 4 * n_neurons)

    @overrides(AbstractSynapseType.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        # 1 parameter per neuron per synapse type (4 bytes each)
        return (2 * 1 * 4 * n_neurons)

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        pass

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables.set_value(ISYN_EXC, self._isyn_exc)
        state_variables.set_value(ISYN_INH, self._isyn_inh)

    @overrides(AbstractSynapseType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractSynapseType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractSynapseType.get_data)
    def get_data(self, parameters, state_variables, vertex_slice):

        # Add the rest of the data
        items = [
            (state_variables[ISYN_EXC], DataType.S1615),
            (state_variables[ISYN_INH], DataType.S1615)
        ]
        return utility_calls.get_parameter_data(items, vertex_slice)

    @overrides(AbstractSynapseType.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):

        # Read the data
        types = [DataType.S1615 * 2]
        offset, (isyn_exc, isyn_inh) = \
            utility_calls.read_parameter_data(
                types, data, offset, vertex_slice.n_atoms)

        utility_calls.copy_values(
            isyn_exc, state_variables[ISYN_EXC], vertex_slice)
        utility_calls.copy_values(
            isyn_inh, state_variables[ISYN_INH], vertex_slice)

        return offset

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self):
        return 2

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "inhibitory":
            return 1
        return None

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self):
        return "excitatory", "inhibitory"

    @property
    def isyn_exc(self):
        return self._isyn_exc

    @isyn_exc.setter
    def isyn_exc(self, isyn_exc):
        self._isyn_exc = isyn_exc

    @property
    def isyn_inh(self):
        return self._isyn_inh

    @isyn_inh.setter
    def isyn_inh(self, isyn_inh):
        self._isyn_inh = isyn_inh
