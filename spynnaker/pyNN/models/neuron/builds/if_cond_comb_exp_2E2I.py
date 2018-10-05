from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models \
    import NeuronModelLeakyIntegrateAndFireVHist
from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance2E2I
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeCombExp2E2I
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex

# global objects
DEFAULT_MAX_ATOMS_PER_CORE = 255

default_parameters = {
    'tau_m': 20.0,
    'cm': 1.0,
    'v_rest': -65.0,
    'v_reset': -65.0,
    'v_thresh': -50.0,
    'tau_refrac': 0.1,
    'i_offset': 0,
    'v_hist':None,

    ##### synapse parameters #####
    # excitatory
    'exc_a_response':0,
    'exc_a_A':1,
    'exc_a_tau': 1,
    'exc_b_response':0,
    'exc_b_B':-1,
    'exc_b_tau': 5,
    # excitatory2
    'exc2_a_response':0,
    'exc2_a_A':1,
    'exc2_a_tau': 1,
    'exc2_b_response':0,
    'exc2_b_B':-1,
    'exc2_b_tau': 5,
    # inhibitory
    'inh_a_response': 0,
    'inh_a_A':1,
    'inh_a_tau': 1,
    'inh_b_response':0,
    'inh_b_B':-1,
    'inh_b_tau': 5,
    # inhibitory2
    'inh2_a_response': 0,
    'inh2_a_A':1,
    'inh2_a_tau': 1,
    'inh2_b_response':0,
    'inh2_b_B':-1,
    'inh2_b_tau': 5}
    ##############################

initialize_parameters = {'v_init': None}




class IFCondCombExp2E2I(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        conductance input.
    """

    @default_initial_values({"v", "v_hist",
                             "exc_a_response", "exc_b_response",
                             "exc2_a_response", "exc2_b_response",
                             "inh_a_response", "inh_b_response",
                             "inh2_a_response", "inh2_b_response"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
            v_thresh=-50.0,  tau_refrac=0.1, v_hist=None,
            i_offset=0.0, v=-65.0,
            e_rev_E=0.0, e_rev_E2=5.0, e_rev_I=-70.0, e_rev_I2=-70.0,

            # excitatory
            exc_a_response=default_parameters['exc_a_response'],
            exc_a_A=default_parameters['exc_a_A'],
            exc_a_tau=default_parameters['exc_a_tau'],
            exc_b_response=default_parameters['exc_b_response'],
            exc_b_B=default_parameters['exc_b_B'],
            exc_b_tau=default_parameters['exc_b_tau'],

            # excitatory2
            exc2_a_response=default_parameters['exc2_a_response'],
            exc2_a_A=default_parameters['exc2_a_A'],
            exc2_a_tau=default_parameters['exc2_a_tau'],
            exc2_b_response=default_parameters['exc2_b_response'],
            exc2_b_B=default_parameters['exc2_b_B'],
            exc2_b_tau=default_parameters['exc2_b_tau'],

            # inhibitory
            inh_a_response=default_parameters['inh_a_response'],
            inh_a_A=default_parameters['inh_a_A'],
            inh_a_tau=default_parameters['inh_a_tau'],
            inh_b_response=default_parameters['inh_b_response'],
            inh_b_B=default_parameters['inh_b_B'],
            inh_b_tau=default_parameters['inh_b_tau'],

            # inhibitory2
            inh2_a_response=default_parameters['inh2_a_response'],
            inh2_a_A=default_parameters['inh2_a_A'],
            inh2_a_tau=default_parameters['inh2_a_tau'],
            inh2_b_response=default_parameters['inh2_b_response'],
            inh2_b_B=default_parameters['inh2_b_B'],
            inh2_b_tau=default_parameters['inh2_b_tau']

            ):

        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFireVHist(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac, v_hist)

        synapse_type = SynapseTypeCombExp2E2I(
                # excitatory
                exc_a_response,
                exc_a_A,
                exc_a_tau,
                exc_b_response,
                exc_b_B,
                exc_b_tau,

                # excitatory2
                exc2_a_response,
                exc2_a_A,
                exc2_a_tau,
                exc2_b_response,
                exc2_b_B,
                exc2_b_tau,

                # inhibitory
                inh_a_response,
                inh_a_A,
                inh_a_tau,
                inh_b_response,
                inh_b_B,
                inh_b_tau,

                # inhibitory2
                inh2_a_response,
                inh2_a_A,
                inh2_a_tau,
                inh2_b_response,
                inh2_b_B,
                inh2_b_tau
            )

        input_type = InputTypeConductance2E2I(
            e_rev_E,
            e_rev_E2,
            e_rev_I,
            e_rev_I2
            )

        threshold_type = ThresholdTypeStatic(v_thresh)

        super(IFCondCombExp2E2I, self).__init__(
            model_name="IF_cond_comb_exp_2E2I", binary="IF_cond_comb_exp_2E2I.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)


