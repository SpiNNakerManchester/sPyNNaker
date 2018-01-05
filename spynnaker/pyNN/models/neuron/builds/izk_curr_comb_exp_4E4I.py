from spynnaker.pyNN.models.neuron.neuron_models\
    .neuron_model_izh \
    import NeuronModelIzh
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_comb_exp_4E4I\
    import SynapseTypeCombExp4E4I
from spynnaker.pyNN.models.neuron.neuron_models import neuron_model_izh
from spynnaker.pyNN.models.neuron.input_types.input_type_current \
    import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types.threshold_type_static \
    import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.abstract_population_vertex \
    import AbstractPopulationVertex
import numpy

_IZK_THRESHOLD = 30.0
class IzkCurrCombExp4E4I(AbstractPopulationVertex):

    _max_feasible_max_atoms_per_core =  64
    _model_based_max_atoms_per_core = _max_feasible_max_atoms_per_core

    baseline_defaults = {
        'x_a_response': 0,
        'x_a_A': 1,
        'x_a_tau': 50,
        'x_b_response': 0,
        'x_b_B': -1,
        'x_b_tau': 1,

        'i_a_response': 0,
        'i_a_A': 1,
        'i_a_tau': 5,
        'i_b_response': 0,
        'i_b_B': -1,
        'i_b_tau': 10
        }


    default_parameters = {
        #'tau_m': 20.0,
        #'cm': 1.0,
        #'v_rest': -65.0,
        #'v_reset': -65.0,
        #'v_thresh': -50.0,
        'a': 0.02, 'c': -65.0, 'b': 0.2, 'd': 2.0, 'i_offset': 0,
        'u_init': -14.0, 'v_init': -70.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
        'isyn_exc': 0, 'isyn_inh': 0,

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


        ##############################

        'tau_refrac': 0.1,
        'i_offset': 0}

    def __init__(
            self, n_neurons, spikes_per_second=None, ring_buffer_sigma=None,
            incoming_spike_buffer_size=None, constraints=None, label=None,
            #tau_m=default_parameters['tau_m'],
            #cm=default_parameters['cm'],
            #v_rest=default_parameters['v_rest'],
            #v_reset=default_parameters['v_reset'],
            #v_thresh=default_parameters['v_thresh'],


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


            tau_refrac=default_parameters['tau_refrac'],
            i_offset=default_parameters['i_offset'],
            a =   default_parameters['a'],
            c =default_parameters['c'] ,
            b = default_parameters['b'],
            d = default_parameters['d'],
            u_init =  default_parameters['u_init'],
            v_init =  default_parameters['v_init']
            #tau_syn_E = default_parameters['tau_syn_E'], tau_syn_I =default_parameters['tau_syn_I'],
            #isyn_exc =  default_parameters['isyn_exc'],
            #isyn_inh =  default_parameters['isyn_inh'],
            ):


        # Construct model objects
        neuron_model = NeuronModelIzh(
            n_neurons, a, b, c, d, v_init, u_init, i_offset)

        synapse_type = SynapseTypeCombExp4E4I(
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
                inh4_b_tau)



        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(n_neurons, _IZK_THRESHOLD)

        AbstractPopulationVertex.__init__(
            self, n_neurons=n_neurons, binary="IZK_curr_comb_exp_4E4I.aplx", label=label,
            max_atoms_per_core=IzkCurrCombExp4E4I._model_based_max_atoms_per_core,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            model_name="IZK_curr_comb_exp_4E4I", neuron_model=neuron_model,
            input_type=input_type, synapse_type=synapse_type,
            threshold_type=threshold_type, constraints=constraints, max_feasible_atoms_per_core=IzkCurrCombExp4E4I._max_feasible_max_atoms_per_core)

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IZK_curr_comb_exp_4E4I._model_based_max_atoms_per_core = new_value

    @staticmethod
    def get_max_atoms_per_core():
        return  IzkCurrCombExp4E4I._model_based_max_atoms_per_core

