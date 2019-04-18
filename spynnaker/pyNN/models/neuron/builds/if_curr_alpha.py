import logging
from spinn_utilities import logger_utils
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFire)
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeAlpha
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic

logger = FormatAdapter(logging.getLogger(__name__))


class IFCurrAlpha(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with an alpha-shaped current-based\
        input.
    """

    @default_initial_values({
        "v", "exc_response", "exc_exp_response", "inh_response",
        "inh_exp_response"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
            v_thresh=-50.0, tau_syn_E=0.5, tau_syn_I=0.5, tau_refrac=0.1,
            i_offset=0.0, v=None, exc_response=None, exc_exp_response=None,
            inh_response=None, inh_exp_response=None):
        # pylint: disable=too-many-arguments, too-many-locals
        if v is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'v' should be set "
                        "using initial_values = not cellparams")
        if exc_response is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'exc_response' should be "
                        "set using initial_values = not cellparams")
        if exc_exp_response is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'exc_exp_response' should "
                        "be set using initial_values = not cellparams")
        if inh_response is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'inh_response' should be "
                        "set using initial_values = not cellparams")
        if inh_exp_response is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'inh_exp_response' should "
                        "be set using initial_values = not cellparams")
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)

        synapse_type = SynapseTypeAlpha(
            exc_response, exc_exp_response, tau_syn_E, inh_response,
            inh_exp_response, tau_syn_I)

        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)

        super(IFCurrAlpha, self).__init__(
            model_name="IF_curr_alpha", binary="IF_curr_alpha.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
