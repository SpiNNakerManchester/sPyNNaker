from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.defaults import defaults, default_initial_values


@defaults
class IFFacetsConductancePopulation(object):
    """ Leaky integrate and fire neuron with conductance-based synapses and\
        fixed threshold as it is resembled by the FACETS Hardware Stage 1
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v"})
    def __init__(
            self, g_leak=40.0, tau_syn_E=30.0, tau_syn_I=30.0, v_thresh=-55.0,
            v_rest=-65.0, e_rev_I=-80, v_reset=-80.0, v=-65.0):
        # pylint: disable=too-many-arguments, unused-argument
        raise SpynnakerException(
            "This neuron model is currently not supported by the tool chain")
