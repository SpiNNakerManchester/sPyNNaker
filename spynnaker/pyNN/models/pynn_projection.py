from spynnaker.pyNN.models.neuron.bag_of_neurons_vertex import \
    BagOfNeuronsVertex
from spynnaker.pyNN.models.neuron.synapse_dynamics.synapse_dynamics_static \
    import SynapseDynamicsStatic
from spynnaker.pyNN.models.neuron.connection_holder import ConnectionHolder
from spinn_front_end_common.abstract_models.abstract_changable_after_run \
    import AbstractChangableAfterRun

from spinn_front_end_common.utilities import exceptions

from spinn_machine.utilities.progress_bar import ProgressBar

import logging

logger = logging.getLogger(__name__)


# noinspection PyProtectedMember
class Projection(object):
    """ A container for all the connections of a given type (same synapse type\
        and plasticity mechanisms) between two populations, together with\
        methods to set parameters of those connections, including of\
        plasticity mechanisms.
    """

    # partition id used by all edges of projections
    EDGE_PARTITION_ID = "SPIKE"

    # noinspection PyUnusedLocal
    def __init__(
            self, presynaptic_population, postsynaptic_population, label,
            connector, spinnaker_control, machine_time_step, timescale_factor,
            source=None, target='excitatory', synapse_dynamics=None, rng=None):
        self._spinnaker = spinnaker_control
        self._presynaptic_population = presynaptic_population
        self._postsynaptic_population = postsynaptic_population
        self._connector = connector
        self._target = target
        self._rng = rng
        self._virtual_connection_list = None
        self._synapse_information = None

        if source is not None:
            logger.warn(
                "source currently means nothing to the SpiNNaker implementation"
                " of the PyNN projection, therefore it will be ignored")

        self._projection_edge = None
        self._host_based_synapse_list = None
        self._has_retrieved_synaptic_list_from_machine = False

        # check projection is to a vertex which can handle spikes reception
        if not issubclass(postsynaptic_population._class,
                          BagOfNeuronsVertex):
            raise exceptions.ConfigurationException(
                "postsynaptic population is not designed to receive"
                " synaptic projections")

        # update atom's synapse dynamics.
        synapse_dynamics_stdp = None
        if synapse_dynamics is None:
            synapse_dynamics_stdp = SynapseDynamicsStatic()
        else:
            synapse_dynamics_stdp = synapse_dynamics.slow
        atoms_for_population = postsynaptic_population._get_atoms_for_pop()
        for atom in atoms_for_population:
            atom.synapse_dynamics = synapse_dynamics_stdp

        # check that the projection edges label is not none, and give an
        # auto generated label if set to None
        if label is None:
            self._label = "projection edge {}".format(
                spinnaker_control.none_labelled_edge_count)
            spinnaker_control.increment_none_labelled_edge_count()
        else:
            self._label = label

        spinnaker_control._add_projection(self)

    @property
    def label(self):
        return self._label

    @property
    def target(self):
        return self._target

    @property
    def requires_mapping(self):
        if (isinstance(self._projection_edge, AbstractChangableAfterRun) and
                self._projection_edge.requires_mapping):
            return True
        return False

    def mark_no_changes(self):
        if isinstance(self._projection_edge, AbstractChangableAfterRun):
            self._projection_edge.mark_no_changes()

    def describe(self, template='projection_default.txt', engine='default'):
        """ Return a human-readable description of the projection.

        The output may be customised by specifying a different template
        together with an associated template engine (see ``pyNN.descriptions``)

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
    def getSynapseDynamics(self, parameter_name, list_format='list',
                           gather=True):
        """ Get parameters of the dynamic synapses for all connections in this\
            Projection.
        :param parameter_name:
        :param list_format:
        :param gather:
        """
        # TODO: Need to work out what is to be returned
        raise NotImplementedError

    def _get_synaptic_data(self, as_list, data_to_get):

        post_vertex = self._projection_edge.post_vertex
        pre_vertex = self._projection_edge.pre_vertex

        # If in virtual board mode, the connection data should be set
        if self._virtual_connection_list is not None:
            post_vertex = self._projection_edge.post_vertex
            pre_vertex = self._projection_edge.pre_vertex
            return ConnectionHolder(
                data_to_get, as_list, pre_vertex.n_atoms, post_vertex.n_atoms,
                self._virtual_connection_list)

        connection_holder = ConnectionHolder(
            data_to_get, as_list, pre_vertex.n_atoms, post_vertex.n_atoms)

        # If we haven't run, add the holder to get connections, and return it
        if not self._spinnaker.has_ran:

            post_vertex.add_pre_run_connection_holder(
                connection_holder, self._projection_edge,
                self._synapse_information)
            return connection_holder

        # Otherwise, get the connections now
        graph_mapper = self._spinnaker.graph_mapper
        placements = self._spinnaker.placements
        transceiver = self._spinnaker.transceiver
        routing_infos = self._spinnaker.routing_infos
        partitioned_graph = self._spinnaker.partitioned_graph
        subedges = graph_mapper.get_partitioned_edges_from_partitionable_edge(
            self._projection_edge)
        progress = ProgressBar(
            len(subedges),
            "Getting {}s for projection between {} and {}".format(
                data_to_get, pre_vertex.label, post_vertex.label))
        for subedge in subedges:
            placement = placements.get_placement_of_subvertex(
                subedge.post_subvertex)
            connections = post_vertex.get_connections_from_machine(
                transceiver, placement, subedge, graph_mapper, routing_infos,
                self._synapse_information, partitioned_graph)
            if connections is not None:
                connection_holder.add_connections(connections)
            progress.update()
        progress.end()
        connection_holder.finish()
        return connection_holder

    # noinspection PyPep8Naming
    def getWeights(self, format='list', gather=True):  # @ReservedAssignment
        """
        Get synaptic weights for all connections in this Projection.

        Possible formats are: a list of length equal to the number of
        connections in the projection, a 2D weight array (with NaN for
        non-existent connections). Note that for the array format, if there is
        more than connection between two cells, the summed weight will be
        given.
        :param format: the type of format to be returned (only support "list")
        :param gather: gather the weights from stuff. currently has no meaning\
                in spinnaker when set to false. Therefore is always true
        """
        if not gather:
            exceptions.ConfigurationException(
                "the gather param has no meaning for spinnaker when set to "
                "false")

        return self._get_synaptic_data(format == 'list', "weight")

    # noinspection PyPep8Naming
    def getDelays(self, format='list', gather=True):  # @ReservedAssignment
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

        return self._get_synaptic_data(format == 'list', "delay")

    def __len__(self):
        """ Return the total number of local connections.
        """

        # TODO: Need to work out what this means
        raise NotImplementedError

    # noinspection PyPep8Naming
    def printDelays(self, file_name, list_format='list', gather=True):
        """ Print synaptic weights to file. In the array format, zeros are\
            printed for non-existent connections.
        """
        # TODO:
        raise NotImplementedError

    # noinspection PyPep8Naming
    def printWeights(self, file_name, list_format='list', gather=True):
        """ Print synaptic weights to file. In the array format, zeros are\
            printed for non-existent connections.
        """
        # TODO:
        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomizeWeights(self, rand_distr):
        """ Set weights to random values taken from rand_distr.
        """
        # TODO: Requires that the synapse list is not created proactively
        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomizeDelays(self, rand_distr):
        """ Set delays to random values taken from rand_distr.
        """
        # TODO: Requires that the synapse list is not created proactively
        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomizeSynapseDynamics(self, param, rand_distr):
        """ Set parameters of the synapse dynamics to values taken from\
            rand_distr
        """
        # TODO: Look at what this is randomising
        raise NotImplementedError

    def __repr__(self):
        return "projection {}".format(self._projection_edge.label)

    # noinspection PyPep8Naming
    def saveConnections(self, file_name, gather=True, compatible_output=True):
        """ Save connections to file in a format suitable for reading in with\
            a FromFileConnector.
        """
        # TODO
        raise NotImplementedError

    def size(self, gather=True):
        """ Return the total number of connections.
         - only local connections, if gather is False,
         - all connections, if gather is True (default)
        """
        # TODO
        raise NotImplementedError

    # noinspection PyPep8Naming
    def setDelays(self, d):
        """ Set the delays

        d can be a single number, in which case all delays are set to this\
        value, or a list/1D array of length equal to the number of connections\
        in the projection, or a 2D array with the same dimensions as the\
        connectivity matrix (as returned by `getDelays(format='array')`).
        """
        # TODO: Requires that the synapse list is not created proactively
        raise NotImplementedError

    # noinspection PyPep8Naming
    def setSynapseDynamics(self, param, value):
        """ Set parameters of the dynamic synapses for all connections in this\
            projection.
        """
        # TODO: Need to set this in the edge
        raise NotImplementedError

    # noinspection PyPep8Naming
    def setWeights(self, w):
        """ Set the weights

        w can be a single number, in which case all weights are set to this\
        value, or a list/1D array of length equal to the number of connections\
        in the projection, or a 2D array with the same dimensions as the\
        connectivity matrix (as returned by `getWeights(format='array')`).\
        Weights should be in nA for current-based and uS for conductance-based\
        synapses.
        """

        # TODO: Requires that the synapse list is not created proactively
        raise NotImplementedError

    # noinspection PyPep8Naming
    def weightHistogram(self, min_weight=None, max_weight=None, nbins=10):
        """ Return a histogram of synaptic weights.

        If min and max are not given, the minimum and maximum weights are\
        calculated automatically.
        """
        # TODO
        raise NotImplementedError
