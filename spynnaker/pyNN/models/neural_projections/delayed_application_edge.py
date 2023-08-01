# Copyright (c) 2016 The University of Manchester
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
from __future__ import annotations
from collections.abc import Iterable
from typing import List, Optional, Union, cast, TYPE_CHECKING
from pacman.model.graphs.application import ApplicationEdge
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
    from spynnaker.pyNN.models.utility_models.delays import (
        DelayExtensionVertex)
    from spynnaker.pyNN.models.neural_projections import (
        SynapseInformation, ProjectionApplicationEdge)


class DelayedApplicationEdge(ApplicationEdge):
    __slots__ = (
        "__synapse_information",
        "__undelayed_edge")

    def __init__(
            self, pre_vertex: DelayExtensionVertex,
            post_vertex: AbstractPopulationVertex,
            synapse_information: Union[
                SynapseInformation, Iterable[SynapseInformation]],
            undelayed_edge: ProjectionApplicationEdge,
            label: Optional[str] = None):
        """
        :param DelayExtensionVertex pre_vertex:
            The delay extension at the start of the edge
        :param AbstractPopulationVertex post_vertex:
            The target of the synapses
        :param synapse_information:
            The synapse information on this edge
        :type synapse_information:
            SynapseInformation or iterable(SynapseInformation)
        :param ProjectionApplicationEdge undelayed_edge:
            The edge that is used for projections without extended delays
        :param str label:
            The edge label
        """
        super().__init__(pre_vertex, post_vertex, label=label)
        if isinstance(synapse_information, Iterable):
            self.__synapse_information = list(synapse_information)
        else:
            self.__synapse_information = [synapse_information]
        self.__undelayed_edge = undelayed_edge

    @property
    def pre_vertex(self) -> DelayExtensionVertex:
        return cast(DelayExtensionVertex, super().pre_vertex)

    @property
    def synapse_information(self) -> List[SynapseInformation]:
        """
        :rtype: list(SynapseInformation)
        """
        return self.__synapse_information

    def add_synapse_information(self, synapse_information: SynapseInformation):
        """
        :param SynapseInformation synapse_information:
        """
        self.__synapse_information.append(synapse_information)

    @property
    def undelayed_edge(self) -> ProjectionApplicationEdge:
        """
        The edge for projections without extended delays.

        :rtype: ProjectionApplicationEdge
        """
        return self.__undelayed_edge
