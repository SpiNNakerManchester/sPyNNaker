"""
Projection
"""
from pacman.model.constraints.partitioner_constraints.\
    partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint
from pacman.model.partitionable_graph.multi_cast_partitionable_edge \
    import MultiCastPartitionableEdge

from spynnaker.pyNN.models.neural_projections.synapse_information \
    import SynapseInformation
from spynnaker.pyNN.models.neuron.synapse_dynamics.synapse_dynamics_static \
    import SynapseDynamicsStatic
from spynnaker.pyNN.models.neuron.abstract_population_vertex \
    import AbstractPopulationVertex
from spynnaker.pyNN.models.utility_models.delay_extension_vertex \
    import DelayExtensionVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.neural_projections.projection_partitionable_edge \
    import ProjectionPartitionableEdge
from spynnaker.pyNN.models.neural_projections\
    .delay_afferent_partitionable_edge \
    import DelayAfferentPartitionableEdge
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList

from spinn_front_end_common.utilities import exceptions


import logging
import math
import numpy

logger = logging.getLogger(__name__)


# noinspection PyProtectedMember
class Projection(object):
    """
    A container for all the connections of a given type (same synapse type
    and plasticity mechanisms) between two populations, together with methods
    to set parameters of those connections, including of plasticity mechanisms.
    """
    _projection_count = 0

    # noinspection PyUnusedLocal
    def __init__(
            self, presynaptic_population, postsynaptic_population, label,
            connector, spinnaker_control, machine_time_step, user_max_delay,
            timescale_factor, source=None, target='excitatory',
            synapse_dynamics=None, rng=None):
        """
        Instantiates a :py:object:`Projection`.
        """
        self._spinnaker = spinnaker_control
        self._projection_edge = None
        self._host_based_synapse_list = None
        self._has_retrieved_synaptic_list_from_machine = False

        if not isinstance(postsynaptic_population._get_vertex,
                          AbstractPopulationVertex):

            raise exceptions.ConfigurationException(
                "postsynaptic_population is not a supposed receiver of"
                " synaptic projections")

        synapse_type = postsynaptic_population._get_vertex\
            .synapse_type.get_synapse_id_by_target(target)
        if synapse_type is None:
            raise exceptions.ConfigurationException(
                "Synapse target {} not found in {}".format(
                    target, postsynaptic_population.label))

        if synapse_dynamics is None:
            synapse_dynamics = SynapseDynamicsStatic()
        postsynaptic_population._get_vertex.synapse_dynamics = synapse_dynamics

        # Set and store information for future processing
        self._synapse_information = SynapseInformation(
            connector, synapse_dynamics, synapse_type)
        connector.set_population_information(
            presynaptic_population._get_vertex.n_atoms,
            postsynaptic_population._get_vertex.n_atoms)

        max_delay = synapse_dynamics.get_delay_maximum(connector)
        if max_delay is None:
            max_delay = user_max_delay

        # check if all delays requested can fit into the natively supported
        # delays in the models
        delay_extention_max_supported_delay = (
            constants.MAX_DELAY_BLOCKS *
            constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK)
        post_vertex_max_supported_delay_ms = \
            postsynaptic_population._get_vertex.maximum_delay_supported_in_ms

        if max_delay > (post_vertex_max_supported_delay_ms +
                        delay_extention_max_supported_delay):
            raise exceptions.ConfigurationException(
                "The maximum delay {} for projection is not supported".format(
                    max_delay))

        if max_delay > (user_max_delay / (machine_time_step / 1000.0)):
            logger.warn("The end user entered a max delay"
                        " for which the projection breaks")

        # check that the projection edges label is not none, and give an
        # auto-generated label if set to None
        if label is None:
            label = "projection edge {}".format(Projection._projection_count)
            Projection._projection_count += 1

        # Find out if there is an existing edge between the populations
        edge_to_merge = self._find_existing_edge(
            presynaptic_population._get_vertex,
            postsynaptic_population._get_vertex)
        if edge_to_merge is not None:

            # If there is an existing edge, add the connector
            edge_to_merge.add_synapse_information(self._synapse_information)
            self._projection_edge = edge_to_merge
        else:

            # If there isn't an existing edge, create a new one
            self._projection_edge = ProjectionPartitionableEdge(
                presynaptic_population._get_vertex,
                postsynaptic_population._get_vertex,
                self._synapse_information, label=label)

            # add edge to the graph
            spinnaker_control.add_edge(self._projection_edge)

        # If the delay exceeds the post vertex delay, add a delay extension
        if max_delay > post_vertex_max_supported_delay_ms:
            delay_edge = self._add_delay_extension(
                presynaptic_population, postsynaptic_population, label,
                max_delay, post_vertex_max_supported_delay_ms,
                machine_time_step, timescale_factor)
            self._projection_edge.delay_edge = delay_edge

    def _find_existing_edge(self, presynaptic_vertex, postsynaptic_vertex):
        """ searches though the partitionable graph's edges to locate any
        edge which has the same post and pre vertex

        :param presynaptic_vertex: the source partitionable vertex of the
        multapse
        :type presynaptic_vertex: instance of
        pacman.model.partitionable_graph.abstract_partitionable_vertex
        :param postsynaptic_vertex: The destination partitionable vertex of
        the multapse
        :type postsynaptic_vertex: instance of
        pacman.model.partitionable_graph.abstract_partitionable_vertex
        :return: None or the edge going to these vertices.
        """
        graph_edges = self._spinnaker.partitionable_graph.edges
        for edge in graph_edges:
            if ((edge.pre_vertex == presynaptic_vertex) and
                    (edge.post_vertex == postsynaptic_vertex)):
                return edge
        return None

    def _add_delay_extension(
            self, presynaptic_population, postsynaptic_population, label,
            max_delay_for_projection, max_delay_per_neuron, machine_time_step,
            timescale_factor):
        """
        Instantiate new delay extension component, connecting a new edge from
        the source vertex to it and new edges from it to the target (given
        by numBlocks).
        The outgoing edges cover each required block of delays, in groups of
        MAX_DELAYS_PER_NEURON delay slots (currently 16).
        """

        # Create a delay extension vertex to do the extra delays
        delay_vertex = presynaptic_population._internal_delay_vertex
        pre_vertex = presynaptic_population._get_vertex
        if delay_vertex is None:
            delay_name = "{}_delayed".format(pre_vertex.label)
            delay_vertex = DelayExtensionVertex(
                pre_vertex.n_atoms, max_delay_per_neuron, pre_vertex,
                machine_time_step, timescale_factor, label=delay_name)
            presynaptic_population._internal_delay_vertex = delay_vertex
            pre_vertex.add_constraint(
                PartitionerSameSizeAsVertexConstraint(delay_vertex))
            self._spinnaker.add_vertex(delay_vertex)

            # Add the edge
            delay_afferent_edge = DelayAfferentPartitionableEdge(
                pre_vertex, delay_vertex, label="{}_to_DelayExtension".format(
                    pre_vertex.label))
            self._spinnaker.add_edge(delay_afferent_edge)

        # Ensure that the delay extension knows how many states it will support
        num_stages = int(math.floor(float(max_delay_for_projection - 1) /
                                    float(max_delay_per_neuron)))
        if num_stages > delay_vertex.max_stages:
            delay_vertex.max_stages = num_stages

        # Create the delay edge if there isn't one already
        post_vertex = postsynaptic_population._get_vertex
        delay_edge = self._find_existing_edge(delay_vertex, post_vertex)
        if delay_edge is None:
            delay_edge = MultiCastPartitionableEdge(
                delay_vertex, post_vertex, label="{}_delayed_to_{}".format(
                    pre_vertex.label, post_vertex.label))
            self._spinnaker.add_edge(delay_edge)
        return delay_edge

    def describe(self, template='projection_default.txt', engine='default'):
        """
        Returns a human-readable description of the projection.

        The output may be customized by specifying a different template
        togther with an associated template engine (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template context
        will be returned.
        """
        # TODO
        raise NotImplementedError

    def __getitem__(self, i):
        """Return the `i`th connection within the Projection."""
        # TODO: Need to work out what is being returned
        raise NotImplementedError

    # noinspection PyPep8Naming
    def getDelays(self, format='list', gather=True):
        """
        Get synaptic delays for all connections in this Projection.

        Possible formats are: a list of length equal to the number of
        connections in the projection, a 2D delay array (with NaN for
        non-existent connections).
        """
        if not gather:
            exceptions.ConfigurationException(
                "the gather param has no meaning for spinnaker when set to "
                "false")

        if (self._spinnaker.has_ran and not
                self._has_retrieved_synaptic_list_from_machine):
            self._retrieve_synaptic_data_from_machine()

        if format == 'list':
            delays = list()
            for row in self._host_based_synapse_list.get_rows():
                delays.extend(
                    numpy.asarray(
                        row.delays * (
                            float(self._spinnaker.machine_time_step) / 1000.0),
                        dtype=float))
            return delays

        delays = numpy.zeros((self._projection_edge.pre_vertex.n_atoms,
                              self._projection_edge.post_vertex.n_atoms))
        rows = self._host_based_synapse_list.get_rows()
        for pre_atom in range(len(rows)):
            row = rows[pre_atom]
            for i in xrange(len(row.target_indices)):
                post_atom = row.target_indices[i]
                delay = (float(row.delays[i]) *
                         (float(self._spinnaker.machine_time_step) / 1000.0))
                delays[pre_atom][post_atom] = delay
        return delays

    # noinspection PyPep8Naming
    def getSynapseDynamics(self, parameter_name, list_format='list',
                           gather=True):
        """
        Get parameters of the dynamic synapses for all connections in this
        Projection.
        :param parameter_name: ????????
        :param list_format: ?????????
        :param gather: ??????????
        """
        # TODO: Need to work out what is to be returned
        raise NotImplementedError

    # noinspection PyPep8Naming
    def getWeights(self, format='list', gather=True):
        """
        Get synaptic weights for all connections in this Projection.
        (pyNN gather parameter not supported from the signiture
        getWeights(self, format='list', gather=True):)

        Possible formats are: a list of length equal to the number of
        connections in the projection, a 2D weight array (with NaN for
        non-existent connections). Note that for the array format, if there is
        more than connection between two cells, the summed weight will be
        given.
        :param format: the type of format to be returned (only support "list")
        :param gather: gather the weights from stuff. currently has no meaning
        in spinnaker when set to false. Therefore is always true
        """
        if not gather:
            exceptions.ConfigurationException(
                "the gather param has no meaning for spinnaker when set to "
                "false")

        if (self._spinnaker.has_ran and not
                self._has_retrieved_synaptic_list_from_machine):
            self._retrieve_synaptic_data_from_machine()

        if format == 'list':
            weights = list()
            for row in self._host_based_synapse_list.get_rows():
                weights.extend(row.weights / self._weight_scale)
            return weights

        weights = numpy.empty((self._projection_edge.pre_vertex.n_atoms,
                               self._projection_edge.post_vertex.n_atoms))
        weights.fill(numpy.nan)
        rows = self._host_based_synapse_list.get_rows()
        for pre_atom in range(len(rows)):
            row = rows[pre_atom]
            for i in xrange(len(row.target_indices)):
                post_atom = row.target_indices[i]
                weight = row.weights[i]
                weights[pre_atom][post_atom] = weight / self._weight_scale
        return weights

    def __len__(self):
        """Return the total number of local connections."""

        # TODO: Need to work out what this means
        raise NotImplementedError

    # noinspection PyPep8Naming
    def printDelays(self, file_name, list_format='list', gather=True):
        """
        Print synaptic weights to file. In the array format, zeros are printed
        for non-existent connections.
        """
        # TODO:
        raise NotImplementedError

    # noinspection PyPep8Naming
    def printWeights(self, file_name, list_format='list', gather=True):
        """
        Print synaptic weights to file. In the array format, zeros are printed
        for non-existent connections.
        """
        # TODO:
        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomizeWeights(self, rand_distr):
        """
        Set weights to random values taken from rand_distr.
        """
        # TODO: Requires that the synapse list is not created proactively
        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomizeDelays(self, rand_distr):
        """
        Set delays to random values taken from rand_distr.
        """
        # TODO: Requires that the synapse list is not created proactively
        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomizeSynapseDynamics(self, param, rand_distr):
        """
        Set parameters of the synapse dynamics to values taken from rand_distr
        """
        # TODO: Look at what this is randomizing
        raise NotImplementedError

    def __repr__(self):
        """
        returns a string rep of the projection
        """
        return "projection {}".format(self._projection_edge.label)

    def _retrieve_synaptic_data_from_machine(self):
        synapse_list = None
        delay_synapse_list = None
        if self._projection_edge is not None:
            synapse_list = \
                self._projection_edge.get_synaptic_list_from_machine(
                    graph_mapper=self._spinnaker.graph_mapper,
                    partitioned_graph=self._spinnaker.partitioned_graph,
                    placements=self._spinnaker.placements,
                    transceiver=self._spinnaker.transceiver,
                    routing_infos=self._spinnaker.routing_infos)
        if self._delay_edge is not None:
            delay_synapse_list = \
                self._delay_edge.get_synaptic_list_from_machine(
                    graph_mapper=self._spinnaker.graph_mapper,
                    placements=self._spinnaker.placements,
                    transceiver=self._spinnaker.transceiver,
                    partitioned_graph=self._spinnaker.partitioned_graph,
                    routing_infos=self._spinnaker.routing_infos)

        # If there is both a delay and a non-delay list, merge them
        if synapse_list is not None and delay_synapse_list is not None:
            rows = synapse_list.get_rows()
            delay_rows = delay_synapse_list.get_rows()
            combined_rows = list()
            for i in range(len(rows)):
                combined_row = rows[i][self._projection_list_ranges[i]]
                combined_row.append(delay_rows[i][self._delay_list_ranges[i]])
                combined_rows.append(combined_row)
            self._host_based_synapse_list = SynapticList(combined_rows)

        # If there is only a synapse list, return that
        elif synapse_list is not None:
            rows = synapse_list.get_rows()
            new_rows = list()
            for i in range(len(rows)):
                new_rows.append(rows[i][self._projection_list_ranges[i]])
            self._host_based_synapse_list = SynapticList(new_rows)

        # Otherwise return the delay list (there should be at least one!)
        else:
            rows = delay_synapse_list.get_rows()
            new_rows = list()
            for i in range(len(rows)):
                new_rows.append(rows[i][self._delay_list_ranges[i]])
            self._host_based_synapse_list = SynapticList(new_rows)

        self._has_retrieved_synaptic_list_from_machine = True

    # noinspection PyPep8Naming
    def saveConnections(self, file_name, gather=True, compatible_output=True):
        """
        Save connections to file in a format suitable for reading in with a
        FromFileConnector.
        """
        # TODO
        raise NotImplementedError

    def size(self, gather=True):
        """
        Return the total number of connections.
         - only local connections, if gather is False,
         - all connections, if gather is True (default)
        """
        # TODO
        raise NotImplementedError

    # noinspection PyPep8Naming
    def setDelays(self, d):
        """
        d can be a single number, in which case all delays are set to this
        value, or a list/1D array of length equal to the number of connections
        in the projection, or a 2D array with the same dimensions as the
        connectivity matrix (as returned by `getDelays(format='array')`).
        """
        # TODO: Requires that the synapse list is not created proactively
        raise NotImplementedError

    # noinspection PyPep8Naming
    def setSynapseDynamics(self, param, value):
        """
        Set parameters of the dynamic synapses for all connections in this
        projection.
        """
        # TODO: Need to set this in the edge
        raise NotImplementedError

    # noinspection PyPep8Naming
    def setWeights(self, w):
        """
        w can be a single number, in which case all weights are set to this
        value, or a list/1D array of length equal to the number of connections
        in the projection, or a 2D array with the same dimensions as the
        connectivity matrix (as returned by `getWeights(format='array')`).
        Weights should be in nA for current-based and uS for conductance-based
        synapses.
        """

        # TODO: Requires that the synapse list is not created proactively
        raise NotImplementedError

    # noinspection PyPep8Naming
    def weightHistogram(self, min_weight=None, max_weight=None, nbins=10):
        """
        Return a histogram of synaptic weights.
        If min and max are not given, the minimum and maximum weights are
        calculated automatically.
        """
        # TODO
        raise NotImplementedError
