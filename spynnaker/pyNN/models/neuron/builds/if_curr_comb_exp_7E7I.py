from spynnaker.pyNN.models.neuron.neuron_models\
    .neuron_model_leaky_integrate_and_fire \
    import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_comb_exp_7E7I\
    import SynapseTypeCombExp7E7I
from spynnaker.pyNN.models.neuron.input_types.input_type_current_pfc \
    import InputTypeCurrentPfc
from spynnaker.pyNN.models.neuron.threshold_types.threshold_type_static \
    import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.abstract_population_vertex \
    import AbstractPopulationVertex
import numpy

class IFCurrCombExp7E7I(AbstractPopulationVertex):
    """ Leaky integrate and fire neuron with 7 excitatory and 7 inhibitory\
        synapses, each comprised of a combination of exponential functions:\
        synaptic response = Ae^(-t/tau_a) + Be^(-t/tau_b)
    """

    _max_feasible_max_atoms_per_core = 32
    _model_based_max_atoms_per_core = _max_feasible_max_atoms_per_core

    baseline_defaults = {
        'x_a_response': 0,
        'x_a_A': 1,
        'x_a_tau': 5,
        'x_b_response': 0,
        'x_b_B': -1,
        'x_b_tau': 1,

        'i_a_response': 0,
        'i_a_A': 1,
        'i_a_tau': 5,
        'i_b_response': 0,
        'i_b_B': -1,
        'i_b_tau': 1
        }


    default_parameters = {
        'tau_m': 20.0,
        'cm': 1.0,
        'v_rest': -65.0,
        'v_reset': -65.0,
        'v_thresh': -50.0,

        ##### synapse parameters #####
        # excitatory
        'exc_a_response':baseline_defaults['x_a_response'],
        'exc_a_A':baseline_defaults['x_a_A'],
        'exc_a_tau':baseline_defaults['x_a_tau'],
        'exc_b_response':baseline_defaults['x_b_response'],
        'exc_b_B':baseline_defaults['x_b_B'],
        'exc_b_tau':baseline_defaults['x_b_tau'],

        # excitatory2
        'exc2_a_response':baseline_defaults['x_a_response'],
        'exc2_a_A':baseline_defaults['x_a_A'],
        'exc2_a_tau':baseline_defaults['x_a_tau'],
        'exc2_b_response':baseline_defaults['x_b_response'],
        'exc2_b_B':baseline_defaults['x_b_B'],
        'exc2_b_tau':baseline_defaults['x_b_tau'],

        # excitatory3
        'exc3_a_response':baseline_defaults['x_a_response'],
        'exc3_a_A':baseline_defaults['x_a_A'],
        'exc3_a_tau':baseline_defaults['x_a_tau'],
        'exc3_b_response':baseline_defaults['x_b_response'],
        'exc3_b_B':baseline_defaults['x_b_B'],
        'exc3_b_tau':baseline_defaults['x_b_tau'],

        # excitatory4
        'exc4_a_response':baseline_defaults['x_a_response'],
        'exc4_a_A':baseline_defaults['x_a_A'],
        'exc4_a_tau':baseline_defaults['x_a_tau'],
        'exc4_b_response':baseline_defaults['x_b_response'],
        'exc4_b_B':baseline_defaults['x_b_B'],
        'exc4_b_tau':baseline_defaults['x_b_tau'],

        # excitatory5
        'exc5_a_response':baseline_defaults['x_a_response'],
        'exc5_a_A':baseline_defaults['x_a_A'],
        'exc5_a_tau':baseline_defaults['x_a_tau'],
        'exc5_b_response':baseline_defaults['x_b_response'],
        'exc5_b_B':baseline_defaults['x_b_B'],
        'exc5_b_tau':baseline_defaults['x_b_tau'],

        # excitatory6
        'exc6_a_response':baseline_defaults['x_a_response'],
        'exc6_a_A':baseline_defaults['x_a_A'],
        'exc6_a_tau':baseline_defaults['x_a_tau'],
        'exc6_b_response':baseline_defaults['x_b_response'],
        'exc6_b_B':baseline_defaults['x_b_B'],
        'exc6_b_tau':baseline_defaults['x_b_tau'],

        # excitatory7
        'exc7_a_response':baseline_defaults['x_a_response'],
        'exc7_a_A':baseline_defaults['x_a_A'],
        'exc7_a_tau':baseline_defaults['x_a_tau'],
        'exc7_b_response':baseline_defaults['x_b_response'],
        'exc7_b_B':baseline_defaults['x_b_B'],
        'exc7_b_tau':baseline_defaults['x_b_tau'],

        # inhibitory
        'inh_a_response':baseline_defaults['i_a_response'],
        'inh_a_A':baseline_defaults['i_a_A'],
        'inh_a_tau':baseline_defaults['i_a_tau'],
        'inh_b_response':baseline_defaults['i_b_response'],
        'inh_b_B':baseline_defaults['i_b_B'],
        'inh_b_tau':baseline_defaults['i_b_tau'],

        # inhibitory2
        'inh2_a_response':baseline_defaults['i_a_response'],
        'inh2_a_A':baseline_defaults['i_a_A'],
        'inh2_a_tau':baseline_defaults['i_a_tau'],
        'inh2_b_response':baseline_defaults['i_b_response'],
        'inh2_b_B':baseline_defaults['i_b_B'],
        'inh2_b_tau':baseline_defaults['i_b_tau'],

        # inhibitory3
        'inh3_a_response':baseline_defaults['i_a_response'],
        'inh3_a_A':baseline_defaults['i_a_A'],
        'inh3_a_tau':baseline_defaults['i_a_tau'],
        'inh3_b_response':baseline_defaults['i_b_response'],
        'inh3_b_B':baseline_defaults['i_b_B'],
        'inh3_b_tau':baseline_defaults['i_b_tau'],

        # inhibitory4
        'inh4_a_response':baseline_defaults['i_a_response'],
        'inh4_a_A':baseline_defaults['i_a_A'],
        'inh4_a_tau':baseline_defaults['i_a_tau'],
        'inh4_b_response':baseline_defaults['i_b_response'],
        'inh4_b_B':baseline_defaults['i_b_B'],
        'inh4_b_tau':baseline_defaults['i_b_tau'],

        # inhibitory5
        'inh5_a_response':baseline_defaults['i_a_response'],
        'inh5_a_A':baseline_defaults['i_a_A'],
        'inh5_a_tau':baseline_defaults['i_a_tau'],
        'inh5_b_response':baseline_defaults['i_b_response'],
        'inh5_b_B':baseline_defaults['i_b_B'],
        'inh5_b_tau':baseline_defaults['i_b_tau'],

        # inhibitory6
        'inh6_a_response':baseline_defaults['i_a_response'],
        'inh6_a_A':baseline_defaults['i_a_A'],
        'inh6_a_tau':baseline_defaults['i_a_tau'],
        'inh6_b_response':baseline_defaults['i_b_response'],
        'inh6_b_B':baseline_defaults['i_b_B'],
        'inh6_b_tau':baseline_defaults['i_b_tau'],

        # inhibitory7
        'inh7_a_response':baseline_defaults['i_a_response'],
        'inh7_a_A':baseline_defaults['i_a_A'],
        'inh7_a_tau':baseline_defaults['i_a_tau'],
        'inh7_b_response':baseline_defaults['i_b_response'],
        'inh7_b_B':baseline_defaults['i_b_B'],
        'inh7_b_tau':baseline_defaults['i_b_tau'],



        ##############################

        'tau_refrac': 0.1,
        'i_offset': 0}

    def __init__(
            self, n_neurons, spikes_per_second=None, ring_buffer_sigma=None,
            incoming_spike_buffer_size=None, constraints=None, label=None,
            tau_m=default_parameters['tau_m'], cm=default_parameters['cm'],
            v_rest=default_parameters['v_rest'],
            v_reset=default_parameters['v_reset'],
            v_thresh=default_parameters['v_thresh'],

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

            # excitatory3
            exc3_a_response=default_parameters['exc3_a_response'],
            exc3_a_A=default_parameters['exc3_a_A'],
            exc3_a_tau=default_parameters['exc3_a_tau'],
            exc3_b_response=default_parameters['exc3_b_response'],
            exc3_b_B=default_parameters['exc3_b_B'],
            exc3_b_tau=default_parameters['exc3_b_tau'],

            # excitatory4
            exc4_a_response=default_parameters['exc4_a_response'],
            exc4_a_A=default_parameters['exc4_a_A'],
            exc4_a_tau=default_parameters['exc4_a_tau'],
            exc4_b_response=default_parameters['exc4_b_response'],
            exc4_b_B=default_parameters['exc4_b_B'],
            exc4_b_tau=default_parameters['exc4_b_tau'],

            # excitatory5
            exc5_a_response=default_parameters['exc5_a_response'],
            exc5_a_A=default_parameters['exc5_a_A'],
            exc5_a_tau=default_parameters['exc5_a_tau'],
            exc5_b_response=default_parameters['exc5_b_response'],
            exc5_b_B=default_parameters['exc5_b_B'],
            exc5_b_tau=default_parameters['exc5_b_tau'],

            # excitatory6
            exc6_a_response=default_parameters['exc6_a_response'],
            exc6_a_A=default_parameters['exc6_a_A'],
            exc6_a_tau=default_parameters['exc6_a_tau'],
            exc6_b_response=default_parameters['exc6_b_response'],
            exc6_b_B=default_parameters['exc6_b_B'],
            exc6_b_tau=default_parameters['exc6_b_tau'],

            # excitatory7
            exc7_a_response=default_parameters['exc7_a_response'],
            exc7_a_A=default_parameters['exc7_a_A'],
            exc7_a_tau=default_parameters['exc7_a_tau'],
            exc7_b_response=default_parameters['exc7_b_response'],
            exc7_b_B=default_parameters['exc7_b_B'],
            exc7_b_tau=default_parameters['exc7_b_tau'],

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

            # inhibitory3
            inh3_a_response=default_parameters['inh3_a_response'],
            inh3_a_A=default_parameters['inh3_a_A'],
            inh3_a_tau=default_parameters['inh3_a_tau'],
            inh3_b_response=default_parameters['inh3_b_response'],
            inh3_b_B=default_parameters['inh3_b_B'],
            inh3_b_tau=default_parameters['inh3_b_tau'],

            # inhibitory4
            inh4_a_response=default_parameters['inh4_a_response'],
            inh4_a_A=default_parameters['inh4_a_A'],
            inh4_a_tau=default_parameters['inh4_a_tau'],
            inh4_b_response=default_parameters['inh4_b_response'],
            inh4_b_B=default_parameters['inh4_b_B'],
            inh4_b_tau=default_parameters['inh4_b_tau'],

            # inhibitory5
            inh5_a_response=default_parameters['inh5_a_response'],
            inh5_a_A=default_parameters['inh5_a_A'],
            inh5_a_tau=default_parameters['inh5_a_tau'],
            inh5_b_response=default_parameters['inh5_b_response'],
            inh5_b_B=default_parameters['inh5_b_B'],
            inh5_b_tau=default_parameters['inh5_b_tau'],

            # inhibitory6
            inh6_a_response=default_parameters['inh6_a_response'],
            inh6_a_A=default_parameters['inh6_a_A'],
            inh6_a_tau=default_parameters['inh6_a_tau'],
            inh6_b_response=default_parameters['inh6_b_response'],
            inh6_b_B=default_parameters['inh6_b_B'],
            inh6_b_tau=default_parameters['inh6_b_tau'],

            # inhibitory7
            inh7_a_response=default_parameters['inh7_a_response'],
            inh7_a_A=default_parameters['inh7_a_A'],
            inh7_a_tau=default_parameters['inh7_a_tau'],
            inh7_b_response=default_parameters['inh7_b_response'],
            inh7_b_B=default_parameters['inh7_b_B'],
            inh7_b_tau=default_parameters['inh7_b_tau'],

            tau_refrac=default_parameters['tau_refrac'],
            i_offset=default_parameters['i_offset'], v_init=None):


        # Construct neuron/synapse objects
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            n_neurons, v_init, v_rest, tau_m, cm, i_offset,
            v_reset, tau_refrac)

        synapse_type = SynapseTypeCombExp7E7I(
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

                # excitatory3
                exc3_a_response,
                exc3_a_A,
                exc3_a_tau,
                exc3_b_response,
                exc3_b_B,
                exc3_b_tau,

                # excitatory4
                exc4_a_response,
                exc4_a_A,
                exc4_a_tau,
                exc4_b_response,
                exc4_b_B,
                exc4_b_tau,

                # excitatory5
                exc5_a_response,
                exc5_a_A,
                exc5_a_tau,
                exc5_b_response,
                exc5_b_B,
                exc5_b_tau,

                # excitatory6
                exc6_a_response,
                exc6_a_A,
                exc6_a_tau,
                exc6_b_response,
                exc6_b_B,
                exc6_b_tau,

                # excitatory7
                exc7_a_response,
                exc7_a_A,
                exc7_a_tau,
                exc7_b_response,
                exc7_b_B,
                exc7_b_tau,

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
                inh2_b_tau,

                # inhibitory3
                inh3_a_response,
                inh3_a_A,
                inh3_a_tau,
                inh3_b_response,
                inh3_b_B,
                inh3_b_tau,

                # inhibitory4
                inh4_a_response,
                inh4_a_A,
                inh4_a_tau,
                inh4_b_response,
                inh4_b_B,
                inh4_b_tau,

                # inhibitory5
                inh5_a_response,
                inh5_a_A,
                inh5_a_tau,
                inh5_b_response,
                inh5_b_B,
                inh5_b_tau,

                # inhibitory5
                inh6_a_response,
                inh6_a_A,
                inh6_a_tau,
                inh6_b_response,
                inh6_b_B,
                inh6_b_tau,

                # inhibitory5
                inh7_a_response,
                inh7_a_A,
                inh7_a_tau,
                inh7_b_response,
                inh7_b_B,
                inh7_b_tau)

        input_type = InputTypeCurrentPfc()
        threshold_type = ThresholdTypeStatic(n_neurons, v_thresh)

        AbstractPopulationVertex.__init__(
            self, n_neurons=n_neurons, binary="IF_curr_comb_exp_7E7I.aplx", label=label,
            max_atoms_per_core=IFCurrCombExp7E7I._model_based_max_atoms_per_core,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            model_name="IF_curr_comb_exp_7E7I", neuron_model=neuron_model,
            input_type=input_type, synapse_type=synapse_type,
            threshold_type=threshold_type, constraints=constraints, max_feasible_atoms_per_core=IFCurrCombExp7E7I._max_feasible_max_atoms_per_core)

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IFCurrCombExp7E7I._model_based_max_atoms_per_core = new_value
        print "Adjusting neurons per core to: {}".format(new_value)

    @staticmethod
    def get_max_atoms_per_core():
        return IFCurrCombExp7E7I._model_based_max_atoms_per_core

