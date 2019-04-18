import logging
from spinn_utilities import logger_utils
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.defaults import defaults, default_initial_values

logger = FormatAdapter(logging.getLogger(__name__))


@defaults
class HHCondExp(object):
    """ Single-compartment Hodgkin-Huxley model with exponentially decaying \
        current input.
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "gsyn_exc", "gsyn_inh"})
    def __init__(
            self, gbar_K=6.0, cm=0.2, e_rev_Na=50.0, tau_syn_E=0.2,
            tau_syn_I=2.0, i_offset=0.0, g_leak=0.01, e_rev_E=0.0,
            gbar_Na=20.0, e_rev_leak=-65.0, e_rev_I=-80, e_rev_K=-90.0,
            v_offset=-63, v=None, gsyn_exc=None, gsyn_inh=None):
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
