from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex
from spynnaker.pyNN.models.abstract_models.abstract_exp_population_vertex \
    import AbstractExponentialPopulationVertex
from spynnaker.pyNN.models.abstract_models.abstract_integrate_and_fire_properties \
    import AbstractIntegrateAndFireProperties
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.abstract_models.abstract_conductance_vertex \
    import AbstractConductanceVertex


class HHConductanceExponentialPopulation(AbstractExponentialPopulationVertex,
                                         AbstractConductanceVertex,
                                         AbstractIntegrateAndFireProperties,
                                         AbstractPopulationVertex):

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma, constraints=None,
                 label=None, gbar_K=6.0, cm=0.2, e_rev_Na=50.0, tau_syn_E=0.2,
                 tau_syn_I=2.0, i_offset=0.0, g_leak=0.01, e_rev_E=0.0,
                 gbar_Na=20.0, e_rev_leak=-65.0, e_rev_I=-80, e_rev_K=-90.0,
                 v_offset=-63, v_init=None):
        """
        Single-compartment Hodgkin-Huxley model
        """
        raise exceptions.SpynnakerException("This neuron model is currently not"
                                            " supported by the tool chain....."
                                            "watch this space")

    def model_name(self):
        raise exceptions.SpynnakerException("This neuron model is currently not"
                                            " supported by the tool chain....."
                                            "watch this space")

    def get_parameters(self):
        raise exceptions.SpynnakerException("This neuron model is currently not"
                                            " supported by the tool chain....."
                                            "watch this space")

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        raise exceptions.SpynnakerException("This neuron model is currently not"
                                            " supported by the tool chain....."
                                            "watch this space")

    def is_population_vertex(self):
        return True

    def is_integrate_and_fire_vertex(self):
        pass

    def is_conductive(self):
        pass

    def is_exp_vertex(self):
        pass

    def is_recordable(self):
        pass

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        pass
