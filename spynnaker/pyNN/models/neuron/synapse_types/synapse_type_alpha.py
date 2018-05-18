from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.utilities.ranged import SpynakkerRangeDictionary
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_exponential \
    import get_exponential_decay_and_init

from spynnaker.pyNN.models.neuron.synapse_types.abstract_synapse_type import \
    AbstractSynapseType
from spynnaker.pyNN.utilities.utility_calls import convert_param_to_numpy
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter

from data_specification.enums.data_type import DataType
from enum import Enum

EXC_RESPONSE = "exc_response"
EXC_EXP_RESPONSE = "exc_exp_response"
TAU_SYN_E = "tau_syn_E"
INH_RESPONSE = "inh_response"
INH_EXP_RESPONSE = "inh_exp_response"
TAU_SYN_I = "tau_syn_I"


class _COMB_EXP_TYPES(Enum):
    RESPONSE_EXC = (1, DataType.S1615)
    RESPONSE_EXC_EXP = (2, DataType.S1615)
    CONST_EXC = (3, DataType.S1615)
    DECAY_EXC = (4, DataType.UINT32)
    RESPONSE_INH = (5, DataType.S1615)
    RESPONSE_INH_EXP = (6, DataType.S1615)
    CONST_INH = (7, DataType.S1615)
    DECAY_INH = (8, DataType.UINT32)

    def __new__(cls, value, data_type, doc=""):
        # pylint: disable=protected-access
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        obj.__doc__ = doc
        return obj

    @property
    def data_type(self):
        return self._data_type


class SynapseTypeAlpha(AbstractSynapseType):
    __slots__ = [
        "_data",
        "_exc_exp_response",
        "_exc_response",
        "_inh_exp_response",
        "_inh_response",
        "_tau_syn_E",
        "_tau_syn_I"]

    def __init__(self, n_neurons, exc_response, exc_exp_response,
                 tau_syn_E, inh_response, inh_exp_response, tau_syn_I):
        # pylint: disable=too-many-arguments
        self._data = SpynakkerRangeDictionary(size=n_neurons)
        self._data[EXC_RESPONSE] = exc_response
        self._data[EXC_EXP_RESPONSE] = exc_exp_response
        self._data[TAU_SYN_E] = tau_syn_E
        self._data[INH_RESPONSE] = inh_response
        self._data[INH_EXP_RESPONSE] = inh_exp_response
        self._data[TAU_SYN_I] = tau_syn_I

        self._exc_response = convert_param_to_numpy(exc_response, n_neurons)
        self._exc_exp_response = convert_param_to_numpy(
            exc_exp_response, n_neurons)
        self._tau_syn_E = convert_param_to_numpy(tau_syn_E, n_neurons)

        self._inh_response = convert_param_to_numpy(inh_response, n_neurons)
        self._inh_exp_response = convert_param_to_numpy(
            inh_exp_response, n_neurons)
        self._tau_syn_I = convert_param_to_numpy(tau_syn_I, n_neurons)

    @property
    def exc_response(self):
        return self._data[EXC_RESPONSE]

    @exc_response.setter
    def exc_response(self, exc_response):
        self._data.set_value(key=EXC_RESPONSE, value=exc_response)

    @property
    def tau_syn_E(self):
        return self._data[TAU_SYN_E]

    @tau_syn_E.setter
    def tau_syn_E(self, tau_syn_E):
        self._data.set_value(key=TAU_SYN_E, value=tau_syn_E)

    @property
    def inh_response(self):
        return self._data[INH_RESPONSE]

    @inh_response.setter
    def inh_response(self, inh_response):
        self._data.set_value(key=INH_RESPONSE, value=inh_response)

    @property
    def tau_syn_I(self):
        return self._data[TAU_SYN_I]

    @tau_syn_I.setter
    def tau_syn_I(self, tau_syn_I):
        self._data.set_value(key=TAU_SYN_I, value=tau_syn_I)

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

    @overrides(AbstractSynapseType.get_n_synapse_type_parameters)
    def get_n_synapse_type_parameters(self):
        return 8

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_synapse_type_parameters(self, machine_time_step):
        # pylint: disable=arguments-differ
        e_decay, _ = get_exponential_decay_and_init(
            self._data[TAU_SYN_E], machine_time_step)

        i_decay, _ = get_exponential_decay_and_init(
            self._data[TAU_SYN_I], machine_time_step)

        # pre-multiply constants (convert to millisecond)
        dt_divided_by_tau_syn_E_sqr = self._data[TAU_SYN_E].apply_operation(
            lambda x: (float(machine_time_step) / 1000.0) / (x * x))
        dt_divided_by_tau_syn_I_sqr = self._data[TAU_SYN_I].apply_operation(
            lambda x: (float(machine_time_step) / 1000.0) / (x * x))

        return [
            # linear term buffer
            NeuronParameter(self._data[EXC_RESPONSE],
                            _COMB_EXP_TYPES.RESPONSE_EXC.data_type),
            # exponential term buffer
            NeuronParameter(self._data[EXC_EXP_RESPONSE],
                            _COMB_EXP_TYPES.RESPONSE_EXC_EXP.data_type),
            # evolution parameters
            NeuronParameter(dt_divided_by_tau_syn_E_sqr,
                            _COMB_EXP_TYPES.CONST_EXC.data_type),
            NeuronParameter(e_decay, _COMB_EXP_TYPES.DECAY_EXC.data_type),

            NeuronParameter(self._data[INH_RESPONSE],
                            _COMB_EXP_TYPES.RESPONSE_INH.data_type),
            NeuronParameter(self._data[INH_EXP_RESPONSE],
                            _COMB_EXP_TYPES.RESPONSE_INH_EXP.data_type),
            NeuronParameter(dt_divided_by_tau_syn_I_sqr,
                            _COMB_EXP_TYPES.CONST_INH.data_type),
            NeuronParameter(i_decay, _COMB_EXP_TYPES.DECAY_INH.data_type),
        ]

    @overrides(AbstractSynapseType.get_synapse_type_parameter_types)
    def get_synapse_type_parameter_types(self):
        return [item.data_type for item in DataType]

    @overrides(AbstractSynapseType.get_n_cpu_cycles_per_neuron)
    def get_n_cpu_cycles_per_neuron(self):
        # a guess
        return 100
