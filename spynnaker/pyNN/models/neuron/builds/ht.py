from sklearn.linear_model.tests.test_least_angle import default_parameter
from spynnaker.pyNN.models.neuron.neuron_models \
    import NeuronModelHT
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex

# global objects
DEFAULT_MAX_ATOMS_PER_CORE = 255
_apv_defs = AbstractPopulationVertex.non_pynn_default_parameters


class HillTononiNeuron(AbstractPopulationVertex):
    """
        HT Neuron
    """

    _model_based_max_atoms_per_core = DEFAULT_MAX_ATOMS_PER_CORE

    default_parameters = {
        'g_Na': 0.2,
        'E_Na': 30.0,
        'g_K': 1.85,
        'E_K': -90.0,
        'tau_m': 16,
        'i_offset': 0.0,

        'v_thresh': -30,
        'isyn_exc': 0.0,
        'isyn_inh': 0.0,
        'tau_syn_E': 5.0,
        'tau_syn_I': 5.0}

    initialize_parameters = {'v_init': None}

    def __init__(
            self, n_neurons,
            spikes_per_second=_apv_defs['spikes_per_second'],
            ring_buffer_sigma=_apv_defs['ring_buffer_sigma'],
            incoming_spike_buffer_size=_apv_defs['incoming_spike_buffer_size'],
            constraints=_apv_defs['constraints'],
            label=_apv_defs['label'],

            # neuron model parameters
            v_init=initialize_parameters['v_init'],
            g_Na=default_parameters['g_Na'],
            E_Na=default_parameters['E_Na'],
            g_K=default_parameters['g_K'],
            E_K=default_parameters['E_K'],
            tau_m=default_parameters['tau_m'],
            i_offset=default_parameters['i_offset'],

            v_thresh=default_parameters['v_thresh'],
            tau_syn_E=default_parameters['tau_syn_E'],
            tau_syn_I=default_parameters['tau_syn_I'],
            isyn_exc=default_parameters['isyn_exc'],
            isyn_inh=default_parameters['isyn_inh']):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelHT(
            n_neurons,
            v_init,
            g_Na,
            E_Na,
            g_K,
            E_K,
            tau_m,
            i_offset)
        synapse_type = SynapseTypeExponential(
            n_neurons, tau_syn_E, tau_syn_I, isyn_exc, isyn_inh)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(n_neurons, v_thresh)

        super(HillTononiNeuron, self).__init__(
            n_neurons=n_neurons, binary="ht.aplx", label=label,
            max_atoms_per_core=HillTononiNeuron._model_based_max_atoms_per_core,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            model_name="ht", neuron_model=neuron_model,
            input_type=input_type, synapse_type=synapse_type,
            threshold_type=threshold_type, constraints=constraints)

    @staticmethod
    def set_model_max_atoms_per_core(new_value=DEFAULT_MAX_ATOMS_PER_CORE):
        HillTononiNeuron._model_based_max_atoms_per_core = new_value

    @staticmethod
    def get_max_atoms_per_core():
        return HillTononiNeuron._model_based_max_atoms_per_core

    @property
    def isyn_exc(self):
        return self.synapse_type.initial_value_exc

    @property
    def isyn_inh(self):
        return self.synapse_type.initial_value_inh

    @isyn_exc.setter
    def isyn_exc(self, new_value):
        self.synapse_type.initial_value_exc = new_value

    @isyn_inh.setter
    def isyn_inh(self, new_value):
        self.synapse_type.initial_value_inh = new_value
