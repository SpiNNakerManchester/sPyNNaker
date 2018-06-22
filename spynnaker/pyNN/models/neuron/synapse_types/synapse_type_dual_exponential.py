from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from .abstract_synapse_type import AbstractSynapseType
from data_specification.enums import DataType
import numpy
from spynnaker.pyNN.utilities import utility_calls

TAU_SYN_E = 'tau_syn_E'
TAU_SYN_E2 = 'tau_syn_E2'
TAU_SYN_I = 'tau_syn_I'
ISYN_EXC = "isyn_exc"
ISYN_EXC2 = "isyn_exc2"
ISYN_INH = "isyn_inh"

UNITS = {
    TAU_SYN_E: "mV",
    TAU_SYN_E2: "mV",
    TAU_SYN_I: 'mV',
    ISYN_EXC: "",
    ISYN_EXC2: "",
    ISYN_INH: "",
}


class SynapseTypeDualExponential(AbstractSynapseType):
    __slots__ = [
        "_tau_syn_E",
        "_tau_syn_E2",
        "_tau_syn_I",
        "_isyn_exc",
        "_isyn_exc2",
        "_isyn_inh"]

    def __init__(
            self, tau_syn_E, tau_syn_E2, tau_syn_I, isyn_exc, isyn_exc2,
            isyn_inh):
        self._tau_syn_E = tau_syn_E
        self._tau_syn_E2 = tau_syn_E2
        self._tau_syn_I = tau_syn_I
        self._isyn_exc = isyn_exc
        self._isyn_exc2 = isyn_exc2
        self._isyn_inh = isyn_inh

    @overrides(AbstractSynapseType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 100 * n_neurons

    @overrides(AbstractSynapseType.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        # 3 parameters per neuron per synapse type (4 bytes each)
        return (3 * 3 * 4 * n_neurons)

    @overrides(AbstractSynapseType.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        # 3 parameters per neuron per synapse type (4 bytes each)
        return (3 * 3 * 4 * n_neurons)

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        parameters.set_value(TAU_SYN_E, self._tau_syn_E)
        parameters.set_value(TAU_SYN_E2, self._tau_syn_E2)
        parameters.set_value(TAU_SYN_I, self._tau_syn_I)

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables.set_value(ISYN_EXC, self._isyn_exc)
        state_variables.set_value(ISYN_EXC2, self._isyn_exc2)
        state_variables.set_value(ISYN_INH, self._isyn_inh)

    @overrides(AbstractSynapseType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractSynapseType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractSynapseType.get_data,
               additional_arguments={'ts'})
    def get_data(self, parameters, state_variables, vertex_slice, ts):

        decay = lambda x: int(numpy.exp(-ts / x) * ulfract)  # noqa E731
        init = lambda x: (x / ts) * (1.0 - numpy.exp(-ts / x))  # noqa E731

        # Add the rest of the data
        items = [
            (parameters[TAU_SYN_E].apply_operation(decay), DataType.U032),
            (parameters[TAU_SYN_E].apply_operation(init), DataType.U032),
            (parameters[TAU_SYN_E2].apply_operation(decay), DataType.U032),
            (parameters[TAU_SYN_E2].apply_operation(init), DataType.U032),
            (parameters[TAU_SYN_I].apply_operation(decay), DataType.U032),
            (parameters[TAU_SYN_I].apply_operation(init), DataType.U032),
            (state_variables[ISYN_EXC], DataType.S1615),
            (state_variables[ISYN_EXC2], DataType.S1615),
            (state_variables[ISYN_INH], DataType.S1615)
        ]
        return utility_calls.get_parameter_data(items, vertex_slice)

    @overrides(AbstractSynapseType.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):

        # Read the data
        types = [DataType.U032, DataType.U032, DataType.U032, DataType.U032,
                 DataType.U032, DataType.U032, DataType.S1615, DataType.S1615,
                 DataType.S1615]
        offset, (_decay_E, _init_E, _decay_E2, _init_E2, _decay_I, _init_I,
                 isyn_exc, isyn_exc2, isyn_inh) = \
            utility_calls.read_parameter_data(
                types, data, offset, vertex_slice.n_atoms)

        utility_calls.copy_values(
            isyn_exc, state_variables[ISYN_EXC], vertex_slice)
        utility_calls.copy_values(
            isyn_exc2, state_variables[ISYN_EXC2], vertex_slice)
        utility_calls.copy_values(
            isyn_inh, state_variables[ISYN_INH], vertex_slice)

        return offset

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self):
        return 3

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "excitatory2":
            return 1
        elif target == "inhibitory":
            return 2
        return None

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self):
        return "excitatory", "excitatory2", "inhibitory"

    @property
    def tau_syn_E(self):
        return self._tau_syn_E

    @tau_syn_E.setter
    def tau_syn_E(self, tau_syn_E):
        self._tau_syn_E = tau_syn_E

    @property
    def tau_syn_E2(self):
        return self._tau_syn_E2

    @tau_syn_E2.setter
    def tau_syn_E2(self, tau_syn_E2):
        self._tau_syn_E2 = tau_syn_E2

    @property
    def tau_syn_I(self):
        return self._tau_syn_I

    @tau_syn_I.setter
    def tau_syn_I(self, tau_syn_I):
        self._tau_syn_I = tau_syn_I

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

    @property
    def isyn_exc2(self):
        return self._isyn_exc2

    @isyn_exc2.setter
    def isyn_exc2(self, isyn_exc2):
        self._isyn_exc2 = isyn_exc2
