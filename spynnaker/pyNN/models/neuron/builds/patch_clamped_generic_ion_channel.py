from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models \
    import NeuronModelPatchClamped
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.additional_inputs \
    import AdditionalInputSingleGenericIonChannel





class PatchClampedGenericSingleChannel(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        current input
    """

    @default_initial_values({"v", "isyn_exc", "isyn_inh",

                             })
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-5000.0, v_reset=-65.0,
            v_thresh=5000.0, tau_syn_E=5.0, tau_syn_I=5.0, tau_refrac=0.1,
            i_offset=0.0, v=-65.0, isyn_exc=0.0, isyn_inh=0.0,

            # ##########################
            # #### Additional Input ####
            # ##########################
            I_ion,
            g,
            E,
            # activation parameters
            m_pow,
            m_K,
            m_v_half,
            m_N,
            m_sigma,
            m_delta,
            # activation state
            m,
            m_inf,
            tau_m,
            # inactivation parameters
            h_pow,
            h_K,
            h_v_half,
            h_N,
            h_sigma,
            h_delta,

            # inactivation state
            h,
            h_inf,
            tau_h
            ):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelPatchClamped(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeExponential(
            tau_syn_E, tau_syn_I, isyn_exc, isyn_inh)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)
        additional_input = AdditionalInputSingleGenericIonChannel(
            I_ion,
            g,
            E,
            # activation parameters
            m_pow,
            m_K,
            m_v_half,
            m_N,
            m_sigma,
            m_delta,
            # activation state
            m,
            m_inf,
            tau_m,

            # inactivation parameters
            h_pow,
            h_K,
            h_v_half,
            h_N,
            h_sigma,
            h_delta,
            # inactivation state
            h,
            h_inf,
            tau_h,
        )

        super(PatchClamped, self).__init__(
            model_name="patch_clamped_single_generic_channel",
            binary="patch_clamped_generic.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type,
            additional_input_type=additional_input)
