"""
IFCurrentExponentialPopulation
"""
from spynnaker.pyNN.models.neuron.neuron_models\
    .neuron_model_leaky_integrate_and_fire \
    import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_exponential \
    import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.input_types.input_type_current \
    import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types.threshold_type_static \
    import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.abstract_population_vertex \
    import AbstractPopulationVertex


class IFCurrentExponentialPopulation(AbstractPopulationVertex):
    """
    IFCurrentExponentialPopulation: model which represents a leaky intergate
    and fire model with a exponetial decay curve and based off current.
    """

    _model_based_max_atoms_per_core = 256

    def __init__(self, n_neurons, machine_time_step, timescale_factor,
                 spikes_per_second=None, ring_buffer_sigma=None,
                 constraints=None, label=None,
                 tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
                 v_thresh=-50.0, tau_syn_E=5.0, tau_syn_I=5.0, tau_refrac=0.1,
                 i_offset=0, v_init=None):

        neuron_model = NeuronModelLeakyIntegrateAndFire(
            machine_time_step, v_init, v_rest, tau_m, cm, i_offset, v_reset,
            tau_refrac)
        synapse_type = SynapseTypeExponential(
            machine_time_step, tau_syn_E, tau_syn_I)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)

        AbstractPopulationVertex.__init__(
            self, n_neurons=n_neurons, binary="IF_curr_exp.aplx", label=label,
            max_atoms_per_core=(IFCurrentExponentialPopulation.
                                _model_based_max_atoms_per_core),
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            model_name="IF_curr_exp", neuron_model=neuron_model,
            input_type=input_type, synapse_type=synapse_type,
            threshold_type=threshold_type, constraints=constraints)

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        """

        :param new_value:
        :return:
        """
        IFCurrentExponentialPopulation.\
            _model_based_max_atoms_per_core = new_value
