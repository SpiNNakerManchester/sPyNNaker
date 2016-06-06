from collections import OrderedDict
from pacman.model.constraints.partitioner_constraints.\
    partitioner_same_size_as_vertex_constraint import \
    PartitionerSameSizeAsVertexConstraint
from pacman.model.partitionable_graph.multi_cast_partitionable_edge import \
    MultiCastPartitionableEdge
from pacman.model.partitionable_graph.partitionable_graph import \
    PartitionableGraph

from spinn_front_end_common.utilities import exceptions
from spinn_machine.utilities.progress_bar import ProgressBar

from spynnaker.pyNN import ProjectionPartitionableEdge, DelayExtensionVertex, \
    DelayAfferentPartitionableEdge
from spynnaker.pyNN.models.neural_projections.synapse_information import \
    SynapseInformation
from spynnaker.pyNN.models.neuron.abstract_population_model import \
    AbstractPopulationModel
from spynnaker.pyNN.models.neuron.connection_holder import ConnectionHolder
from spynnaker.pyNN.utilities import constants


import logging
import math
logger = logging.getLogger(__name__)


class Grouper(object):
    """
    grouper: a function which takes a bag of neurons and maps them into vertices
    """

    def __call__(
            self, population_atom_mapping, projections, user_max_delay,
            using_virtual_board):

        # build a partitionable graph
        partitionable_graph = PartitionableGraph("grouped_application_graph")
        pop_to_vertex_mapping = dict()
        vertex_to_pop_mapping = OrderedDict()

        progress_bar = ProgressBar(
            len(population_atom_mapping.keys()),
            "grouping atoms together to create vertices")

        # for each model type build a monolithic vertex for them all
        for model_type in population_atom_mapping.keys():
            local_atom_mapping = dict(population_atom_mapping[model_type])
            while len(local_atom_mapping.keys()) != 0:
                self._handle_model_type(
                    local_atom_mapping, model_type, partitionable_graph,
                    pop_to_vertex_mapping, vertex_to_pop_mapping)
            progress_bar.update()
        progress_bar.end()

        # handle projections
        self.handle_projections(
            projections, population_atom_mapping, pop_to_vertex_mapping,
            user_max_delay, partitionable_graph, using_virtual_board)

        return {'partitionable_graph': partitionable_graph,
                'pop_to_vertex_mapping': pop_to_vertex_mapping,
                'vertex_to_pop_mapping': vertex_to_pop_mapping}

    def handle_projections(
            self, projections, population_atom_mapping, pop_to_vertex_mapping,
            user_max_delay, partitionable_graph, using_virtual_board):
        """

        :param projections:
        :param population_atom_mapping:
        :param pop_to_vertex_mapping:
        :param user_max_delay:
        :param partitionable_graph:
        :param using_virtual_board:
        :return:
        """
        delay_to_vertex_mapping = dict()

        progress_bar = ProgressBar(
            len(projections), "Updating graph with projection edges")

        for projection in projections:
            # get populations from the projection
            presynaptic_population = projection._presynaptic_population
            postsynaptic_population = projection._postsynaptic_population

            # get mapped vertex's and their sections for the pops.
            (post_pop_vertex, post_vertex_lo_atom, post_vertex_hi_atom) = \
                pop_to_vertex_mapping[postsynaptic_population]
            (pre_pop_vertex, pre_vertex_lo_atom, pre_vertex_hi_atom) = \
                pop_to_vertex_mapping[presynaptic_population]

            # get the synapse type
            synapse_type = self._get_synapse_type(
                post_pop_vertex, postsynaptic_population, projection.target)

            # get synapse information
            synapse_information = self._get_synapse_info(
                projection._connector, synapse_type, population_atom_mapping,
                postsynaptic_population, presynaptic_population,
                projection._rng)

            projection._synapse_information = synapse_information

            # add delay extensions and edges as required
            self._sort_out_delays(
                post_pop_vertex, pre_pop_vertex, postsynaptic_population,
                presynaptic_population, population_atom_mapping,
                synapse_information, projection, user_max_delay,
                partitionable_graph, using_virtual_board,
                delay_to_vertex_mapping)
            progress_bar.update()
        progress_bar.end()

    def _sort_out_delays(
            self, post_pop_vertex, pre_pop_vertex, postsynaptic_population,
            presynaptic_population, population_atom_mapping,
            synapse_information, projection, user_max_delay,
            partitionable_graph, using_virtual_board, delay_to_vertex_mapping):
        """

        :param post_pop_vertex:
        :param pre_pop_vertex:
        :param postsynaptic_population:
        :param presynaptic_population:
        :param population_atom_mapping:
        :param synapse_information:
        :param projection:
        :param user_max_delay:
        :param partitionable_graph:
        :param using_virtual_board:
        :param delay_to_vertex_mapping:
        :return:
        """

        # check if all delays requested can fit into the natively supported
        # delays in the models
        synapse_dynamics_stdp = synapse_information.synapse_dynamics
        max_delay = \
            synapse_dynamics_stdp.get_delay_maximum(projection._connector)
        if max_delay is None:
            max_delay = user_max_delay
        delay_extension_max_supported_delay = (
            constants.MAX_DELAY_BLOCKS *
            constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK)

        # get post vertex max delay
        post_vertex_max_supported_delay_ms = \
            post_pop_vertex.maximum_delay_supported_in_ms

        # verify that the max delay is less than the max supported by the
        # implementation of delays
        if max_delay > (post_vertex_max_supported_delay_ms +
                        delay_extension_max_supported_delay):
            raise exceptions.ConfigurationException(
                "The maximum delay {} for projection is not supported".format(
                    max_delay))

        # all atoms from a given pop have the same synapse dynamics,
        #  machine_time_step, and time_scale_factor so get from population
        pop_atoms = population_atom_mapping[
            postsynaptic_population._class][postsynaptic_population]
        machine_time_step = \
            pop_atoms[0].population_parameters["machine_time_step"]
        time_scale_factor = \
            pop_atoms[0].population_parameters["time_scale_factor"]

        # verify max delay is less than the max delay entered by the user
        # during setup.
        if max_delay > (user_max_delay / (machine_time_step / 1000.0)):
            logger.warn("The end user entered a max delay"
                        " for which the projection breaks")

        # handle edge processing
        self._handle_edges(
            post_pop_vertex, pre_pop_vertex, projection, synapse_information,
            partitionable_graph, max_delay, post_vertex_max_supported_delay_ms,
            presynaptic_population, postsynaptic_population,
            using_virtual_board, machine_time_step, time_scale_factor,
            delay_to_vertex_mapping)

    def _handle_edges(
            self, post_pop_vertex, pre_pop_vertex, projection,
            synapse_information, partitionable_graph, max_delay,
            post_vertex_max_supported_delay_ms, presynaptic_population,
            postsynaptic_population, using_virtual_board, machine_time_step,
            time_scale_factor, delay_to_vertex_mapping):
        """

        :param post_pop_vertex:
        :param pre_pop_vertex:
        :param projection:
        :param synapse_information:
        :param partitionable_graph:
        :param max_delay:
        :param post_vertex_max_supported_delay_ms:
        :param presynaptic_population:
        :param postsynaptic_population:
        :param using_virtual_board:
        :param machine_time_step:
        :param time_scale_factor:
        :return:
        """

        # Find out if there is an existing edge between the populations
        edge_to_merge = self._find_existing_edge(
            pre_pop_vertex, post_pop_vertex, partitionable_graph)

        if edge_to_merge is not None:

            # If there is an existing edge, add the connector
            edge_to_merge.add_synapse_information(synapse_information)
            projection_edge = edge_to_merge
        else:

            # If there isn't an existing edge, create a new one
            projection_edge = ProjectionPartitionableEdge(
                pre_pop_vertex, post_pop_vertex, synapse_information,
                label=projection.label)

            # add to graph
            partitionable_graph.add_edge(projection_edge,
                                         projection.EDGE_PARTITION_ID)

        # update projection
        projection._projection_edge = projection_edge

        # If the delay exceeds the post vertex delay, add a delay extension
        if max_delay > post_vertex_max_supported_delay_ms:
            delay_edge = self._add_delay_extension(
                presynaptic_population, pre_pop_vertex, post_pop_vertex,
                max_delay, post_vertex_max_supported_delay_ms,
                machine_time_step, time_scale_factor, partitionable_graph,
                projection, delay_to_vertex_mapping)
            projection_edge.delay_edge = delay_edge

        # If there is a virtual board, we need to hold the data in case the
        # user asks for it
        if using_virtual_board:
            virtual_connection_list = list()
            connection_holder = ConnectionHolder(
                None, False, presynaptic_population.size,
                postsynaptic_population.size,
                virtual_connection_list)

            post_pop_vertex.add_pre_run_connection_holder(
                connection_holder, projection_edge,
                synapse_information)

            projection._virtual_connection_list = virtual_connection_list

    def _add_delay_extension(
            self, presynaptic_population,
            pre_pop_vertex, post_pop_vertex, max_delay_for_projection,
            max_delay_per_neuron, machine_time_step, timescale_factor,
            partitionable_graph, projection, delay_to_vertex_mapping):
        """ Instantiate delay extension component
        """

        # Create a delay extension vertex to do the extra delays
        delay_vertex = None
        if pre_pop_vertex in delay_to_vertex_mapping:
            delay_vertex = delay_to_vertex_mapping[pre_pop_vertex]

        if delay_vertex is None:

            # build a delay vertex
            delay_name = "{}_delayed".format(pre_pop_vertex.label)
            delay_vertex = DelayExtensionVertex(
                pre_pop_vertex.n_atoms, max_delay_per_neuron, pre_pop_vertex,
                machine_time_step, timescale_factor, label=delay_name)

            # store in map for other projections
            delay_to_vertex_mapping[pre_pop_vertex] = delay_vertex

            # add partitioner constraint to the pre pop vertex
            pre_pop_vertex.add_constraint(
                PartitionerSameSizeAsVertexConstraint(delay_vertex))
            partitionable_graph.add_vertex(delay_vertex)

            # Add the edge
            delay_afferent_edge = DelayAfferentPartitionableEdge(
                pre_pop_vertex, delay_vertex,
                label="{}_to_DelayExtension".format(pre_pop_vertex.label))
            partitionable_graph.add_edge(delay_afferent_edge,
                                         projection.EDGE_PARTITION_ID)

        # Ensure that the delay extension knows how many states it will support
        n_stages = int(math.ceil(
            float(max_delay_for_projection - max_delay_per_neuron) /
            float(max_delay_per_neuron)))
        if n_stages > delay_vertex.n_delay_stages:
            delay_vertex.n_delay_stages = n_stages

        # Create the delay edge if there isn't one already
        delay_edge = self._find_existing_edge(
            delay_vertex, post_pop_vertex, partitionable_graph)
        if delay_edge is None:
            delay_edge = MultiCastPartitionableEdge(
                delay_vertex, post_pop_vertex, label="{}_delayed_to_{}".format(
                    pre_pop_vertex.label, post_pop_vertex.label))
            partitionable_graph.add_edge(
                delay_edge, projection.EDGE_PARTITION_ID)
        return delay_edge

    @staticmethod
    def _get_synapse_info(
            projection_connector, synapse_type, population_atom_mapping,
            postsynaptic_population, presynaptic_population, projection_rng):
        """

        :param projection_connector:
        :param synapse_type:
        :param population_atom_mapping:
        :param postsynaptic_population:
        :param presynaptic_population:
        :param projection_rng:
        :return:
        """

        # all atoms from a given pop have the same synapse dynamics
        #  so get first atom's
        pop_atoms = population_atom_mapping[
            postsynaptic_population._class][postsynaptic_population]
        synapse_dynamics_stdp = pop_atoms[0].synapse_dynamics

        # all atoms from a given pop have the same machine time step so
        # get from the population.
        machine_time_step = \
            pop_atoms[0].population_parameters["machine_time_step"]

        # Set and store information for future processing
        synapse_information = SynapseInformation(
            projection_connector, synapse_dynamics_stdp, synapse_type)

        # update the connector with projection info.
        projection_connector.set_projection_information(
            presynaptic_population, postsynaptic_population, projection_rng,
            machine_time_step)
        return synapse_information

    @staticmethod
    def _get_synapse_type(
            post_population_vertex, postsynaptic_population, target):
        """
        locate the synapse type for a projection from the post vertex
        :param post_population_vertex:
        :param postsynaptic_population:
        :param target:
        :return:
        """
        synapse_type = post_population_vertex.synapse_type.\
            get_synapse_id_by_target(target)
        if synapse_type is None:
            raise exceptions.ConfigurationException(
                "Synapse target {} not found in {}".format(
                    target, postsynaptic_population.label))
        return synapse_type

    @staticmethod
    def _find_existing_edge(
             presynaptic_vertex, postsynaptic_vertex,
             partitionable_graph):
        """ Searches though the partitionable graph's edges to locate any\
            edge which has the same post and pre vertex

        :param presynaptic_vertex: the source partitionable vertex of the\
                multapse
        :type presynaptic_vertex: instance of\
                pacman.model.partitionable_graph.abstract_partitionable_vertex
        :param postsynaptic_vertex: The destination partitionable vertex of\
                the multapse
        :type postsynaptic_vertex: instance of\
                pacman.model.partitionable_graph.abstract_partitionable_vertex
        :return: None or the edge going to these vertices.
        """
        graph_edges = partitionable_graph.edges
        for edge in graph_edges:
            if ((edge.pre_vertex == presynaptic_vertex) and
                    (edge.post_vertex == postsynaptic_vertex)):
                return edge
        return None

    def _handle_model_type(
            self, things_containing_model_type, model_type,
            partitionable_graph, pop_to_vertex_mapping, vertex_to_pop_mapping):
        """

        :param things_containing_model_type:
        :param model_type:
        :param partitionable_graph:
        :param pop_to_vertex_mapping:
        :return:
        """

        atoms = list()

        # core based objects
        located = False
        has_constraints = False
        constraints = list()
        fixed_parameters = None
        internal_pop_to_atom_mapping = dict()

        # accumulate all atoms from those populations of this model type
        label = ""
        added_pops = list()
        for pop_pop_view_assembly in things_containing_model_type:

            # test if the population can be added to the current group.
            located, has_constraints, constraints, added, fixed_parameters = \
                self._check_population_for_addition(
                    pop_pop_view_assembly, located,
                    things_containing_model_type,
                    has_constraints, constraints, fixed_parameters)

            # if added, add to pops to remove from this list.
            if added:
                # update mapping object
                internal_pop_to_atom_mapping[pop_pop_view_assembly] = \
                    (len(atoms),
                     len(atoms) + len(
                         things_containing_model_type[pop_pop_view_assembly]))

                # add to atoms and label objects for the vertex
                atoms += things_containing_model_type[pop_pop_view_assembly]
                label += pop_pop_view_assembly.label

                # holder for array iteration modifications
                added_pops.append(pop_pop_view_assembly)

        # remove added pops
        for pop in added_pops:
            del things_containing_model_type[pop]

        # build inputs for the vertex
        inputs = dict()
        inputs['label'] = label
        inputs['constraints'] = constraints

        if issubclass(model_type, AbstractPopulationModel):
            inputs['model_class'] = model_type

        # create vertex and add to partitionable graph
        vertex = model_type.create_vertex(atoms, inputs)
        partitionable_graph.add_vertex(vertex)

        # update pop to vertex mapping
        for pop in added_pops:
            pop_to_vertex_mapping[pop] = (
                vertex,
                internal_pop_to_atom_mapping[pop][0],
                internal_pop_to_atom_mapping[pop][1])

            pop._mapped_vertices = pop_to_vertex_mapping[pop]

        # update vertex to pop mapping
        vertex_to_pop_mapping[vertex] = list()
        for pop in added_pops:
            vertex_to_pop_mapping[vertex].append(
                (pop, internal_pop_to_atom_mapping[pop][0],
                 internal_pop_to_atom_mapping[pop][1]))

    @staticmethod
    def _check_population_for_addition(
            pop_pop_view_assembly, located, things_containing_model_type,
            has_constraints, constraints, fixed_parameters):
        """

        :param pop_pop_view_assembly:
        :param located:
        :param has_constraints:
        :param constraints:
        :param fixed_parameters:
        :return:
        """

        added = False
        # if first population, record data needed for comparison
        if not located:
            if len(pop_pop_view_assembly.constraints) != 0:
                has_constraints = True
                constraints = pop_pop_view_assembly.constraints

            fixed_parameters = \
                things_containing_model_type[pop_pop_view_assembly][0].\
                population_parameters

            located = True
            added = True

        else:  # not first population, therefore compare
            # verify the pop is merge able
            if (not has_constraints and
                    len(pop_pop_view_assembly.constraints) == 0):

                # other fixed parameter extraction
                other_fixed_parameters = \
                    things_containing_model_type[pop_pop_view_assembly][0].\
                    population_parameters

                added = True
                for parameter_name in fixed_parameters:
                    if (other_fixed_parameters[parameter_name] !=
                            fixed_parameters[parameter_name]):
                        added = False

        # return data items
        return located, has_constraints, \
            constraints, added, fixed_parameters
