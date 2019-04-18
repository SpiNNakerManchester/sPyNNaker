import logging
from spinn_utilities import logger_utils
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.defaults import defaults, default_initial_values

logger = FormatAdapter(logging.getLogger(__name__))


@defaults
class IFCondAlpha(object):
    """ Leaky integrate and fire neuron with an alpha-shaped current input.
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "gsyn_exc", "gsyn_inh"})
    def __init__(
            self, tau_m=20, cm=1.0, e_rev_E=0.0, e_rev_I=-70.0, v_rest=-65.0,
            v_reset=-65.0, v_thresh=-50.0, tau_syn_E=0.3, tau_syn_I=0.5,
            tau_refrac=0.1, i_offset=0, v=None, gsyn_exc=None, gsyn_inh=None):
        # pylint: disable=too-many-arguments, too-many-locals, unused-argument
        if v is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'v' should be set "
                        "using initial_values = not cellparams")
        if gsyn_exc is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'gsyn_exc' should be set "
                        "using initial_values = not cellparams")
        if gsyn_inh is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'gsyn_inh' should be set "
                        "using initial_values = not cellparams")
        raise SpynnakerException(
            "This neuron model is currently not supported by the tool chain")
