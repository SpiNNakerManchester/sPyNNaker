from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from .abstract_synapse_type import AbstractSynapseType

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
        "__isyn_exc",
        "__isyn_inh"]

    def __init__(self, isyn_exc, isyn_inh):
        super(SynapseTypeDelta, self).__init__([
            DataType.S1615,   # isyn_exc
            DataType.S1615])  # isyn_inh
        self.__isyn_exc = isyn_exc
        self.__isyn_inh = isyn_inh

    @overrides(AbstractSynapseType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 1 * n_neurons

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        pass

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[ISYN_EXC] = self.__isyn_exc
        state_variables[ISYN_INH] = self.__isyn_inh

    @overrides(AbstractSynapseType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractSynapseType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractSynapseType.get_values)
    def get_values(self, parameters, state_variables, vertex_slice):

        # Add the rest of the data
        return [state_variables[ISYN_EXC], state_variables[ISYN_INH]]

    @overrides(AbstractSynapseType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (isyn_exc, isyn_inh) = values

        state_variables[ISYN_EXC] = isyn_exc
        state_variables[ISYN_INH] = isyn_inh

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
        return self.__isyn_exc

    @isyn_exc.setter
    def isyn_exc(self, isyn_exc):
        self.__isyn_exc = isyn_exc

    @property
    def isyn_inh(self):
        return self.__isyn_inh

    @isyn_inh.setter
    def isyn_inh(self, isyn_inh):
        self.__isyn_inh = isyn_inh
