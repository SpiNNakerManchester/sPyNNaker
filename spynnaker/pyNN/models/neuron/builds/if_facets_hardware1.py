from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neuron.abstract_population_vertex \
    import AbstractPopulationVertex


class IFFacetsConductancePopulation(AbstractPopulationVertex):
    """ Leaky integrate and fire neuron with conductance-based synapses and\
        fixed threshold as it is resembled by the FACETS Hardware Stage 1
    """

    # noinspection PyPep8Naming
    def __init__(
            self, n_neurons, machine_time_step, timescale_factor,
            spikes_per_second=None, ring_buffer_sigma=None,
            incoming_spike_buffer_size=None, constraints=None, label=None,
            g_leak=40.0, tau_syn_E=30.0, tau_syn_I=30.0, v_thresh=-55.0,
            v_rest=-65.0, e_rev_I=-80, v_reset=-80.0, v_init=None):
        raise exceptions.SpynnakerException(
            "This neuron model is currently not supported by the tool chain")

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        pass
