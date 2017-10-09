from spynnaker.pyNN.models.neuron import AbstractPopulationVertex

from spynnaker.pyNN.models.neuron.neuron_models\
    .neuron_model_leaky_integrate_and_fire \
    import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_alpha\
    import SynapseTypeAlpha
from spynnaker.pyNN.models.neuron.input_types.input_type_current_alpha \
    import InputTypeCurrentAlpha
from spynnaker.pyNN.models.neuron.threshold_types.threshold_type_static \
    import ThresholdTypeStatic


class IFCurrAlpha(AbstractPopulationVertex):
    """ Leaky integrate and fire neuron with an alpha-shaped current input
    """

    # noinspection PyPep8Naming


    _model_based_max_atoms_per_core = 255

    default_parameters = {
        'tau_m': 20.0,
        'cm': 1.0,
        'v_rest': -65.0,
        'v_reset': -65.0,
        'v_thresh': -50.0,

        'dt':0.1,

        'exc_response':0,
        'exc_exp_response':0,
        'exc_tau':2,

        'inh_response':0,
        'inh_exp_response':0,
        'inh_tau':2,

        'tau_refrac': 0.1,
        'i_offset': 0}

    def __init__(
            self, n_neurons, spikes_per_second=None, ring_buffer_sigma=None,
            incoming_spike_buffer_size=None, constraints=None, label=None,
            tau_m=default_parameters['tau_m'], cm=default_parameters['cm'],
            v_rest=default_parameters['v_rest'],
            v_reset=default_parameters['v_reset'],
            v_thresh=default_parameters['v_thresh'],

            dt = default_parameters['dt'],

            exc_response=default_parameters['exc_response'],
            exc_exp_response=default_parameters['exc_exp_response'],
            exc_tau=default_parameters['exc_tau'],

            inh_response=default_parameters['inh_response'],
            inh_exp_response=default_parameters['inh_exp_response'],
            inh_tau=default_parameters['inh_tau'],

            tau_refrac=default_parameters['tau_refrac'],
            i_offset=default_parameters['i_offset'], v_init=None):

        # Construct neuron/synapse objects
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            n_neurons, v_init, v_rest, tau_m, cm, i_offset,
            v_reset, tau_refrac)

        synapse_type = SynapseTypeAlpha(
                n_neurons,

                dt,

                exc_response,
                exc_exp_response,
                exc_tau,

                inh_response,
                inh_exp_response,
                inh_tau
                )


        input_type = InputTypeCurrentAlpha()
        threshold_type = ThresholdTypeStatic(n_neurons, v_thresh)

        AbstractPopulationVertex.__init__(
            self, n_neurons=n_neurons, binary="IF_curr_alpha.aplx",
            label=label, max_atoms_per_core= \
                IFCurrAlpha._model_based_max_atoms_per_core,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            model_name="IF_curr_alpha", neuron_model=neuron_model,
            input_type=input_type, synapse_type=synapse_type,
            threshold_type=threshold_type, constraints=constraints)


    @staticmethod
    def get_max_atoms_per_core():
        return IFCurrAlpha._model_based_max_atoms_per_core

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IFCurrAlpha._model_based_max_atoms_per_core = new_value
