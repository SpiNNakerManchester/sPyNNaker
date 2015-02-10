import logging
import math

import numpy

from pacman.model.constraints.partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint

from spynnaker.pyNN.models.abstract_models.abstract_population_vertex \
    import AbstractPopulationVertex
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.utility_models.delay_extension_vertex \
    import DelayExtensionVertex
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.neural_projections.projection_partitionable_edge \
    import ProjectionPartitionableEdge
from spynnaker.pyNN.models.neural_projections.delay_afferent_partitionable_edge \
    import DelayAfferentPartitionableEdge
from spynnaker.pyNN.models.neural_projections.delay_partitionable_edge \
    import DelayPartitionableEdge
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList

from spynnaker.pyNN.utilities.timer import Timer

logger = logging.getLogger(__name__)


# noinspection PyProtectedMember
class Projection(object):
    """
    A container for all the connections of a given type (same synapse type
    and plasticity mechanisms) between two populations, together with methods
    to set parameters of those connections, including of plasticity mechanisms.

    :param `pacman103.front.pynn.Population` presynaptic_population:
        presynaptic Population for the Projection
    :param `pacman103.front.pynn.Population` postsynaptic_population:
        postsynaptic Population for the Projection
    :param `pacman103.front.pynn.connectors` method:
        an instance of the connection method and parameters for the Projection
    """
    _projection_count = 0

    # noinspection PyUnusedLocal
    def __init__(self, presynaptic_population, postsynaptic_population, label,
                 connector, spinnaker_control, machine_time_step,
                 timescale_factor, source=None, target='excitatory',
                 synapse_dynamics=None, rng=None):
        """
        Instantiates a :py:object:`Projection`.
        """
        self._spinnaker = spinnaker_control
        self._projection_edge = None
        self._projection_list_ranges = None
        self._delay_edge = None
        self._delay_list_ranges = None
        self._host_based_synapse_list = None
        self._has_retrieved_synaptic_list_from_machine = False

        if isinstance(postsynaptic_population._get_vertex,
                      AbstractPopulationVertex):
            # Check that the "target" is an acceptable value
            targets = postsynaptic_population._get_vertex.get_synapse_targets()
            if target not in targets:
                raise exceptions.ConfigurationException(
                    "Target {} is not available in the post-synaptic "
                    "pynn_population.py (choices are {})"
                    .format(target, targets))
            synapse_type = \
                postsynaptic_population._get_vertex.get_synapse_id(target)
        else:
            raise exceptions.ConfigurationException(
                "postsynaptic_population is not a supposal reciever of"
                " synaptic projections")

        self._weight_scale = postsynaptic_population._get_vertex.weight_scale
        synapse_list = \
            connector.generate_synapse_list(
                presynaptic_population, postsynaptic_population,
                1000.0 / machine_time_step,
                postsynaptic_population._get_vertex.weight_scale, synapse_type)
        self._host_based_synapse_list = synapse_list

        # If there are some negative weights
        if synapse_list.get_min_weight() < 0:

            # If there are mixed negative and positive weights,
            # raise an exception
            if synapse_list.get_max_weight() > 0:
                raise exceptions.ConfigurationException("Weights must be "
                                                        "positive")

            # Otherwise, the weights are all negative, so invert them(!)
            else:
                synapse_list.flip()

        # Set any weight scaling for STDP
        if synapse_dynamics is not None:
            synapse_dynamics.weight_scale =\
                postsynaptic_population._get_vertex.weight_scale

        # check if all delays requested can fit into the natively supported
        # delays in the models
        max_delay = synapse_list.get_max_delay()
        natively_supported_delay_for_models = \
            constants.MAX_SUPPORTED_DELAY_TICS

        delay_extention_max_supported_delay = \
            constants.MAX_DELAY_BLOCKS * \
            constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK

        if max_delay > (natively_supported_delay_for_models
                        + delay_extention_max_supported_delay):
            raise exceptions.ConfigurationException(
                "the max delay for projection {} is not supported by the "
                "pacman toolchain".format(max_delay))

        if conf.config.has_option("Model", "max_delay"):
            user_max_delay = conf.config.get("Model", "max_delay")
            if max_delay > user_max_delay:
                logger.warn("The end user entered a max delay"
                            " for which the projection breaks")

        # check that the projection edges label is not none, and give an
        # autogenerated label if set to None
        if label is None:
            label = "projection edge {}".format(Projection._projection_count)
            Projection._projection_count += 1

        if max_delay > natively_supported_delay_for_models:
            source_sz = presynaptic_population._get_vertex.n_atoms
            self._add_delay_extension(
                source_sz, max_delay, natively_supported_delay_for_models,
                synapse_list, presynaptic_population, postsynaptic_population,
                machine_time_step, timescale_factor, label, synapse_dynamics)

        else:

            # Find out if there is an existing edge between the populations
            edge_to_merge = self._find_existing_edge(
                presynaptic_population._get_vertex,
                postsynaptic_population._get_vertex)
            if edge_to_merge is not None:

                # If there is an existing edge, merge the lists
                self._projection_list_ranges = \
                    edge_to_merge.synapse_list.merge(synapse_list)
                self._projection_edge = edge_to_merge
            else:

                # If there isn't an existing edge, create a new one
                self._projection_edge = ProjectionPartitionableEdge(
                    presynaptic_population, postsynaptic_population,
                    machine_time_step, synapse_list=synapse_list,
                    synapse_dynamics=synapse_dynamics, label=label)
                spinnaker_control.add_edge(self._projection_edge)
                self._projection_list_ranges = synapse_list.ranges()

    def _find_existing_edge(self, presynaptic_vertex, postsynaptic_vertex):
        graph_edges = self._spinnaker.partitionable_graph.edges
        for edge in graph_edges:
            if ((edge.pre_vertex == presynaptic_vertex)
                    and (edge.post_vertex == postsynaptic_vertex)):
                return edge
        return None

    def _add_delay_extension(self, num_src_neurons, max_delay_for_projection,
                             max_delay_per_neuron, original_synapse_list,
                             presynaptic_population, postsynaptic_population,
                             machine_time_step, timescale_factor, label,
                             synapse_dynamics):
        """
        Instantiate new delay extension component, connecting a new edge from
        the source vertex to it and new edges from it to the target (given
        by numBlocks).
        The outgoing edges cover each required block of delays, in groups of
        MAX_DELAYS_PER_NEURON delay slots (currently 16).
        """
        # If there are any connections with a delay of less than the maximum,
        # create a direct connection between the two populations only
        # containing these connections
        direct_synaptic_sublist = original_synapse_list.create_delay_sublist(
            0, max_delay_per_neuron)
        if direct_synaptic_sublist.get_max_n_connections() != 0:
            edge_to_merge = self._find_existing_edge(
                presynaptic_population._get_vertex,
                postsynaptic_population._get_vertex)
            if edge_to_merge is not None:
                self._projection_list_ranges = \
                    edge_to_merge.synapse_list.merge(direct_synaptic_sublist)
                self._projection_edge = edge_to_merge
            else:
                direct_edge = ProjectionPartitionableEdge(
                    presynaptic_population, postsynaptic_population,
                    self._spinnaker.machine_time_step,
                    synapse_list=direct_synaptic_sublist, label=label)
                self._spinnaker.add_edge(direct_edge)
                self._projection_edge = direct_edge
                self._projection_list_ranges = direct_synaptic_sublist.ranges()

        # Create a delay extension vertex to do the extra delays
        delay_vertex = presynaptic_population._internal_delay_vertex
        if delay_vertex is None:
            source_name = presynaptic_population._get_vertex.label
            delay_name = "{}_delayed".format(source_name)
            delay_vertex = DelayExtensionVertex(
                n_neurons=num_src_neurons,
                source_vertex=presynaptic_population._get_vertex,
                max_delay_per_neuron=max_delay_per_neuron,
                machine_time_step=machine_time_step,
                timescale_factor=timescale_factor, label=delay_name)
            presynaptic_population._internal_delay_vertex = delay_vertex
            presynaptic_population._get_vertex.add_constraint(
                PartitionerSameSizeAsVertexConstraint(delay_vertex))
            self._spinnaker.add_vertex(delay_vertex)

        # Create a connection from the source pynn_population.py to the
        # delay vertex
        existing_remaining_edge = self._find_existing_edge(
            presynaptic_population._get_vertex, delay_vertex)
        if existing_remaining_edge is None:
            new_label = "{}_to_DE".format(label)
            remaining_edge = DelayAfferentPartitionableEdge(
                presynaptic_population._get_vertex, delay_vertex,
                label=new_label)
            self._spinnaker.add_edge(remaining_edge)

        # Create a list of the connections with delay larger than that which
        # can be handled by the neuron itself
        remaining_sublist = original_synapse_list.create_delay_sublist(
            max_delay_per_neuron + 1, max_delay_for_projection)

        # Create a special DelayEdge from the delay vertex to the outgoing
        # pynn_population.py, with the same set of connections
        delay_label = "DE to {}".format(label)
        num_blocks = int(math.floor(float(max_delay_for_projection - 1)
                                    / float(max_delay_per_neuron)))
        if num_blocks > delay_vertex.max_stages:
            delay_vertex.max_stages = num_blocks

        # Create the delay edge
        existing_delay_edge = self._find_existing_edge(
            delay_vertex, postsynaptic_population._get_vertex)
        if existing_delay_edge is not None:
            self._delay_list_ranges = existing_delay_edge.synapse_list.merge(
                remaining_sublist)
            self._delay_edge = existing_delay_edge
        else:
            self._delay_edge = DelayPartitionableEdge(
                presynaptic_population, postsynaptic_population,
                self._spinnaker.machine_time_step, num_blocks,
                max_delay_per_neuron, synapse_list=remaining_sublist,
                synapse_dynamics=synapse_dynamics, label=delay_label)
            self._delay_list_ranges = remaining_sublist.ranges()
            self._spinnaker.add_edge(self._delay_edge)

    def describe(self, template='projection_default.txt', engine='default'):
        """
        Returns a human-readable description of the projection.

        The output may be customized by specifying a different template
        togther with an associated template engine (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template context
        will be returned.
        """
        raise NotImplementedError

    def __getitem__(self, i):
        """Return the `i`th connection within the Projection."""
        raise NotImplementedError

    # noinspection PyPep8Naming
    def getDelays(self, list_format='list', gather=True):
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

        if list_format == 'list':
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
                delay = (float(row.delays[i])
                         * (float(self._spinnaker.machine_time_step) / 1000.0))
                delays[pre_atom][post_atom] = delay
        return delays

    # noinspection PyPep8Naming
    def getSynapseDynamics(self, parameter_name, list_format='list',
                           gather=True):
        """
        Get parameters of the dynamic synapses for all connections in this
        Projection.
        """
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

        weights = numpy.zeros((self._projection_edge.pre_vertex.n_atoms,
                               self._projection_edge.post_vertex.n_atoms))
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
        raise NotImplementedError

    # noinspection PyPep8Naming
    def printDelays(self, file_name, list_format='list', gather=True):
        """
        Print synaptic weights to file. In the array format, zeros are printed
        for non-existent connections.
        """
        raise NotImplementedError

    # noinspection PyPep8Naming
    def printWeights(self, file_name, list_format='list', gather=True):
        """
        Print synaptic weights to file. In the array format, zeros are printed
        for non-existent connections.
        """
        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomizeWeights(self, rand_distr):
        """
        Set weights to random values taken from rand_distr.
        """
        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomizeDelays(self, rand_distr):
        """
        Set delays to random values taken from rand_distr.
        """
        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomizeSynapseDynamics(self, param, rand_distr):
        """
        Set parameters of the synapse dynamics to values taken from rand_distr
        """
        raise NotImplementedError

    def __repr__(self):
        """
        returns a string rep of the projection
        """
        return "projection {}".format(self._projection_edge.label)

    def _retrieve_synaptic_data_from_machine(self):
        timer = None
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer = Timer()
            timer.start_timing()
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
                combined_row = rows[i][self._projection_list_ranges]
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

        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer.take_sample()
        self._has_retrieved_synaptic_list_from_machine = True

    # noinspection PyPep8Naming
    def saveConnections(self, file_name, gather=True, compatible_output=True):
        """
        Save connections to file in a format suitable for reading in with a
        FromFileConnector.
        """
        raise NotImplementedError

    def size(self, gather=True):
        """
        Return the total number of connections.
         - only local connections, if gather is False,
         - all connections, if gather is True (default)
        """
        raise NotImplementedError

    # noinspection PyPep8Naming
    def setDelays(self, d):
        """
        d can be a single number, in which case all delays are set to this
        value, or a list/1D array of length equal to the number of connections
        in the projection, or a 2D array with the same dimensions as the
        connectivity matrix (as returned by `getDelays(format='array')`).
        """
        raise NotImplementedError

    # noinspection PyPep8Naming
    def setSynapseDynamics(self, param, value):
        """
        Set parameters of the dynamic synapses for all connections in this
        projection.
        """
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
        raise NotImplementedError

    # noinspection PyPep8Naming
    def weightHistogram(self, min_weight=None, max_weight=None, nbins=10):
        """
        Return a histogram of synaptic weights.
        If min and max are not given, the minimum and maximum weights are
        calculated automatically.
        """
        raise NotImplementedError
