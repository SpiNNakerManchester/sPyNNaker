from .abstract_pynn_neuron_model import AbstractPyNNNeuronModel
from spynnaker.pyNN.models.neuron.implementations import NeuronImplStandard


class AbstractPyNNNeuronModelStandard(AbstractPyNNNeuronModel):
    __slots__ = []

    def __init__(
            self, model_name, binary, neuron_model, input_type,
            synapse_type, threshold_type, additional_input_type=None):
        AbstractPyNNNeuronModel.__init__(self, NeuronImplStandard(
            model_name, binary, neuron_model, input_type, synapse_type,
            threshold_type, additional_input_type))
