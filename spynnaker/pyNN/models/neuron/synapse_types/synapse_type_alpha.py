from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from .abstract_synapse_type import AbstractSynapseType
from data_specification.enums import DataType
import numpy

EXC_RESPONSE = "exc_response"
EXC_EXP_RESPONSE = "exc_exp_response"
TAU_SYN_E = "tau_syn_E"
INH_RESPONSE = "inh_response"
INH_EXP_RESPONSE = "inh_exp_response"
TAU_SYN_I = "tau_syn_I"

UNITS = {
    EXC_RESPONSE: "",
    EXC_EXP_RESPONSE: "",
    TAU_SYN_E: "ms",
    INH_RESPONSE: "",
    INH_EXP_RESPONSE: "",
    TAU_SYN_I: "ms"
}


class SynapseTypeAlpha(AbstractSynapseType):
    __slots__ = [
        "_exc_exp_response",
        "_exc_response",
        "_inh_exp_response",
        "_inh_response",
        "_tau_syn_E",
        "_tau_syn_I"]

    def __init__(self, exc_response, exc_exp_response,
                 tau_syn_E, inh_response, inh_exp_response, tau_syn_I):
        super(SynapseTypeAlpha, self).__init__([
            DataType.S1615,  # exc_response
            DataType.S1615,  # exc_exp_response
            DataType.S1615,  # 1 / tau_syn_E^2
            DataType.U032,   # e^(-ts / tau_syn_E)
            DataType.S1615,  # inh_response
            DataType.S1615,  # inh_exp_response
            DataType.S1615,  # 1 / tau_syn_I^2
            DataType.U032])  # e^(-ts / tau_syn_I)

        # pylint: disable=too-many-arguments
        self._exc_response = exc_response
        self._exc_exp_response = exc_exp_response
        self._tau_syn_E = tau_syn_E
        self._inh_response = inh_response
        self._inh_exp_response = inh_exp_response
        self._tau_syn_I = tau_syn_I

    @overrides(AbstractSynapseType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 100 * n_neurons

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        parameters[TAU_SYN_E] = self._tau_syn_E
        parameters[TAU_SYN_I] = self._tau_syn_I

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[EXC_RESPONSE] = self._exc_response
        state_variables[EXC_EXP_RESPONSE] = self._exc_exp_response
        state_variables[INH_RESPONSE] = self._inh_response
        state_variables[INH_EXP_RESPONSE] = self._inh_exp_response

    @overrides(AbstractSynapseType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractSynapseType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractSynapseType.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        init = lambda x: (float(ts) / 1000.0) / (x * x)  # noqa
        decay = lambda x: numpy.exp((-float(ts) / 1000.0) / x)  # noqa

        # Add the rest of the data
        return [state_variables[EXC_RESPONSE],
                state_variables[EXC_EXP_RESPONSE],
                parameters[TAU_SYN_E].apply_operation(init),
                parameters[TAU_SYN_E].apply_operation(decay),
                state_variables[INH_RESPONSE],
                state_variables[INH_EXP_RESPONSE],
                parameters[TAU_SYN_I].apply_operation(init),
                parameters[TAU_SYN_I].apply_operation(decay)]

    @overrides(AbstractSynapseType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (exc_resp, exc_exp_resp, _dt_over_tau_E_sq, _exp_tau_E,
         inh_resp, inh_exp_resp, _dt_over_tau_I_sq, _exp_tau_I) = values

        state_variables[EXC_RESPONSE] = exc_resp
        state_variables[EXC_EXP_RESPONSE] = exc_exp_resp
        state_variables[INH_RESPONSE] = inh_resp
        state_variables[INH_EXP_RESPONSE] = inh_exp_resp

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self):
        return 2  # EX and IH

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
    def exc_response(self):
        return self._exc_response

    @exc_response.setter
    def exc_response(self, exc_response):
        self._exc_response = exc_response

    @property
    def tau_syn_E(self):
        return self._tau_syn_E

    @tau_syn_E.setter
    def tau_syn_E(self, tau_syn_E):
        self._tau_syn_E = tau_syn_E

    @property
    def inh_response(self):
        return self._inh_response

    @inh_response.setter
    def inh_response(self, inh_response):
        self._inh_response = inh_response

    @property
    def tau_syn_I(self):
        return self._tau_syn_I

    @tau_syn_I.setter
    def tau_syn_I(self, tau_syn_I):
        self._tau_syn_I = tau_syn_I
