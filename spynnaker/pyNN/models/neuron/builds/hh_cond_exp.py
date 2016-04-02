from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neuron.abstract_population_vertex \
    import AbstractPopulationVertex


class HHCondExp(AbstractPopulationVertex):
    """ Single-compartment Hodgkin-Huxley model with exponentially decaying \
        current input
    """

    # noinspection PyPep8Naming
    def __init__(
            self, n_neurons, machine_time_step, timescale_factor,
            spikes_per_second=None, ring_buffer_sigma=None,
            incoming_spike_buffer_size=None, constraints=None, label=None,
            gbar_K=6.0, cm=0.2, e_rev_Na=50.0, tau_syn_E=0.2, tau_syn_I=2.0,
            i_offset=0.0, g_leak=0.01, e_rev_E=0.0, gbar_Na=20.0,
            e_rev_leak=-65.0, e_rev_I=-80, e_rev_K=-90.0, v_offset=-63,
            v_init=None):
        raise exceptions.SpynnakerException(
            "This neuron model is currently not supported by the tool chain")

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        pass
