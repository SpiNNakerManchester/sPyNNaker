# Copyright (c) 2014 The University of Manchester
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
from typing import List, Sequence
from spinn_utilities.overrides import overrides
from spinn_utilities.config_holder import get_config_bool
from pacman.model.graphs.application import (
    ApplicationEdgePartition, ApplicationVertex)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.exceptions import DelayExtensionException
from spynnaker.pyNN.models.abstract_models import AbstractHasDelayStages
from spynnaker.pyNN.utilities.constants import POP_TABLE_MAX_ROW_LENGTH
from spynnaker.pyNN.models.neural_projections import DelayedApplicationEdge

_DELAY_PARAM_HEADER_WORDS = 9


class DelayExtensionVertex(ApplicationVertex, AbstractHasDelayStages):
    """
    Provide delays to incoming spikes in multiples of the maximum delays
    of a neuron (typically 16 or 32).
    """
    __slots__ = (
        # The partition this Delay is supporting
        "__partition",
        "__delay_per_stage",
        "__n_delay_stages",
        "__drop_late_spikes",
        "__outgoing_edges",
        "__n_colour_bits")

    # this maps to what master assumes
    MAX_SLOTS = 8
    SAFETY_FACTOR = 5000
    MAX_DTCM_AVAILABLE = 59756 - SAFETY_FACTOR

    def __init__(
            self, partition: ApplicationEdgePartition, delay_per_stage: int,
            n_delay_stages: int, n_colour_bits: int,
            label: str = "DelayExtension"):
        """
        :param partition: The partition that this delay is supporting
        :type partition:
            ~pacman.model.graphs.application.ApplicationEdgePartition
        :param int delay_per_stage: the delay per stage
        :param int n_delay_stages: the (initial) number of delay stages needed
        :param int n_colour_bits: the number of bits for event colouring
        :param str label: the vertex label
        """
        # pylint: disable=too-many-arguments
        super().__init__(
            label, POP_TABLE_MAX_ROW_LENGTH, splitter=None)

        self.__partition = partition
        self.__n_delay_stages = n_delay_stages
        self.__delay_per_stage = delay_per_stage

        self.__drop_late_spikes = get_config_bool(
            "Simulation", "drop_late_spikes") or False

        self.__outgoing_edges: List[DelayedApplicationEdge] = list()

        self.__n_colour_bits = n_colour_bits

    @property
    def n_atoms(self) -> int:
        """
        The number of atoms in this vertex.

        :rtype: int
        """
        return self.__partition.pre_vertex.n_atoms

    @property
    def drop_late_spikes(self) -> bool:
        """
        Whether to drop late spikes.
        """
        return self.__drop_late_spikes

    @staticmethod
    def get_max_delay_ticks_supported(delay_ticks_at_post_vertex: int) -> int:
        return DelayExtensionVertex.MAX_SLOTS * delay_ticks_at_post_vertex

    @property
    @overrides(AbstractHasDelayStages.n_delay_stages)
    def n_delay_stages(self) -> int:
        return self.__n_delay_stages

    def set_new_n_delay_stages_and_delay_per_stage(
            self, n_delay_stages: int, delay_per_stage: int):
        if delay_per_stage != self.__delay_per_stage:
            raise DelayExtensionException(
                "The delay per stage is already set to "
                f"{self.__delay_per_stage}, and therefore {delay_per_stage} "
                "is not yet feasible. "
                "Please report it to Spinnaker user mail list.")

        if n_delay_stages > self.__n_delay_stages:
            self.__n_delay_stages = n_delay_stages

    @property
    def delay_per_stage(self) -> int:
        """
        The delay per stage, in timesteps.
        """
        return self.__delay_per_stage

    @property
    def source_vertex(self) -> ApplicationVertex:
        return self.__partition.pre_vertex

    def delay_params_size(self):
        """
        The size of the delay parameters.
        """
        return BYTES_PER_WORD * _DELAY_PARAM_HEADER_WORDS

    @property
    def partition(self) -> ApplicationEdgePartition:
        """
        The partition that this delay is supporting.
        """
        return self.__partition

    def add_outgoing_edge(self, edge: DelayedApplicationEdge):
        """
        Add an outgoing edge to the delay extension.

        :param DelayedApplicationEdge edge: The edge to add
        """
        self.__outgoing_edges.append(edge)

    @property
    def outgoing_edges(self) -> Sequence[DelayedApplicationEdge]:
        """
        The outgoing edges from this vertex.
        """
        return self.__outgoing_edges

    @property
    def n_colour_bits(self) -> int:
        """
        The number of bits for event colouring.
        """
        return self.__n_colour_bits
