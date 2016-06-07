from spynnaker.pyNN.models.neuron.bag_of_neurons_vertex import \
    BagOfNeuronsVertex
from spynnaker.pyNN.models.neuron.neuron_models\
    .neuron_model_leaky_integrate_and_fire \
    import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.models.neuron.input_types.input_type_conductance \
    import InputTypeConductance
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_exponential \
    import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.threshold_types.threshold_type_static \
    import ThresholdTypeStatic


class IFCondExp(BagOfNeuronsVertex):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        conductance input
    """

    model_based_max_atoms_per_core = 255

    default_parameters = {
        'tau_m': 20.0, 'cm': 1.0, 'e_rev_E': 0.0, 'e_rev_I': -70.0,
        'v_rest': -65.0, 'v_reset': -65.0, 'v_thresh': -50.0,
        'tau_syn_E': 5.0, 'tau_syn_I': 5.0, 'tau_refrac': 0.1,
        'i_offset': 0, 'v_init': None}

    state_variables = {'v'}

    neuron_model = NeuronModelLeakyIntegrateAndFire
    synapse_type = SynapseTypeExponential
    input_type = InputTypeConductance
    threshold_type = ThresholdTypeStatic

    binary_name = "IF_cond_exp.aplx"
    model_name = "IF_cond_exp"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IFCondExp.model_based_max_atoms_per_core = new_value
