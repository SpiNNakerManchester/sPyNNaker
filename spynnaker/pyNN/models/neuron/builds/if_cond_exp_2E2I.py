from spynnaker.pyNN.models.neuron.neuron_models \
    import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance2E2I
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential2E2I
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex

# global objects
DEFAULT_MAX_ATOMS_PER_CORE = 255


class IFCondExp2E2I(AbstractPopulationVertex):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        conductance input.
    """

    _model_based_max_atoms_per_core = DEFAULT_MAX_ATOMS_PER_CORE

    default_parameters = {
        'tau_m': 20.0, 'cm': 1.0,
        'e_rev_E': 0.0,
        'e_rev_E2': 5.0,
        'e_rev_I': -70.0,
        'e_rev_I2': -75.0,
        'v_rest': -65.0, 'v_reset': -65.0, 'v_thresh': -50.0,
        'tau_syn_E': 10.0,
        'tau_syn_E2': 10.0,
        'tau_syn_I': 10.0,
        'tau_syn_I2': 10.0,
        'tau_refrac': 0.1,
        'i_offset': 0,
        'isyn_exc': 0.0,
        'isyn_exc_2': 0.0,
        'isyn_inh': 0.0,
        'isyn_inh_2': 0.0
        }

    initialize_parameters = {'v_init': None}

    def __init__(
            self, n_neurons,
            spikes_per_second=AbstractPopulationVertex.
            non_pynn_default_parameters['spikes_per_second'],
            ring_buffer_sigma=AbstractPopulationVertex.
            non_pynn_default_parameters['ring_buffer_sigma'],
            incoming_spike_buffer_size=AbstractPopulationVertex.
            non_pynn_default_parameters['incoming_spike_buffer_size'],
            constraints=AbstractPopulationVertex.
            non_pynn_default_parameters['constraints'],
            label=AbstractPopulationVertex.non_pynn_default_parameters[
                'label'],
            tau_m=default_parameters['tau_m'],
            cm=default_parameters['cm'], v_rest=default_parameters['v_rest'],
            v_reset=default_parameters['v_reset'],
            v_thresh=default_parameters['v_thresh'],
            tau_syn_E=default_parameters['tau_syn_E'],
            tau_syn_E2=default_parameters['tau_syn_E2'],
            tau_syn_I=default_parameters['tau_syn_I'],
            tau_syn_I2=default_parameters['tau_syn_I2'],
            tau_refrac=default_parameters['tau_refrac'],
            i_offset=default_parameters['i_offset'],
            e_rev_E=default_parameters['e_rev_E'],
            e_rev_E2=default_parameters['e_rev_E2'],
            e_rev_I=default_parameters['e_rev_I'],
            e_rev_I2=default_parameters['e_rev_I2'],
            v_init=initialize_parameters['v_init'],
            isyn_exc=default_parameters['isyn_exc'],
            isyn_exc_2=default_parameters['isyn_exc_2'],
            isyn_inh=default_parameters['isyn_inh'],
            isyn_inh_2=default_parameters['isyn_inh_2']):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            n_neurons, v_init, v_rest, tau_m, cm, i_offset,
            v_reset, tau_refrac)
        synapse_type = SynapseTypeExponential2E2I(
            n_neurons,
            tau_syn_E,
            tau_syn_E2,
            tau_syn_I,
            tau_syn_I2,
            isyn_exc,
            isyn_exc_2,
            isyn_inh,
            isyn_inh_2
            )
        input_type = InputTypeConductance2E2I(
            n_neurons,
            e_rev_E,
            e_rev_E2,
            e_rev_I,
            e_rev_I2
            )
        threshold_type = ThresholdTypeStatic(n_neurons, v_thresh)

        super(IFCondExp2E2I, self).__init__(
            n_neurons=n_neurons, binary="IF_cond_exp_2E2I.aplx", label=label,
            max_atoms_per_core=IFCondExp2E2I._model_based_max_atoms_per_core,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            model_name="IF_cond_exp_2E2I", neuron_model=neuron_model,
            input_type=input_type, synapse_type=synapse_type,
            threshold_type=threshold_type, constraints=constraints)

    @staticmethod
    def set_model_max_atoms_per_core(new_value=DEFAULT_MAX_ATOMS_PER_CORE):
        IFCondExp2E2I._model_based_max_atoms_per_core = new_value

    @staticmethod
    def get_max_atoms_per_core():
        return IFCondExp2E2I._model_based_max_atoms_per_core
