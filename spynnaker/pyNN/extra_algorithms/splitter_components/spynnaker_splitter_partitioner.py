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
from __future__ import division

import logging
from pacman.model.partitioner_interfaces import AbstractSlicesConnect
from pacman.operations.partition_algorithms import SplitterPartitioner
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION)
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.exceptions import DelayExtensionException
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    AbstractSpynnakerSplitterDelay)
from spynnaker.pyNN.extra_algorithms.splitter_components.\
    splitter_delay_vertex_slice import SplitterDelayVertexSlice
from spynnaker.pyNN.models.neural_projections import (
    DelayAfferentApplicationEdge, DelayedApplicationEdge,
    ProjectionApplicationEdge)
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
from spynnaker.pyNN.utilities import constants

logger = FormatAdapter(logging.getLogger(__name__))


class SpynnakerSplitterPartitioner(SplitterPartitioner):
    """ a splitter partitioner that's bespoke for spynnaker vertices.
    """

    __slots__ = [
        "_app_to_delay_map",
        "_delay_post_edge_map",
        "_delay_pre_edges",
        "_app_edge_min_delay"]

    INVALID_SPLITTER_FOR_DELAYS_ERROR_MSG = (
        "The app vertex {} with splitter {} does not support delays and yet "
        "requires a delay support for edge {}. Please use a Splitter which "
        "utilises the AbstractSpynnakerSplitterDelay interface.")

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
        self._app_edge_min_delay = dict()

    def __call__(
            self, app_graph, machine, plan_n_time_steps, machine_time_step,
            user_max_delay, pre_allocated_resources=None):
        """
        :param ApplicationGraph app_graph: app graph
        :param ~spinn_machine.Machine machine: machine
        :param int plan_n_time_steps: the number of time steps to run for
        :param pre_allocated_resources: any pre allocated res to account for\
            before doing any splitting.
        :type pre_allocated_resources: PreAllocatedResourceContainer or None
        :rtype: tuple(MachineGraph, int)
        :raise PacmanPartitionException: when it cant partition
        """

        # add the delay extensions now that the splitter objects are all set.
        self._add_delay_app_graph_components(
            app_graph, machine_time_step, user_max_delay)

        # do partitioning in same way
        machine_graph, chips_used = SplitterPartitioner.__call__(
            self, app_graph, machine, plan_n_time_steps,
            pre_allocated_resources)

        # return the accepted things
        return machine_graph, chips_used

    def _add_delay_app_graph_components(
            self, app_graph, machine_time_step, user_max_delay):
        """ adds the delay extensions to the app graph, now that all the
        splitter objects have been set.

        :param ApplicationGraph app_graph: the app graph
        :param int machine_time_step: the machine time step
        :param int user_max_delay: the user defined max delay
        :rtype: None
        """

        # progress abr and data holders
        progress = ProgressBar(
            len(app_graph.outgoing_edge_partitions),
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
                            app_edge, user_max_delay, machine_time_step,
                            synapse_infos)

                    # if we need a delay, add it to the app graph.
                    if need_delay_extension:
                        delay_app_vertex = (
                            self._create_delay_app_vertex_and_pre_edge(
                                app_outgoing_edge_partition, app_edge,
                                post_vertex_max_delay, app_graph,
                                max_delay_needed))

                        # update the delay extension for the max delay slots.
                        # NOTE do it accumulately. coz else more loops.
                        delay_app_vertex.\
                            set_new_n_delay_stages_and_delay_per_stage(
                                post_vertex_max_delay, max_delay_needed)

                        # add the edge from the delay extension to the
                        # dest vertex
                        self._create_post_delay_edge(
                            delay_app_vertex, app_edge)

        # avoids mutating the list of outgoing partitions. add them afterwards
        self._add_new_app_edges(app_graph)

    def _add_new_app_edges(self, app_graph):
        """ adds new edges to the app graph. avoids mutating the arrays being
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
        """ creates the edge between delay extension and post vertex. stores
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
                    app_edge.pre_vertex.label, app_edge.post_vertex.label))
            self._delay_post_edge_map[
                (delay_app_vertex, app_edge.post_vertex)] = delay_edge
            app_edge.delay_edge = delay_edge

    def _create_delay_app_vertex_and_pre_edge(
            self, app_outgoing_edge_partition, app_edge, post_vertex_max_delay,
            app_graph, max_delay_needed):
        """ creates the delay extension app vertex and the edge from the src
        vertex to this delay extension. Adds to the graph, as safe to do so.

        :param OutgoingEdgePartition app_outgoing_edge_partition: \
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
            delay_app_vertex.splitter_object = (
                SplitterDelayVertexSlice(app_edge.pre_vertex.splitter_object))
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
            self, app_edge, user_max_delay, machine_time_step, synapse_infos):
        """ checks the delay required from the user defined max, the max delay
            supported by the post vertex splitter and the delay Extensions.

        :param ApplicationEdge app_edge: the undelayed app edge
        :param int user_max_delay: user max delay of the sim.
        :param int machine_time_step: machine time step of the sim.
        :param iterable[SynapseInfo] synapse_infos: iterable of synapse infos
        :return:tuple of max_delay_needed, post_vertex_max_delay, bool.
        """

        # get max delay required
        self._app_edge_min_delay[app_edge] = max(
            synapse_info.synapse_dynamics.get_delay_maximum(
                synapse_info.connector, synapse_info)
            for synapse_info in synapse_infos)
        max_delay_needed = self._app_edge_min_delay[app_edge]

        # store min delay for later lookup
        self._app_edge_min_delay[app_edge] = min(
            synapse_info.synapse_dynamics.get_delay_minimum(
                synapse_info.connector, synapse_info)
            for synapse_info in synapse_infos)

        # check max delay works
        if max_delay_needed > user_max_delay:
            logger.warning(self.END_USER_MAX_DELAY_DEFILING_ERROR_MESSAGE)

        # get if the post vertex needs a delay extension
        post_splitter_object = app_edge.post_vertex.splitter_object
        if not isinstance(
                post_splitter_object, AbstractSpynnakerSplitterDelay):
            raise DelayExtensionException(
                self.INVALID_SPLITTER_FOR_DELAYS_ERROR_MSG.format(
                    app_edge.post_vertex, post_splitter_object, app_edge))
        post_vertex_max_delay = (
            app_edge.post_vertex.splitter_object.max_support_delay() *
            (machine_time_step / MICRO_TO_MILLISECOND_CONVERSION))

        # if does not need a delay extension, run away
        if post_vertex_max_delay >= max_delay_needed:
            return max_delay_needed, post_vertex_max_delay, False

        # needs a delay extension, check can be supported with 1 delay
        # extension. coz we dont do more than 1 at the moment
        total_supported_delay = (
            post_vertex_max_delay +
            (DelayExtensionVertex.get_max_delay_ticks_supported(
                post_vertex_max_delay) *
             (machine_time_step / MICRO_TO_MILLISECOND_CONVERSION)))
        if total_supported_delay < max_delay_needed:
            raise DelayExtensionException(
                self.NOT_SUPPORTED_DELAY_ERROR_MSG.format(
                    max_delay_needed, app_edge,
                    app_edge.post_vertex.splitter_object,
                    post_vertex_max_delay,
                    DelayExtensionVertex.MAX_SUPPORTED_DELAY_IN_TICKS))

        # return data for building delay extensions
        return max_delay_needed, post_vertex_max_delay, True

    @overrides(SplitterPartitioner.create_machine_edge)
    def create_machine_edge(
            self, src_machine_vertex, dest_machine_vertex,
            common_edge_type, app_edge, machine_graph,
            app_outgoing_edge_partition, resource_tracker):
        """ overridable method for creating the machine edges from
            SplitterPartitioner

        :param MachineVertex src_machine_vertex: the src machine vertex of \
            the new machine edge.
        :param MachineVertex dest_machine_vertex: the dest machine vertex of \
            the new machine edge.
        :param MachineEdge common_edge_type: the edge type to build.
        :param ApplicationEdge app_edge: the app edge this machine edge is \
            associated with
        :param MachineGraph machine_graph: the machine graph
        :param Resource resource_tracker: the resource tracker
        :param OutgoingEdgePartition app_outgoing_edge_partition: \
            the outgoing partition to get the identifier for.
        :rtype: None
        """

        # filter off connectivity
        if (isinstance(app_edge, AbstractSlicesConnect) and not
                app_edge.could_connect(
                    src_machine_vertex.vertex_slice,
                    dest_machine_vertex.vertex_slice)):
            return

        # TODO: this only works when the synaptic manager is reengineered to
        #       not assume the un-delayed edge still exists.
        """
        filter off delay values
        post_splitter = dest_machine_vertex.app_vertex.splitter_object
        if ((not isinstance(
                src_machine_vertex, DelayExtensionMachineVertex)) and
                isinstance(post_splitter, AbstractSpynnakerSplitterDelay)):
            min_delay = self._app_edge_min_delay[app_edge]
            if post_splitter.max_support_delay() < min_delay:
                return
        """

        # build edge and add to machine graph
        machine_edge = common_edge_type(
            src_machine_vertex, dest_machine_vertex, app_edge=app_edge)
        machine_graph.add_edge(
            machine_edge, app_outgoing_edge_partition.identifier)
