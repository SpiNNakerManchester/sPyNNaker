from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFireERBPErrorNeuron)
from spynnaker.pyNN.models.neuron.synapse_types import (
    SynapseTypeErrorNeuronExponential)
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


class ErrorNeuron(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with exponentially decaying \
        excitatory and inhibitory inputs, with firing gated by second \
        compartment integarting label spikes from 3rd receptor
    """

    @default_initial_values(
        {"v", "isyn_exc", "isyn_exc2", "isyn_inh", "local_err"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
            v_thresh=-50.0, tau_syn_E=5.0, tau_syn_E2=5.0, tau_syn_I=5.0,
            tau_refrac=0.1, i_offset=0.0, v=-65.0, isyn_exc=0.0, isyn_inh=0.0,
            isyn_exc2=0.0, local_err=0, tau_err=5):

        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFireERBPErrorNeuron(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac, local_err,
            tau_err)

        synapse_type = SynapseTypeErrorNeuronExponential(
            tau_syn_E, tau_syn_E2, tau_syn_I,
             isyn_exc, isyn_exc2, isyn_inh)

        input_type = InputTypeCurrent()

        threshold_type = ThresholdTypeStatic(v_thresh)

        super(ErrorNeuron, self).__init__(
            model_name="error_neuron", binary="error_neuron.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
