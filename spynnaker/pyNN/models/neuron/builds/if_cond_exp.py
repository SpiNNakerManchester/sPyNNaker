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

    neuron_model = NeuronModelLeakyIntegrateAndFire
    synapse_type = SynapseTypeExponential
    input_type = InputTypeConductance
    threshold_type = ThresholdTypeStatic

    binary_name = "IF_cond_exp.aplx"
    model_name = "IF_cond_exp"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IFCondExp.model_based_max_atoms_per_core = new_value
