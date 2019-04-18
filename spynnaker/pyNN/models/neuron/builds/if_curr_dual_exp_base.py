import logging
from spinn_utilities import logger_utils
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFire)
from spynnaker.pyNN.models.neuron.synapse_types import (
    SynapseTypeDualExponential)
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic

logger = FormatAdapter(logging.getLogger(__name__))


class IFCurrDualExpBase(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with two exponentially decaying \
        excitatory current inputs, and one exponentially decaying inhibitory \
        current input
    """

    @default_initial_values({"v", "isyn_exc", "isyn_exc2", "isyn_inh"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
            v_thresh=-50.0, tau_syn_E=5.0, tau_syn_E2=5.0, tau_syn_I=5.0,
            tau_refrac=0.1, i_offset=0.0, v=None, isyn_exc=None, isyn_inh=None,
            isyn_exc2=None):
        if v is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'v' should be set "
                        "using initial_values = not cellparams")
        if isyn_exc is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'isyn_exc' should be set "
                        "using initial_values = not cellparams")
        if isyn_exc2 is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'isyn_exc2' should be set "
                        "using initial_values = not cellparams")
        if isyn_inh is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'isyn_inh' shoud be set "
                        "using initial_values = not cellparams")
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeDualExponential(
            tau_syn_E, tau_syn_E2, tau_syn_I, isyn_exc, isyn_exc2, isyn_inh)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)

        super(IFCurrDualExpBase, self).__init__(
            model_name="IF_curr_dual_exp", binary="IF_curr_exp_dual.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
