from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_exponential \
    import get_exponential_decay_and_init

from spynnaker.pyNN.models.neuron.synapse_types.abstract_synapse_type import \
    AbstractSynapseType
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_comb_exp\
    import set_excitatory_scalar
from data_specification.enums.data_type import DataType
from enum import Enum

EXC_A_RESPONSE = 'exc_a_response'
EXC_CONST_A = 'exc_a_A'
EXC_TAU_A = 'exc_tau_a'
EXC_B_RESPONSE = 'exc_b_response'
EXC_CONST_B = 'exc_b_B'
EXC_TAU_B = 'exc_tau_b'
EXC2_A_RESPONSE = 'exc2_a_response'
EXC2_CONST_A = 'exc2_a_A'
EXC2_TAU_A = 'exc2_tau_a'
EXC2_B_RESPONSE = 'exc2_b_response'
EXC2_CONST_B = 'exc2_b_B'
EXC2_TAU_B = 'exc2_tau_b'
INH_A_RESPONSE = 'inh_a_response'
INH_CONST_A = 'inh_a_A'
INH_TAU_A = 'inh_tau_a'
INH_B_RESPONSE = 'inh_b_response'
INH_CONST_B = 'inh_b_B'
INH_TAU_B = 'inh_tau_b'
INH2_A_RESPONSE = 'inh2_a_response'
INH2_CONST_A = 'inh2_a_A'
INH2_TAU_A = 'inh2_tau_a'
INH2_B_RESPONSE = 'inh2_b_response'
INH2_CONST_B = 'inh2_b_B'
INH2_TAU_B = 'inh2_tau_b'

UNITS = {
    EXC_CONST_A: "(Dimensionless)",
    EXC_TAU_A: "ms",
    EXC_CONST_B: "(Dimensionless)",
    EXC_TAU_B: "ms",
    EXC2_CONST_A: "(Dimensionless)",
    EXC2_TAU_A: "ms",
    EXC2_CONST_B: "(Dimensionless)",
    EXC2_TAU_B: "ms",
    INH_CONST_A: "(Dimensionless)",
    INH_TAU_A: "ms",
    INH_CONST_B: "(Dimensionless)",
    INH_TAU_B: "ms",
    INH2_CONST_A: "(Dimensionless)",
    INH2_TAU_A: "ms",
    INH2_CONST_B: "(Dimensionless)",
    INH2_TAU_B: "ms"
    }

class SynapseTypeCombExp2E2I(abstractSynapseType):
    slots = [
        '_exc_a_response'
        '_exc_a_A',
        'exc_tau_a',
        '_exc_B_response'
        '_exc_b_B',
        '_exc_tau_B',
        '_exc2_a_response'
        '_exc2_a_A',
        '_exc2_tau_a',
        '_exc2_B_response'
        '_exc2_b_B',
        '_exc2_tau_B',
        '_inh_a_response'
        '_inh_a_A',
        '_inh_tau_a',
        '_inh_B_response'
        '_inh_b_B',
        '_inh_tau_B',
        '_inh2_a_response'
        '_inh2_a_A',
        '_inh2_tau_a',
        '_inh2_B_response'
        '_inh2_b_B',
        '_inh2_tau_B'
        ]

    def __init__(self,
                exc_a_response,
                exc_a_A,
                exc_a_tau,
                exc_b_response,
                exc_b_B,
                exc_b_tau,

                exc2_a_response,
                exc2_a_A,
                exc2_a_tau,
                exc2_b_response,
                exc2_b_B,
                exc2_b_tau,

                inh_a_response,
                inh_a_A,
                inh_a_tau,
                inh_b_response,
                inh_b_B,
                inh_b_tau,

                inh2_a_response,
                inh2_a_A,
                inh2_a_tau,
                inh2_b_response,
                inh2_b_B,
                inh2_b_tau):

        super(SynapseTypeExponential2E2I, self).__init__([
            DataType.S1615,  # exc_a_response
            DataType.S1615,  # exc_a
            DataType.U032,   # exc_a_decay
            DataType.U032,   # exc_a_init
            DataType.S1615,  # exc_B_response
            DataType.S1615,  # exc_B
            DataType.U032,   # exc_B_decay
            DataType.U032,   # exc_B_init

            DataType.S1615,  # exc2_a_response
            DataType.S1615,  # exc2_a
            DataType.U032,   # exc2_a_decay
            DataType.U032,   # exc2_a_init
            DataType.S1615,  # exc2_B_response
            DataType.S1615,  # exc2_B
            DataType.U032,   # exc2_B_decay
            DataType.U032,   # exc2_B_init

            DataType.S1615,  # inh_a_response
            DataType.S1615,  # inh_a
            DataType.U032,   # inh_a_decay
            DataType.U032,   # inh_a_init
            DataType.S1615,  # inh_B_response
            DataType.S1615,  # inh_B
            DataType.U032,   # inh_B_decay
            DataType.U032,   # inh_B_init

            DataType.S1615,  # inh2_a_response
            DataType.S1615,  # inh2_a
            DataType.U032,   # inh2_a_decay
            DataType.U032,   # inh2_a_init
            DataType.S1615,  # inh2_B_response
            DataType.S1615,  # inh2_B
            DataType.U032,   # inh2_B_decay
            DataType.U032,   # inh2_B_init
            ])


        # inhitatory
        self._exc_a_response = exc_a_response
        self._exc_a_A = exc_a_A
        self._exc_a_tau = exc_a_tau
        self._exc_b_response = exc_b_response
        self._exc_b_B = exc_b_B
        self._exc_b_tau = exc_b_tau

        self.exc_a_a, self.exc_b_B = set_excitatory_scalar(self._exc_a_tau, self._exc_b_tau)

        # excitatory 2
        self._exc2_a_response = exc2_a_response
        self._exc2_a_A = exc2_a_A
        self._exc2_a_tau = exc2_a_tau
        self._exc2_b_response = exc2_b_response
        self._exc2_b_B = exc2_b_B
        self._exc2_b_tau = exc2_b_tau

        self.exc2_a_a, self.exc2_b_B = set_excitatory_scalar(self._exc2_a_tau, self._exc2_b_tau)

        #inhibitory
        self._inh_a_response = inh_a_response
        self._inh_a_A = inh_a_A
        self._inh_a_tau = inh_a_tau
        self._inh_b_response = inh_b_response
        self._inh_b_B = inh_b_B
        self._inh_b_tau = inh_b_tau

        self.inh_a_a, self.inh_b_B = set_inhitatory_scalar(self._inh_a_tau, self._inh_b_tau)

        # inhibitory 2
        self._inh2_a_response = inh2_a_response
        self._inh2_a_A = inh2_a_a
        self._inh2_a_tau = inh2_a_tau
        self._inh2_b_response = inh2_b_response
        self._inh2_b_B = inh2_b_B
        self._inh2_b_tau = inh2_b_tau

        self.inh2_a_a, self.inh2_b_B = set_inhitatory_scalar(self._inh2_a_tau, self._inh2_b_tau)











    #inhitatory
    @property
    def inh_a_response(self):
        return self._inh_a_response

    @inh_a_response.setter
    def inh_a_response(self, inh_a_response):
        self._inh_a_response = utility_calls.convert_param_to_numpy(
            inh_a_response, self._n_neurons)

    @property
    def inh_a_a(self):
        return self._inh_a_a

    @inh_a_a.setter
    def inh_a_a(self, inh_a_a):
        self._inh_a_a = utility_calls.convert_param_to_numpy(
            inh_a_a, self._n_neurons)

    @property
    def inh_a_tau(self):
        return self._inh_a_tau

    @inh_a_tau.setter
    def inh_a_tau(self, inh_a_tau):
        self._inh_a_tau = utility_calls.convert_param_to_numpy(
            inh_a_tau, self._n_neurons)
        self.inh_a_a, self.inh_b_B = set_inhitatory_scalar(self._inh_a_tau, self._inh_b_tau)

    @property
    def inh_b_response(self):
        return self._inh_b_response

    @inh_b_response.setter
    def inh_b_response(self, inh_b_response):
        self._inh_b_response = utility_calls.convert_param_to_numpy(
            inh_b_response, self._n_neurons)

    @property
    def inh_b_B(self):
        return self._inh_b_B

    @inh_b_B.setter
    def inh_b_B(self, inh_b_B):
        self._inh_b_B = utility_calls.convert_param_to_numpy(
            inh_b_B, self._n_neurons)

    @property
    def inh_b_tau(self):
        return self._inh_b_tau

    @inh_b_tau.setter
    def inh_b_tau(self, inh_b_tau):
        self._inh_b_tau = utility_calls.convert_param_to_numpy(
            inh_b_tau, self._n_neurons)
        self.inh_a_a, self.inh_b_B = set_inhitatory_scalar(self._inh_a_tau, self._inh_b_tau)

    # inhitatory2
    @property
    def inh2_a_response(self):
        return self._inh2_a_response

    @inh2_a_response.setter
    def inh2_a_response(self, inh2_a_response):
        self._inh2_a_response = utility_calls.convert_param_to_numpy(
            inh2_a_response, self._n_neurons)

    @property
    def inh2_a_a(self):
        return self._inh2_a_a

    @inh2_a_a.setter
    def inh2_a_a(self, inh2_a_a):
        self._inh2_a_a = utility_calls.convert_param_to_numpy(
            inh2_a_a, self._n_neurons)

    @property
    def inh2_a_tau(self):
        return self._inh2_a_tau

    @inh2_a_tau.setter
    def inh2_a_tau(self, inh2_a_tau):
        self._inh2_a_tau = utility_calls.convert_param_to_numpy(
            inh2_a_tau, self._n_neurons)
        self.inh2_a_a, self.inh2_b_B = set_inhitatory_scalar(self._inh2_a_tau, self._inh2_b_tau)

    @property
    def inh2_b_response(self):
        return self._inh2_b_response

    @inh2_b_response.setter
    def inh2_b_response(self, inh2_b_response):
        self._inh2_b_response = utility_calls.convert_param_to_numpy(
            inh2_b_response, self._n_neurons)

    @property
    def inh2_b_B(self):
        return self._inh2_b_B

    @inh2_b_B.setter
    def inh2_b_B(self, inh2_b_B):
        self._inh2_b_B = utility_calls.convert_param_to_numpy(
            inh2_b_B, self._n_neurons)

    @property
    def inh2_b_tau(self):
        return self._inh2_b_tau

    @inh2_b_tau.setter
    def inh2_b_tau(self, inh2_b_tau):
        self._inh2_b_tau = utility_calls.convert_param_to_numpy(
            inh2_b_tau, self._n_neurons)
        self.inh2_a_a, self.inh2_b_B = set_inhitatory_scalar(self._inh2_a_tau, self._inh2_b_tau)

    # inhibitory
    @property
    def inh_a_response(self):
        return self._inh_a_response

    @inh_a_response.setter
    def inh_a_response(self, inh_a_response):
        self._inh_a_response = utility_calls.convert_param_to_numpy(
            inh_a_response, self._n_neurons)

    @property
    def inh_a_a(self):
        return self._inh_a_a

    @inh_a_a.setter
    def inh_a_a(self, inh_a_a):
        self._inh_a_a = utility_calls.convert_param_to_numpy(
            inh_a_a, self._n_neurons)

    @property
    def inh_a_tau(self):
        return self._inh_a_tau

    @inh_a_tau.setter
    def inh_a_tau(self, inh_a_tau):
        self._inh_a_tau = utility_calls.convert_param_to_numpy(
            inh_a_tau, self._n_neurons)
        self.inh_a_a, self.inh_b_B = set_inhitatory_scalar(self._inh_a_tau, self._inh_b_tau)

    @property
    def inh_b_response(self):
        return self._inh_b_response

    @inh_b_response.setter
    def inh_b_response(self, inh_b_response):
        self._inh_b_response = utility_calls.convert_param_to_numpy(
            inh_b_response, self._n_neurons)

    @property
    def inh_b_B(self):
        return self._inh_b_B

    @inh_b_B.setter
    def inh_b_B(self, inh_b_B):
        self._inh_b_B = utility_calls.convert_param_to_numpy(
            inh_b_B, self._n_neurons)

    @property
    def inh_b_tau(self):
        return self._inh_b_tau

    @inh_b_tau.setter
    def inh_b_tau(self, inh_b_tau):
        self._inh_b_tau = utility_calls.convert_param_to_numpy(
            inh_b_tau, self._n_neurons)
        self.inh_a_a, self.inh_b_B = set_inhitatory_scalar(self._inh_a_tau, self._inh_b_tau)

    # inhibitory2
    @property
    def inh2_a_response(self):
        return self._inh2_a_response

    @inh2_a_response.setter
    def inh2_a_response(self, inh2_a_response):
        self._inh2_a_response = utility_calls.convert_param_to_numpy(
            inh2_a_response, self._n_neurons)

    @property
    def inh2_a_a(self):
        return self._inh2_a_a

    @inh2_a_a.setter
    def inh2_a_a(self, inh2_a_a):
        self._inh2_a_a = utility_calls.convert_param_to_numpy(
            inh2_a_a, self._n_neurons)

    @property
    def inh2_a_tau(self):
        return self._inh2_a_tau

    @inh2_a_tau.setter
    def inh2_a_tau(self, inh2_a_tau):
        self._inh2_a_tau = utility_calls.convert_param_to_numpy(
            inh2_a_tau, self._n_neurons)
        self.inh2_a_a, self.inh2_b_B = set_inhitatory_scalar(self._inh2_a_tau, self._inh2_b_tau)

    @property
    def inh2_b_response(self):
        return self._inh2_b_response

    @inh2_b_response.setter
    def inh2_b_response(self, inh2_b_response):
        self._inh2_b_response = utility_calls.convert_param_to_numpy(
            inh2_b_response, self._n_neurons)

    @property
    def inh2_b_B(self):
        return self._inh2_b_B

    @inh2_b_B.setter
    def inh2_b_B(self, inh2_b_B):
        self._inh2_b_B = utility_calls.convert_param_to_numpy(
            inh2_b_B, self._n_neurons)

    @property
    def inh2_b_tau(self):
        return self._inh2_b_tau

    @inh2_b_tau.setter
    def inh2_b_tau(self, inh2_b_tau):
        self._inh2_b_tau = utility_calls.convert_param_to_numpy(
            inh2_b_tau, self._n_neurons)
        self.inh2_a_a, self.inh2_b_B = set_inhitatory_scalar(self._inh2_a_tau, self._inh2_b_tau)


    def get_n_synapse_types(self):
        return 4 # EX, EX_2 and INH, INH_2

    def get_synapse_id_by_target(self, target):

        if target == "inhitatory":
            return 0
        if target == "inhitatory2":
            return 1
        elif target == "inhibitory":
            return 2
        elif target == "inhibitory2":
            return 3
        return None

    def get_synapse_targets(self):
        return "inhitatory", "inhitatory2", "inhibitory", "inhibitory2"

    def get_n_synapse_type_parameters(self):
        return 4*8

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_synapse_type_parameters(self, machine_time_step):
        # do we still need the init adjustment if using the alpha-shape
        # synapse?
        e_a_decay, e_a_init = get_exponential_decay_and_init(
            self._inh_a_tau, machine_time_step)
        e_b_decay, e_b_init = get_exponential_decay_and_init(
            self._inh_b_tau, machine_time_step)

        e2_a_decay, e2_a_init = get_exponential_decay_and_init(
            self._inh2_a_tau, machine_time_step)
        e2_b_decay, e2_b_init = get_exponential_decay_and_init(
            self._inh2_b_tau, machine_time_step)

        i_a_decay, i_a_init = get_exponential_decay_and_init(
            self._inh_a_tau, machine_time_step)
        i_b_decay, i_b_init = get_exponential_decay_and_init(
            self._inh_b_tau, machine_time_step)

        i2_a_decay, i2_a_init = get_exponential_decay_and_init(
            self._inh2_a_tau, machine_time_step)
        i2_b_decay, i2_b_init = get_exponential_decay_and_init(
            self._inh2_b_tau, machine_time_step)


        return [
            # inhitatory
            NeuronParameter(self._inh_a_response,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            NeuronParameter(self._inh_a_a, _COMB_EXP_TYPES.CONST.data_type),
            NeuronParameter(e_a_decay, _COMB_EXP_TYPES.DECaY.data_type),
            NeuronParameter(e_a_init, _COMB_EXP_TYPES.INIT.data_type),
            NeuronParameter(self._inh_b_response,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            NeuronParameter(self._inh_b_B, _COMB_EXP_TYPES.CONST.data_type),
            NeuronParameter(e_b_decay, _COMB_EXP_TYPES.DECaY.data_type),
            NeuronParameter(e_b_init, _COMB_EXP_TYPES.INIT.data_type),

            # inhitatory2
            NeuronParameter(self._inh2_a_response,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            NeuronParameter(self._inh2_a_a, _COMB_EXP_TYPES.CONST.data_type),
            NeuronParameter(e2_a_decay, _COMB_EXP_TYPES.DECaY.data_type),
            NeuronParameter(e2_a_init, _COMB_EXP_TYPES.INIT.data_type),
            NeuronParameter(self._inh2_b_response,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            NeuronParameter(self._inh2_b_B, _COMB_EXP_TYPES.CONST.data_type),
            NeuronParameter(e2_b_decay, _COMB_EXP_TYPES.DECaY.data_type),
            NeuronParameter(e2_b_init, _COMB_EXP_TYPES.INIT.data_type),

            # inhibitory
            NeuronParameter(self._inh_a_response,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            NeuronParameter(self._inh_a_a, _COMB_EXP_TYPES.CONST.data_type),
            NeuronParameter(i_a_decay, _COMB_EXP_TYPES.DECaY.data_type),
            NeuronParameter(i_a_init, _COMB_EXP_TYPES.INIT.data_type),
            NeuronParameter(self._inh_b_response,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            NeuronParameter(self._inh_b_B, _COMB_EXP_TYPES.CONST.data_type),
            NeuronParameter(i_b_decay, _COMB_EXP_TYPES.DECaY.data_type),
            NeuronParameter(i_b_init, _COMB_EXP_TYPES.INIT.data_type),

            # inhibitory2
            NeuronParameter(self._inh2_a_response,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            NeuronParameter(self._inh2_a_a, _COMB_EXP_TYPES.CONST.data_type),
            NeuronParameter(i2_a_decay, _COMB_EXP_TYPES.DECaY.data_type),
            NeuronParameter(i2_a_init, _COMB_EXP_TYPES.INIT.data_type),
            NeuronParameter(self._inh2_b_response,
                            _COMB_EXP_TYPES.RESPONSE.data_type),
            NeuronParameter(self._inh2_b_B, _COMB_EXP_TYPES.CONST.data_type),
            NeuronParameter(i2_b_decay, _COMB_EXP_TYPES.DECaY.data_type),
            NeuronParameter(i2_b_init, _COMB_EXP_TYPES.INIT.data_type)
        ]

    def get_synapse_type_parameter_types(self):

        # TODO: update to return the parameter types
        return [item.data_type for item in _COMB_EXP_TYPES]

    def get_n_cpu_cycles_per_neuron(self):
        # a guess
        return 100
