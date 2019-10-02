from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelStoreRecallReadout)
from spynnaker.pyNN.models.neuron.synapse_types import (
    SynapseTypeEPropAdaptive)
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


class StoreRecallReadout(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron which fires Poisson spikes with rate
        set by the neurons membrane potential
    """

    @default_initial_values({"v", "isyn_exc", "isyn_exc2", "isyn_inh",
                             "isyn_inh2", "mean_isi_ticks",
                             "time_to_spike_ticks"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=0.0, v_reset=0.0,
            v_thresh=100, tau_refrac=0.1,
            isyn_exc=0.0, isyn_exc2=0.0, isyn_inh=0.0, isyn_inh2=0.0,
            tau_syn_E=5.0, tau_syn_E2=5.0, tau_syn_I=5.0, tau_syn_I2=5.0,
            mean_isi_ticks=65000, time_to_spike_ticks=65000,
            i_offset=0.0, v=50, rate_update_threshold=0.25,
            prob_command=1./6., rate_on=50, rate_off=0):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelStoreRecallReadout(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
            mean_isi_ticks, time_to_spike_ticks, rate_update_threshold,
            prob_command, rate_on, rate_off)
        synapse_type = SynapseTypeEPropAdaptive(
            tau_syn_E, tau_syn_E2, tau_syn_I, tau_syn_I2,
            isyn_exc, isyn_exc2, isyn_inh, isyn_inh2)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)

        super(StoreRecallReadout, self).__init__(
            model_name="store_recall_readout_neuron",
            binary="store_recall_readout_neuron.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
