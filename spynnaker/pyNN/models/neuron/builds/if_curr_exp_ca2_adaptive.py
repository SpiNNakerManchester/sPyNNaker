from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.neuron.neuron_models \
    import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.additional_inputs \
    import AdditionalInputCa2Adaptive


class IFCurrExpCa2Adaptive(AbstractPopulationVertex):
    """ Model from Liu, Y. H., & Wang, X. J. (2001). Spike-frequency\
        adaptation of a generalized leaky integrate-and-fire model neuron. \
        Journal of Computational Neuroscience, 10(1), 25-45. \
        doi:10.1023/A:1008916026143
    """

    _model_based_max_atoms_per_core = 255

    default_parameters = {
        'tau_m': 20.0, 'cm': 1.0, 'v_rest': -65.0, 'v_reset': -65.0,
        'v_thresh': -50.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
        'tau_refrac': 0.1, 'i_offset': 0,
        'tau_ca2': 50.0, "i_ca2": 0.0, "i_alpha": 0.1, 'isyn_exc': 0.0,
        'isyn_inh': 0.0}

    none_pynn_default_parameters = {'v_init': None}

    def __init__(
            self, n_neurons, spikes_per_second=AbstractPopulationVertex.
            none_pynn_default_parameters['spikes_per_second'],
            ring_buffer_sigma=AbstractPopulationVertex.
            none_pynn_default_parameters['ring_buffer_sigma'],
            incoming_spike_buffer_size=AbstractPopulationVertex.
            none_pynn_default_parameters['incoming_spike_buffer_size'],
            constraints=AbstractPopulationVertex.none_pynn_default_parameters[
                'constraints'],
            label=AbstractPopulationVertex.none_pynn_default_parameters[
                'label'],
            tau_m=default_parameters['tau_m'], cm=default_parameters['cm'],
            v_rest=default_parameters['v_rest'],
            v_reset=default_parameters['v_reset'],
            v_thresh=default_parameters['v_thresh'],
            tau_syn_E=default_parameters['tau_syn_E'],
            tau_syn_I=default_parameters['tau_syn_I'],
            tau_refrac=default_parameters['tau_refrac'],
            i_offset=default_parameters['i_offset'],
            tau_ca2=default_parameters["tau_ca2"],
            i_ca2=default_parameters["i_ca2"],
            i_alpha=default_parameters["i_alpha"],
            v_init=none_pynn_default_parameters['v_init'],
            isyn_exc=default_parameters['isyn_exc'],
            isyn_inh=default_parameters['isyn_inh']):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            n_neurons, v_init, v_rest, tau_m, cm, i_offset,
            v_reset, tau_refrac)
        synapse_type = SynapseTypeExponential(
            n_neurons, tau_syn_E, tau_syn_I, initial_input_exc=isyn_exc,
            initial_input_inh=isyn_inh)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(n_neurons, v_thresh)
        additional_input = AdditionalInputCa2Adaptive(
            n_neurons, tau_ca2, i_ca2, i_alpha)

        AbstractPopulationVertex.__init__(
            self, n_neurons=n_neurons, binary="IF_curr_exp_ca2_adaptive.aplx",
            label=label,
            max_atoms_per_core=(
                IFCurrExpCa2Adaptive._model_based_max_atoms_per_core),
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            model_name="IF_curr_exp_ca2_adaptive", neuron_model=neuron_model,
            input_type=input_type, synapse_type=synapse_type,
            threshold_type=threshold_type, additional_input=additional_input,
            constraints=constraints)

    @staticmethod
    def get_max_atoms_per_core():
        return IFCurrExpCa2Adaptive._model_based_max_atoms_per_core

    @staticmethod
    def set_max_atoms_per_core(new_value):
        IFCurrExpCa2Adaptive._model_based_max_atoms_per_core = new_value
