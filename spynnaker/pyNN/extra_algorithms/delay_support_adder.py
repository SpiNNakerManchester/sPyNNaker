# Copyright (c) 2020 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import math
from typing import Dict, List, Sequence, Tuple
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.graphs.application import (
    ApplicationEdge, ApplicationEdgePartition)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import DelayExtensionException
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    AbstractSpynnakerSplitterDelay, SplitterDelayVertexSlice)
from spynnaker.pyNN.models.neural_projections import (
    ProjectionApplicationEdge, DelayedApplicationEdge,
    DelayAfferentApplicationEdge)
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex


def delay_support_adder() -> Tuple[
        Sequence[DelayExtensionVertex], Sequence[ApplicationEdge]]:
    """
    Adds the delay extensions to the application graph, now that all the
    splitter objects have been set.

    :return: The delay vertices and delay edges that were added
    :rtype: tuple(list(DelayExtensionVertex), list(DelayedApplicationEdge or
        DelayAfferentApplicationEdge))
    """
    adder = _DelaySupportAdder()
    # pylint: disable=protected-access
    return adder.add_delays()


class _DelaySupportAdder(object):
    """
    Adds delay extension vertices into the application graph as needed.
    """

    __slots__ = (
        "_app_to_delay_map",
        "_delay_post_edge_map",
        "_new_edges",
        "_new_vertices")

    def __init__(self) -> None:
        self._app_to_delay_map: Dict[
            ApplicationEdgePartition, DelayExtensionVertex] = dict()
        self._delay_post_edge_map: Dict[
            Tuple[DelayExtensionVertex, AbstractPopulationVertex],
            DelayedApplicationEdge] = dict()
        self._new_edges: List[ApplicationEdge] = list()
        self._new_vertices: List[DelayExtensionVertex] = list()

    def add_delays(self) -> Tuple[
            List[DelayExtensionVertex], List[ApplicationEdge]]:
        """
        Adds the delay extensions to the application graph, now that all the
        splitter objects have been set.

        :rtype: tuple(list(DelayExtensionVertex), list(DelayedApplicationEdge))
        """
        progress = ProgressBar(1 + SpynnakerDataView.get_n_partitions(),
                               "Adding delay extensions as required")

        for vertex in SpynnakerDataView.get_vertices_by_type(
                DelayExtensionVertex):
            self._app_to_delay_map[vertex.partition] = vertex
            for edge in vertex.outgoing_edges:
                self._delay_post_edge_map[vertex, edge.post_vertex] = edge
        progress.update(1)

        # go through all partitions.
        for app_outgoing_edge_partition in progress.over(
                SpynnakerDataView.iterate_partitions()):
            for app_edge in app_outgoing_edge_partition.edges:
                if isinstance(app_edge, ProjectionApplicationEdge):
                    self.__examine_edge_for_delays_to_add(
                        app_edge, app_outgoing_edge_partition)
        return self._new_vertices, self._new_edges

    def __examine_edge_for_delays_to_add(
            self, edge: ProjectionApplicationEdge,
            partition: ApplicationEdgePartition):
        """
        Look at a particular edge to see if it needs a delay vertex+edge
        inserted, and add it in if it does.

        :param ProjectionApplicationEdge edge:
        :param ApplicationEdgePartition partition:
        """
        # figure the max delay and if we need a delay extension
        n_stages, steps_per_stage, need_delay_ext = self._check_delay_values(
            edge, edge.synapse_information)

        # if we need a delay, add it to the app graph.
        if need_delay_ext:
            delay_app_vertex = self._create_delay_app_vertex_and_pre_edge(
                partition, edge, steps_per_stage, n_stages)

            # add the edge from the delay extension to the dest vertex
            self._create_post_delay_edge(delay_app_vertex, edge)

    def _create_post_delay_edge(
            self, delay_app_vertex: DelayExtensionVertex,
            app_edge: ProjectionApplicationEdge):
        """
        Creates the edge between delay extension and post vertex. Stores
        for future loading to the application graph when safe to do so.

        :param DelayExtensionVertex delay_app_vertex: delay extension vertex
        :param ProjectionApplicationEdge app_edge:
            the undelayed application edge this is associated with.
        """
        # check for post edge
        delayed_edge = self._delay_post_edge_map.get(
            (delay_app_vertex, app_edge.post_vertex), None)
        if delayed_edge is None:
            delay_edge = DelayedApplicationEdge(
                delay_app_vertex, app_edge.post_vertex,
                app_edge.synapse_information,
                label=(f"{app_edge.pre_vertex.label}_delayed_"
                       f"to_{app_edge.post_vertex.label}"),
                undelayed_edge=app_edge)
            self._delay_post_edge_map[
                (delay_app_vertex, app_edge.post_vertex)] = delay_edge
            self._new_edges.append(delay_edge)
            app_edge.delay_edge = delay_edge
            delay_app_vertex.add_outgoing_edge(delay_edge)

    def _create_delay_app_vertex_and_pre_edge(
            self, app_outgoing_edge_partition: ApplicationEdgePartition,
            app_edge: ProjectionApplicationEdge, delay_per_stage: int,
            n_delay_stages: int):
        """
        Creates the delay extension application vertex and the edge from the
        source vertex to this delay extension. Adds to the graph, as safe to
        do so.

        :param ApplicationEdgePartition app_outgoing_edge_partition:
            the original outgoing edge partition.
        :param ApplicationEdge app_edge: the undelayed application edge.
        :param int delay_per_stage: delay for each delay stage
        :param int n_delay_stages: the number of delay stages needed
        :return: the DelayExtensionAppVertex
        :rtype: DelayExtensionVertex
        """
        # get delay extension vertex if it already exists.
        delay_app_vertex = self._app_to_delay_map.get(
            app_outgoing_edge_partition, None)
        if delay_app_vertex is None:
            # build delay app vertex
            delay_app_vertex = DelayExtensionVertex(
                app_outgoing_edge_partition, delay_per_stage, n_delay_stages,
                app_edge.pre_vertex.n_colour_bits,
                label=f"{app_edge.pre_vertex.label}_delayed")

            # set trackers
            delay_app_vertex.splitter = SplitterDelayVertexSlice()
            self._new_vertices.append(delay_app_vertex)
            self._app_to_delay_map[app_outgoing_edge_partition] = (
                delay_app_vertex)

            # build afferent app edge
            delay_pre_edge = DelayAfferentApplicationEdge(
                app_edge.pre_vertex, delay_app_vertex,
                label=f"{app_edge.pre_vertex.label}_to_DelayExtension")
            self._new_edges.append(delay_pre_edge)
        else:
            delay_app_vertex.set_new_n_delay_stages_and_delay_per_stage(
                n_delay_stages, delay_per_stage)
        return delay_app_vertex

    def _check_delay_values(self, app_edge, synapse_infos):
        """
        Checks the delay required from the user defined max, the max delay
        supported by the post vertex splitter and the delay Extensions.

        :param ApplicationEdge app_edge: the undelayed application edge
        :param iterable[SynapseInformation] synapse_infos:
            the synapse information objects
        :return: tuple(n_delay_stages, delay_steps_per_stage, extension_needed)
        """
        # get max delay required
        max_delay_needed_ms = max(
            synapse_info.synapse_dynamics.get_delay_maximum(
                synapse_info.connector, synapse_info)
            for synapse_info in synapse_infos)

        # get if the post vertex needs a delay extension
        post_splitter = app_edge.post_vertex.splitter
        if not isinstance(
                post_splitter, AbstractSpynnakerSplitterDelay):
            raise DelayExtensionException(
                f"The app vertex {app_edge.post_vertex} "
                f"with splitter {post_splitter} does not support delays "
                f"and yet requires a delay support for edge {app_edge}. "
                "Please use a Splitter which utilises the "
                "AbstractSpynnakerSplitterDelay interface.")
        max_delay_steps = app_edge.post_vertex.splitter.max_support_delay()
        time_step_ms = SpynnakerDataView.get_simulation_time_step_ms()
        max_delay_ms = max_delay_steps * time_step_ms

        # if does not need a delay extension, run away
        if max_delay_ms >= max_delay_needed_ms:
            return 0, max_delay_steps, False

        # Check post vertex is OK with getting a delay
        if not post_splitter.accepts_edges_from_delay_vertex():
            raise DelayExtensionException(
                f"The app vertex {app_edge.post_vertex} "
                f"with splitter {post_splitter} does not support delays "
                f"and yet requires a delay support for edge {app_edge}. "
                "Please use a Splitter which does not have "
                "accepts_edges_from_delay_vertex turned off.")

        # needs a delay extension, check can be supported with 1 delay
        # extension. We don't do more than 1 at the moment
        ext_provided_ms = DelayExtensionVertex.get_max_delay_ticks_supported(
                max_delay_steps) * time_step_ms
        total_delay_ms = ext_provided_ms + max_delay_ms
        if total_delay_ms < max_delay_needed_ms:
            raise DelayExtensionException(
                f"Edge:{app_edge.label} "
                f"has a max delay of {max_delay_needed_ms}. "
                f"But at a timestep of {time_step_ms} "
                f"the max delay supported is {total_delay_ms}")

        # return data for building delay extensions
        n_stages = int(math.ceil(max_delay_needed_ms / max_delay_ms)) - 1
        return n_stages, max_delay_steps, True
