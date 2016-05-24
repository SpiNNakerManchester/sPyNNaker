from spynnaker.pyNN.models.neuron.abstract_population_model import \
    AbstractPopulationModel
from spynnaker.pyNN.models.neuron.neuron_models\
    .neuron_model_leaky_integrate_and_fire \
    import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_dual_exponential \
    import SynapseTypeDualExponential
from spynnaker.pyNN.models.neuron.input_types.input_type_current \
    import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types.threshold_type_static \
    import ThresholdTypeStatic


class IFCurrDualExp(AbstractPopulationModel):
    """ Leaky integrate and fire neuron with two exponentially decaying \
        excitatory current inputs, and one exponentially decaying inhibitory \
        current input
    """

    _model_based_max_atoms_per_core = 255

    default_parameters = {
        'tau_m': 20.0, 'cm': 1.0, 'v_rest': -65.0, 'v_reset': -65.0,
        'v_thresh': -50.0, 'tau_syn_E': 5.0, 'tau_syn_E2': 5.0,
        'tau_syn_I': 5.0, 'tau_refrac': 0.1, 'i_offset': 0}

    state_variables = {'v'}

    neuron_model = NeuronModelLeakyIntegrateAndFire
    synapse_type = SynapseTypeDualExponential
    input_type = InputTypeCurrent
    threshold_type = ThresholdTypeStatic

    binary_name = "IF_curr_exp_dual.aplx"
    model_name = "IF_curr_dual_exp"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IFCurrDualExp._model_based_max_atoms_per_core = new_value
