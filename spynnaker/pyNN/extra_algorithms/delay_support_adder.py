# Copyright (c) 2020-2021 The University of Manchester
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

from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spinn_front_end_common.utilities.globals_variables import (
    machine_time_step_ms)
from spynnaker.pyNN.exceptions import DelayExtensionException
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    AbstractSpynnakerSplitterDelay, SplitterDelayVertexSlice)
from spynnaker.pyNN.models.neural_projections import (
    ProjectionApplicationEdge, DelayedApplicationEdge,
    DelayAfferentApplicationEdge)
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
from spynnaker.pyNN.utilities import constants

logger = FormatAdapter(logging.getLogger(__name__))


class DelaySupportAdder(object):
    """ adds delay extension vertices into the APP graph as needed

    :param ApplicationGraph app_graph: the app graph
    :param int user_max_delay: the user defined max delay
    :rtype: None
    """

    __slots__ = [
        "_app_to_delay_map",
        "_delay_post_edge_map",
        "_delay_pre_edges"]

    INVALID_SPLITTER_FOR_DELAYS_ERROR_MSG = (
        "The app vertex {} with splitter {} does not support delays and yet "
        "requires a delay support for edge {}. Please use a Splitter which "
        "utilises the AbstractSpynnakerSplitterDelay interface.")

    DELAYS_NOT_SUPPORTED_SPLITTER = (
        "The app vertex {} with splitter {} does not support delays and yet "
        "requires a delay support for edge {}. Please use a Splitter which "
        "does not have accepts_edges_from_delay_vertex turned off.")

    NOT_SUPPORTED_DELAY_ERROR_MSG = (
        "The maximum delay {} for projection {} is not supported "
        "by the splitter {} (max supported delay of the splitter is {} and "
        "a delay extension can add {} extra delay). either reduce "
        "the delay, or use a splitter which supports a larger delay, or "
        "finally implement the code to allow multiple delay extensions. "
        "good luck.")

    END_USER_MAX_DELAY_DEFILING_ERROR_MESSAGE = (
        "The end user entered a max delay for which the projection breaks")

    APP_DELAY_PROGRESS_BAR_TEXT = "Adding delay extensions as required"

    def __init__(self):
        self._app_to_delay_map = dict()
        self._delay_post_edge_map = dict()
        self._delay_pre_edges = list()

    def __call__(self, app_graph, user_max_delay):
        """ adds the delay extensions to the app graph, now that all the\
            splitter objects have been set.

        :param ~pacman.model.graphs.application.ApplicationGraph app_graph:
            the app graph
        :param int user_max_delay: the user defined max delay
        """

        # progress abr and data holders
        progress = ProgressBar(
            len(list(app_graph.outgoing_edge_partitions)),
            self.APP_DELAY_PROGRESS_BAR_TEXT)

        # go through all partitions.
        for app_outgoing_edge_partition in progress.over(
                app_graph.outgoing_edge_partitions):
            for app_edge in app_outgoing_edge_partition.edges:
                if isinstance(app_edge, ProjectionApplicationEdge):

                    # figure the max delay and if we need a delay extension
                    synapse_infos = app_edge.synapse_information
                    (max_delay_needed, post_vertex_max_delay,
                     need_delay_extension) = self._check_delay_values(
                        app_edge, user_max_delay, synapse_infos)

                    # if we need a delay, add it to the app graph.
                    if need_delay_extension:
                        delay_app_vertex = (
                            self._create_delay_app_vertex_and_pre_edge(
                                app_outgoing_edge_partition, app_edge,
                                post_vertex_max_delay, app_graph,
                                max_delay_needed))

                        # update the delay extension for the max delay slots.
                        # NOTE do it accumulately. coz else more loops.
                        delay_app_vertex. \
                            set_new_n_delay_stages_and_delay_per_stage(
                                post_vertex_max_delay, max_delay_needed)

                        # add the edge from the delay extension to the
                        # dest vertex
                        self._create_post_delay_edge(
                            delay_app_vertex, app_edge)

        # avoids mutating the list of outgoing partitions. add them afterwards
        self._add_new_app_edges(app_graph)

    def _add_new_app_edges(self, app_graph):
        """ adds new edges to the app graph. avoids mutating the arrays being\
            iterated over previously.

        :param ApplicationGraph app_graph: app graph
        :rtype: None
        """
        for key in self._delay_post_edge_map:
            delay_edge = self._delay_post_edge_map[key]
            app_graph.add_edge(delay_edge, constants.SPIKE_PARTITION_ID)
        for edge in self._delay_pre_edges:
            app_graph.add_edge(edge, constants.SPIKE_PARTITION_ID)

    def _create_post_delay_edge(self, delay_app_vertex, app_edge):
        """ creates the edge between delay extension and post vertex. stores\
            for future loading to the app graph when safe to do so.

        :param ApplicationVertex delay_app_vertex: delay extension vertex
        :param app_edge: the undelayed app edge this is associated with.
        :rtype: None
        """
        # check for post edge
        delayed_edge = self._delay_post_edge_map.get(
            (delay_app_vertex, app_edge.post_vertex), None)
        if delayed_edge is None:
            delay_edge = DelayedApplicationEdge(
                delay_app_vertex, app_edge.post_vertex,
                app_edge.synapse_information,
                label="{}_delayed_to_{}".format(
                    app_edge.pre_vertex.label, app_edge.post_vertex.label),
                undelayed_edge=app_edge)
            self._delay_post_edge_map[
                (delay_app_vertex, app_edge.post_vertex)] = delay_edge
            app_edge.delay_edge = delay_edge

    def _create_delay_app_vertex_and_pre_edge(
            self, app_outgoing_edge_partition, app_edge, post_vertex_max_delay,
            app_graph, max_delay_needed):
        """ creates the delay extension app vertex and the edge from the src\
            vertex to this delay extension. Adds to the graph, as safe to do\
            so.

        :param OutgoingEdgePartition app_outgoing_edge_partition:
            the original outgoing edge partition.
        :param AppEdge app_edge: the undelayed app edge.
        :param int post_vertex_max_delay: delay supported by post vertex.
        :param int max_delay_needed: the max delay needed by this app edge.
        :param ApplicationGraph app_graph: the app graph.
        :return: the DelayExtensionAppVertex
        """

        # get delay extension vertex if it already exists.
        delay_app_vertex = self._app_to_delay_map.get(
            app_outgoing_edge_partition, None)
        if delay_app_vertex is None:
            # build delay app vertex
            delay_name = "{}_delayed".format(app_edge.pre_vertex.label)
            delay_app_vertex = DelayExtensionVertex(
                app_edge.pre_vertex.n_atoms, post_vertex_max_delay,
                max_delay_needed - post_vertex_max_delay, app_edge.pre_vertex,
                label=delay_name)

            # set trackers
            delay_app_vertex.splitter = (
                SplitterDelayVertexSlice(app_edge.pre_vertex.splitter))
            app_graph.add_vertex(delay_app_vertex)
            self._app_to_delay_map[app_outgoing_edge_partition] = (
                delay_app_vertex)

            # build afferent app edge
            delay_pre_edge = DelayAfferentApplicationEdge(
                app_edge.pre_vertex, delay_app_vertex,
                label="{}_to_DelayExtension".format(
                    app_edge.pre_vertex.label))
            self._delay_pre_edges.append(delay_pre_edge)
        return delay_app_vertex

    def _check_delay_values(
            self, app_edge, user_max_delay, synapse_infos):
        """ checks the delay required from the user defined max, the max delay\
            supported by the post vertex splitter and the delay Extensions.

        :param ApplicationEdge app_edge: the undelayed app edge
        :param int user_max_delay: user max delay of the sim.
        :param iterable[SynapseInfo] synapse_infos: iterable of synapse infos
        :return:tuple of max_delay_needed, post_vertex_max_delay, bool.
        """

        # get max delay required
        max_delay_needed = max(
            synapse_info.synapse_dynamics.get_delay_maximum(
                synapse_info.connector, synapse_info)
            for synapse_info in synapse_infos)

        # check max delay works
        if max_delay_needed > user_max_delay:
            logger.warning(self.END_USER_MAX_DELAY_DEFILING_ERROR_MESSAGE)

        # get if the post vertex needs a delay extension
        post_splitter = app_edge.post_vertex.splitter
        if not isinstance(
                post_splitter, AbstractSpynnakerSplitterDelay):
            raise DelayExtensionException(
                self.INVALID_SPLITTER_FOR_DELAYS_ERROR_MSG.format(
                    app_edge.post_vertex, post_splitter, app_edge))

        post_vertex_max_delay = (
                app_edge.post_vertex.splitter.max_support_delay() *
                machine_time_step_ms())

        # if does not need a delay extension, run away
        if post_vertex_max_delay >= max_delay_needed:
            return max_delay_needed, post_vertex_max_delay, False

        # Check post vertex is ok with getting a delay
        if not post_splitter.accepts_edges_from_delay_vertex():
            raise DelayExtensionException(
                self.DELAYS_NOT_SUPPORTED_SPLITTER.format(
                    app_edge.post_vertex, post_splitter, app_edge))

        # needs a delay extension, check can be supported with 1 delay
        # extension. coz we dont do more than 1 at the moment
        total_supported_delay = (
            post_vertex_max_delay +
            (DelayExtensionVertex.get_max_delay_ticks_supported(
                post_vertex_max_delay) * machine_time_step_ms()))
        if total_supported_delay < max_delay_needed:
            raise DelayExtensionException(
                self.NOT_SUPPORTED_DELAY_ERROR_MSG.format(
                    max_delay_needed, app_edge,
                    app_edge.post_vertex.splitter,
                    post_vertex_max_delay,
                    DelayExtensionVertex.get_max_delay_ticks_supported(
                        post_vertex_max_delay)))

        # return data for building delay extensions
        return max_delay_needed, post_vertex_max_delay, True
