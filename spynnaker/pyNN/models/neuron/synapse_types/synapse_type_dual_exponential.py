import numpy
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from pacman.executor.injection_decorator import inject_items
from .abstract_synapse_type import AbstractSynapseType

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
        "__tau_syn_E",
        "__tau_syn_E2",
        "__tau_syn_I",
        "__isyn_exc",
        "__isyn_exc2",
        "__isyn_inh"]

    def __init__(
            self, tau_syn_E, tau_syn_E2, tau_syn_I, isyn_exc, isyn_exc2,
            isyn_inh):
        super(SynapseTypeDualExponential, self).__init__(
            [DataType.U032,    # decay_E
             DataType.U032,    # init_E
             DataType.S1615,   # isyn_exc
             DataType.U032,    # decay_E2
             DataType.U032,    # init_E2
             DataType.S1615,   # isyn_exc2
             DataType.U032,    # decay_I
             DataType.U032,    # init_I
             DataType.S1615])  # isyn_inh
        self.__tau_syn_E = tau_syn_E
        self.__tau_syn_E2 = tau_syn_E2
        self.__tau_syn_I = tau_syn_I
        self.__isyn_exc = isyn_exc
        self.__isyn_exc2 = isyn_exc2
        self.__isyn_inh = isyn_inh

    @overrides(AbstractSynapseType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 100 * n_neurons

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        parameters[TAU_SYN_E] = self.__tau_syn_E
        parameters[TAU_SYN_E2] = self.__tau_syn_E2
        parameters[TAU_SYN_I] = self.__tau_syn_I

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[ISYN_EXC] = self.__isyn_exc
        state_variables[ISYN_EXC2] = self.__isyn_exc2
        state_variables[ISYN_INH] = self.__isyn_inh

    @overrides(AbstractSynapseType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractSynapseType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractSynapseType.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        tsfloat = float(ts) / 1000.0
        decay = lambda x: numpy.exp(-tsfloat / x)  # noqa E731
        init = lambda x: (x / tsfloat) * (1.0 - numpy.exp(-tsfloat / x))  # noqa E731

        # Add the rest of the data
        return [parameters[TAU_SYN_E].apply_operation(decay),
                parameters[TAU_SYN_E].apply_operation(init),
                state_variables[ISYN_EXC],
                parameters[TAU_SYN_E2].apply_operation(decay),
                parameters[TAU_SYN_E2].apply_operation(init),
                state_variables[ISYN_EXC2],
                parameters[TAU_SYN_I].apply_operation(decay),
                parameters[TAU_SYN_I].apply_operation(init),
                state_variables[ISYN_INH]]

    @overrides(AbstractSynapseType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_decay_E, _init_E, isyn_exc, _decay_E2, _init_E2, isyn_exc2,
         _decay_I, _init_I, isyn_inh) = values

        state_variables[ISYN_EXC] = isyn_exc
        state_variables[ISYN_EXC2] = isyn_exc2
        state_variables[ISYN_INH] = isyn_inh

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
        return self.__tau_syn_E

    @tau_syn_E.setter
    def tau_syn_E(self, tau_syn_E):
        self.__tau_syn_E = tau_syn_E

    @property
    def tau_syn_E2(self):
        return self.__tau_syn_E2

    @tau_syn_E2.setter
    def tau_syn_E2(self, tau_syn_E2):
        self.__tau_syn_E2 = tau_syn_E2

    @property
    def tau_syn_I(self):
        return self.__tau_syn_I

    @tau_syn_I.setter
    def tau_syn_I(self, tau_syn_I):
        self.__tau_syn_I = tau_syn_I

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

    @property
    def isyn_exc2(self):
        return self.__isyn_exc2

    @isyn_exc2.setter
    def isyn_exc2(self, isyn_exc2):
        self.__isyn_exc2 = isyn_exc2
