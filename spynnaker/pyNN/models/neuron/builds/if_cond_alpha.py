from spynnaker.pyNN.models.components.neuron_components.\
    abstract_population_vertex import AbstractPopulationVertex
from spynnaker.pyNN.models.components.model_components.\
    integrate_and_fire_component import IntegrateAndFireComponent
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.components.inputs_components.\
    conductance_component import ConductanceComponent


class IFConductanceAlphaPopulation(
        ConductanceComponent, IntegrateAndFireComponent,
        AbstractPopulationVertex):
    """
    IFConductanceAlphaPopulation
    """

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma, constraints=None,
                 label=None, tau_m=20, cm=1.0, e_rev_E=0.0, e_rev_I=-70.0,
                 v_rest=-65.0, v_reset=-65.0, v_thresh=-50.0, tau_syn_E=0.3,
                 tau_syn_I=0.5, tau_refrac=0.1, i_offset=0, v_init=None):
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
