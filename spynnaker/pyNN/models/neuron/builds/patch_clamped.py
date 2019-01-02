from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models \
    import NeuronModelPatchClamped
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.additional_inputs \
    import AdditionalInputHTIntrinsicCurrents


default_parameters = {
    # #### Additional Input ####
    # Pacemaker (H)
    'I_H':0.0,
    'g_H':2.0,
    'E_H':-40.0,  # 40 in Synthesis code and 43.0 in Huguenard's paper.
    'm_H':4.0,  # should be calculated according to initial m_inf
    'm_inf_H':5.0,  # should be calculated according to initial V
    'e_to_t_on_tau_m_H':6.0,  # should be calculated according to initial V
    # Calcium (T)
    'I_T':0.0,
    'g_T':11.0,
    'E_T':120.0,  # 0.0 in synthesis but experimental value approx 120.0.
    'm_T':13.0,
    'm_inf_T':14.0, # should be calculated according to initial m_inf
    'e_to_t_on_tau_m_T':15.0,  # should be calculated according to initial V
    'h_T':16.0,
    'h_inf_T':17.0,
    'e_to_t_on_tau_h_T':18.0,  # should be calculated according to initial V
    # Sodium (Na)
    'I_NaP':0.0,
    'g_NaP':0.5,
    'E_NaP':30,  # 30.0 in Synthesis
    'm_inf_NaP':0.0,  # should be calculated according to initial V
    # Potassium (K)
    'I_DK':0.0,
    'g_DK':0.5,
    'E_DK':-90.0,
    'm_inf_DK':0.0,  # should be calculated according to initial V
    'e_to_t_on_tau_m_DK': 1250,  # should be calculated according to initial V
    'D':0.0,  # should be calculated according to initial V
    'D_infinity':0.0, # should be calculated according to initial V
    # Voltage Clamp
    'v_clamp': -75.0,
    's_clamp': 3.0,
    't_clamp': 1.0,
    'dt':1.0
    }


class PatchClamped(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        current input
    """

    @default_initial_values({"v", "isyn_exc", "isyn_inh",
                            "I_H", 'm_H', 'm_inf_H', 'e_to_t_on_tau_m_H',
                            "I_T", 'm_T', 'm_inf_T', 'e_to_t_on_tau_m_T', 'h_T', 'h_inf_T', 'e_to_t_on_tau_h_T',
                            "I_NaP", 'm_inf_NaP',
                            "I_DK", 'm_inf_DK', 'e_to_t_on_tau_m_DK', 'D', 'D_infinity'
                             })
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-5000.0, v_reset=-65.0,
            v_thresh=5000.0, tau_syn_E=5.0, tau_syn_I=5.0, tau_refrac=0.1,
            i_offset=0.0, v=-65.0, isyn_exc=0.0, isyn_inh=0.0,

            # ##########################
            # #### Additional Input ####
            # ##########################
            # Pacemaker
            I_H = default_parameters['I_H'],
            g_H = default_parameters['g_H'],
            E_H = default_parameters['E_H'],
            m_H = default_parameters['m_H'],
            m_inf_H = default_parameters['m_inf_H'],
            e_to_t_on_tau_m_H = default_parameters['e_to_t_on_tau_m_H'],
            # Calcium
            I_T=default_parameters['I_T'],
            g_T=default_parameters['g_T'],
            E_T=default_parameters['E_T'],
            m_T=default_parameters['m_T'],
            m_inf_T=default_parameters['m_inf_T'],
            e_to_t_on_tau_m_T=default_parameters['e_to_t_on_tau_m_T'],
            h_T=default_parameters['h_T'],
            h_inf_T=default_parameters['h_inf_T'],
            e_to_t_on_tau_h_T=default_parameters['e_to_t_on_tau_h_T'],
            # Sodium
            I_NaP = default_parameters['I_NaP'],
            g_NaP = default_parameters['g_NaP'],
            E_NaP = default_parameters['E_NaP'],
            m_inf_NaP = default_parameters['m_inf_NaP'],
            # Potassium
            I_DK = default_parameters['I_DK'],
            g_DK = default_parameters['g_DK'],
            E_DK = default_parameters['E_DK'],
            m_inf_DK = default_parameters['m_inf_DK'],
            e_to_t_on_tau_m_DK = default_parameters['e_to_t_on_tau_m_DK'],
            D = default_parameters['D'],
            D_infinity = default_parameters['D_infinity'],

            v_clamp = default_parameters['v_clamp'],
            s_clamp = default_parameters['s_clamp'],
            t_clamp = default_parameters['t_clamp'],
            # Other
            dt = default_parameters['dt'],
            ):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelPatchClamped(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeExponential(
            tau_syn_E, tau_syn_I, isyn_exc, isyn_inh)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)
        additional_input = AdditionalInputHTIntrinsicCurrents(
            # Pacemaker
            I_H,
            g_H,
            E_H,
            m_H,
            m_inf_H,
            e_to_t_on_tau_m_H,
            # Calcium
            I_T,
            g_T,
            E_T,
            m_T,
            m_inf_T,
            e_to_t_on_tau_m_T,
            h_T,
            h_inf_T,
            e_to_t_on_tau_h_T,
            # Sodium
            I_NaP,
            g_NaP,
            E_NaP,
            m_inf_NaP,
            # Potassium
            I_DK,
            g_DK,
            E_DK,
            m_inf_DK,
            e_to_t_on_tau_m_DK,
            D,
            D_infinity,
            # Voltage Clamp
            v_clamp, s_clamp, t_clamp,
            dt)

        super(PatchClamped, self).__init__(
            model_name="patch_clamped", binary="patch_clamped.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type,
            additional_input_type=additional_input)
