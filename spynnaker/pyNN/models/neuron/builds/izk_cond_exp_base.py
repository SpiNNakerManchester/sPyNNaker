import logging
from spinn_utilities import logger_utils
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance
from spynnaker.pyNN.models.neuron.neuron_models import NeuronModelIzh
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values

_IZK_THRESHOLD = 30.0
logger = FormatAdapter(logging.getLogger(__name__))


class IzkCondExpBase(AbstractPyNNNeuronModelStandard):

    # noinspection PyPep8Naming
    @default_initial_values({"v", "u", "isyn_exc", "isyn_inh"})
    def __init__(
            self, a=0.02, b=0.2, c=-65.0, d=2.0, i_offset=0.0, u=None,
            v=None, tau_syn_E=5.0, tau_syn_I=5.0, e_rev_E=0.0, e_rev_I=-70.0,
            isyn_exc=None, isyn_inh=None):
        # pylint: disable=too-many-arguments, too-many-locals
        if v is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'v' shoud be set "
                        "using initial_values = not cellparams")
        if u is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'u' shoud be set "
                        "using initial_values = not cellparams")
        if isyn_exc is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'isyn_exc' shoud be set "
                        "using initial_values = not cellparams")
        if isyn_inh is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'isyn_inh' shoud be set "
                        "using initial_values = not cellparams")
        neuron_model = NeuronModelIzh(a, b, c, d, v, u, i_offset)
        synapse_type = SynapseTypeExponential(
            tau_syn_E, tau_syn_I, isyn_exc, isyn_inh)
        input_type = InputTypeConductance(e_rev_E, e_rev_I)
        threshold_type = ThresholdTypeStatic(_IZK_THRESHOLD)

        super(IzkCondExpBase, self).__init__(
            model_name="IZK_cond_exp", binary="IZK_cond_exp.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
