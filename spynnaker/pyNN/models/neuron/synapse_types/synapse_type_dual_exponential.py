from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_exponential \
    import get_exponential_decay_and_init
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.synapse_types.abstract_synapse_type \
    import AbstractSynapseType

from spynnaker.pyNN.utilities import utility_calls

from data_specification.enums.data_type import DataType


class SynapseTypeDualExponential(AbstractSynapseType):

    def __init__(self, n_neurons, machine_time_step, tau_syn_E, tau_syn_E2,
                 tau_syn_I):
        AbstractSynapseType.__init__(self)
        self._n_neurons = n_neurons
        self._machine_time_step = machine_time_step
        self._tau_syn_E = utility_calls.convert_param_to_numpy(
            tau_syn_E, n_neurons)
        self._tau_syn_E2 = utility_calls.convert_param_to_numpy(
            tau_syn_E2, n_neurons)
        self._tau_syn_I = utility_calls.convert_param_to_numpy(
            tau_syn_I, n_neurons)

    @property
    def tau_syn_E(self):
        return self._tau_syn_E

    @tau_syn_E.setter
    def tau_syn_E(self, tau_syn_E):
        self._tau_syn_E = utility_calls.convert_param_to_numpy(
            tau_syn_E, self._n_neurons)

    @property
    def tau_syn_E2(self):
        return self._tau_syn_E2

    @tau_syn_E2.setter
    def tau_syn_E2(self, tau_syn_E2):
        self._tau_syn_E2 = utility_calls.convert_param_to_numpy(
            tau_syn_E2, self._n_neurons)

    @property
    def tau_syn_I(self):
        return self._tau_syn_I

    @tau_syn_I.setter
    def tau_syn_I(self, tau_syn_I):
        self._tau_syn_E = utility_calls.convert_param_to_numpy(
            tau_syn_I, self._n_neurons)

    def get_n_synapse_types(self):
        return 3

    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "excitatory2":
            return 1
        elif target == "inhibitory":
            return 2
        return None

    def get_synapse_targets(self):
        return "excitatory", "excitatory2", "inhibitory"

    def get_n_synapse_type_parameters(self):
        return 6

    def get_synapse_type_parameters(self):
        e_decay, e_init = get_exponential_decay_and_init(
            self._tau_syn_E, self._machine_time_step)
        e_decay2, e_init2 = get_exponential_decay_and_init(
            self._tau_syn_E2, self._machine_time_step)
        i_decay, i_init = get_exponential_decay_and_init(
            self._tau_syn_I, self._machine_time_step)

        return [
            NeuronParameter(e_decay, DataType.UINT32),
            NeuronParameter(e_init, DataType.UINT32),
            NeuronParameter(e_decay2, DataType.UINT32),
            NeuronParameter(e_init2, DataType.UINT32),
            NeuronParameter(i_decay, DataType.UINT32),
            NeuronParameter(i_init, DataType.UINT32)
        ]

    def get_n_cpu_cycles_per_neuron(self):

        # A guess
        return 100
