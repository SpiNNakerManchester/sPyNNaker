from six import itervalues
import numpy as np
import collections

from spinn_utilities.overrides import overrides
from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.models.neural_projections import ProjectionMachineEdge
from .abstract_plastic_synapse_dynamics import AbstractPlasticSynapseDynamics
from .abstract_synapse_dynamics_structural import \
    AbstractSynapseDynamicsStructural
from .synapse_dynamics_stdp import SynapseDynamicsSTDP
from .synapse_dynamics_static import SynapseDynamicsStatic
from spynnaker.pyNN.utilities import constants


class SynapseDynamicsStructural(AbstractSynapseDynamicsStructural):
    """ Class enables synaptic rewiring. It acts as a wrapper around \
        SynapseDynamicsStatic or SynapseDynamicsSTDP. This means rewiring \
        can operate in parallel with these types of synapses.

        Example usage to allow rewiring in parallel with STDP::

            stdp_model = sim.STDPMechanism(...)

            structure_model_with_stdp = sim.StructuralMechanism(
                stdp_model=stdp_model,
                weight=0,
                s_max=32,
                grid=[np.sqrt(pop_size), np.sqrt(pop_size)],
                random_partner=True,
                f_rew=10 ** 4,  # Hz
                sigma_form_forward=1.,
                delay=10
            )


    :param f_rew: Frequency of rewiring (Hz). How many rewiring attempts will
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
    :param lateral_inhibition: Flag whether to mark synapses formed within a
        layer as inhibitory or excitatory
    :type lateral_inhibition: bool
    :param random_partner: Flag whether to randomly select pre-synaptic
        partner for formation
    :type random_partner: bool
    :param seed: seed the random number generators
    :type seed: int
    """
    __slots__ = [
        # Frequency of rewiring (Hz)
        "_f_rew",
        # Period of rewiring (ms)
        "_p_rew",
        # Initial weight assigned to a newly formed connection
        "_weight",
        # Delay assigned to a newly formed connection
        "_delay",
        # Maximum fan-in per target layer neuron
        "_s_max",
        # Flag whether to mark synapses formed within a layer as
        # inhibitory or excitatory
        "_lateral_inhibition",
        # Spread of feed-forward formation receptive field
        "_sigma_form_forward",
        # Spread of lateral formation receptive field
        "_sigma_form_lateral",
        # Peak probability for feed-forward formation
        "_p_form_forward",
        # Peak probability for lateral formation
        "_p_form_lateral",
        # Probability of elimination of a depressed synapse
        "_p_elim_dep",
        # Probability of elimination of a potentiated synapse
        "_p_elim_pot",
        # Grid shape
        "_grid",
        # Flag whether to randomly select pre-synaptic partner for formation
        "_random_partner",
        # Holds initial connectivity as defined via connector
        "_connections",
        # SDRAM usage estimates are not perfect. This value adjusts estimates
        "fudge_factor",
        # Maximum synaptic row length based on connectivity + padding
        "_actual_row_max_length",
        # The actual type of weights: static through the simulation or those
        # that can be change through STDP
        "_weight_dynamics",
        # Shared RNG seed to be written on all cores
        "_seeds",
        # Stores the actual SDRAM usage (value obtained only after writing spec
        # is finished)
        "_actual_sdram_usage",
        # Exponentially decayed probability LUT for feed-forward formations
        "_ff_distance_probabilities",
        # Exponentially decayed probability LUT for lateral formations
        "_lat_distance_probabilities"]

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

        AbstractSynapseDynamicsStructural.__init__(self)
        self._f_rew = f_rew
        self._p_rew = 1. / self._f_rew
        self._weight = weight
        self._delay = delay
        self._s_max = s_max
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

        self.fudge_factor = 1.5
        self._actual_row_max_length = self._s_max

        if stdp_model is not None and \
                isinstance(stdp_model, SynapseDynamicsSTDP):
            self._weight_dynamics = SynapseDynamicsSTDP(
                timing_dependence=stdp_model.timing_dependence,
                weight_dependence=stdp_model.weight_dependence,
                dendritic_delay_fraction=stdp_model.dendritic_delay_fraction,
                pad_to_length=self._s_max)
        else:
            self._weight_dynamics = \
                SynapseDynamicsStatic(pad_to_length=self._s_max)

        # Generate a seed for the RNG on chip that should be the same for all
        # of the cores that have my learning rule
        _rng = np.random.RandomState(seed)
        self._seeds = []
        for _ in range(4):
            self._seeds.append(_rng.randint(0x7FFFFFFF))

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

    @property
    def weight_dynamics(self):
        return self._weight_dynamics

    @overrides(AbstractSynapseDynamicsStructural.get_parameter_names)
    def get_parameter_names(self):
        names = ['weight', 'delay', 'f_rew', 's_max', 'lateral_inhibition',
                 'sigma_form_forward', 'sigma_form_lateral', 'p_form_forward',
                 'p_form_lateral', 'p_elim_dep', 'p_elim_pot', 'grid',
                 'random_partner']
        names.extend(self._weight_dynamics.get_parameter_names())
        return names

    def distance(self, x0, x1, grid=np.asarray([16, 16]),
                 type='euclidian'):  # @ReservedAssignment
        """
        Compute the distance between points x0 and x1 place on the grid using
        periodic boundary conditions
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
        """
        Generate the exponentially decaying probability LUTs
        :param probability: peak probability
        :type probability: float
        :param sigma: spread
        :type sigma: float
        :return: distance-dependent probabilities
        :rtype: np.ndarray of floats
        """
        euclidian_distances = np.ones(self._grid ** 2) * np.nan
        for row in range(euclidian_distances.shape[0]):
            for column in range(euclidian_distances.shape[1]):
                if self._grid[0] > 1:
                    pre = (row // self._grid[0], row % self._grid[1])
                    post = (column // self._grid[0], column % self._grid[1])
                else:
                    pre = (0, row % self._grid[1])
                    post = (0, column % self._grid[1])

                euclidian_distances[row, column] = \
                    self.distance(pre, post, grid=self._grid, type='euclidian')
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
                 np.zeros(
                     filtered_probabilities.size % 2, dtype="uint16")))

        return filtered_probabilities

    @property
    def p_rew(self):
        """
        The period of rewiring

        :return: The period of rewiring
        :rtype: int
        """
        return self._p_rew

    @property
    def actual_sdram_usage(self):
        """
        Actual SDRAM usage (based on what is written to spec)

        :return: actual SDRAM usage
        :rtype: int
        """
        return self._actual_sdram_usage

    @property
    def approximate_sdram_usage(self):
        """
        Approximate the SDRAM usage before final partitioning

        :return: SDRAM usage approximation
        :rtype: int
        """
        return self._approximate_sdram_usage

    @overrides(
        AbstractSynapseDynamicsStructural.write_parameters,
        additional_arguments={
            "application_graph", "machine_graph", "app_vertex",
            "post_slice", "machine_vertex", "graph_mapper", "routing_info"})
    def write_parameters(
            self, spec, region, machine_time_step, weight_scales,
            application_graph, machine_graph, app_vertex, post_slice,
            machine_vertex, graph_mapper, routing_info):
        """
        Write the synapse parameters to the spec

        :param spec: the data spec
        :type spec: spec
        :param region: memory region
        :type region: int
        :param machine_time_step: the duration of a machine time step (ms)
        :type machine_time_step: int
        :param weight_scales: scaling the weights
        :type weight_scales: float
        :param application_graph: the entire, highest level, graph of the
            network to be simulated
        :type application_graph: ApplicationGraph
        :param machine_graph: the entire, lowest level, graph of the
            network to be simulated
        :type machine_graph: MachineGraph
        :param app_vertex: the highest level object of the post-synaptic
            population
        :type app_vertex: ApplicationVertex
        :param post_slice: the slice of the App Vertex corresponding to this
            Machine Vertex
        :type post_slice: Slice
        :param machine_vertex: the lowest level object of the post-synaptic
            population
        :type machine_vertex: MachineVertex
        :param graph_mapper: ?????
        :type graph_mapper: GraphMapper
        :param routing_info: All of the routing information on the network
        :type routing_info: RoutingInfo
        :return: None
        :rtype: None
        """
        self._weight_dynamics.write_parameters(spec, region, machine_time_step,
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

        # scale the excitatory weight appropriately
        spec.write_value(data=int(round(self._weight * weight_scales[0])),
                         data_type=DataType.INT32)
        # scale the inhibitory weight appropriately
        spec.write_value(data=int(round(self._weight * weight_scales[1])),
                         data_type=DataType.INT32)
        spec.write_value(data=self._delay, data_type=DataType.INT32)
        spec.write_value(data=int(self._s_max), data_type=DataType.INT32)
        spec.write_value(data=int(self._lateral_inhibition),
                         data_type=DataType.INT32)
        spec.write_value(data=int(self._random_partner),
                         data_type=DataType.INT32)
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

        # Write presynaptic (sub)population information

        self.__write_presynaptic_information(
            spec, application_graph, machine_graph,
            app_vertex, post_slice, machine_vertex, graph_mapper,
            routing_info)

    def __compute_aux(self, application_graph, machine_graph,
                      app_vertex, machine_vertex, graph_mapper, routing_info):
        """
        Compute all of the relavant pre-synaptic population information, as
        well as the key of the current vertex

        :param application_graph: the entire, highest level, graph of the
            network to be simulated
        :type application_graph: ApplicationGraph
        :param machine_graph: the entire, lowest level, graph of the
            network to be simulated
        :type machine_graph: MachineGraph
        :param app_vertex: the highest level object of the post-synaptic
            population
        :type app_vertex: ApplicationVertex
        :param post_slice: the slice of the App Vertex corresponding to this
            Machine Vertex
        :type post_slice: Slice
        :param machine_vertex: the lowest level object of the post-synaptic
            population
        :type machine_vertex: MachineVertex
        :param graph_mapper: ?????
        :type graph_mapper: GraphMapper
        :param routing_info: All of the routing information on the network
        :type routing_info: RoutingInfo
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
                    if synapse_info.synapse_dynamics is self:
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
                itervalues(population_to_subpopulation_information):
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
        """
        All cores which do synaptic rewiring have information about all
        the relevant pre-synaptic populations.
        :param spec: the data spec
        :type spec: spec
        :param application_graph: the entire, highest level, graph of the
            network to be simulated
        :type application_graph: ApplicationGraph
        :param machine_graph: the entire, lowest level, graph of the
            network to be simulated
        :type machine_graph: MachineGraph
        :param app_vertex: the highest level object of the post-synaptic
            population
        :type app_vertex: ApplicationVertex
        :param post_slice: the slice of the App Vertex corresponding to this
            Machine Vertex
        :type post_slice: Slice
        :param machine_vertex: the lowest level object of the post-synaptic
            population
        :type machine_vertex: MachineVertex
        :param graph_mapper: ?????
        :type graph_mapper: GraphMapper
        :param routing_info: All of the routing information on the network
        :type routing_info: RoutingInfo
        :return: None
        :rtype: None
        """
        # Compute all the auxilliary stuff
        results = self.__compute_aux(application_graph, machine_graph,
                                     app_vertex, machine_vertex, graph_mapper,
                                     routing_info)

        population_to_subpopulation_information = results[0]
        current_key = results[1]
        no_pre_populations = results[2]

        # Table header
        spec.write_value(data=no_pre_populations, data_type=DataType.INT32)

        total_words_written = 0
        for subpopulation_list in \
                itervalues(population_to_subpopulation_information):

            # Population header(s)
            # Number of subpopulations
            spec.write_value(data=len(subpopulation_list),
                             data_type=DataType.UINT16)

            # Custom header for commands / controls
            # currently, controls = 1 if the subvertex (on the current core)
            # is part of this population
            controls = 1 if current_key in np.asarray(
                subpopulation_list)[:0] else 0
            spec.write_value(data=controls, data_type=DataType.UINT16)

            spec.write_value(
                data=np.sum(np.asarray(subpopulation_list)[:, 1]) if len(
                    subpopulation_list) > 0 else 0,
                data_type=DataType.INT32)
            words_written = 2

            # Ensure the following values are written in ascending
            # order of low_atom (implicit)
            dt = np.dtype(
                [('key', 'int'), ('n_atoms', 'int'), ('lo_atom', 'int'),
                 ('mask', 'uint')])
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

        # Write post to pre table (inverse of synaptic matrix)
        self.__write_post_to_pre_table(spec, app_vertex, post_slice,
                                       machine_vertex, graph_mapper,
                                       population_to_subpopulation_information,
                                       total_words_written)

    def __write_post_to_pre_table(self, spec, app_vertex, post_slice,
                                  machine_vertex, graph_mapper,
                                  population_to_subpopulation_information,
                                  total_words_written):
        """
        Post to pre table is basically the transverse of the synaptic matrix
        :param spec: the data spec
        :type spec: spec
        :param app_vertex: the highest level object of the post-synaptic
            population
        :type app_vertex: ApplicationVertex
        :param post_slice: the slice of the App Vertex corresponding to this
            Machine Vertex
        :type post_slice: Slice
        :param machine_vertex: the lowest level object of the post-synaptic
            population
        :type machine_vertex: MachineVertex
        :param graph_mapper: ?????
        :type graph_mapper: GraphMapper
        :param population_to_subpopulation_information: generated relevant
            information
        :type population_to_subpopulation_information: dict
        :param total_words_written: keeping track of how many words have been
            written
        :type total_words_written: int
        :return: None
        :rtype: None
        """

        # Setting up Post to Pre table
        post_to_pre_table = np.ones((post_slice.n_atoms, self._s_max),
                                    dtype=np.int32) * -1
        for row in self._connections[post_slice.lo_atom]:
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

        spec.write_array(post_to_pre_table.ravel())

        total_words_written += (post_to_pre_table.size)
        self.actual_sdram_usage[
            machine_vertex] = 4 * 27 + 4 * total_words_written

    def get_extra_sdram_usage_in_bytes(self, machine_in_edges):
        """
        Better aprox of sdram usage based on incoming machine edges
        :param machine_in_edges: incoming machine edges
        :type machine_in_edges: machine edges
        :return: sdram usage
        :rtype: int
        """
        relevant_edges = []
        for edge in machine_in_edges:
            for synapse_info in edge._synapse_information:
                if synapse_info.synapse_dynamics is self:
                    relevant_edges.append(edge)
        return int(self.fudge_factor * (4 * (12 * len(relevant_edges))))

    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types,
                                            in_edges=None):
        """
        approximate sdram usage
        :param n_neurons: number of neurons
        :type n_neurons: int
        :param n_synapse_types: number of synapse types (i.e. excitatory and
            inhibitory)
        :type n_synapse_types: int
        :param in_edges: incoming edges
        :type in_edges: edges
        :return: sdram usage
        :rtype: int
        """
        structure_size = 27 * 4 + 4 * 4  # parameters + rng seed
        post_to_pre_table_size = n_neurons * self._s_max * 4
        structure_size += post_to_pre_table_size

        initial_size = \
            self._weight_dynamics.get_parameters_sdram_usage_in_bytes(
                n_neurons, n_synapse_types)
        total_size = structure_size + initial_size

        # Aproximation of the sizes of both probability vs distance tables
        total_size += (80 * 4)
        pop_size = 0

        # approximate the size of the pop -> subpop table
        if (in_edges is not None and
                isinstance(in_edges[0], ProjectionApplicationEdge)):

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
        elif (in_edges is not None and
              isinstance(in_edges[0], ProjectionMachineEdge)):
            pop_size += self.get_extra_sdram_usage_in_bytes(in_edges)
        return int(self.fudge_factor * (total_size + pop_size))  # bytes

    def get_plastic_synaptic_data(self, connections, connection_row_indices,
                                  n_rows, post_vertex_slice,
                                  n_synapse_types, app_edge, machine_edge):
        """
        Get plastic synaptic data

        """
        if post_vertex_slice.lo_atom not in self._connections.keys():
            self._connections[post_vertex_slice.lo_atom] = []
        self._connections[post_vertex_slice.lo_atom].append(
            (connections, app_edge, machine_edge))
        if isinstance(self._weight_dynamics, AbstractPlasticSynapseDynamics):
            return self._weight_dynamics.get_plastic_synaptic_data(
                connections, connection_row_indices, n_rows,
                post_vertex_slice, n_synapse_types)
        return self._weight_dynamics.get_static_synaptic_data(
            connections, connection_row_indices, n_rows, post_vertex_slice,
            n_synapse_types)

    def get_static_synaptic_data(self, connections, connection_row_indices,
                                 n_rows, post_vertex_slice,
                                 n_synapse_types, app_edge, machine_edge):
        """
        Get static synaptic data

        """
        if post_vertex_slice.lo_atom not in self._connections.keys():
            self._connections[post_vertex_slice.lo_atom] = []
        self._connections[post_vertex_slice.lo_atom].append(
            (connections, app_edge, machine_edge))
        return self._weight_dynamics.get_static_synaptic_data(
            connections, connection_row_indices, n_rows, post_vertex_slice,
            n_synapse_types)

    def get_n_words_for_plastic_connections(self, n_connections):
        """
        Get size of plastic connections in words

        """
        try:
            self._actual_row_max_length = \
                self._weight_dynamics.\
                get_n_words_for_plastic_connections(n_connections)
        except Exception:
            self._actual_row_max_length = \
                self._weight_dynamics.\
                get_n_words_for_static_connections(n_connections)
        return self._actual_row_max_length

    def get_n_words_for_static_connections(self, n_connections):
        """
        Get size of static connections in words

        """

        self._actual_row_max_length = \
            self._weight_dynamics.\
            get_n_words_for_static_connections(n_connections)
        return self._actual_row_max_length

    def get_n_synapses_in_rows(self, pp_size, fp_size=None):
        """
        Get number of synapses in a row

        """
        if fp_size is not None:
            return self._weight_dynamics.\
                get_n_synapses_in_rows(pp_size, fp_size)
        return self._weight_dynamics.get_n_synapses_in_rows(pp_size)

    def read_plastic_synaptic_data(self, post_vertex_slice, n_synapse_types,
                                   pp_size, pp_data, fp_size, fp_data):
        """
        Get plastic synaptic data

        """
        return self._weight_dynamics.read_plastic_synaptic_data(
            post_vertex_slice, n_synapse_types, pp_size, pp_data, fp_size,
            fp_data)

    def read_static_synaptic_data(self, post_vertex_slice, n_synapse_types,
                                  ff_size, ff_data):
        """
        Get static synaptic data

        """
        return self._weight_dynamics.read_static_synaptic_data(
            post_vertex_slice, n_synapse_types, ff_size, ff_data)

    def get_n_fixed_plastic_words_per_row(self, fp_size):
        """
        Get size (in words) of fixed plastic (FP) elements in a row

        """
        return self._weight_dynamics.get_n_fixed_plastic_words_per_row(fp_size)

    def get_n_plastic_plastic_words_per_row(self, pp_size):
        """
        Get size (in words) of plastic plastic (PP) elements in a row

        """
        return self._weight_dynamics.\
            get_n_plastic_plastic_words_per_row(pp_size)

    @overrides(AbstractSynapseDynamicsStructural.are_weights_signed)
    def are_weights_signed(self):
        return self._weight_dynamics.are_weights_signed()

    @overrides(AbstractSynapseDynamicsStructural.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self):
        name = self._weight_dynamics.get_vertex_executable_suffix()
        name += "_structural"
        return name

    def get_n_static_words_per_row(self, ff_size):
        """
        Get size (in words) of fixed fixed (FF/static) elements in a row

        """
        return self._weight_dynamics.get_n_static_words_per_row(ff_size)

    @overrides(AbstractSynapseDynamicsStructural.is_same_as)
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

    @overrides(AbstractSynapseDynamicsStructural.get_max_synapses)
    def get_max_synapses(self, n_words):
        return self._weight_dynamics.get_max_synapses(n_words)
