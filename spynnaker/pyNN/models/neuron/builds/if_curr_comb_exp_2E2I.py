from spynnaker.pyNN.models.neuron.neuron_models\
    .neuron_model_leaky_integrate_and_fire_v_hist \
    import NeuronModelLeakyIntegrateAndFireVHist
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_comb_exp_2E2I\
    import SynapseTypeCombExp2E2I
from spynnaker.pyNN.models.neuron.input_types.input_type_current \
    import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types.threshold_type_static \
    import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.abstract_population_vertex \
    import AbstractPopulationVertex
import numpy

class IFCurrCombExp2E2I(AbstractPopulationVertex):
    """ Leaky integrate and fire neuron with 2 excitatory and 2 inhibitory\
        synapses, each comprised of a combination of exponential functions:\
        synaptic response = Ae^(-t/tau_a) + Be^(-t/tau_b)
    """

    _model_based_max_atoms_per_core = 32
    _max_feasible_max_atoms_per_core = 32

    default_parameters = {
        'tau_m': 20.0,
        'cm': 1.0,
        'v_rest': -65.0,
        'v_reset': -65.0,
        'v_thresh': -50.0,
        'tau_refrac': 0.1,
        'i_offset': 0,
        'v_hist':0,

        ##### synapse parameters #####
        # excitatory
        'exc_a_response':0,
        'exc_a_A':1,
        'exc_a_tau': 5,
        'exc_b_response':0,
        'exc_b_B':-1,
        'exc_b_tau': 1,
        # excitatory2
        'exc2_a_response':0,
        'exc2_a_A':1,
        'exc2_a_tau': 5,
        'exc2_b_response':0,
        'exc2_b_B':-1,
        'exc2_b_tau': 1,
        # inhibitory
        'inh_a_response': 0,
        'inh_a_A':1,
        'inh_a_tau': 5,
        'inh_b_response':0,
        'inh_b_B':-1,
        'inh_b_tau': 1,
        # inhibitory2
        'inh2_a_response': 0,
        'inh2_a_A':1,
        'inh2_a_tau': 5,
        'inh2_b_response':0,
        'inh2_b_B':-1,
        'inh2_b_tau': 1}
        ##############################


    def __init__(
            self, n_neurons, spikes_per_second=None, ring_buffer_sigma=None,
            incoming_spike_buffer_size=None, constraints=None, label=None,
            tau_m=default_parameters['tau_m'], cm=default_parameters['cm'],
            v_rest=default_parameters['v_rest'],
            v_reset=default_parameters['v_reset'],
            v_thresh=default_parameters['v_thresh'],
            v_hist=default_parameters['v_hist'],

            # excitatory
            exc_a_response=default_parameters['exc_a_response'],
            exc_a_A=default_parameters['exc_a_A'],
            exc_a_tau=default_parameters['exc_a_tau'],
            exc_b_response=default_parameters['exc_b_response'],
            exc_b_B=default_parameters['exc_b_B'],
            exc_b_tau=default_parameters['exc_b_tau'],

            # excitatory2
            exc2_a_response=default_parameters['exc2_a_response'],
            exc2_a_A=default_parameters['exc2_a_A'],
            exc2_a_tau=default_parameters['exc2_a_tau'],
            exc2_b_response=default_parameters['exc2_b_response'],
            exc2_b_B=default_parameters['exc2_b_B'],
            exc2_b_tau=default_parameters['exc2_b_tau'],

            # inhibitory
            inh_a_response=default_parameters['inh_a_response'],
            inh_a_A=default_parameters['inh_a_A'],
            inh_a_tau=default_parameters['inh_a_tau'],
            inh_b_response=default_parameters['inh_b_response'],
            inh_b_B=default_parameters['inh_b_B'],
            inh_b_tau=default_parameters['inh_b_tau'],

            # inhibitory2
            inh2_a_response=default_parameters['inh2_a_response'],
            inh2_a_A=default_parameters['inh2_a_A'],
            inh2_a_tau=default_parameters['inh2_a_tau'],
            inh2_b_response=default_parameters['inh2_b_response'],
            inh2_b_B=default_parameters['inh2_b_B'],
            inh2_b_tau=default_parameters['inh2_b_tau'],

            tau_refrac=default_parameters['tau_refrac'],
            i_offset=default_parameters['i_offset'], v_init=None):


        # Construct neuron/synapse objects
        neuron_model = NeuronModelLeakyIntegrateAndFireVHist(
            n_neurons, v_init, v_rest, tau_m, cm, i_offset,
            v_reset, tau_refrac, v_hist)

        synapse_type = SynapseTypeCombExp2E2I(
                n_neurons,

                # excitatory
                exc_a_response,
                exc_a_A,
                exc_a_tau,
                exc_b_response,
                exc_b_B,
                exc_b_tau,

                # excitatory2
                exc2_a_response,
                exc2_a_A,
                exc2_a_tau,
                exc2_b_response,
                exc2_b_B,
                exc2_b_tau,

                # inhibitory
                inh_a_response,
                inh_a_A,
                inh_a_tau,
                inh_b_response,
                inh_b_B,
                inh_b_tau,

                # inhibitory2
                inh2_a_response,
                inh2_a_A,
                inh2_a_tau,
                inh2_b_response,
                inh2_b_B,
                inh2_b_tau)

        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(n_neurons, v_thresh)

        AbstractPopulationVertex.__init__(
            self, n_neurons=n_neurons, binary="IF_curr_comb_exp_2E2I.aplx", label=label,
            max_atoms_per_core=IFCurrCombExp2E2I._model_based_max_atoms_per_core,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            model_name="IF_curr_comb_exp_2E2I", neuron_model=neuron_model,
            input_type=input_type, synapse_type=synapse_type,
            threshold_type=threshold_type, constraints=constraints, max_feasible_atoms_per_core=IFCurrCombExp2E2I._max_feasible_max_atoms_per_core)

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IFCurrCombExp2E2I._model_based_max_atoms_per_core = new_value
        print "neurons per core changed to: {}".format(new_value)

    @staticmethod
    def get_max_atoms_per_core():
        return IFCurrCombExp2E2I._model_based_max_atoms_per_core

