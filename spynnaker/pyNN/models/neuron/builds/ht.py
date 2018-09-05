from spynnaker.pyNN.models.neuron.neuron_models \
    import NeuronModelHT
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeHT
from spynnaker.pyNN.models.neuron.input_types import InputTypeHTConductance
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeHTDynamic
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

        # #### Neuron model #####
        'g_Na': 0.2,
        'E_Na': 30.0,
        'g_K': 1.85,
        'E_K': -90.0,
        'tau_m': 16,
        'i_offset': 0.0,
        'g_spike': 1.0,
        'tau_spike': 1.75,
        't_spike': 2.0,

        # #### Threshold #####
        'v_thresh': -50,
        'v_thresh_resting': -50,
        'v_thresh_tau': 2,
        'v_thresh_Na_reversal': 30,

        # ##### Synapse Model #####
        # AMPA - excitatory
        'exc_a_response': 0, 'exc_a_A': 1, 'exc_a_tau': 0.5,
        'exc_b_response': 0, 'exc_b_B': -1, 'exc_b_tau': 2.4,
        # NMDA - excitatory2
        'exc2_a_response': 0, 'exc2_a_A': 1, 'exc2_a_tau': 4,
        'exc2_b_response': 0, 'exc2_b_B': -1, 'exc2_b_tau': 40,
        # GABA_A - inhibitory
        'inh_a_response': 0, 'inh_a_A': 1, 'inh_a_tau': 1,
        'inh_b_response': 0, 'inh_b_B': -1, 'inh_b_tau': 7,
        # GABA_B - inhibitory2
        'inh2_a_response': 0, 'inh2_a_A': 1, 'inh2_a_tau': 60,
        'inh2_b_response': 0, 'inh2_b_B': -1, 'inh2_b_tau': 200,

        # #### Input Type ####
        'ampa_rev_E': 0,
        'nmda_rev_E': 0,
        'gaba_a_rev_E': -70,
        'gaba_b_rev_E': -90

        }

    initialize_parameters = {'v_init': -78.25}

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

            g_spike=default_parameters['g_spike'],
            tau_spike=default_parameters['tau_spike'],
            t_spike=default_parameters['t_spike'],


            # #### Threshold Paramters ####
            v_thresh=default_parameters['v_thresh'],
            v_thresh_resting=default_parameters['v_thresh_resting'],
            v_thresh_tau=default_parameters['v_thresh_tau'],
            v_thresh_Na_reversal=default_parameters['v_thresh_Na_reversal'],


            # #### Synapse parameters ####
            # AMPA - excitatory
            exc_a_response=default_parameters['exc_a_response'],
            exc_a_A=default_parameters['exc_a_A'],
            exc_a_tau=default_parameters['exc_a_tau'],
            exc_b_response=default_parameters['exc_b_response'],
            exc_b_B=default_parameters['exc_b_B'],
            exc_b_tau=default_parameters['exc_b_tau'],

            # NMDA - excitatory2
            exc2_a_response=default_parameters['exc2_a_response'],
            exc2_a_A=default_parameters['exc2_a_A'],
            exc2_a_tau=default_parameters['exc2_a_tau'],
            exc2_b_response=default_parameters['exc2_b_response'],
            exc2_b_B=default_parameters['exc2_b_B'],
            exc2_b_tau=default_parameters['exc2_b_tau'],

            # GABA_A - inhibitory
            inh_a_response=default_parameters['inh_a_response'],
            inh_a_A=default_parameters['inh_a_A'],
            inh_a_tau=default_parameters['inh_a_tau'],
            inh_b_response=default_parameters['inh_b_response'],
            inh_b_B=default_parameters['inh_b_B'],
            inh_b_tau=default_parameters['inh_b_tau'],

            # GABA_B - inhibitory2
            inh2_a_response=default_parameters['inh2_a_response'],
            inh2_a_A=default_parameters['inh2_a_A'],
            inh2_a_tau=default_parameters['inh2_a_tau'],
            inh2_b_response=default_parameters['inh2_b_response'],
            inh2_b_B=default_parameters['inh2_b_B'],
            inh2_b_tau=default_parameters['inh2_b_tau'],

            # #### Input Type ####
            ampa_rev_E=default_parameters['ampa_rev_E'],
            nmda_rev_E=default_parameters['nmda_rev_E'],
            gaba_a_rev_E=default_parameters['gaba_a_rev_E'],
            gaba_b_rev_E=default_parameters['gaba_b_rev_E']
            ):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelHT(
            n_neurons,
            v_init,
            g_Na,
            E_Na,
            g_K,
            E_K,
            tau_m,
            g_spike,
            tau_spike,
            t_spike,
            i_offset)

        synapse_type = SynapseTypeHT(
            n_neurons,
            # AMPA - excitatory
            exc_a_response,
            exc_a_A,
            exc_a_tau,
            exc_b_response,
            exc_b_B,
            exc_b_tau,
            # NMDA - excitatory2
            exc2_a_response,
            exc2_a_A,
            exc2_a_tau,
            exc2_b_response,
            exc2_b_B,
            exc2_b_tau,
            # GABA_A - inhibitory
            inh_a_response,
            inh_a_A,
            inh_a_tau,
            inh_b_response,
            inh_b_B,
            inh_b_tau,
            # GABA_B - inhibitory2
            inh2_a_response,
            inh2_a_A,
            inh2_a_tau,
            inh2_b_response,
            inh2_b_B,
            inh2_b_tau
            )

        input_type = InputTypeHTConductance(
            n_neurons,
            ampa_rev_E,
            nmda_rev_E,
            gaba_a_rev_E,
            gaba_b_rev_E)

        threshold_type = ThresholdTypeHTDynamic(n_neurons,
                                                v_thresh,
                                                v_thresh_resting,
                                                v_thresh_tau,
                                                v_thresh_Na_reversal)

        super(HillTononiNeuron, self).__init__(
            n_neurons=n_neurons, binary="ht.aplx", label=label,
            max_atoms_per_core=HillTononiNeuron.
                                        _model_based_max_atoms_per_core,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            model_name="ht", neuron_model=neuron_model,
            input_type=input_type, synapse_type=synapse_type,
            threshold_type=threshold_type,
            constraints=constraints)

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
