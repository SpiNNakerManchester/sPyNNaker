from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models \
    import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance2E2I
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential2E2I
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex

# global objects
DEFAULT_MAX_ATOMS_PER_CORE = 255

class IFCondExp2E2I(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        conductance input.
    """

    @default_initial_values({"v", "isyn_exc", "isyn_exc2",
                             "isyn_inh", "isyn_inh2"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
            v_thresh=-50.0,  tau_refrac=0.1,
            i_offset=0.0, v=-65.0,
            isyn_exc=0.0, isyn_exc2=0.0, isyn_inh=0.0, isyn_inh2=0.0,
            tau_syn_E=5.0, tau_syn_E2=10.0, tau_syn_I=5.0, tau_syn_I2=10.0,
            e_rev_E=0.0, e_rev_E2=5.0, e_rev_I=-70.0, e_rev_I2=-70.0):

        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)

        synapse_type = SynapseTypeExponential2E2I(
            tau_syn_E,
            tau_syn_E2,
            tau_syn_I,
            tau_syn_I2,
            isyn_exc,
            isyn_exc2,
            isyn_inh,
            isyn_inh2
            )

        input_type = InputTypeConductance2E2I(
            e_rev_E,
            e_rev_E2,
            e_rev_I,
            e_rev_I2
            )

        threshold_type = ThresholdTypeStatic(v_thresh)

        super(IFCondExp2E2I, self).__init__(
            model_name="IF_cond_exp_2E2I", binary="IF_cond_exp_2E2I.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
