import numpy as np
import collections

from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge

from spynnaker.pyNN.models.neural_projections.projection_machine_edge import \
    ProjectionMachineEdge
from spynnaker.pyNN.models.neuron.synapse_dynamics. \
    abstract_plastic_synapse_dynamics \
    import AbstractPlasticSynapseDynamics
from spynnaker.pyNN.models.neuron.synapse_dynamics. \
    abstract_synapse_dynamics_structural import \
    AbstractSynapseDynamicsStructural
from spynnaker.pyNN.models.neuron.synapse_dynamics.synapse_dynamics_stdp \
    import SynapseDynamicsSTDP
from spynnaker.pyNN.models.neuron.synapse_dynamics.synapse_dynamics_static \
    import SynapseDynamicsStatic
from spynnaker.pyNN.utilities import constants


class SynapseDynamicsStructural(AbstractSynapseDynamicsStructural):
    def __init__(self, stdp_model=None, f_rew=10 ** 4, weight=0, delay=1,
                 s_max=32,
                 sigma_form_forward=2.5, sigma_form_lateral=1,
                 p_form_forward=0.16, p_form_lateral=1,
                 p_elim_dep=0.0245, p_elim_pot=1.36 * 10 ** -4,
                 grid=np.array([16, 16]), lateral_inhibition=0, random_partner=False,
                 seed=None):

        AbstractSynapseDynamicsStructural.__init__(self)
        self._f_rew = f_rew  # Hz
        self._p_rew = 1. / self._f_rew  # ms
        self._weight = weight
        self._delay = delay
        self._s_max = s_max  # maximum number of presynaptic neurons
        self._lateral_inhibition = lateral_inhibition
        self._sigma_form_forward = sigma_form_forward
        self._sigma_form_lateral = sigma_form_lateral
        self._p_form_forward = p_form_forward
        self._p_form_lateral = p_form_lateral
        self._p_elim_dep = p_elim_dep
        self._p_elim_pot = p_elim_pot
        self._grid = np.asarray(grid, dtype=int)
        self._random_partner = random_partner
        self._connections = {}

        self.fudge_factor = 1.3
        self._actual_row_max_length = self._s_max

        if stdp_model is not None:
            self.super = SynapseDynamicsSTDP(
                timing_dependence=stdp_model.timing_dependence,
                weight_dependence=stdp_model.weight_dependence,
                dendritic_delay_fraction=stdp_model._dendritic_delay_fraction,
                pad_to_length=self._s_max)
        else:
            self.super = SynapseDynamicsStatic(pad_to_length=self._s_max)

        # Generate a seed for the RNG on chip that should be the same for all
        # of the cores that have my learning rule
        self._rng = np.random.RandomState(seed)
        self._seeds = []
        for _ in range(4):
            self._seeds.append(self._rng.randint(0x7FFFFFFF))

        # Addition information -- used for SDRAM usage
        self._actual_sdram_usage = {}

        self._ff_distance_probabilities = \
            self.generate_distance_probability_array(
                self._p_form_forward,
                self._sigma_form_forward)
        self._lat_distance_probabilities = \
            self.generate_distance_probability_array(
                self._p_form_lateral,
                self._sigma_form_lateral)

    def distance(self, x0, x1, grid=np.asarray([16, 16]), type='euclidian'):
        x0 = np.asarray(x0)
        x1 = np.asarray(x1)
        delta = np.abs(x0 - x1)
        #     delta = np.where(delta > grid * .5, delta - grid, delta)
        #     print delta, grid
        if delta[0] > grid[0] * .5 and grid[0] > 0:
            delta[0] -= grid[0]

        if delta[1] > grid[1] * .5 and grid[1] > 0:
            delta[1] -= grid[1]

        if type == 'manhattan':
            return np.abs(delta).sum(axis=-1)
        return np.sqrt((delta ** 2).sum(axis=-1))

    def generate_distance_probability_array(self, probability, sigma):
        euclidian_distances = np.ones(self._grid ** 2) * np.nan
        for row in range(euclidian_distances.shape[0]):
            for column in range(euclidian_distances.shape[1]):
                if self._grid[0] > 1:
                    pre = (row // self._grid[0], row % self._grid[1])
                    post = (column // self._grid[0], column % self._grid[1])
                else:
                    pre = (0, row % self._grid[1])
                    post = (0, column % self._grid[1])
                euclidian_distances[row, column] = self.distance(
                    pre,
                    post,
                    grid=self._grid,
                    type='euclidian')
        largest_squared_distance = np.max(euclidian_distances ** 2)
        squared_distances = np.arange(largest_squared_distance)
        raw_probabilities = probability * (
            np.e ** (-(squared_distances) / (2 * (sigma ** 2))))
        quantised_probabilities = raw_probabilities * ((2 ** 16) - 1)
        # Quantize probabilities and cast as uint16 / short
        unfiltered_probabilities = quantised_probabilities.astype(
            dtype="uint16")
        # Only return probabilities which are non-zero
        filtered_probabilities = unfiltered_probabilities[
            unfiltered_probabilities > 0]
        if filtered_probabilities.size % 2 != 0:
            filtered_probabilities = np.concatenate(
                (filtered_probabilities,
                 np.zeros(
                     filtered_probabilities.size % 2, dtype="uint16")))

        return filtered_probabilities

    @property
    def p_rew(self):
        return self._p_rew

    @property
    def actual_sdram_usage(self):
        return self._actual_sdram_usage

    @property
    def approximate_sdram_usage(self):
        return self._approximate_sdram_usage

    def write_parameters(self, spec, region, machine_time_step, weight_scales,
                         application_graph, machine_graph,
                         app_vertex, post_slice, machine_vertex, graph_mapper,
                         routing_info):
        self.super.write_parameters(spec, region, machine_time_step,
                                    weight_scales)
        spec.comment("Writing structural plasticity parameters")
        if spec.current_region != constants.POPULATION_BASED_REGIONS. \
                SYNAPSE_DYNAMICS.value:
            spec.switch_write_focus(region)

        if self._p_rew * 1000. < machine_time_step / 1000.:
            # Fast rewiring
            spec.write_value(data=1)
            spec.write_value(
                data=int(machine_time_step / (self._p_rew * 10 ** 6)),
                data_type=DataType.INT32)
        else:
            # Slow rewiring
            spec.write_value(data=0)
            spec.write_value(
                data=int((self._p_rew * 10 ** 6) / float(machine_time_step)),
                data_type=DataType.INT32)

        # TODO when implementing inhibitory connections add another
        # spec.write_value here multiplied by weight_scale[1]
        spec.write_value(data=int(round(self._weight * weight_scales[0])),
                         data_type=DataType.INT32)
        spec.write_value(data=int(round(self._weight * weight_scales[1])),
                         data_type=DataType.INT32)
        spec.write_value(data=self._delay, data_type=DataType.INT32)
        spec.write_value(data=int(self._s_max), data_type=DataType.INT32)
        spec.write_value(data=int(self._lateral_inhibition), data_type=DataType.INT32)
        spec.write_value(data=int(self._random_partner), data_type=DataType.INT32)
        # write total number of atoms in the application vertex
        spec.write_value(data=app_vertex.n_atoms, data_type=DataType.INT32)
        # write local low, high and number of atoms
        spec.write_value(data=post_slice[0], data_type=DataType.INT32)
        spec.write_value(data=post_slice[1], data_type=DataType.INT32)
        spec.write_value(data=post_slice[2], data_type=DataType.INT32)

        # write the grid size for periodic boundary distance computation
        spec.write_value(data=self._grid[0], data_type=DataType.INT32)
        spec.write_value(data=self._grid[1], data_type=DataType.INT32)

        # write probabilities for elimination
        spec.write_value(data=int(self._p_elim_dep * (2 ** 32 - 1)),
                         data_type=DataType.UINT32)
        spec.write_value(data=int(self._p_elim_pot * (2 ** 32 - 1)),
                         data_type=DataType.UINT32)

        # write the random seed (4 words), generated randomly,
        # but the same for all postsynaptic vertices!
        for seed in self._seeds:
            spec.write_value(data=seed)

        # write local seed (4 words), generated randomly!
        for _ in range(4):
            spec.write_value(data=np.random.randint(0x7FFFFFFF))

        # Compute the max number of presynaptic subpopulations
        population_to_subpopulation_information = collections.OrderedDict()

        # Can figure out the presynaptic subvertices (machine vertices)
        # for the current machine vertex
        # by calling graph_mapper.get_machine_edges for the relevant
        # application edges (i.e. the structural ones)
        # This allows me to find the partition (?) which then plugged
        # into routing_info can give me the keys
        presynaptic_machine_vertices = []
        structural_application_edges = []
        structural_machine_edges = []
        max_subpartitions = 0

        for app_edge in application_graph.get_edges_ending_at_vertex(
                app_vertex):
            if isinstance(app_edge, ProjectionApplicationEdge):
                for synapse_info in app_edge.synapse_information:
                    if synapse_info.synapse_dynamics is self:
                        structural_application_edges.append(app_edge)
                        population_to_subpopulation_information[
                            app_edge.pre_vertex] = []
                        break

        no_pre_populations = len(structural_application_edges)
        # For each structurally plastic APPLICATION edge find the c
        # orresponding machine edges
        for machine_edge in machine_graph.get_edges_ending_at_vertex(
                machine_vertex):
            if isinstance(machine_edge, ProjectionMachineEdge):
                for synapse_info in machine_edge._synapse_information:
                    if synapse_info.synapse_dynamics is self:
                        structural_machine_edges.append(machine_edge)
                        # For each structurally plastic MACHINE edge find the
                        # corresponding presynaptic subvertices
                        presynaptic_machine_vertices.append(
                            machine_edge.pre_vertex)

        # For each presynaptic subvertex figure out the partition (?)
        # to retrieve the key and n_atoms
        for vertex in presynaptic_machine_vertices:
            population_to_subpopulation_information[
                graph_mapper.get_application_vertex(vertex)].append(
                (routing_info.get_routing_info_from_pre_vertex(
                    vertex, constants.SPIKE_PARTITION_ID).first_key,
                 graph_mapper.get_slice(vertex)[2],
                 graph_mapper.get_slice(vertex)[0],
                routing_info.get_routing_info_from_pre_vertex(
                    vertex, constants.SPIKE_PARTITION_ID).first_mask))

        for subpopulation_list in \
                population_to_subpopulation_information.itervalues():
            max_subpartitions = np.maximum(max_subpartitions,
                                           len(subpopulation_list))

        # Current machine vertex key (for future checks)
        current_key = routing_info.get_routing_info_from_pre_vertex(
            machine_vertex, constants.SPIKE_PARTITION_ID)

        if current_key is not None:
            current_key = current_key.first_key
        else:
            current_key = -1

        # Table header
        spec.write_value(data=no_pre_populations, data_type=DataType.INT32)

        total_words_written = 0
        for subpopulation_list in \
                population_to_subpopulation_information.itervalues():
            # Population header(s)
            # Number of subpopulations
            spec.write_value(data=len(subpopulation_list),
                             data_type=DataType.UINT16)

            # Custom header for commands / controls

            # currently, controls = 1 if the subvertex (on the current core)
            # is part of this population
            controls = 1 if current_key in np.asarray(subpopulation_list)[:,
                                           0] else 0
            spec.write_value(data=controls, data_type=DataType.UINT16)

            spec.write_value(
                data=np.sum(np.asarray(subpopulation_list)[:, 1]) if len(
                    subpopulation_list) > 0 else 0,
                data_type=DataType.INT32)
            words_written = 2
            # Ensure the following values are written in ascending
            # order of low_atom (implicit)
            dt = np.dtype(
                [('key', 'int'), ('n_atoms', 'int'), ('lo_atom', 'int'), ('mask', 'uint')])
            structured_array = np.array(subpopulation_list, dtype=dt)
            sorted_info_list = np.sort(structured_array, order='lo_atom')
            for subpopulation_info in sorted_info_list:
                # Subpopulation information (i.e. key and number of atoms)
                # Key
                spec.write_value(data=subpopulation_info[0],
                                 data_type=DataType.INT32)
                # n_atoms
                spec.write_value(data=subpopulation_info[1],
                                 data_type=DataType.INT32)
                # lo_atom
                spec.write_value(data=subpopulation_info[2],
                                 data_type=DataType.INT32)
                # mask
                spec.write_value(data=subpopulation_info[3],
                                 data_type=DataType.UINT32)

                words_written += 4

            total_words_written += words_written * 4

        # Now we write the probability tables for formation
        # (feedforward and lateral)
        spec.write_value(data=self._ff_distance_probabilities.size,
                         data_type=DataType.INT32)
        spec.write_array(self._ff_distance_probabilities.view(dtype=np.uint32))
        total_words_written += self._ff_distance_probabilities.size // 2
        spec.write_value(data=self._lat_distance_probabilities.size,
                         data_type=DataType.INT32)
        spec.write_array(
            self._lat_distance_probabilities.view(dtype=np.uint32))
        total_words_written += self._lat_distance_probabilities.size // 2

        # Setting up Post to Pre table
        post_to_pre_table = np.ones((post_slice.n_atoms, self._s_max),
                                    dtype=np.int32) * -1
        for row in self._connections[post_slice.lo_atom]:
            if row[0].size > 0 and row[1].post_vertex is app_vertex:
                for source, target, weight, delay, syn_type in row[0]:
                    # Select pre vertex
                    pre_vertex_slice = graph_mapper._slice_by_machine_vertex[
                        row[2].pre_vertex]
                    pre_vertex_id = source - pre_vertex_slice.lo_atom
                    masked_pre_vertex_id = pre_vertex_id & (2 ** 17 - 1)
                    # Select population index
                    pop_index = population_to_subpopulation_information.keys().index(
                        row[1].pre_vertex)
                    masked_pop_index = pop_index & (2 ** 9 - 1)
                    # Select subpopulation index
                    dt = np.dtype(
                        [('key', 'int'), ('n_atoms', 'int'),
                         ('lo_atom', 'int'), ('mask', 'uint')])
                    structured_array = np.array(
                        population_to_subpopulation_information[
                            row[1].pre_vertex], dtype=dt)
                    sorted_info_list = np.sort(structured_array,
                                               order='lo_atom')
                    # find index where lo_atom equals the one in pre_vertex_slice
                    subpop_index = np.argwhere(sorted_info_list[
                                                   'lo_atom'] == pre_vertex_slice.lo_atom).ravel()[
                        0]
                    masked_sub_pop_index = subpop_index & (2 ** 9 - 1)
                    # identifier combines the vertex, pop and subpop
                    # into 1 x 32 bit word
                    identifier = (masked_pop_index << (32 - 8)) | (
                    masked_sub_pop_index << 16) | masked_pre_vertex_id
                    try:
                        synaptic_entry = np.argmax(post_to_pre_table[
                                                       target - post_slice.lo_atom] == -1).ravel()[
                            0]
                    except:
                        break
                    post_to_pre_table[
                        target - post_slice.lo_atom, synaptic_entry] = identifier

        spec.write_array(post_to_pre_table.ravel())

        total_words_written += (post_to_pre_table.size)
        self.actual_sdram_usage[
            machine_vertex] = 4 * 27 + 4 * total_words_written

    def get_extra_sdram_usage_in_bytes(self, machine_in_edges):
        #
        relevant_edges = []
        for edge in machine_in_edges:
            for synapse_info in edge._synapse_information:
                if synapse_info.synapse_dynamics is self:
                    relevant_edges.append(edge)
        return int(self.fudge_factor * (4 * (12 * len(relevant_edges))))

    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types,
                                            in_edges=None):
        structure_size = 27 * 4 + 4 * 4  # parameters + rng seed
        post_to_pre_table_size = n_neurons * self._s_max * 4
        structure_size += post_to_pre_table_size

        self.structure_size = structure_size
        initial_size = self.super.get_parameters_sdram_usage_in_bytes(
            n_neurons, n_synapse_types)
        total_size = structure_size + initial_size
        # Aproximation of the sizes of both probability vs distance tables
        total_size += (80 * 4)
        pop_size = 0
        # approximate the size of the pop -> subpop table
        if in_edges is not None and isinstance(in_edges[0],
                                               ProjectionApplicationEdge):
            # Approximation gets computed here based on number of
            # afferent edges
            # How many afferent application vertices?
            # How large are they?
            no_pre_vertices_estimate = 0
            for edge in in_edges:
                for synapse_info in edge.synapse_information:
                    if synapse_info.synapse_dynamics is self:
                        no_pre_vertices_estimate += 1 * np.ceil(
                            edge.pre_vertex.n_atoms / 32.)
            no_pre_vertices_estimate *= 4
            pop_size += int(50 * (no_pre_vertices_estimate + len(in_edges)))
        elif in_edges is not None and isinstance(in_edges[0],
                                                 ProjectionMachineEdge):
            pop_size += self.get_extra_sdram_usage_in_bytes(in_edges)
        return int(self.fudge_factor * (total_size + pop_size))  # bytes

    def get_plastic_synaptic_data(self, connections, connection_row_indices,
                                  n_rows, post_vertex_slice,
                                  n_synapse_types, app_edge, machine_edge):
        if not post_vertex_slice.lo_atom in self._connections.keys():
            self._connections[post_vertex_slice.lo_atom] = []
        self._connections[post_vertex_slice.lo_atom].append(
            (connections, app_edge, machine_edge))
        if isinstance(self.super, AbstractPlasticSynapseDynamics):
            return self.super.get_plastic_synaptic_data(connections,
                                                        connection_row_indices,
                                                        n_rows,
                                                        post_vertex_slice,
                                                        n_synapse_types)
        else:
            return self.super.get_static_synaptic_data(connections,
                                                       connection_row_indices,
                                                       n_rows,
                                                       post_vertex_slice,
                                                       n_synapse_types)

    def get_static_synaptic_data(self, connections, connection_row_indices,
                                 n_rows, post_vertex_slice,
                                 n_synapse_types, app_edge, machine_edge):
        if not post_vertex_slice.lo_atom in self._connections.keys():
            self._connections[post_vertex_slice.lo_atom] = []
        self._connections[post_vertex_slice.lo_atom].append(
            (connections, app_edge, machine_edge))
        return self.super.get_static_synaptic_data(connections,
                                                   connection_row_indices,
                                                   n_rows, post_vertex_slice,
                                                   n_synapse_types)

    def get_n_words_for_plastic_connections(self, n_connections):
        try:
            self._actual_row_max_length = self.super.get_n_words_for_plastic_connections(
                n_connections)
            return self._actual_row_max_length
        except:
            self._actual_row_max_length = self.super.get_n_words_for_static_connections(n_connections)
            return self._actual_row_max_length

    def get_n_words_for_static_connections(self, n_connections):
        self._actual_row_max_length = self.super.get_n_words_for_static_connections(n_connections)
        return self._actual_row_max_length

    def get_n_synapses_in_rows(self, pp_size, fp_size=None):
        if fp_size is not None:
            return self.super.get_n_synapses_in_rows(pp_size, fp_size)
        else:
            return self.super.get_n_synapses_in_rows(pp_size)

    def read_plastic_synaptic_data(self, post_vertex_slice, n_synapse_types,
                                   pp_size, pp_data, fp_size, fp_data):
        return self.super.read_plastic_synaptic_data(post_vertex_slice,
                                                     n_synapse_types, pp_size,
                                                     pp_data, fp_size,
                                                     fp_data)

    def read_static_synaptic_data(self, post_vertex_slice, n_synapse_types,
                                  ff_size, ff_data):
        return self.super.read_static_synaptic_data(post_vertex_slice,
                                                    n_synapse_types, ff_size,
                                                    ff_data)

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

    def get_n_static_words_per_row(self, ff_size):
        return self.super.get_n_static_words_per_row(ff_size)

    def is_same_as(self, synapse_dynamics):
        if not isinstance(synapse_dynamics, AbstractSynapseDynamicsStructural):
            return False
        return (
            self._f_rew == synapse_dynamics._f_rew and
            self._s_max == synapse_dynamics._s_max and
            np.isclose(self._sigma_form_forward,
                       synapse_dynamics._sigma_form_forward) and
            np.isclose(self._sigma_form_lateral,
                       synapse_dynamics._sigma_form_lateral) and
            np.isclose(self._p_form_forward,
                       synapse_dynamics._p_form_forward) and
            np.isclose(self._p_form_lateral,
                       synapse_dynamics._p_form_lateral) and
            np.isclose(self._p_elim_dep, synapse_dynamics._p_elim_dep) and
            np.isclose(self._p_elim_pot, synapse_dynamics._p_elim_pot)
        )
