from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex
from spynnaker.pyNN.models.abstract_models.abstract_model_components.\
    abstract_integrate_and_fire_properties \
    import AbstractIntegrateAndFireProperties
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.abstract_models.abstract_model_components.\
    abstract_conductance_vertex import AbstractConductanceVertex


class IFConductanceAlphaPopulation(
        AbstractConductanceVertex, AbstractIntegrateAndFireProperties,
        AbstractPopulationVertex):

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma, constraints=None,
                 label=None):
        """
        Leaky integrate and fire model with fixed threshold and alpha-function\
        -shaped post-synaptic conductance.
        """
        raise exceptions.SpynnakerException(
            "This neuron model is currently not supported by the tool chain")

    def model_name(self):
        raise exceptions.SpynnakerException(
            "This neuron model is currently not supported by the tool chain")

    def get_parameters(self):
        raise exceptions.SpynnakerException(
            "This neuron model is currently not supported by the tool chain")

    def get_global_parameters(self):
        raise exceptions.SpynnakerException(
            "This neuron model is currently not supported by the tool chain")

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        raise exceptions.SpynnakerException(
            "This neuron model is currently not supported by the tool chain")

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        pass

    def is_population_vertex(self):
        return True

    def get_n_synapse_type_bits(self):
        pass

    def is_integrate_and_fire_vertex(self):
        pass

    def is_conductance(self):
        pass

    def write_synapse_parameters(self, spec, subvertex, vertex_slice):
        pass

    def is_recordable(self):
        pass
