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

from collections import defaultdict
import math
from spinn_utilities.overrides import overrides
from spinn_utilities.config_holder import get_config_bool
from spinn_front_end_common.utilities.constants import (
    BITS_PER_WORD, BYTES_PER_WORD)
from spinn_front_end_common.abstract_models.impl import (
    TDMAAwareApplicationVertex)
from spynnaker.pyNN.exceptions import DelayExtensionException
from spynnaker.pyNN.models.abstract_models import AbstractHasDelayStages
from spynnaker.pyNN.utilities.constants import (
    POP_TABLE_MAX_ROW_LENGTH)
from .delay_block import DelayBlock
from .delay_generator_data import DelayGeneratorData

_DELAY_PARAM_HEADER_WORDS = 8


class DelayExtensionVertex(
        TDMAAwareApplicationVertex, AbstractHasDelayStages):
    """ Provide delays to incoming spikes in multiples of the maximum delays\
        of a neuron (typically 16 or 32)
    """
    __slots__ = [
        # The parition this Delay is supporting
        "__partition",
        "__delay_blocks",
        "__delay_per_stage",
        "__n_delay_stages",
        "__delay_generator_data",
        "__drop_late_spikes",
        "__outgoing_edges"]

    # this maps to what master assumes
    MAX_SLOTS = 8
    SAFETY_FACTOR = 5000
    MAX_DTCM_AVAILABLE = 59756 - SAFETY_FACTOR

    MISMATCHED_DELAY_PER_STAGE_ERROR_MESSAGE = (
        "The delay per stage is already set to {}, and therefore {} is not "
        "yet feasible. Please report it to Spinnaker user mail list.")

    def __init__(
            self, partition, delay_per_stage, n_delay_stages,
            label="DelayExtension"):
        """
        :param partition: The parition this Delay is supporting
        :type partition:
            ~pacman.mode.graph.application.ApplicationEdgePartition
        :param int delay_per_stage: the delay per stage
        :param int n_delay_stages: the (initial) number of delay stages needed
        :param str label: the vertex label
        """
        # pylint: disable=too-many-arguments
        super().__init__(
            label, POP_TABLE_MAX_ROW_LENGTH, splitter=None)

        self.__partition = partition
        self.__n_delay_stages = n_delay_stages
        self.__delay_per_stage = delay_per_stage
        self.__delay_generator_data = defaultdict(list)

        # Dictionary of vertex_slice -> delay block for data specification
        self.__delay_blocks = dict()

        self.__drop_late_spikes = get_config_bool(
            "Simulation", "drop_late_spikes")

        self.__outgoing_edges = list()

    @property
    def n_atoms(self):
        return self.__partition.pre_vertex.n_atoms

    @property
    def drop_late_spikes(self):
        return self.__drop_late_spikes

    @staticmethod
    def get_max_delay_ticks_supported(delay_ticks_at_post_vertex):
        return DelayExtensionVertex.MAX_SLOTS * delay_ticks_at_post_vertex

    @property
    @overrides(AbstractHasDelayStages.n_delay_stages)
    def n_delay_stages(self):
        """ The maximum number of delay stages required by any connection\
            out of this delay extension vertex

        :rtype: int
        """
        return self.__n_delay_stages

    def set_new_n_delay_stages_and_delay_per_stage(
            self, n_delay_stages, delay_per_stage):
        if delay_per_stage != self.__delay_per_stage:
            raise DelayExtensionException(
                self.MISMATCHED_DELAY_PER_STAGE_ERROR_MESSAGE.format(
                    self.__delay_per_stage, delay_per_stage))

        if n_delay_stages > self.__n_delay_stages:
            self.__n_delay_stages = n_delay_stages

    @property
    def delay_per_stage(self):
        return self.__delay_per_stage

    @property
    def source_vertex(self):
        """
        :rtype: ~pacman.model.graphs.application.ApplicationVertex
        """
        return self.__partition.pre_vertex

    def add_delays(self, vertex_slice, source_ids, stages):
        """ Add delayed connections for a given vertex slice

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param list(int) source_ids:
        :param list(int) stages:
        """
        if vertex_slice not in self.__delay_blocks:
            self.__delay_blocks[vertex_slice] = DelayBlock(
                self.__n_delay_stages, vertex_slice)
        for (source_id, stage) in zip(source_ids, stages):
            self.__delay_blocks[vertex_slice].add_delay(source_id, stage)

    def delay_blocks_for(self, vertex_slice):
        if vertex_slice in self.__delay_blocks:
            return self.__delay_blocks[vertex_slice]
        else:
            return DelayBlock(
                self.__n_delay_stages, vertex_slice)

    def add_generator_data(
            self, max_row_n_synapses, max_delayed_row_n_synapses, pre_slices,
            post_slices, pre_vertex_slice, post_vertex_slice,
            synapse_information, max_stage, max_delay_per_stage):
        """ Add delays for a connection to be generated

        :param int max_row_n_synapses:
            The maximum number of synapses in a row
        :param int max_delayed_row_n_synapses:
            The maximum number of synapses in a delay row
        :param list(~pacman.model.graphs.common.Slice) pre_slices:
            The list of slices of the pre application vertex
        :param list(~pacman.model.graphs.common.Slice) post_slices:
            The list of slices of the post application vertex
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
            The slice of the pre applcation vertex currently being
            considered
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The slice of the post application vertex currently being
            considered
        :param ~spynnaker.pyNN.models.neural_projections.SynapseInformation \
                synapse_information:
            The synapse information of the connection
        :param synapse_information:
        :type synapse_information:
            ~spynnaker.pyNN.models.neural_projections.SynapseInformation
        :param int max_stage:
            The maximum delay stage
        """
        self.__delay_generator_data[pre_vertex_slice].append(
            DelayGeneratorData(
                max_row_n_synapses, max_delayed_row_n_synapses,
                pre_slices, post_slices,
                pre_vertex_slice, post_vertex_slice,
                synapse_information, max_stage, max_delay_per_stage))

    def gen_on_machine(self, vertex_slice):
        """ Determine if the given slice needs to be generated on the machine

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: bool
        """
        return vertex_slice in self.__delay_generator_data

    def delay_generator_data(self, vertex_slice):
        return self.__delay_generator_data.get(vertex_slice, None)

    def delay_params_size(self, vertex_slice):
        """ The size of the delay parameters for a given vertex slice

        :param Slice slice: The slice to get the size of the parameters for
        """
        n_words_per_stage = int(
            math.ceil(vertex_slice.n_atoms / BITS_PER_WORD))
        return BYTES_PER_WORD * (
            _DELAY_PARAM_HEADER_WORDS +
            (self.__n_delay_stages * n_words_per_stage))

    @overrides(TDMAAwareApplicationVertex.get_n_cores)
    def get_n_cores(self):
        return len(self._splitter.get_out_going_slices())

    @property
    def partition(self):
        return self.__partition

    def add_outgoing_edge(self, edge):
        """ Add an outgoing edge to the delay extension

        :param DelayedApplicationEdge delay_edge: The edge to add
        """
        self.__outgoing_edges.append(edge)

    @property
    def outgoing_edges(self):
        """ Get the outgoing edges from this vertex

        :rtype: list(DelayApplicationEdge)
        """
        return self.__outgoing_edges
