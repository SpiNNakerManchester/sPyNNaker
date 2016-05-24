from spynnaker.pyNN.models.neuron.abstract_population_model import \
    AbstractPopulationModel
from spynnaker.pyNN.models.neuron.neuron_models.neuron_model_izh \
    import NeuronModelIzh
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_exponential \
    import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.input_types.input_type_current \
    import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types.threshold_type_static \
    import ThresholdTypeStatic

_IZK_THRESHOLD = 30.0


class IzkCurrExp(AbstractPopulationModel):

    _model_based_max_atoms_per_core = 255

    default_parameters = {
        'a': 0.02, 'c': -65.0, 'b': 0.2, 'd': 2.0, 'i_offset': 0,
        'u_init': -14.0, 'v_init': -70.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
        'machine_time_step': 1000}

    state_variables = {'v', 'u'}

    neuron_model = NeuronModelIzh
    synapse_type = SynapseTypeExponential
    input_type = InputTypeCurrent
    threshold_type = ThresholdTypeStatic

    binary_name = "IZK_curr_exp.aplx"
    model_name = "IZK_curr_exp"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        IzkCurrExp._model_based_max_atoms_per_core = new_value