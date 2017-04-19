from pacman.model.constraints.partitioner_constraints \
    import PartitionerSameSizeAsVertexConstraint

from spynnaker.pyNN.models.abstract_models.abstract_accepts_incoming_synapses \
    import AbstractAcceptsIncomingSynapses
from spynnaker.pyNN.models.neural_projections.delayed_application_edge \
    import DelayedApplicationEdge
from spynnaker.pyNN.models.neural_projections.synapse_information \
    import SynapseInformation
from spynnaker.pyNN.models.utility_models.delay_extension_vertex \
    import DelayExtensionVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.neural_projections.projection_application_edge \
    import ProjectionApplicationEdge
from spynnaker.pyNN.models.neural_projections.delay_afferent_application_edge \
    import DelayAfferentApplicationEdge
from spynnaker.pyNN.models.neuron.connection_holder import ConnectionHolder

from spinn_front_end_common.utilities import exceptions as common_exceptions

from spinn_machine.utilities.progress_bar import ProgressBar

import logging
import math
import numpy

logger = logging.getLogger(__name__)


# noinspection PyProtectedMember
class PyNNProjectionCommon(object):
    """ A container for all the connections of a given type (same synapse type\
            and plasticity mechanisms) between two populations, together with\
            methods to set parameters of those connections, including of\
            plasticity mechanisms.
        """

    # noinspection PyUnusedLocal

    def __init__(
            self, spinnaker_control, connector, synapse_dynamics_stdp,
            target, pre_synaptic_population, post_synaptic_population,
            rng, machine_time_step, user_max_delay, label, time_scale_factor):
        self._spinnaker_control = spinnaker_control
        self._projection_edge = None
        self._host_based_synapse_list = None
        self._has_retrieved_synaptic_list_from_machine = False

        if not isinstance(post_synaptic_population._get_vertex,
                          AbstractAcceptsIncomingSynapses):

            raise common_exceptions.ConfigurationException(
                "postsynaptic population is not designed to receive"
                " synaptic projections")

        # sort out synapse type
        synapse_type = post_synaptic_population._get_vertex \
            .synapse_type.get_synapse_id_by_target(target)
        if synapse_type is None:
            raise common_exceptions.ConfigurationException(
                "Synapse target {} not found in {}".format(
                    target, post_synaptic_population.label))

        # set the plasticity dynamics for the post pop (allows plastic stuff
        #  when needed)
        post_synaptic_population._get_vertex.set_synapse_dynamics(
            synapse_dynamics_stdp)

        # Set and store information for future processing
        self._synapse_information = SynapseInformation(
            connector, synapse_dynamics_stdp, synapse_type)
        connector.set_projection_information(
            pre_synaptic_population, post_synaptic_population, rng,
            machine_time_step)

        # handle max delay
        max_delay = synapse_dynamics_stdp.get_delay_maximum(connector)
        if max_delay is None:
            max_delay = user_max_delay

        # check if all delays requested can fit into the natively supported
        # delays in the models
        delay_extension_max_supported_delay = (
            constants.MAX_DELAY_BLOCKS *
            constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK)
        post_vertex_max_supported_delay_ms = \
            post_synaptic_population._get_vertex \
            .get_maximum_delay_supported_in_ms(machine_time_step)

        if max_delay > (post_vertex_max_supported_delay_ms +
                        delay_extension_max_supported_delay):
            raise common_exceptions.ConfigurationException(
                "The maximum delay {} for projection is not supported".format(
                    max_delay))

        if max_delay > (user_max_delay / (machine_time_step / 1000.0)):
            logger.warn("The end user entered a max delay"
                        " for which the projection breaks")

        # check that the projection edges label is not none, and give an
        # auto generated label if set to None
        if label is None:
            label = "projection edge {}".format(
                spinnaker_control.none_labelled_edge_count)
            spinnaker_control.increment_none_labelled_edge_count()

        # Find out if there is an existing edge between the populations
        edge_to_merge = self._find_existing_edge(
            pre_synaptic_population._get_vertex,
            post_synaptic_population._get_vertex)
        if edge_to_merge is not None:

            # If there is an existing edge, add the connector
            edge_to_merge.add_synapse_information(self._synapse_information)
            self._projection_edge = edge_to_merge
        else:

            # If there isn't an existing edge, create a new one
            self._projection_edge = ProjectionApplicationEdge(
                pre_synaptic_population._get_vertex,
                post_synaptic_population._get_vertex,
                self._synapse_information, label=label)

            # add edge to the graph
            spinnaker_control.add_application_edge(
                self._projection_edge, constants.SPIKE_PARTITION_ID)

        # If the delay exceeds the post vertex delay, add a delay extension
        if max_delay > post_vertex_max_supported_delay_ms:
            delay_edge = self._add_delay_extension(
                pre_synaptic_population, post_synaptic_population, max_delay,
                post_vertex_max_supported_delay_ms, machine_time_step,
                time_scale_factor)
            self._projection_edge.delay_edge = delay_edge

        # add projection to the spinnaker control system
        spinnaker_control.add_projection(self)

        # If there is a virtual board, we need to hold the data in case the
        # user asks for it
        self._virtual_connection_list = None
        if spinnaker_control.use_virtual_board:
            self._virtual_connection_list = list()
            pre_vertex = pre_synaptic_population._get_vertex
            post_vertex = post_synaptic_population._get_vertex
            connection_holder = ConnectionHolder(
                None, False, pre_vertex.n_atoms, post_vertex.n_atoms,
                self._virtual_connection_list)

            post_vertex.add_pre_run_connection_holder(
                connection_holder, self._projection_edge,
                self._synapse_information)

    @property
    def requires_mapping(self):
        return False

    def mark_no_changes(self):
        # Does Nothing currently
        pass

    def _find_existing_edge(self, pre_synaptic_vertex, post_synaptic_vertex):
        """ Searches though the graph's edges to locate any\
            edge which has the same post and pre vertex

        :param pre_synaptic_vertex: the source vertex of the multapse
        :type pre_synaptic_vertex: instance of\
                pacman.model.graph.application.abstract_application_vertex
        :param post_synaptic_vertex: The destination vertex of the multapse
        :type post_synaptic_vertex: instance of\
                pacman.model.graph.application.abstract_application_vertex
        :return: None or the edge going to these vertices.
        """

        # Find edges ending at the postsynaptic vertex
        graph_edges = self._spinnaker_control.application_graph.\
            get_edges_ending_at_vertex(post_synaptic_vertex)

        # Search the edges for any that start at the presynaptic vertex
        for edge in graph_edges:
            if edge.pre_vertex == pre_synaptic_vertex:
                return edge
        return None

    def _add_delay_extension(
            self, pre_synaptic_population, post_synaptic_population,
            max_delay_for_projection, max_delay_per_neuron, machine_time_step,
            timescale_factor):
        """ Instantiate delay extension component
        """

        # Create a delay extension vertex to do the extra delays
        delay_vertex = pre_synaptic_population._internal_delay_vertex
        pre_vertex = pre_synaptic_population._get_vertex
        if delay_vertex is None:
            delay_name = "{}_delayed".format(pre_vertex.label)
            delay_vertex = DelayExtensionVertex(
                pre_vertex.n_atoms, max_delay_per_neuron, pre_vertex,
                machine_time_step, timescale_factor, label=delay_name)
            pre_synaptic_population._internal_delay_vertex = delay_vertex
            pre_vertex.add_constraint(
                PartitionerSameSizeAsVertexConstraint(delay_vertex))
            self._spinnaker_control.add_application_vertex(delay_vertex)

            # Add the edge
            delay_afferent_edge = DelayAfferentApplicationEdge(
                pre_vertex, delay_vertex, label="{}_to_DelayExtension".format(
                    pre_vertex.label))
            self._spinnaker_control.add_application_edge(
                delay_afferent_edge, constants.SPIKE_PARTITION_ID)

        # Ensure that the delay extension knows how many states it will
        # support
        n_stages = int(math.ceil(
            float(max_delay_for_projection - max_delay_per_neuron) /
            float(max_delay_per_neuron)))
        if n_stages > delay_vertex.n_delay_stages:
            delay_vertex.n_delay_stages = n_stages

        # Create the delay edge if there isn't one already
        post_vertex = post_synaptic_population._get_vertex
        delay_edge = self._find_existing_edge(delay_vertex, post_vertex)
        if delay_edge is None:
            delay_edge = DelayedApplicationEdge(
                delay_vertex, post_vertex, self._synapse_information,
                label="{}_delayed_to_{}".format(
                    pre_vertex.label, post_vertex.label))
            self._spinnaker_control.add_application_edge(
                delay_edge, constants.SPIKE_PARTITION_ID)
        else:
            delay_edge.add_synapse_information(self._synapse_information)
        return delay_edge

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
        if not self._spinnaker_control.has_ran:
            post_vertex.add_pre_run_connection_holder(
                connection_holder, self._projection_edge,
                self._synapse_information)
            return connection_holder

        # Otherwise, get the connections now
        graph_mapper = self._spinnaker_control.graph_mapper
        placements = self._spinnaker_control.placements
        transceiver = self._spinnaker_control.transceiver
        routing_infos = self._spinnaker_control.routing_infos
        machine_time_step = self._spinnaker_control.machine_time_step
        edges = graph_mapper.get_machine_edges(
            self._projection_edge)
        progress = ProgressBar(
            len(edges),
            "Getting {}s for projection between {} and {}".format(
                data_to_get, pre_vertex.label, post_vertex.label))
        for edge in edges:
            placement = placements.get_placement_of_vertex(
                edge.post_vertex)
            connections = post_vertex.get_connections_from_machine(
                transceiver, placement, edge, graph_mapper, routing_infos,
                self._synapse_information, machine_time_step)
            if connections is not None:
                connection_holder.add_connections(connections)
            progress.update()
        progress.end()
        connection_holder.finish()
        return connection_holder

    def __repr__(self):
        return "projection {}".format(self._projection_edge.label)

    def size(self, gather=True):
        """ Return the total number of connections.
         - only local connections, if gather is False,
         - all connections, if gather is True (default)
        """
        # TODO
        raise NotImplementedError

    def get(self, parameter, format, gather):  # @ReservedAssignment
        """ supports getting things from a projection

        :param parameter: the parameter, "weights, delays, plastic param"
        :param format: "list" or "array".
        :param gather: supposedly if True, get connection information from \
            all MPI nodes, otherwise only from connections that exist in \
            this node.
        :return: the returns param
        """

        # do the gather check before trying to get data
        if not gather:
            common_exceptions.ConfigurationException(
                "the gather param has no meaning for spinnaker when set to "
                "false")

        # try for each possible parameters
        if parameter in {"weight", "delay", "source", "target"}:
            return self._get_synaptic_data(format == 'list', parameter)
        else:
            # get the n_connections and the parameter and then expand to
            # correct size
            size = len(self._get_synaptic_data(format == 'list', 'source'))
            data = numpy.empty(size)
            data.fill(self._synapse_information.synapse_dynamics.get_value(
                parameter))
            return data
