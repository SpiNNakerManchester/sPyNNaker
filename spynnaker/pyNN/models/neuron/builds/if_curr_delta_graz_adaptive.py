from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models \
    import NeuronModelLeakyIntegrateAndFireGrazAdaptive
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeAdaptive
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeDelta



#     default_parameters = {
#         'tau_m': 20.0, 'cm': 1.0, 'v_rest': -65.0, 'v_reset': -65.0,
#
#         # Adaptive threshold parameters
#         'thresh_B': 10,
#         "thresh_b": 0,
#         "thresh_b_0": 10,
#         "thresh_tau_a": 500,
#         "thresh_beta": 1.8,
#
# #         'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
#         'tau_refrac': 0.1, 'i_offset': 0,
#
#         # Synapse type parameters
#         'isyn_exc': 0.0, 'isyn_inh': 0.0}


class IFCurrDeltaGrazAdaptive(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with an instantaneous \
        current input
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "isyn_exc", "isyn_inh", "B", "small_b"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
            tau_refrac=0.1, i_offset=0.0, v=-65.0,
            isyn_exc=0.0, isyn_inh=0.0,
            # Threshold parameters
            B=10, small_b=0, small_b_0=10, tau_a=500, beta=1.8
            ):

        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFireGrazAdaptive(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)

        synapse_type = SynapseTypeDelta(isyn_inh, isyn_exc)

        input_type = InputTypeCurrent()

        threshold_type = ThresholdTypeAdaptive(B,
                                            small_b,
                                            small_b_0,
                                            tau_a,
                                            beta)

        super(IFCurrDeltaGrazAdaptive, self).__init__(
            model_name="IF_curr_delta_graz_adaptive",
            binary="IF_curr_delta_graz_adaptive.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)