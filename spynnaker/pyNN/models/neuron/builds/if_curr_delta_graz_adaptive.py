from spynnaker.pyNN.models.neuron.neuron_models \
    import NeuronModelLeakyIntegrateAndFireGrazAdaptive
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeDelta
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeAdaptive
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex

# global objects
DEFAULT_MAX_ATOMS_PER_CORE = 255
_apv_defs = AbstractPopulationVertex.non_pynn_default_parameters


class IFCurrDeltaGrazAdaptive(AbstractPopulationVertex):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        current input, and adaptive threshold which increases on spiking
        before decaying back to a baseline threshold.
    """

    _model_based_max_atoms_per_core = DEFAULT_MAX_ATOMS_PER_CORE

    default_parameters = {
        'tau_m': 20.0, 'cm': 1.0, 'v_rest': -65.0, 'v_reset': -65.0,

        # Adaptive threshold parameters
        'thresh_B': 10,
        "thresh_b": 0,
        "thresh_b_0": 10,
        "thresh_tau_a": 500,
        "thresh_beta": 1.8,

#         'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
        'tau_refrac': 0.1, 'i_offset': 0,

        # Synapse type parameters
        'isyn_exc': 0.0, 'isyn_inh': 0.0}

    initialize_parameters = {'v_init': None}

    def __init__(
            self, n_neurons,
            spikes_per_second=_apv_defs['spikes_per_second'],
            ring_buffer_sigma=_apv_defs['ring_buffer_sigma'],
            incoming_spike_buffer_size=_apv_defs['incoming_spike_buffer_size'],
            constraints=_apv_defs['constraints'],
            label=_apv_defs['label'],
            tau_m=default_parameters['tau_m'],
            cm=default_parameters['cm'],
            v_rest=default_parameters['v_rest'],
            v_reset=default_parameters['v_reset'],

            #Adaptive threshold parameters
            thresh_B=default_parameters['thresh_B'],
            thresh_b=default_parameters['thresh_b'],
            thresh_b_0=default_parameters['thresh_b_0'],
            thresh_tau_a=default_parameters['thresh_tau_a'],
            thresh_beta=default_parameters['thresh_beta'],

#             tau_syn_E=default_parameters['tau_syn_E'],
#             tau_syn_I=default_parameters['tau_syn_I'],
            tau_refrac=default_parameters['tau_refrac'],
            i_offset=default_parameters['i_offset'],
            v_init=initialize_parameters['v_init'],
            isyn_exc=default_parameters['isyn_exc'],
            isyn_inh=default_parameters['isyn_inh']):
        # pylint: disable=too-many-arguments, too-many-locals

        neuron_model = NeuronModelLeakyIntegrateAndFireGrazAdaptive(
            n_neurons, v_init, v_rest, tau_m, cm, i_offset,
            v_reset, tau_refrac)

        synapse_type = SynapseTypeDelta(
            n_neurons=n_neurons, initial_input_inh=isyn_inh,
            initial_input_exc=isyn_exc)


        input_type = InputTypeCurrent()

        threshold_type = ThresholdTypeAdaptive(n_neurons,
                                               thresh_B,
                                               thresh_b,
                                               thresh_b_0,
                                               thresh_tau_a,
                                               thresh_beta)

        super(IFCurrDeltaGrazAdaptive, self).__init__(
            n_neurons=n_neurons, binary="IF_curr_delta_graz_adaptive.aplx", label=label,
            max_atoms_per_core=IFCurrDeltaGrazAdaptive._model_based_max_atoms_per_core,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            model_name="IF_curr_delta_graz_adaptive", neuron_model=neuron_model,
            input_type=input_type, synapse_type=synapse_type,
            threshold_type=threshold_type, constraints=constraints)

    @staticmethod
    def set_model_max_atoms_per_core(new_value=DEFAULT_MAX_ATOMS_PER_CORE):
        IFCurrDeltaGrazAdaptive._model_based_max_atoms_per_core = new_value

    @staticmethod
    def get_max_atoms_per_core():
        return IFCurrDeltaGrazAdaptive._model_based_max_atoms_per_core

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
