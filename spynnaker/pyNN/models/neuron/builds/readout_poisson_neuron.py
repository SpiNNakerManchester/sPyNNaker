from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFirePoissonReadout)
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


class ReadoutPoissonNeuron(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron which fires Poisson spikes with rate
        set by the neurons membrane potential
    """

    @default_initial_values({"v", "isyn_exc", "isyn_inh",
                             "mean_isi_ticks", "time_to_spike_ticks"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=0.0, v_reset=0.0,
            v_thresh=100, tau_syn_E=5.0, tau_syn_I=5.0, tau_refrac=0.1,
            mean_isi_ticks=100, time_to_spike_ticks=1000,
            i_offset=0.0, v=50, isyn_exc=0.0, isyn_inh=0.0,):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFirePoissonReadout(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
            mean_isi_ticks, time_to_spike_ticks)
        synapse_type = SynapseTypeExponential(
            tau_syn_E, tau_syn_I, isyn_exc, isyn_inh)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)

        super(ReadoutPoissonNeuron, self).__init__(
            model_name="readout_poisson_neuron",
            binary="readout_poisson_neuron.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
