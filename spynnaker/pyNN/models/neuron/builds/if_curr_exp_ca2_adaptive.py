from spynnaker.pyNN.models.abstract_models \
    import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.neuron.implementations.defaults \
    import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models \
    import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.additional_inputs \
    import AdditionalInputCa2Adaptive


class IFCurrExpCa2Adaptive(AbstractPyNNNeuronModelStandard):
    """ Model from Liu, Y. H., & Wang, X. J. (2001). Spike-frequency\
        adaptation of a generalized leaky integrate-and-fire model neuron. \
        Journal of Computational Neuroscience, 10(1), 25-45. \
        doi:10.1023/A:1008916026143
    """

    @default_initial_values({"v", "isyn_exc", "isyn_inh", "i_ca2"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
            v_thresh=-50.0, tau_syn_E=5.0, tau_syn_I=5.0, tau_refrac=0.1,
            i_offset=0.0, tau_ca2=50.0, i_ca2=0.0, i_alpha=0.1, v=-65.0,
            isyn_exc=0.0, isyn_inh=0.0):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeExponential(
            tau_syn_E, tau_syn_I, isyn_exc, isyn_inh)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)
        additional_input = AdditionalInputCa2Adaptive(tau_ca2, i_ca2, i_alpha)

        super(IFCurrExpCa2Adaptive, self).__init__(
            model_name="IF_curr_exp_ca2_adaptive",
            binary="IF_curr_exp_ca2_adaptive.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type,
            additional_input=additional_input)
