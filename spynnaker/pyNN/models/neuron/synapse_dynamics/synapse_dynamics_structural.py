import numpy as np

from data_specification.enums.data_type import DataType

from spynnaker.pyNN import ProjectionApplicationEdge
from spynnaker.pyNN.models.neural_projections.projection_machine_edge import ProjectionMachineEdge
from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_plastic_synapse_dynamics \
    import AbstractPlasticSynapseDynamics
from spynnaker.pyNN.models.neuron.synapse_dynamics.synapse_dynamics_stdp \
    import SynapseDynamicsSTDP
from spynnaker.pyNN.models.neuron.synapse_dynamics.synapse_dynamics_static \
    import SynapseDynamicsStatic
from spynnaker.pyNN.utilities import constants


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

        # Addition information -- used for SDRAM usage
        self._actual_sdram_usage = {}

    @property
    def p_rew(self):
        return self._p_rew

    @property
    def actual_sdram_usage(self):
        return self._actual_sdram_usage

    @property
    def approximate_sdram_usage(self):
        return self._approximate_sdram_usage

    def write_parameters(self, spec, region, machine_time_step, weight_scales, application_graph, machine_graph,
                         app_vertex, post_slice, machine_vertex, graph_mapper, routing_info):
        self.super.write_parameters(spec, region, machine_time_step, weight_scales)
        spec.comment("Writing structural plasticity parameters")

        # # Switch focus to the region:
        # spec.switch_write_focus(region)
        #
        # # Word aligned for convenience
        #
        spec.write_value(data=int(self._p_rew * machine_time_step), data_type=DataType.INT32)
        spec.write_value(data=int(self._s_max), data_type=DataType.INT32)
        spec.write_value(data=self._sigma_form_forward, data_type=DataType.S1615)
        spec.write_value(data=self._sigma_form_lateral, data_type=DataType.S1615)
        spec.write_value(data=self._p_form_forward, data_type=DataType.S1615)
        spec.write_value(data=self._p_form_lateral, data_type=DataType.S1615)
        spec.write_value(data=self._p_elim_dep, data_type=DataType.S1615)
        spec.write_value(data=self._p_elim_pot, data_type=DataType.S1615)
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
        population_to_subpopulation_information = {}

        # Can figure out the presynaptic subvertices (machine vertices) for the current machine vertex
        # by calling graph_mapper.get_machine_edges for the relevant application edges (i.e. the structural ones)
        # This allows me to find the partition (?) which then plugged into routing_info can give me the keys
        presynaptic_machine_vertices = []
        structural_application_edges = []
        structural_machine_edges = []
        no_pre_populations = 0
        max_subpartitions = 0

        for app_edge in application_graph.get_edges_ending_at_vertex(app_vertex):
            for synapse_info in app_edge.synapse_information:
                if synapse_info.synapse_dynamics is self:
                    structural_application_edges.append(app_edge)
                    population_to_subpopulation_information[app_edge.pre_vertex] = []
                    break

        no_pre_populations = len(structural_application_edges)
        # For each structurally plastic APPLICATION edge find the corresponding machine edges
        for machine_edge in machine_graph.get_edges_ending_at_vertex(machine_vertex):
            for synapse_info in machine_edge._synapse_information:
                if synapse_info.synapse_dynamics is self:
                    structural_machine_edges.append(machine_edge)
                    # For each structurally plastic MACHINE edge find the corresponding presynaptic subvertices
                    presynaptic_machine_vertices.append(machine_edge.pre_vertex)

        # For each presynaptic subvertex figure out the partition (?) to retrieve the key and n_atoms
        for vertex in presynaptic_machine_vertices:
            population_to_subpopulation_information[graph_mapper.get_application_vertex(vertex)].append(
                (routing_info.get_routing_info_from_pre_vertex(
                    vertex, constants.SPIKE_PARTITION_ID).first_key, graph_mapper.get_slice(vertex)[2]))

        for subpopulation_list in population_to_subpopulation_information.itervalues():
            max_subpartitions = np.maximum(max_subpartitions, len(subpopulation_list))
        # Table header
        spec.write_value(data=no_pre_populations, data_type=DataType.INT32)

        words_needed_to_be_written = max_subpartitions * 2
        total_words_written = 0
        for subpopulation_list in population_to_subpopulation_information.itervalues():
            # Population header(s)
            spec.write_value(data=len(subpopulation_list), data_type=DataType.INT32)
            words_written = 0
            for subpopulation_info in subpopulation_list:
                # Subpopulation information (i.e. key and number of atoms)
                # Key
                spec.write_value(data=subpopulation_info[0], data_type=DataType.INT32)
                # n_atoms
                spec.write_value(data=subpopulation_info[1], data_type=DataType.INT32)

                words_written += 2
            # If we didn't write enough to ensure equal sized blocks, add padding
            if words_written < words_needed_to_be_written:
                for _ in xrange(words_needed_to_be_written - words_written):
                    spec.write_value(data=-1, data_type=DataType.INT32)
            total_words_written += words_written + 4

        self.actual_sdram_usage[machine_vertex] = 4 * 16 + 4 * total_words_written

    def get_extra_sdram_usage_in_bytes(self, machine_in_edges):
        #
        relevant_edges = []
        for edge in machine_in_edges:
            for synapse_info in edge._synapse_information:
                if synapse_info.synapse_dynamics is self:
                    relevant_edges.append(edge)
        return 4 * (12 * len(relevant_edges))

    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types, in_edges=None):
        structure_size = 12 * 4 + 4 * 4  # parameters + rng seed
        self.structure_size = structure_size
        initial_size = self.super.get_parameters_sdram_usage_in_bytes(n_neurons, n_synapse_types)
        total_size = structure_size + initial_size
        pop_size = 0
        # approximate the size of the pop -> subpop table
        if in_edges is not None and isinstance(in_edges[0], ProjectionApplicationEdge):
            # Approximation gets computed here based on number of afferent edges
            # How many afferent application vertices?
            # How large are they?
            no_pre_vertices_estimate = 0
            for edge in in_edges:
                for synapse_info in edge.synapse_information:
                    if synapse_info.synapse_dynamics is self:
                        no_pre_vertices_estimate += 1 * np.ceil(edge.pre_vertex.n_atoms / 32.)
            no_pre_vertices_estimate *= 4
            pop_size += int(40 * (no_pre_vertices_estimate + len(in_edges)))
        elif in_edges is not None and isinstance(in_edges[0], ProjectionMachineEdge):
            pop_size += self.get_extra_sdram_usage_in_bytes(in_edges)
        return total_size + pop_size # bytes

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
