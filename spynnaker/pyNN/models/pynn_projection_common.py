from spinn_front_end_common.abstract_models.abstract_changable_after_run import \
    AbstractChangableAfterRun
from spynnaker.pyNN import ProjectionApplicationEdge
from spynnaker.pyNN.models.neural_projections.synapse_information import \
    SynapseInformation
from spynnaker.pyNN.models.neuron.connection_holder import ConnectionHolder
from spynnaker.pyNN.utilities import constants


class PyNNProjectionCommon(object):
    def __init__(
            self, connector, synapse_dynamics_stdp, synapse_type,
            pre_synaptic_population, post_synaptic_population, rng,
            machine_time_step, user_max_delay, label, time_scale_factor):

        self._projection_edge = None
        self._host_based_synapse_list = None
        self._has_retrieved_synaptic_list_from_machine = False

        # Set and store information for future processing
        self._synapse_information = SynapseInformation(
            connector, synapse_dynamics_stdp, synapse_type)
        connector.set_projection_information(
            pre_synaptic_population, post_synaptic_population, rng,
            machine_time_step)

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
            raise exceptions.ConfigurationException(
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
        spinnaker_control._add_projection(self)

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
        if (isinstance(self._projection_edge, AbstractChangableAfterRun) and
                self._projection_edge.requires_mapping):
            return True
        return False

    def mark_no_changes(self):
        if isinstance(self._projection_edge, AbstractChangableAfterRun):
            self._projection_edge.mark_no_changes()

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
        machine_time_step = self._spinnaker.machine_time_step
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
        graph_edges = self._spinnaker.application_graph.edges
        for edge in graph_edges:
            if ((edge.pre_vertex == pre_synaptic_vertex) and
                    (edge.post_vertex == post_synaptic_vertex)):
                return edge
        return None
