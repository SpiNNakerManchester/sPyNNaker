"""
IFCurrentAlphaPopulation
"""
from spynnaker.pyNN.models.abstract_models.abstract_population_vertex import \
    AbstractPopulationVertex
from spynnaker.pyNN.models.abstract_models.abstract_model_components.\
    abstract_integrate_and_fire_properties \
    import AbstractIntegrateAndFireProperties
from spynnaker.pyNN import exceptions


class IFCurrentAlphaPopulation(AbstractIntegrateAndFireProperties,
                               AbstractPopulationVertex):
    """
    IFCurrentAlphaPopulation
    """

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma, constraints=None,
                 label=None, tau_m=20, cm=1.0, v_rest=-65.0, v_reset=-65.0,
                 v_thresh=-50.0, tau_syn_E=0.5, tau_syn_I=0.5, tau_refrac=0.1,
                 i_offset=0, v_init=None):
        """
        Leaky integrate and fire model with fixed threshold and alpha-function\
        -shaped post-synaptic current.
        """
        raise exceptions.SpynnakerException(
            "This neuron model is currently not supported by the tool chain")

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """

        :param vertex_slice:
        :param graph:
        :return:
        """
        raise exceptions.SpynnakerException(
            "This neuron model is currently not supported by the tool chain")

    def model_name(self):
        """

        :return:
        """
        raise exceptions.SpynnakerException(
            "This neuron model is currently not supported by the tool chain")

    def get_parameters(self):
        """

        :return:
        """
        raise exceptions.SpynnakerException(
            "This neuron model is currently not supported by the tool chain")

    def is_population_vertex(self):
        """

        :return:
        """
        return True

    def get_n_synapse_type_bits(self):
        """

        :return:
        """
        pass

    def is_integrate_and_fire_vertex(self):
        """

        :return:
        """
        pass

    def write_synapse_parameters(self, spec, subvertex, vertex_slice):
        """

        :param spec:
        :param subvertex:
        :param vertex_slice:
        :return:
        """
        pass

    def is_recordable(self):
        """

        :return:
        """
        pass

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        """

        :param new_value:
        :return:
        """
        pass
