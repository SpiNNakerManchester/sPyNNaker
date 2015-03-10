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


class IFFacetsConductancePopulation(AbstractConductanceVertex,
                                    AbstractIntegrateAndFireProperties,
                                    AbstractPopulationVertex):

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma, constraints=None,
                 label=None, g_leak=40.0, tau_syn_E=30.0, tau_syn_I=30.0,
                 v_thresh=-55.0, v_rest=-65.0, e_rev_I=-80, v_reset=-80.0,
                 v_init=None):
        """
        Leaky integrate and fire model with conductance-based synapses and \
        fixed threshold as it is resembled by the FACETS Hardware Stage 1.
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

    def get_n_synapse_type_bits(self):
        pass

    def is_integrate_and_fire_vertex(self):
        pass

    def is_conductive(self):
        pass

    def write_synapse_parameters(self, spec, subvertex, vertex_slice):
        pass

    def is_recordable(self):
        pass

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        pass
