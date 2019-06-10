import collections
import numpy as np
from six import itervalues
from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.models.neural_projections import ProjectionMachineEdge
from .abstract_synapse_dynamics_structural import (
    AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.utilities import constants


class SynapseDynamicsStructuralCommon(AbstractSynapseDynamicsStructural):
    """ Common class that enables synaptic rewiring. It acts as a wrapper\
        around SynapseDynamicsStatic or SynapseDynamicsSTDP.\
        This means rewiring can operate in parallel with these\
        types of synapses.

        Written by Petrut Bogdan.

    :param f_rew: Frequency of rewiring (Hz). How many rewiring attempts will\
        be done per second.
    :type f_rew: int
    :param weight: Initial weight assigned to a newly formed connection
    :type weight: float
    :param delay: Delay assigned to a newly formed connection
    :type delay: int
    :param s_max: Maximum fan-in per target layer neuron
    :type s_max: int
    :param sigma_form_forward: Spread of feed-forward formation receptive field
    :type sigma_form_forward: float
    :param sigma_form_lateral: Spread of lateral formation receptive field
    :type sigma_form_lateral: float
    :param p_form_forward: Peak probability for feed-forward formation
    :type p_form_forward: float
    :param p_form_lateral: Peak probability for lateral formation
    :type p_form_lateral: float
    :param p_elim_pot: Probability of elimination of a potentiated synapse
    :type p_elim_pot: float
    :param p_elim_dep: Probability of elimination of a depressed synapse
    :type p_elim_dep: float
    :param grid: Grid shape
    :type grid: 2d int array
    :param lateral_inhibition: Flag whether to mark synapses formed within a\
        layer as inhibitory or excitatory
    :type lateral_inhibition: bool
    :param random_partner: \
        Flag whether to randomly select pre-synaptic partner for formation
    :type random_partner: bool
    :param seed: seed the random number generators
    :type seed: int
    """
    __slots__ = [
        # Frequency of rewiring (Hz)
        "__f_rew",
        # Period of rewiring (ms)
        "__p_rew",
        # Initial weight assigned to a newly formed connection
        "__initial_weight",
        # Delay assigned to a newly formed connection
        "__initial_delay",
        # Maximum fan-in per target layer neuron
        "__s_max",
        # Flag whether to mark synapses formed within a layer as
        # inhibitory or excitatory
        "__lateral_inhibition",
        # Spread of feed-forward formation receptive field
        "__sigma_form_forward",
        # Spread of lateral formation receptive field
        "__sigma_form_lateral",
        # Peak probability for feed-forward formation
        "__p_form_forward",
        # Peak probability for lateral formation
        "__p_form_lateral",
        # Probability of elimination of a depressed synapse
        "__p_elim_dep",
        # Probability of elimination of a potentiated synapse
        "__p_elim_pot",
        # Grid shape
        "__grid",
        # Flag whether to randomly select pre-synaptic partner for formation
        "__random_partner",
        # Holds initial connectivity as defined via connector
        "__connections",
        # SDRAM usage estimates are not perfect. This value adjusts estimates
        "__fudge_factor",
        # Maximum synaptic row length based on connectivity + padding
        "__actual_row_max_length",
        # The actual type of weights: static through the simulation or those
        # that can be change through STDP
        "__weight_dynamics",
        # Shared RNG seed to be written on all cores
        "__seeds",
        # Stores the actual SDRAM usage (value obtained only after writing spec
        # is finished)
        "__actual_sdram_usage",
        # Exponentially decayed probability LUT for feed-forward formations
        "__ff_distance_probabilities",
        # Exponentially decayed probability LUT for lateral formations
        "__lat_distance_probabilities"]

    default_parameters = {
        'stdp_model': None, 'f_rew': 10 ** 4, 'weight': 0, 'delay': 1,
        's_max': 32, 'sigma_form_forward': 2.5, 'sigma_form_lateral': 1,
        'p_form_forward': 0.16, 'p_form_lateral': 1.,
        'p_elim_pot': 1.36 * 10 ** -4, 'p_elim_dep': 0.0245,
        'grid': np.array([16, 16]), 'lateral_inhibition': 0,
        'random_partner': False}

    def __init__(self,
                 stdp_model=default_parameters['stdp_model'],
                 f_rew=default_parameters['f_rew'],
                 weight=default_parameters['weight'],
                 delay=default_parameters['delay'],
                 s_max=default_parameters['s_max'],
                 sigma_form_forward=default_parameters['sigma_form_forward'],
                 sigma_form_lateral=default_parameters['sigma_form_lateral'],
                 p_form_forward=default_parameters['p_form_forward'],
                 p_form_lateral=default_parameters['p_form_lateral'],
                 p_elim_dep=default_parameters['p_elim_dep'],
                 p_elim_pot=default_parameters['p_elim_pot'],
                 grid=default_parameters['grid'],
                 lateral_inhibition=default_parameters['lateral_inhibition'],
                 random_partner=default_parameters['random_partner'],
                 seed=None):
        self.__f_rew = f_rew
        self.__p_rew = 1. / self.__f_rew
        self.__initial_weight = weight
        self.__initial_delay = delay
        self.__s_max = s_max
        self.__lateral_inhibition = lateral_inhibition
        self.__sigma_form_forward = sigma_form_forward
        self.__sigma_form_lateral = sigma_form_lateral
        self.__p_form_forward = p_form_forward
        self.__p_form_lateral = p_form_lateral
        self.__p_elim_dep = p_elim_dep
        self.__p_elim_pot = p_elim_pot
        self.__grid = np.asarray(grid, dtype=int)
        self.__random_partner = random_partner
        self.__connections = {}

        self.__fudge_factor = 1.5
        self.__actual_row_max_length = self.__s_max

        self.__weight_dynamics = stdp_model

        # Generate a seed for the RNG on chip that should be the same for all
        # of the cores that have my learning rule
        _rng = np.random.RandomState(seed)
        self.__seeds = [_rng.randint(0x7FFFFFFF) for _ in range(4)]

        # Addition information -- used for SDRAM usage
        self.__actual_sdram_usage = {}

        self.__ff_distance_probabilities = \
            self.generate_distance_probability_array(
                self.__p_form_forward, self.__sigma_form_forward)
        self.__lat_distance_probabilities = \
            self.generate_distance_probability_array(
                self.__p_form_lateral, self.__sigma_form_lateral)

    @property
    def weight_dynamics(self):
        return self.__weight_dynamics

    def get_parameter_names(self):
        names = ['initial_weight', 'initial_delay', 'f_rew', 's_max',
                 'lateral_inhibition',
                 'sigma_form_forward', 'sigma_form_lateral', 'p_form_forward',
                 'p_form_lateral', 'p_elim_dep', 'p_elim_pot', 'grid',
                 'random_partner']
        return names

    def distance(self, x0, x1, grid=np.asarray([16, 16]),
                 type='euclidian'):  # @ReservedAssignment
        """ Compute the distance between points x0 and x1 place on the grid\
            using periodic boundary conditions.

        :param x0: first point in space
        :type x0: np.ndarray of ints
        :param x1: second point in space
        :type x1: np.ndarray of ints
        :param grid: shape of grid
        :type grid: np.ndarray of ints
        :param type: distance metric, i.e. euclidian or manhattan
        :type type: str
        :return: the distance
        :rtype: float
        """
        x0 = np.asarray(x0)
        x1 = np.asarray(x1)
        delta = np.abs(x0 - x1)
        if (delta[0] > grid[0] * .5) and grid[0] > 0:
            delta[0] -= grid[0]

        if (delta[1] > grid[1] * .5) and grid[1] > 0:
            delta[1] -= grid[1]

        if type == 'manhattan':
            return np.abs(delta).sum(axis=-1)
        return np.sqrt((delta ** 2).sum(axis=-1))

    def generate_distance_probability_array(self, probability, sigma):
        """ Generate the exponentially decaying probability LUTs.

        :param probability: peak probability
        :type probability: float
        :param sigma: spread
        :type sigma: float
        :return: distance-dependent probabilities
        :rtype: numpy.ndarray(float)
        """
        euclidian_distances = np.ones(self.__grid ** 2) * np.nan
        for row in range(euclidian_distances.shape[0]):
            for column in range(euclidian_distances.shape[1]):
                if self.__grid[0] > 1:
                    pre = (row // self.__grid[0], row % self.__grid[1])
                    post = (column // self.__grid[0], column % self.__grid[1])
                else:
                    pre = (0, row % self.__grid[1])
                    post = (0, column % self.__grid[1])

                euclidian_distances[row, column] = self.distance(
                    pre, post, grid=self.__grid, type='euclidian')
        largest_squared_distance = np.max(euclidian_distances ** 2)
        squared_distances = np.arange(largest_squared_distance)
        raw_probabilities = probability * (
            np.exp(-squared_distances / (2 * sigma ** 2)))
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
                 np.zeros(filtered_probabilities.size % 2, dtype="uint16")))

        return filtered_probabilities

    @property
    def p_rew(self):
        """ The period of rewiring.

        :return: The period of rewiring
        :rtype: int
        """
        return self.__p_rew

    @property
    def actual_sdram_usage(self):
        """ Actual SDRAM usage (based on what is written to spec).

        :return: actual SDRAM usage
        :rtype: int
        """
        return self.__actual_sdram_usage

    def write_parameters(
            self, spec, region, machine_time_step, weight_scales,
            application_graph, machine_graph, app_vertex, post_slice,
            machine_vertex, graph_mapper, routing_info):
        """ Write the synapse parameters to the spec.

        :param spec: the data spec
        :type spec: spec
        :param region: memory region
        :type region: int
        :param machine_time_step: the duration of a machine time step (ms)
        :type machine_time_step: int
        :param weight_scales: scaling the weights
        :type weight_scales: list(float)
        :param application_graph: \
            the entire, highest level, graph of the network to be simulated
        :type application_graph: :py:class:`ApplicationGraph`
        :param machine_graph: \
            the entire, lowest level, graph of the network to be simulated
        :type machine_graph: :py:class:`MachineGraph`
        :param app_vertex: \
            the highest level object of the post-synaptic population
        :type app_vertex: :py:class:`ApplicationVertex`
        :param post_slice: \
            the slice of the app vertex corresponding to this machine vertex
        :type post_slice: :py:class:`Slice`
        :param machine_vertex: \
            the lowest level object of the post-synaptic population
        :type machine_vertex: :py:class:`MachineVertex`
        :param graph_mapper: for looking up application vertices
        :type graph_mapper: :py:class:`GraphMapper`
        :param routing_info: All of the routing information on the network
        :type routing_info: :py:class:`RoutingInfo`
        :return: None
        :rtype: None
        """
        spec.comment("Writing structural plasticity parameters")
        if spec.current_region != constants.POPULATION_BASED_REGIONS. \
                SYNAPSE_DYNAMICS.value:
            spec.switch_write_focus(region)

        # Write the common part of the rewiring data
        self.__write_common_rewiring_data(
            spec, app_vertex, post_slice, weight_scales, machine_time_step)

        # Write presynaptic (sub)population information
        self.__write_presynaptic_information(
            spec, application_graph, machine_graph,
            app_vertex, post_slice, machine_vertex, graph_mapper,
            routing_info)

    def __write_common_rewiring_data(self, spec, app_vertex, post_slice,
                                     weight_scales, machine_time_step):
        """ Write the non-subpopulation synapse parameters to the spec.

        :param spec: the data spec
        :type spec: spec
        :param app_vertex: \
            the highest level object of the post-synaptic population
        :type app_vertex: :py:class:`ApplicationVertex`
        :param post_slice: \
            the slice of the app vertex corresponding to this machine vertex
        :type post_slice: :py:class:`Slice`
        :param weight_scales: scaling the weights
        :type weight_scales: list(float)
        :param machine_time_step: the duration of a machine time step (ms)
        :type machine_time_step: int
        :return: None
        :rtype: None
        """
        if self.__p_rew * 1000. < machine_time_step / 1000.:
            # Fast rewiring
            spec.write_value(data=1)
            spec.write_value(
                data=int(machine_time_step / (self.__p_rew * 10 ** 6)))
        else:
            # Slow rewiring
            spec.write_value(data=0)
            spec.write_value(
                data=int((self.__p_rew * 10 ** 6) / float(machine_time_step)))

        # scale the excitatory weight appropriately
        spec.write_value(
            data=int(round(self.__initial_weight * weight_scales[0])))
        # scale the inhibitory weight appropriately
        spec.write_value(
            data=int(round(self.__initial_weight * weight_scales[1])))
        spec.write_value(data=self.__initial_delay)
        spec.write_value(data=int(self.__s_max))
        spec.write_value(data=int(self.__lateral_inhibition),
                         data_type=DataType.INT32)
        spec.write_value(data=int(self.__random_partner),
                         data_type=DataType.INT32)
        # write total number of atoms in the application vertex
        spec.write_value(data=app_vertex.n_atoms)
        # write local low, high and number of atoms
        spec.write_value(data=post_slice[0])
        spec.write_value(data=post_slice[1])
        spec.write_value(data=post_slice[2])

        # write the grid size for periodic boundary distance computation
        spec.write_value(data=self.__grid[0])
        spec.write_value(data=self.__grid[1])

        # write probabilities for elimination
        spec.write_value(data=self.__p_elim_dep, data_type=DataType.U032)
        spec.write_value(data=self.__p_elim_pot, data_type=DataType.U032)

        # write the random seed (4 words), generated randomly,
        # but the same for all postsynaptic vertices!
        for seed in self.__seeds:
            spec.write_value(data=seed)

        # write local seed (4 words), generated randomly!
        for _ in range(4):
            spec.write_value(data=np.random.randint(0x7FFFFFFF))

    def __compute_aux(self, application_graph, machine_graph,
                      app_vertex, machine_vertex, graph_mapper, routing_info):
        """ Compute all of the relevant pre-synaptic population information,\
            as well as the key of the current vertex.

        :param application_graph: \
            the entire, highest level, graph of the network to be simulated
        :type application_graph: :py:class:`ApplicationGraph`
        :param machine_graph: \
            the entire, lowest level, graph of the network to be simulated
        :type machine_graph: :py:class:`MachineGraph`
        :param app_vertex: \
            the highest level object of the post-synaptic population
        :type app_vertex: :py:class:`ApplicationVertex`
        :param post_slice: \
            the slice of the app vertex corresponding to this machine vertex
        :type post_slice: :py:class:`Slice`
        :param machine_vertex: \
            the lowest level object of the post-synaptic population
        :type machine_vertex: :py:class:`MachineVertex`
        :param graph_mapper: for looking up application vertices
        :type graph_mapper: :py:class:`GraphMapper`
        :param routing_info: All of the routing information on the network
        :type routing_info: :py:class:`RoutingInfo`
        :return: pop info, routing key for current vertex, number of pre pops
        :rtype: tuple
        """
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
                    if synapse_info.synapse_dynamics is self.__weight_dynamics:
                        structural_application_edges.append(app_edge)
                        population_to_subpopulation_information[
                            app_edge.pre_vertex] = []
                        break

        no_pre_populations = len(structural_application_edges)
        # For each structurally plastic APPLICATION edge find the
        # corresponding machine edges
        for machine_edge in machine_graph.get_edges_ending_at_vertex(
                machine_vertex):
            if isinstance(machine_edge, ProjectionMachineEdge):
                for synapse_info in machine_edge._synapse_information:
                    if synapse_info.synapse_dynamics is self.__weight_dynamics:
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

        for subpopulation_list in itervalues(
                population_to_subpopulation_information):
            max_subpartitions = np.maximum(max_subpartitions,
                                           len(subpopulation_list))

        # Current machine vertex key (for future checks)
        current_key = routing_info.get_routing_info_from_pre_vertex(
            machine_vertex, constants.SPIKE_PARTITION_ID)

        if current_key is not None:
            current_key = current_key.first_key
        else:
            current_key = -1
        return (population_to_subpopulation_information, current_key,
                no_pre_populations)

    def __write_presynaptic_information(self, spec, application_graph,
                                        machine_graph,
                                        app_vertex, post_slice, machine_vertex,
                                        graph_mapper,
                                        routing_info):
        """ All cores which do synaptic rewiring have information about all\
            the relevant pre-synaptic populations.

        :param spec: the data spec
        :type spec: spec
        :param application_graph: \
            the entire, highest level, graph of the network to be simulated
        :type application_graph: :py:class:`ApplicationGraph`
        :param machine_graph: \
            the entire, lowest level, graph of the network to be simulated
        :type machine_graph: :py:class:`MachineGraph`
        :param app_vertex: \
            the highest level object of the post-synaptic population
        :type app_vertex: :py:class:`ApplicationVertex`
        :param post_slice: \
            the slice of the app vertex corresponding to this machine vertex
        :type post_slice: :py:class:`Slice`
        :param machine_vertex: \
            the lowest level object of the post-synaptic population
        :type machine_vertex: :py:class:`MachineVertex`
        :param graph_mapper: for looking up application vertices
        :type graph_mapper: :py:class:`GraphMapper`
        :param routing_info: All of the routing information on the network
        :type routing_info: :py:class:`RoutingInfo`
        :return: None
        :rtype: None
        """
        # Compute all the auxiliary stuff
        pop_to_subpop_info, current_key, no_prepops = self.__compute_aux(
            application_graph, machine_graph, app_vertex, machine_vertex,
            graph_mapper, routing_info)

        # Table header
        spec.write_value(data=no_prepops)

        total_words_written = 0
        for subpopulation_list in itervalues(pop_to_subpop_info):
            # Population header(s)
            # Number of subpopulations
            spec.write_value(data=len(subpopulation_list),
                             data_type=DataType.UINT16)

            # Custom header for commands / controls
            # currently, controls = True if the subvertex (on the current core)
            # is part of this population
            controls = current_key in np.asarray(subpopulation_list)[:0]
            spec.write_value(data=int(controls), data_type=DataType.UINT16)

            spec.write_value(
                data=np.sum(np.asarray(subpopulation_list)[:, 1]) if len(
                    subpopulation_list) > 0 else 0)
            words_written = 2

            # Ensure the following values are written in ascending
            # order of low_atom (implicit)
            dt = np.dtype(
                [('key', 'uint'), ('n_atoms', 'uint'), ('lo_atom', 'uint'),
                 ('mask', 'uint')])
            structured_array = np.array(subpopulation_list, dtype=dt)
            sorted_info_list = np.sort(structured_array, order='lo_atom')
            for subpopulation_info in sorted_info_list:
                # Subpopulation information (i.e. key and number of atoms)
                # Key
                spec.write_value(data=subpopulation_info[0])
                # n_atoms
                spec.write_value(data=subpopulation_info[1])
                # lo_atom
                spec.write_value(data=subpopulation_info[2])
                # mask
                spec.write_value(data=subpopulation_info[3])
                words_written += 4

            total_words_written += words_written

        # Now we write the probability tables for formation
        # (feedforward and lateral)
        spec.write_value(data=self.__ff_distance_probabilities.size)
        spec.write_array(
            self.__ff_distance_probabilities.view(dtype=np.uint16),
            data_type=DataType.UINT16)
        total_words_written += self.__ff_distance_probabilities.size // 2 + 1
        spec.write_value(data=self.__lat_distance_probabilities.size,
                         data_type=DataType.INT32)
        spec.write_array(
            self.__lat_distance_probabilities.view(dtype=np.uint16),
            data_type=DataType.UINT16)
        total_words_written += self.__lat_distance_probabilities.size // 2 + 1

        # Write post to pre table (inverse of synaptic matrix)
        self.__write_post_to_pre_table(spec, app_vertex, post_slice,
                                       machine_vertex, graph_mapper,
                                       pop_to_subpop_info, total_words_written)

    def __write_post_to_pre_table(self, spec, app_vertex, post_slice,
                                  machine_vertex, graph_mapper,
                                  population_to_subpopulation_information,
                                  total_words_written):
        """ Post to pre table is basically the transpose of the synaptic\
            matrix

        :param spec: the data spec
        :type spec: spec
        :param app_vertex: \
            the highest level object of the post-synaptic population
        :type app_vertex: ApplicationVertex
        :param post_slice: \
            the slice of the app vertex corresponding to this machine vertex
        :type post_slice: Slice
        :param machine_vertex: \
            the lowest level object of the post-synaptic population
        :type machine_vertex: MachineVertex
        :param graph_mapper: for looking up application vertices
        :type graph_mapper: GraphMapper
        :param population_to_subpopulation_information: \
            generated relevant information
        :type population_to_subpopulation_information: dict
        :param total_words_written: \
            keeping track of how many words have been written
        :type total_words_written: int
        :return: None
        :rtype: None
        """
        # Setting up Post to Pre table
        post_to_pre_table = np.ones((post_slice.n_atoms, self.__s_max),
                                    dtype=np.int32) * -1
        for row in self.__connections[post_slice.lo_atom]:
            if row[0].size > 0 and row[1].post_vertex is app_vertex:
                for source, target, _weight, _delay, _syn_type in row[0]:

                    # Select pre vertex
                    pre_vertex_slice = graph_mapper._slice_by_machine_vertex[
                        row[2].pre_vertex]
                    pre_vertex_id = source - pre_vertex_slice.lo_atom
                    masked_pre_vertex_id = pre_vertex_id & (2 ** 17 - 1)

                    # Select population index
                    pop_index = population_to_subpopulation_information. \
                        keys().index(row[1].pre_vertex)
                    masked_pop_index = pop_index & (2 ** 9 - 1)

                    # Select subpopulation index
                    dt = np.dtype(
                        [('key', 'int'), ('n_atoms', 'int'),
                         ('lo_atom', 'int'), ('mask', 'uint')])
                    structured_array = np.array(
                        population_to_subpopulation_information[
                            row[1].pre_vertex], dtype=dt)
                    sorted_info_list = np.sort(
                        structured_array, order='lo_atom')

                    # find index where lo_atom equals the one in
                    # pre_vertex_slice
                    subpop_index = np.argwhere(
                        sorted_info_list['lo_atom'] ==
                        pre_vertex_slice.lo_atom).ravel()[0]
                    masked_sub_pop_index = subpop_index & (2 ** 9 - 1)

                    # identifier combines the vertex, pop and subpop
                    # into 1 x 32 bit word
                    identifier = (masked_pop_index << (32 - 8)) | (
                            masked_sub_pop_index << 16) | masked_pre_vertex_id
                    try:
                        synaptic_entry = np.argmax(
                            post_to_pre_table[target - post_slice.lo_atom] ==
                            -1).ravel()[0]
                    except Exception:
                        break
                    post_to_pre_table[
                        target - post_slice.lo_atom, synaptic_entry] = \
                        identifier

        spec.write_array(post_to_pre_table.ravel(), data_type=DataType.INT32)
        total_words_written += post_to_pre_table.size

        self.actual_sdram_usage[
            machine_vertex] = 4 * 27 + 4 * total_words_written

    def get_extra_sdram_usage_in_bytes(self, machine_in_edges):
        """ Better approximation of SDRAM usage based on incoming machine edges

        :param machine_in_edges: incoming machine edges
        :type machine_in_edges: machine edges
        :return: SDRAM usage
        :rtype: int
        """
        relevant_edges = []
        for edge in machine_in_edges:
            for synapse_info in edge._synapse_information:
                if synapse_info.synapse_dynamics is self.__weight_dynamics:
                    relevant_edges.append(edge)
        return int(self.__fudge_factor * 4 * 12 * len(relevant_edges))

    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types,
                                            in_edges):
        """ Approximate SDRAM usage

        :param n_neurons: number of neurons
        :type n_neurons: int
        :param n_synapse_types: \
            number of synapse types (i.e. excitatory and inhibitory)
        :type n_synapse_types: int
        :param in_edges: incoming edges
        :type in_edges: edges
        :return: SDRAM usage
        :rtype: int
        """
        structure_size = 27 * 4 + 4 * 4  # parameters + rng seed
        post_to_pre_table_size = n_neurons * self.__s_max * 4
        structure_size += post_to_pre_table_size

        initial_size = 0
        total_size = structure_size + initial_size

        # Approximation of the sizes of both probability vs distance tables
        ff_lut = np.count_nonzero(self.__ff_distance_probabilities) * 4
        lat_lut = np.count_nonzero(self.__lat_distance_probabilities) * 4
        total_size += ff_lut
        total_size += lat_lut
        # total_size += (80 * 4)
        pop_size = 0

        # approximate the size of the pop -> subpop table
        no_pre_vertices_estimate = 0
        if in_edges is not None:

            # Approximation gets computed here based on number of
            # afferent edges
            # How many afferent application vertices?
            # How large are they?

            for edge in in_edges:
                if isinstance(edge, ProjectionApplicationEdge):
                    for synapse_info in edge.synapse_information:
                        if (synapse_info.synapse_dynamics is
                                self.__weight_dynamics):
                            no_pre_vertices_estimate += (1 + np.ceil(
                                edge.pre_vertex.n_atoms / 32.))
                    no_pre_vertices_estimate *= 2
                elif isinstance(edge, ProjectionMachineEdge):
                    pop_size += self.get_extra_sdram_usage_in_bytes(in_edges)
                    break

        pop_size += int(50 * (no_pre_vertices_estimate + len(in_edges)))

        return int(self.__fudge_factor * (total_size + pop_size))  # bytes

    def synaptic_data_update(self, connections,
                             post_vertex_slice,
                             app_edge, machine_edge):
        """ Get static synaptic data
        """
        if post_vertex_slice.lo_atom not in self.__connections.keys():
            self.__connections[post_vertex_slice.lo_atom] = []
        self.__connections[post_vertex_slice.lo_atom].append(
            (connections, app_edge, machine_edge))

    def n_words_for_plastic_connections(self, value):
        """ Get size of plastic connections in words
        """
        self.__actual_row_max_length = value

    def n_words_for_static_connections(self, value):
        """ Get size of static connections in words
        """
        self.__actual_row_max_length = value

    def get_n_synapses_in_rows(self, pp_size, fp_size=None):
        """ Get number of synapses in a row.
        """
        if fp_size is not None:
            return self.__weight_dynamics. \
                get_n_synapses_in_rows(pp_size, fp_size)
        return self.__weight_dynamics.get_n_synapses_in_rows(pp_size)

    def get_vertex_executable_suffix(self):
        name = "_structural"
        return name

    def is_same_as(self, synapse_dynamics):
        if not isinstance(synapse_dynamics, AbstractSynapseDynamicsStructural):
            return False
        return (
                self.__f_rew == synapse_dynamics.f_rew and
                self.__s_max == synapse_dynamics.s_max and
                np.isclose(self.__sigma_form_forward,
                           synapse_dynamics.sigma_form_forward) and
                np.isclose(self.__sigma_form_lateral,
                           synapse_dynamics.sigma_form_lateral) and
                np.isclose(self.__p_form_forward,
                           synapse_dynamics.p_form_forward) and
                np.isclose(self.__p_form_lateral,
                           synapse_dynamics.p_form_lateral) and
                np.isclose(self.__p_elim_dep, synapse_dynamics.p_elim_dep) and
                np.isclose(self.__p_elim_pot, synapse_dynamics.p_elim_pot))
