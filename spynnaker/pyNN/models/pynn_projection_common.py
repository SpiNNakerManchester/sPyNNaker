# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import numpy
from pyNN.random import RandomDistribution
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.models.abstract_models import (
    AbstractAcceptsIncomingSynapses)
from spynnaker.pyNN.models.neural_projections import (
    SynapseInformation, ProjectionApplicationEdge)
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.neuron import ConnectionHolder

# pylint: disable=protected-access

logger = logging.getLogger(__name__)


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
            prepop_is_view, postpop_is_view,
            rng, machine_time_step, label, time_scale_factor):
        """
        :param spinnaker_control: The simulator engine core.
        :type spinnaker_control:
            ~spinn_front_end_common.interface.abstract_spinnaker_base.AbstractSpinnakerBase
        :param AbstractConnector connector:
            What is the connector for this projection.
        :param AbstractSynapseDynamics synapse_dynamics_stdp:
            How synapses behave
        :param str target: What is the target on the post-synaptic population?
        :param AbstractPopulationVertex pre_synaptic_population:
            Where do we connect from?
        :param AbstractPopulationVertex post_synaptic_population:
            Where do we connect to?
        :param rng:
        :type rng: ~pyNN.random.NumpyRNG or None
        :param int machine_time_step:
        :param label: Label for the projection, or None to generate one
        :type label: str or None
        :param int time_scale_factor:
        """
        # pylint: disable=too-many-arguments, too-many-locals
        self.__spinnaker_control = spinnaker_control
        self.__projection_edge = None
        self.__host_based_synapse_list = None
        self.__has_retrieved_synaptic_list_from_machine = False
        self.__requires_mapping = True
        self.__label = None
        pre_vertex = pre_synaptic_population._get_vertex
        post_vertex = post_synaptic_population._get_vertex

        if not isinstance(post_vertex, AbstractAcceptsIncomingSynapses):
            raise ConfigurationException(
                "postsynaptic population is not designed to receive"
                " synaptic projections")

        # sort out synapse type
        synapse_type = post_vertex.get_synapse_id_by_target(target)
        if synapse_type is None:
            raise ConfigurationException(
                "Synapse target {} not found in {}".format(
                    target, post_synaptic_population.label))

        # round the delays to multiples of full timesteps
        # (otherwise SDRAM estimation calculations can go wrong)
        if not isinstance(synapse_dynamics_stdp.delay, RandomDistribution):
            synapse_dynamics_stdp.set_delay(
                numpy.rint(
                    numpy.array(synapse_dynamics_stdp.delay) *
                    (MICRO_TO_MILLISECOND_CONVERSION / machine_time_step)) *
                (machine_time_step / MICRO_TO_MILLISECOND_CONVERSION))

        # set the plasticity dynamics for the post pop (allows plastic stuff
        #  when needed)
        post_vertex.set_synapse_dynamics(synapse_dynamics_stdp)

        # Set and store synapse information for future processing
        self.__synapse_information = SynapseInformation(
            connector, pre_synaptic_population, post_synaptic_population,
            prepop_is_view, postpop_is_view, rng, synapse_dynamics_stdp,
            synapse_type, spinnaker_control.use_virtual_board,
            synapse_dynamics_stdp.weight, synapse_dynamics_stdp.delay)

        # Set projection information in connector
        connector.set_projection_information(
            machine_time_step, self.__synapse_information)

        # check that the projection edges label is not none, and give an
        # auto generated label if set to None
        if label is None:
            label = "projection edge {}".format(
                spinnaker_control.none_labelled_edge_count)
            spinnaker_control.increment_none_labelled_edge_count()

        # Find out if there is an existing edge between the populations
        edge_to_merge = self._find_existing_edge(pre_vertex, post_vertex)
        if edge_to_merge is not None:

            # If there is an existing edge, add the connector
            edge_to_merge.add_synapse_information(self.__synapse_information)
            self.__projection_edge = edge_to_merge
        else:

            # If there isn't an existing edge, create a new one
            self.__projection_edge = ProjectionApplicationEdge(
                pre_vertex, post_vertex, self.__synapse_information,
                label=label)

            # add edge to the graph
            spinnaker_control.add_application_edge(
                self.__projection_edge, constants.SPIKE_PARTITION_ID)

        # add projection to the SpiNNaker control system
        spinnaker_control.add_projection(self)

        # reset the ring buffer shifts
        post_vertex = post_synaptic_population._get_vertex
        post_vertex.reset_ring_buffer_shifts()

        # If there is a virtual board, we need to hold the data in case the
        # user asks for it
        self.__virtual_connection_list = None
        if spinnaker_control.use_virtual_board:
            self.__virtual_connection_list = list()
            connection_holder = ConnectionHolder(
                None, False, pre_vertex.n_atoms, post_vertex.n_atoms,
                self.__virtual_connection_list)

            self.__synapse_information.add_pre_run_connection_holder(
                connection_holder)

    @property
    def requires_mapping(self):
        """ Whether this projection requires mapping.

        :rtype: bool
        """
        return self.__requires_mapping

    def mark_no_changes(self):
        """ Mark this projection as not having changes to be mapped.
        """
        self.__requires_mapping = False

    @property
    def _synapse_information(self):
        """
        :rtype: SynapseInformation
        """
        return self.__synapse_information

    @property
    def _projection_edge(self):
        """
        :rtype: ProjectionApplicationEdge
        """
        return self.__projection_edge

    def _find_existing_edge(self, pre_synaptic_vertex, post_synaptic_vertex):
        """ Searches though the graph's edges to locate any\
            edge which has the same post and pre vertex

        :param pre_synaptic_vertex: the source vertex of the multapse
        :type pre_synaptic_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :param post_synaptic_vertex: The destination vertex of the multapse
        :type post_synaptic_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :return: None or the edge going to these vertices.
        :rtype: ~.ApplicationEdge
        """

        # Find edges ending at the postsynaptic vertex
        graph_edges = self.__spinnaker_control.original_application_graph.\
            get_edges_ending_at_vertex(post_synaptic_vertex)

        # Search the edges for any that start at the presynaptic vertex
        for edge in graph_edges:
            if edge.pre_vertex == pre_synaptic_vertex:
                return edge
        return None

    def _get_synaptic_data(
            self, as_list, data_to_get, fixed_values=None, notify=None):
        """
        :param bool as_list:
        :param list(int) data_to_get:
        :param list(tuple(str,int)) fixed_values:
        :param callable(ConnectionHolder,None) notify:
        :rtype: ConnectionHolder
        """
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
            self.__synapse_information.add_pre_run_connection_holder(
                connection_holder)
            return connection_holder

        # Otherwise, get the connections now, as we have ran and therefore can
        # get them
        self.__get_projection_data(post_vertex, connection_holder)
        return connection_holder

    def __get_projection_data(self, post_vertex, connection_holder):
        """
        :param .AbstractPopulationVertex post_vertex:
            The vertex that the data will be read from
        :param ConnectionHolder connection_holder:
            The connection holder to fill in
        """
        ctl = self.__spinnaker_control

        connections = post_vertex.get_connections_from_machine(
            ctl.transceiver, ctl.placements, self.__projection_edge,
            self.__synapse_information)
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

        :param bool gather:
            If False, only get the number of connections locally.
            Which means nothing on SpiNNaker...
        """
        # TODO
        raise NotImplementedError
