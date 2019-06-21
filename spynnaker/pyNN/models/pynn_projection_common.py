import logging
import math
import numpy
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.constraints.partitioner_constraints import (
    SameAtomsAsVertexConstraint)
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.models.abstract_models import (
    AbstractAcceptsIncomingSynapses)
from spynnaker.pyNN.models.neural_projections import (
    DelayedApplicationEdge, SynapseInformation,
    ProjectionApplicationEdge, DelayAfferentApplicationEdge)
from spynnaker.pyNN.models.utility_models import DelayExtensionVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.neuron import ConnectionHolder
from spinn_front_end_common.utilities.globals_variables import get_simulator

# pylint: disable=protected-access

logger = logging.getLogger(__name__)
_delay_extension_max_supported_delay = (
    constants.MAX_DELAY_BLOCKS * constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK)
# The maximum delay supported by the Delay extension, in ticks.


# noinspection PyProtectedMember
class PyNNProjectionCommon(object):
    """ A container for all the connections of a given type (same synapse type\
        and plasticity mechanisms) between two populations, together with\
        methods to set parameters of those connections, including of\
        plasticity mechanisms.
    """
    __slots__ = [
        "__has_retrieved_synaptic_list_from_machine",
        "__host_based_synapse_list",
        "__label",
        "__projection_edge",
        "__requires_mapping",
        "__spinnaker_control",
        "__synapse_information",
        "__virtual_connection_list"]

    # noinspection PyUnusedLocal

    def __init__(
            self, spinnaker_control, connector, synapse_dynamics_stdp,
            target, pre_synaptic_population, post_synaptic_population,
            rng, machine_time_step, user_max_delay, label, time_scale_factor):
        # pylint: disable=too-many-arguments, too-many-locals
        self.__spinnaker_control = spinnaker_control
        self.__projection_edge = None
        self.__host_based_synapse_list = None
        self.__has_retrieved_synaptic_list_from_machine = False
        self.__requires_mapping = True
        self.__label = None

        if not isinstance(post_synaptic_population._get_vertex,
                          AbstractAcceptsIncomingSynapses):
            raise ConfigurationException(
                "postsynaptic population is not designed to receive"
                " synaptic projections")

        # sort out synapse type
        synapse_type = post_synaptic_population._get_vertex\
            .get_synapse_id_by_target(target)
        if synapse_type is None:
            raise ConfigurationException(
                "Synapse target {} not found in {}".format(
                    target, post_synaptic_population.label))

        # round the delays to multiples of full timesteps
        # (otherwise SDRAM estimation calculations can go wrong)
        if not get_simulator().is_a_pynn_random(synapse_dynamics_stdp.delay):
            synapse_dynamics_stdp.delay = numpy.rint(numpy.array(
                synapse_dynamics_stdp.delay) * (
                    1000.0 / machine_time_step)) * (machine_time_step / 1000.0)

        # set the plasticity dynamics for the post pop (allows plastic stuff
        #  when needed)
        post_synaptic_population._get_vertex.set_synapse_dynamics(
            synapse_dynamics_stdp)

        # Set and store synapse information for future processing
        self.__synapse_information = SynapseInformation(
            connector, synapse_dynamics_stdp, synapse_type,
            synapse_dynamics_stdp.weight, synapse_dynamics_stdp.delay)

        # Set projection information in connector
        connector.set_projection_information(
            pre_synaptic_population, post_synaptic_population, rng,
            machine_time_step)

        # handle max delay
        max_delay = synapse_dynamics_stdp.get_delay_maximum(
            connector, self._synapse_information.delay)
        if max_delay is None:
            max_delay = user_max_delay

        # check if all delays requested can fit into the natively supported
        # delays in the models
        post_vertex_max_supported_delay_ms = \
            post_synaptic_population._get_vertex \
            .get_maximum_delay_supported_in_ms(machine_time_step)
        if max_delay > (post_vertex_max_supported_delay_ms +
                        _delay_extension_max_supported_delay):
            raise ConfigurationException(
                "The maximum delay {} for projection is not supported".format(
                    max_delay))

        if max_delay > user_max_delay / (machine_time_step / 1000.0):
            logger.warning("The end user entered a max delay"
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
            edge_to_merge.add_synapse_information(self.__synapse_information)
            self.__projection_edge = edge_to_merge
        else:

            # If there isn't an existing edge, create a new one
            self.__projection_edge = ProjectionApplicationEdge(
                pre_synaptic_population._get_vertex,
                post_synaptic_population._get_vertex,
                self.__synapse_information, label=label)

            # add edge to the graph
            spinnaker_control.add_application_edge(
                self.__projection_edge, constants.SPIKE_PARTITION_ID)

        # If the delay exceeds the post vertex delay, add a delay extension
        if max_delay > post_vertex_max_supported_delay_ms:
            delay_edge = self._add_delay_extension(
                pre_synaptic_population, post_synaptic_population, max_delay,
                post_vertex_max_supported_delay_ms, machine_time_step,
                time_scale_factor)
            self.__projection_edge.delay_edge = delay_edge

        # add projection to the SpiNNaker control system
        spinnaker_control.add_projection(self)

        # If there is a virtual board, we need to hold the data in case the
        # user asks for it
        self.__virtual_connection_list = None
        if spinnaker_control.use_virtual_board:
            self.__virtual_connection_list = list()
            pre_vertex = pre_synaptic_population._get_vertex
            post_vertex = post_synaptic_population._get_vertex
            connection_holder = ConnectionHolder(
                None, False, pre_vertex.n_atoms, post_vertex.n_atoms,
                self.__virtual_connection_list)

            post_vertex.add_pre_run_connection_holder(
                connection_holder, self.__projection_edge,
                self.__synapse_information)

    @property
    def requires_mapping(self):
        return self.__requires_mapping

    def mark_no_changes(self):
        # Does Nothing currently
        self.__requires_mapping = False

    @property
    def _synapse_information(self):
        return self.__synapse_information

    @property
    def _projection_edge(self):
        return self.__projection_edge

    def _find_existing_edge(self, pre_synaptic_vertex, post_synaptic_vertex):
        """ Searches though the graph's edges to locate any\
            edge which has the same post and pre vertex

        :param pre_synaptic_vertex: the source vertex of the multapse
        :type pre_synaptic_vertex: \
            pacman.model.graph.application.ApplicationVertex
        :param post_synaptic_vertex: The destination vertex of the multapse
        :type post_synaptic_vertex: \
            pacman.model.graph.application.ApplicationVertex
        :return: None or the edge going to these vertices.
        """

        # Find edges ending at the postsynaptic vertex
        graph_edges = self.__spinnaker_control.original_application_graph.\
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
        # pylint: disable=too-many-arguments

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
                SameAtomsAsVertexConstraint(delay_vertex))
            self.__spinnaker_control.add_application_vertex(delay_vertex)

            # Add the edge
            delay_afferent_edge = DelayAfferentApplicationEdge(
                pre_vertex, delay_vertex, label="{}_to_DelayExtension".format(
                    pre_vertex.label))
            self.__spinnaker_control.add_application_edge(
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
                delay_vertex, post_vertex, self.__synapse_information,
                label="{}_delayed_to_{}".format(
                    pre_vertex.label, post_vertex.label))
            self.__spinnaker_control.add_application_edge(
                delay_edge, constants.SPIKE_PARTITION_ID)
        else:
            delay_edge.add_synapse_information(self.__synapse_information)
        return delay_edge

    def _get_synaptic_data(
            self, as_list, data_to_get, fixed_values=None, notify=None,
            handle_time_out_configuration=True):
        # pylint: disable=too-many-arguments
        post_vertex = self.__projection_edge.post_vertex
        pre_vertex = self.__projection_edge.pre_vertex

        # If in virtual board mode, the connection data should be set
        if self.__virtual_connection_list is not None:
            post_vertex = self.__projection_edge.post_vertex
            pre_vertex = self.__projection_edge.pre_vertex
            connection_holder = ConnectionHolder(
                data_to_get, as_list, pre_vertex.n_atoms, post_vertex.n_atoms,
                self.__virtual_connection_list, fixed_values=fixed_values,
                notify=notify)
            connection_holder.finish()
            return connection_holder

        # if not virtual board, make connection holder to be filled in at
        # possible later date
        connection_holder = ConnectionHolder(
            data_to_get, as_list, pre_vertex.n_atoms, post_vertex.n_atoms,
            fixed_values=fixed_values, notify=notify)

        # If we haven't run, add the holder to get connections, and return it
        # and set up a callback for after run to fill in this connection holder
        if not self.__spinnaker_control.has_ran:
            post_vertex.add_pre_run_connection_holder(
                connection_holder, self.__projection_edge,
                self.__synapse_information)
            return connection_holder

        # Otherwise, get the connections now, as we have ran and therefore can
        # get them
        self.__get_projection_data(
            data_to_get, pre_vertex, post_vertex, connection_holder,
            handle_time_out_configuration)
        return connection_holder

    def __get_projection_data(
            self, data_to_get, pre_vertex, post_vertex, connection_holder,
            handle_time_out_configuration):
        # pylint: disable=too-many-arguments, too-many-locals
        ctl = self.__spinnaker_control

        # if using extra monitor functionality, locate extra data items
        if ctl.get_generated_output("UsingAdvancedMonitorSupport"):
            extra_monitors = ctl.get_generated_output(
                "MemoryExtraMonitorVertices")
            receivers = ctl.get_generated_output(
                "MemoryMCGatherVertexToEthernetConnectedChipMapping")
            extra_monitor_placements = ctl.get_generated_output(
                "MemoryExtraMonitorToChipMapping")
        else:
            extra_monitors = None
            receivers = None
            extra_monitor_placements = None

        edges = ctl.graph_mapper.get_machine_edges(self.__projection_edge)
        progress = ProgressBar(
            edges, "Getting {}s for projection between {} and {}".format(
                data_to_get, pre_vertex.label, post_vertex.label))
        for edge in progress.over(edges):
            placement = ctl.placements.get_placement_of_vertex(
                edge.post_vertex)

            # if using extra monitor data extractor find local receiver
            if extra_monitors is not None:
                receiver = helpful_functions.locate_extra_monitor_mc_receiver(
                    placement_x=placement.x, placement_y=placement.y,
                    machine=ctl.machine,
                    packet_gather_cores_to_ethernet_connection_map=receivers)
                sender_extra_monitor_core = extra_monitor_placements[
                    placement.x, placement.y]
                sender_monitor_place = ctl.placements.get_placement_of_vertex(
                    sender_extra_monitor_core)
            else:
                receiver = None
                sender_monitor_place = None

            connections = post_vertex.get_connections_from_machine(
                ctl.transceiver, placement, edge, ctl.graph_mapper,
                ctl.routing_infos, self.__synapse_information,
                ctl.machine_time_step, extra_monitors is not None,
                ctl.placements, receiver, sender_monitor_place,
                extra_monitors, handle_time_out_configuration,
                ctl.fixed_routes)
            if connections is not None:
                connection_holder.add_connections(connections)
        connection_holder.finish()

    def _clear_cache(self):
        post_vertex = self.__projection_edge.post_vertex
        if isinstance(post_vertex, AbstractAcceptsIncomingSynapses):
            post_vertex.clear_connection_cache()

    def __repr__(self):
        return "projection {}".format(self.__projection_edge.label)

    def size(self, gather=True):
        """ Return the total number of connections.

        :param gather: If False, only get the number of connections locally.\
            Which means nothing on SpiNNaker...
        """
        # TODO
        raise NotImplementedError
