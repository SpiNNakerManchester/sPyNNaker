import logging
from spinn_utilities import logger_utils
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.defaults import defaults, default_initial_values

logger = FormatAdapter(logging.getLogger(__name__))


@defaults
class EIFConductanceAlphaPopulation(object):
    """ Exponential integrate and fire neuron with spike triggered and \
        sub-threshold adaptation currents (isfa, ista reps.)
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "w", "gsyn_exc", "gsyn_inh"})
    def __init__(self, tau_m=9.3667, cm=0.281, v_rest=-70.6,
                 v_reset=-70.6, v_thresh=-50.4, tau_syn_E=5.0, tau_syn_I=0.5,
                 tau_refrac=0.1, i_offset=0.0, a=4.0, b=0.0805, v_spike=-40.0,
                 tau_w=144.0, e_rev_E=0.0, e_rev_I=-80.0, delta_T=2.0,
                 v=None, w=0.0, gsyn_exc=0.0, gsyn_inh=0.0):
        if v is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'v' shoud be set "
                        "using initial_values = not cellparams")
        if gsyn_exc is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'gsyn_exc' shoud be set "
                        "using initial_values = not cellparams")
        if gsyn_inh is not None:
            logger_utils.warn_once(
                logger, "Formal Pynn specifies that 'gsyn_inh' shoud be set "
                        "using initial_values = not cellparams")

        # pylint: disable=too-many-arguments, too-many-locals, unused-argument
        raise SpynnakerException(
            "This neuron model is currently not supported by the tool chain")
