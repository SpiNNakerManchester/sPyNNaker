from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neuron.bag_of_neurons_vertex \
    import BagOfNeuronsVertex


class EIFConductanceAlphaPopulation(BagOfNeuronsVertex):

    """ Exponential integrate and fire neuron with spike triggered and \
        sub-threshold adaptation currents (isfa, ista reps.)
    """

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, timescale_factor,
                 spikes_per_second=None, ring_buffer_sigma=None,
                 incoming_spike_buffer_size=None, constraints=None, label=None,
                 tau_m=9.3667, cm=0.281, v_rest=-70.6,
                 v_reset=-70.6, v_thresh=-50.4, tau_syn_E=5.0, tau_syn_I=0.5,
                 tau_refrac=0.1, i_offset=0.0, a=4.0, b=0.0805, v_spike=-40.0,
                 tau_w=144.0, e_rev_E=0.0, e_rev_I=-80.0, delta_T=2.0,
                 v_init=None):

        raise exceptions.SpynnakerException(
            "This neuron model is currently not supported by the tool chain")

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        pass
