from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.neuron.implementations.defaults \
    import defaults, default_initial_values


@defaults
class HHCondExp(object):
    """ Single-compartment Hodgkin-Huxley model with exponentially decaying \
        current input
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "gsyn_exc", "gsyn_inh"})
    def __init__(
            self, gbar_K=6.0, cm=0.2, e_rev_Na=50.0, tau_syn_E=0.2,
            tau_syn_I=2.0, i_offset=0.0, g_leak=0.01, e_rev_E=0.0,
            gbar_Na=20.0, e_rev_leak=-65.0, e_rev_I=-80, e_rev_K=-90.0,
            v_offset=-63, v=-65.0, gsyn_exc=0.0, gsyn_inh=0.0):
        # pylint: disable=too-many-arguments, too-many-locals, unused-argument
        raise SpynnakerException(
            "This neuron model is currently not supported by the tool chain")
