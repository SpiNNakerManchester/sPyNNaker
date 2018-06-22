from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.models.neuron.synapse_types.abstract_synapse_type import \
    AbstractSynapseType

from data_specification.enums.data_type import DataType
from spynnaker.pyNN.utilities import utility_calls
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

    @overrides(AbstractSynapseType.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        # 4 parameters per neuron per synapse type (4 bytes each)
        return (2 * 4 * 4 * n_neurons)

    @overrides(AbstractSynapseType.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        # 4 parameters per neuron per synapse type (4 bytes each)
        return (2 * 4 * 4 * n_neurons)

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters):
        parameters.set_value(TAU_SYN_E, self._tau_syn_E)
        parameters.set_value(TAU_SYN_I, self._tau_syn_I)

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables.set_value(EXC_RESPONSE, self._exc_response)
        state_variables.set_value(EXC_EXP_RESPONSE, self._exc_exp_response)
        state_variables.set_value(INH_RESPONSE, self._inh_response)
        state_variables.set_value(INH_EXP_RESPONSE, self._inh_exp_response)

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

        init = lambda x: (float(ts) / 1000.0) / (x * x)  # noqa
        decay = lambda x: numpy.exp(-ts / x)  # noqa

        # Add the rest of the data
        items = [
            (state_variables[EXC_RESPONSE], DataType.S1615),
            (state_variables[EXC_EXP_RESPONSE], DataType.S1615),
            (parameters[TAU_SYN_E].apply_operation(init), DataType.S1615),
            (parameters[TAU_SYN_E].apply_operation(decay), DataType.U032),
            (state_variables[INH_RESPONSE], DataType.S1615),
            (state_variables[INH_EXP_RESPONSE], DataType.S1615),
            (parameters[TAU_SYN_I].apply_operation(init), DataType.S1615),
            (parameters[TAU_SYN_I].apply_operation(decay), DataType.U032)
        ]
        return utility_calls.get_parameter_data(items, vertex_slice)

    @overrides(AbstractSynapseType.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):

        # Read the data
        types = [DataType.S1615, DataType.S1615, DataType.S1615, DataType.U032,
                 DataType.S1615, DataType.S1615, DataType.S1615, DataType.U032]
        offset, (exc_resp, exc_exp_resp, _dt_over_tau_E_sq, _exp_tau_E,
                 inh_resp, inh_exp_resp, _dt_over_tau_I_sq, _exp_tau_I,) = \
            utility_calls.read_parameter_data(
                types, data, offset, vertex_slice.n_atoms)

        utility_calls.copy_values(
            exc_resp, state_variables[EXC_RESPONSE], vertex_slice)
        utility_calls.copy_values(
            exc_exp_resp, state_variables[EXC_EXP_RESPONSE], vertex_slice)
        utility_calls.copy_values(
            inh_resp, state_variables[INH_RESPONSE], vertex_slice)
        utility_calls.copy_values(
            inh_exp_resp, state_variables[INH_EXP_RESPONSE], vertex_slice)

        return offset

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
