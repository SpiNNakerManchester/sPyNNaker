from spinn_utilities.overrides import overrides
from spinn_utilities.ranged.abstract_list import AbstractList
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from .abstract_synapse_type import AbstractSynapseType
from data_specification.enums import DataType
import numpy

TAU_SYN_E = 'tau_syn_E'
TAU_SYN_E2 = 'tau_syn_E2'
TAU_SYN_I = 'tau_syn_I'
TAU_SYN_I2 = 'tau_syn_I2'
GSYN_EXC = 'gsyn_exc'
GSYN_EXC2 = 'gsyn_exc2'
GSYN_INH = 'gsyn_inh'
GSYN_INH2 = 'gsyn_inh2'

UNITS = {
    TAU_SYN_E: "mV",
    TAU_SYN_E2: "mV",
    TAU_SYN_I: 'mV',
    TAU_SYN_I2: 'mV',
    GSYN_EXC: "uS",
    GSYN_EXC2: "uS",
    GSYN_INH: "uS",
    GSYN_INH2: "uS"}

class SynapseTypeExponential2E2I(AbstractSynapseType):
    __slots__ = [
        "_tau_syn_E",
        "_tau_syn_E2",
        "_tau_syn_I",
        "_tau_syn_I2",
        "_isyn_exc",
        "_isyn_exc2",
        "_isyn_inh",
        "_isyn_inh2"
        ]

    def __init__(self,
                 tau_syn_E,
                 tau_syn_E2,
                 tau_syn_I,
                 tau_syn_I2,
                 initial_input_exc,
                 initial_input_exc2,
                 initial_input_inh,
                 initial_input_inh2
                 ):
        super(SynapseTypeExponential2E2I, self).__init__([
            DataType.U032,    # decay_E
            DataType.U032,    # init_E
            DataType.S1615,   # isyn_exc
            DataType.U032,    # decay_E2
            DataType.U032,    # init_E2
            DataType.S1615,   # isyn_exc2
            DataType.U032,    # decay_I
            DataType.U032,    # init_I
            DataType.S1615,   # isyn_inh
            DataType.U032,    # decay_I2
            DataType.U032,    # init_I2
            DataType.S1615,   # isyn_inh2
            ])


        self._tau_syn_E = tau_syn_E
        self._tau_syn_E2 = tau_syn_E2
        self._tau_syn_I = tau_syn_I
        self._tau_syn_I2 = tau_syn_I2
        self._isyn_exc = initial_input_exc
        self._isyn_exc2 = initial_input_exc2
        self._isyn_inh = initial_input_inh
        self._isyn_inh2 = initial_input_inh2

    @overrides(AbstractSynapseType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 100

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        parameters[TAU_SYN_E] = self._tau_syn_E
        parameters[TAU_SYN_E2] = self._tau_syn_E2
        parameters[TAU_SYN_I] = self._tau_syn_I
        parameters[TAU_SYN_I2] = self._tau_syn_I2

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[GSYN_EXC] = self._isyn_exc
        state_variables[GSYN_EXC2] = self._isyn_exc2
        state_variables[GSYN_INH] = self._isyn_inh
        state_variables[GSYN_INH2] = self._isyn_inh2

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
                state_variables[GSYN_EXC],
                parameters[TAU_SYN_E2].apply_operation(decay),
                parameters[TAU_SYN_E2].apply_operation(init),
                state_variables[GSYN_EXC2],
                parameters[TAU_SYN_I].apply_operation(decay),
                parameters[TAU_SYN_I].apply_operation(init),
                state_variables[GSYN_INH],
                parameters[TAU_SYN_I2].apply_operation(decay),
                parameters[TAU_SYN_I2].apply_operation(init),
                state_variables[GSYN_INH2]
                ]

    @overrides(AbstractSynapseType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_decay_E, _init_E, _decay_E2, _init_E2, _decay_I, _init_I,
         _decay_I2, _init_I2,
         isyn_exc, isyn_exc2, isyn_inh, isyn_inh2) = values

        state_variables[GSYN_EXC] = isyn_exc
        state_variables[GSYN_EXC2] = isyn_exc2
        state_variables[GSYN_INH] = isyn_inh
        state_variables[GSYN_INH2] = isyn_inh2

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self):
        return 4

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "excitatory2":
            return 1
        elif target == "inhibitory":
            return 2
        elif target == "inhibitory2":
            return 3
        return None

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self):
        return "excitatory", "excitatory2", "inhibitory", "inhibitory2"

    @property
    def tau_syn_E(self):
        return self._tau_syn_E

    @tau_syn_E.setter
    def tau_syn_E(self, tau_syn_E):
        self._tau_syn_E=tau_syn_E

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
    def tau_syn_I2(self):
        return self._tau_syn_I2

    @tau_syn_I2.setter
    def tau_syn_I2(self, tau_syn_I2):
        self._tau_syn_I2 = tau_syn_I2

    @property
    def isyn_exc(self):
        return self._isyn_exc

    @isyn_exc.setter
    def isyn_exc(self, new_value):
        self._isyn_exc = isyn_exc

    @property
    def isyn_exc2(self):
        return self._isyn_exc2
    @isyn_exc2.setter
    def isyn_exc2(self, new_value):
        self._isyn_exc2 = isyn_exc2

    @property
    def isyn_inh(self):
        return self._isyn_inh

    @isyn_inh.setter
    def isyn_inh(self, new_value):
        self._isyn_inh = isyn_inh

    @property
    def isyn_inh_2(self):
        return self._isyn_inh_2

    @isyn_inh_2.setter
    def isyn_inh_2(self, new_value):
        self._isyn_inh_2 = isyn_inh_2
