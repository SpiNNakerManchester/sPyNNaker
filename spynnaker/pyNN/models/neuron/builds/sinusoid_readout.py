from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFireSinusoidReadout)
from spynnaker.pyNN.models.neuron.synapse_types import (
    SynapseTypeEPropAdaptive)
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


class SinusoidReadout(AbstractPyNNNeuronModelStandard):
    """
    """

    @default_initial_values({"v", "isyn_exc", "isyn_exc2", "isyn_inh",
                             "isyn_inh2",
                             "l", "w_fb", "eta"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=0.0, v_reset=0.0,
            v_thresh=100, tau_refrac=0.1, i_offset=0.0, v=50,

            isyn_exc=0.0, isyn_exc2=0.0, isyn_inh=0.0, isyn_inh2=0.0,
            tau_syn_E=5.0, tau_syn_E2=5.0, tau_syn_I=5.0, tau_syn_I2=5.0,
#             mean_isi_ticks=65000, time_to_spike_ticks=65000, rate_update_threshold=0.25,

            target_data =[],

            # Learning signal and weight update constants
            l=0, w_fb=0.5, eta=1.0):

        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFireSinusoidReadout(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac, target_data,
            # Learning signal params
            l, w_fb, eta)

        synapse_type = SynapseTypeEPropAdaptive(
            tau_syn_E, tau_syn_E2, tau_syn_I, tau_syn_I2,
            isyn_exc, isyn_exc2, isyn_inh, isyn_inh2)

        input_type = InputTypeCurrent()

        threshold_type = ThresholdTypeStatic(v_thresh)

        super(SinusoidReadout, self).__init__(
            model_name="sinusoid_readout",
            binary="sinusoid_readout.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)