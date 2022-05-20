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

from spinn_utilities.overrides import overrides
from spinn_utilities.config_holder import get_config_bool
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.abstract_models.impl import (
    TDMAAwareApplicationVertex)
from spynnaker.pyNN.exceptions import DelayExtensionException
from spynnaker.pyNN.models.abstract_models import AbstractHasDelayStages
from spynnaker.pyNN.utilities.constants import (
    POP_TABLE_MAX_ROW_LENGTH)

_DELAY_PARAM_HEADER_WORDS = 8


class DelayExtensionVertex(
        TDMAAwareApplicationVertex, AbstractHasDelayStages):
    """ Provide delays to incoming spikes in multiples of the maximum delays\
        of a neuron (typically 16 or 32)
    """
    __slots__ = [
        "__delay_blocks",
        "__delay_per_stage",
        "__n_atoms",
        "__n_delay_stages",
        "__source_vertex",
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
            self, n_neurons, delay_per_stage, n_delay_stages,
            source_vertex, constraints=None, label="DelayExtension"):
        """
        :param int n_neurons: the number of neurons
        :param int delay_per_stage: the delay per stage
        :param int n_delay_stages: the (initial) number of delay stages needed
        :param ~pacman.model.graphs.application.ApplicationVertex \
                source_vertex:
            where messages are coming from
        :param iterable(~pacman.model.constraints.AbstractConstraint) \
                constraints:
            the vertex constraints
        :param str label: the vertex label
        """
        # pylint: disable=too-many-arguments
        super().__init__(
            label, constraints, POP_TABLE_MAX_ROW_LENGTH, splitter=None)

        self.__source_vertex = source_vertex
        self.__n_delay_stages = n_delay_stages
        self.__delay_per_stage = delay_per_stage

        # atom store
        self.__n_atoms = self.round_n_atoms(n_neurons, "n_neurons")

        # Dictionary of vertex_slice -> delay block for data specification
        self.__delay_blocks = dict()

        self.__drop_late_spikes = get_config_bool(
            "Simulation", "drop_late_spikes")

        self.__outgoing_edges = list()

    @property
    def n_atoms(self):
        return self.__n_atoms

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
        return self.__source_vertex

    def delay_params_size(self):
        """ The size of the delay parameters
        """
        return BYTES_PER_WORD * _DELAY_PARAM_HEADER_WORDS

    @overrides(TDMAAwareApplicationVertex.get_n_cores)
    def get_n_cores(self):
        return len(self._splitter.get_out_going_slices())

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
