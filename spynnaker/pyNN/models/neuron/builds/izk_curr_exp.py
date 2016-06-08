from spynnaker.pyNN.models.neuron.bag_of_neurons_vertex import \
    BagOfNeuronsVertex
from spynnaker.pyNN.models.neuron.neuron_models.neuron_model_izh \
    import NeuronModelIzh
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_exponential \
    import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.input_types.input_type_current \
    import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types.threshold_type_static \
    import ThresholdTypeStatic


class IzkCurrExp(BagOfNeuronsVertex):

    model_based_max_atoms_per_core = 255

    neuron_model = NeuronModelIzh
    synapse_type = SynapseTypeExponential
    input_type = InputTypeCurrent
    threshold_type = ThresholdTypeStatic

    binary_name = "IZK_curr_exp.aplx"
    model_name = "IZK_curr_exp"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IzkCurrExp.model_based_max_atoms_per_core = new_value