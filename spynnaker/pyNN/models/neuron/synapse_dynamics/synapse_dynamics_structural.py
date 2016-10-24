import numpy as np

from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_plastic_synapse_dynamics \
    import AbstractPlasticSynapseDynamics
from spynnaker.pyNN.models.neuron.synapse_dynamics.synapse_dynamics_stdp \
    import SynapseDynamicsSTDP
from spynnaker.pyNN.models.neuron.synapse_dynamics.synapse_dynamics_static \
    import SynapseDynamicsStatic


class SynapseDynamicsStructural(AbstractPlasticSynapseDynamics):
    def __init__(self, stdp_model=None, f_rew=10 ** 4, s_max=32,
                 sigma_form_forward=2.5, sigma_form_lateral=1,
                 p_form_forward=0.16, p_form_lateral=1,
                 p_elim_dep=0.0245, p_elim_pot=1.36 * np.e ** -4, seed=None):

        if stdp_model is not None:
            self.super = SynapseDynamicsSTDP(timing_dependence=stdp_model.timing_dependence,
                                             weight_dependence=stdp_model.weight_dependence,
                                             dendritic_delay_fraction=stdp_model._dendritic_delay_fraction,
                                             mad=stdp_model._mad)
        else:
            self.super = SynapseDynamicsStatic()

        self._f_rew = f_rew  # Hz
        self._p_rew = 1. / self._f_rew  # ms
        self._s_max = s_max  # maximum number of presynaptic neurons
        self._sigma_form_forward = sigma_form_forward
        self._sigma_form_lateral = sigma_form_lateral
        self._p_form_forward = p_form_forward
        self._p_form_lateral = p_form_lateral
        self._p_elim_dep = p_elim_dep
        self._p_elim_pot = p_elim_pot

        # Generate a seed for the RNG on chip that should be the same for all
        # of the cores that have my learning rule
        self._rng = np.random.RandomState(seed)
        self._seeds = []
        for _ in range(4):
            self._seeds.append(self._rng.randint(0x7FFFFFFF))

    @property
    def p_rew(self):
        return self._p_rew

    def write_parameters(self, spec, region, machine_time_step, weight_scales, application_graph, machine_graph,
                         app_vertex, post_slice, machine_vertex, graph_mapper, routing_info):
        self.super.write_parameters(spec, region, machine_time_step, weight_scales)
        spec.comment("Writing structural plasticity parameters")

        # Switch focus to the region:
        spec.switch_write_focus(region)
        #
        # # Word aligned for convenience
        #
        spec.write_value(data=int(self._p_rew / (machine_time_step * 1000)), data_type=DataType.INT32)
        spec.write_value(data=int(self._s_max), data_type=DataType.INT32)
        spec.write_value(data=self._sigma_form_forward, data_type=DataType.FLOAT_32)
        spec.write_value(data=self._sigma_form_lateral, data_type=DataType.FLOAT_32)
        spec.write_value(data=self._p_form_forward, data_type=DataType.FLOAT_32)
        spec.write_value(data=self._p_form_lateral, data_type=DataType.FLOAT_32)
        spec.write_value(data=self._p_elim_dep, data_type=DataType.FLOAT_32)
        spec.write_value(data=self._p_elim_pot, data_type=DataType.FLOAT_32)
        # write total number of atoms in the application vertex
        spec.write_value(data=app_vertex.n_atoms, data_type=DataType.INT32)
        # write local low, high and number of atoms
        spec.write_value(data=post_slice[0], data_type=DataType.INT32)
        spec.write_value(data=post_slice[1], data_type=DataType.INT32)
        spec.write_value(data=post_slice[2], data_type=DataType.INT32)
        # Write the random seed (4 words), generated randomly!

        for seed in self._seeds:
            spec.write_value(data=seed)

        # Compute the max number of presynaptic subpopulations
        number_of_subpopulations = dict()
        for app_edge in application_graph.get_edges_ending_at_vertex(app_vertex):
            relevant_edge = False
            for synapse_info in app_edge.synapse_information:
                if synapse_info.synapse_dynamics is self:
                    relevant_edge = True
            if relevant_edge:
                number_of_subpopulations[app_edge.pre_vertex] = 0

        for machine_edge in \
                machine_graph.get_edges_ending_at_vertex(machine_vertex):
            app_edge = graph_mapper.get_application_edge(machine_edge)
            relevant_edge = False
            for synapse_info in app_edge.synapse_information:
                if synapse_info.synapse_dynamics is self:
                    relevant_edge = True
            if relevant_edge:
                number_of_subpopulations[app_edge.pre_vertex] += 1
        pass
        # TODO write pre population information data structure
        # This is done by creating a lookup table from
        # population -> subpopulations.
        # subpopulation information of note: keys, number of atoms (hi, lo)

    def get_extra_sdram_usage_in_bytes(self, machine_in_edges):
        return 1 + 9 * len(machine_in_edges)

    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types, in_edges=None):
        # TODO modify parameter size when adding information about the lo and hi
        structure_size = 12 * 4 + 4 * 4  # parameters + rng seed
        initial_size = self.super.get_parameters_sdram_usage_in_bytes(n_neurons, n_synapse_types)
        total_size = structure_size + initial_size
        # approximate the size of the pop -> subpop table
        if in_edges is not None:
            # Approximation gets computed here based on number of afferent edges
            no_pre_vertices_estimate = 0
            for edge in in_edges:
                no_pre_vertices_estimate += np.ceil(edge.pre_vertex.n_atoms / 128.)
            total_size += int(4 * (no_pre_vertices_estimate + len(in_edges)) + no_pre_vertices_estimate)
        return total_size  # bytes

    def get_plastic_synaptic_data(self, connections, connection_row_indices, n_rows, post_vertex_slice,
                                  n_synapse_types):

        return self.super.get_plastic_synaptic_data(connections, connection_row_indices, n_rows, post_vertex_slice,
                                                    n_synapse_types)

    def get_n_words_for_plastic_connections(self, n_connections):
        return self.super.get_n_words_for_plastic_connections(n_connections)

    def get_n_synapses_in_rows(self, pp_size, fp_size):
        try:
            return self.super.get_n_synapses_in_rows(pp_size, fp_size)
        except TypeError:
            return self.super.get_n_synapses_in_rows(pp_size)

    def read_plastic_synaptic_data(self, post_vertex_slice, n_synapse_types, pp_size, pp_data, fp_size, fp_data):
        return self.super.read_plastic_synaptic_data(post_vertex_slice, n_synapse_types, pp_size, pp_data, fp_size,
                                                     fp_data)

    def get_n_fixed_plastic_words_per_row(self, fp_size):
        return self.super.get_n_fixed_plastic_words_per_row(fp_size)

    def get_n_plastic_plastic_words_per_row(self, pp_size):
        return self.super.get_n_plastic_plastic_words_per_row(pp_size)

    def are_weights_signed(self):
        return self.super.are_weights_signed()

    def get_vertex_executable_suffix(self):
        name = self.super.get_vertex_executable_suffix()
        name += "_structural"
        return name

    def is_same_as(self, synapse_dynamics):
        return (
            self._f_rew == synapse_dynamics._f_rew and
            self._s_max == synapse_dynamics._s_max and
            np.isclose(self._sigma_form_forward, synapse_dynamics._sigma_form_forward) and
            np.isclose(self._sigma_form_lateral, synapse_dynamics._sigma_form_lateral) and
            np.isclose(self._p_form_forward, synapse_dynamics._p_form_forward) and
            np.isclose(self._p_form_lateral, synapse_dynamics._p_form_lateral) and
            np.isclose(self._p_elim_dep, synapse_dynamics._p_elim_dep) and
            np.isclose(self._p_elim_pot, synapse_dynamics._p_elim_pot)
        )
