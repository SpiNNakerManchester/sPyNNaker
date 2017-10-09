from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_exponential \
    import get_exponential_decay_and_init

from spynnaker.pyNN.models.neuron.synapse_types.abstract_synapse_type import \
    AbstractSynapseType
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter

from data_specification.enums.data_type import DataType
from enum import Enum


class _COMB_EXP_TYPES(Enum):
    RESPONSE = (1, DataType.S1615)
    CONST = (2, DataType.S1615)
    DECAY = (3, DataType.UINT32)
    INIT = (4, DataType.UINT32)

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type


class SynapseTypeAlpha(AbstractSynapseType):

    def __init__(self, n_neurons, dt, exc_response, exc_exp_response,
                 tau_syn_E, inh_response, inh_exp_response, tau_syn_I):

        AbstractSynapseType.__init__(self)
        self._n_neurons = n_neurons
        self._dt = 0.1

        self._exc_response = utility_calls.convert_param_to_numpy(
            exc_response, n_neurons)
        self._exc_exp_response = utility_calls.convert_param_to_numpy(
            exc_exp_response, n_neurons)
        self._tau_syn_E = utility_calls.convert_param_to_numpy(
            tau_syn_E, n_neurons)

        self._inh_response = utility_calls.convert_param_to_numpy(
            inh_response, n_neurons)
        self._inh_exp_response = utility_calls.convert_param_to_numpy(
            inh_exp_response, n_neurons)
        self._tau_syn_I = utility_calls.convert_param_to_numpy(
            tau_syn_I, n_neurons)

    @property
    def exc_response(self):
        return self._exc_response

    @exc_response.setter
    def exc_response(self, exc_response):
        self._exc_response = utility_calls.convert_param_to_numpy(
            exc_response, self._n_neurons)

    @property
    def tau_syn_E(self):
        return self._tau_syn_E

    @tau_syn_E.setter
    def tau_syn_E(self, tau_syn_E):
        self._tau_syn_E = utility_calls.convert_param_to_numpy(
            tau_syn_E, self._n_neurons)

    @property
    def inh_response(self):
        return self._inh_response

    @inh_response.setter
    def inh_response(self, inh_response):
        self._inh_response = utility_calls.convert_param_to_numpy(
            inh_response, self._n_neurons)

    @property
    def tau_syn_I(self):
        return self._tau_syn_I

    @tau_syn_I.setter
    def tau_syn_I(self, tau_syn_I):
        self._tau_syn_I = utility_calls.convert_param_to_numpy(
            tau_syn_I, self._n_neurons)

    def get_n_synapse_types(self):
        return 2  # EX and IH

    def get_synapse_id_by_target(self, target):

        if target == "excitatory":
            return 0
        elif target == "inhibitory":
            return 1
        return None

    def get_synapse_targets(self):
        return "excitatory",  "inhibitory"

    def get_n_synapse_type_parameters(self):
        return 10

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_synapse_type_parameters(self, machine_time_step):
        e_decay, e_init = get_exponential_decay_and_init(
            self._tau_syn_E, machine_time_step)

        i_decay, i_init = get_exponential_decay_and_init(
            self._tau_syn_I, machine_time_step)

        inv_tau_syn_E_sqr = 1/(self._tau_syn_E * self._tau_syn_E)
        inv_tau_syn_I_sqr = 1/(self._tau_syn_I * self._tau_syn_I)

        return [

            NeuronParameter(self._dt, _COMB_EXP_TYPES.RESPONSE.data_type),
            # linear term buffer
            NeuronParameter(self._exc_response,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            # exponential term buffer
            NeuronParameter(self._exc_exp_response,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            # evolution parameters
            NeuronParameter(inv_tau_syn_E_sqr,
                            _COMB_EXP_TYPES.CONST.data_type),
            NeuronParameter(e_decay, _COMB_EXP_TYPES.DECAY.data_type),

            NeuronParameter(self._dt,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            NeuronParameter(self._inh_response,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            NeuronParameter(self._inh_exp_response,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            NeuronParameter(inv_tau_syn_I_sqr,
                            _COMB_EXP_TYPES.CONST.data_type),
            NeuronParameter(i_decay, _COMB_EXP_TYPES.DECAY.data_type),
        ]

    def get_synapse_type_parameter_types(self):
        return [item.data_type for item in DataType]

    def get_n_cpu_cycles_per_neuron(self):
        # a guess
        return 100
