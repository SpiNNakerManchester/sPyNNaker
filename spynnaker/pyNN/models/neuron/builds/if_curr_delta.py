from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFire)
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeDelta


class IFCurrDelta(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with an instantaneous \
        current input
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "isyn_exc", "isyn_inh"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
            v_thresh=-50.0, tau_refrac=0.1, i_offset=0.0, v=-65.0,
            isyn_exc=0.0, isyn_inh=0.0):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeDelta(isyn_inh, isyn_exc)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)

        super(IFCurrDelta, self).__init__(
            model_name="IF_curr_delta", binary="IF_curr_delta.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
