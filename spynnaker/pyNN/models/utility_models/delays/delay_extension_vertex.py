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
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint)
from spinn_front_end_common.abstract_models import (
    AbstractProvidesOutgoingPartitionConstraints)
from spinn_front_end_common.abstract_models.impl import (
    TDMAAwareApplicationVertex)
from spinn_front_end_common.utilities import globals_variables
from spynnaker.pyNN.exceptions import DelayExtensionException
from spynnaker.pyNN.models.abstract_models import AbstractHasDelayStages
from spynnaker.pyNN.utilities.constants import (
    POP_TABLE_MAX_ROW_LENGTH)
from .delay_block import DelayBlock
from .delay_generator_data import DelayGeneratorData


class DelayExtensionVertex(
        TDMAAwareApplicationVertex, AbstractHasDelayStages,
        AbstractProvidesOutgoingPartitionConstraints):
    """ Provide delays to incoming spikes in multiples of the maximum delays\
        of a neuron (typically 16 or 32)
    """
    __slots__ = [
        "__delay_blocks",
        "__delay_per_stage",
        "__max_delay_needed_to_support",
        "__n_atoms",
        "__n_delay_stages",
        "__source_vertex",
        "__delay_generator_data",
        "__n_data_specs",
        "__drop_late_spikes"]

    # this maps to what master assumes
    MAX_TICKS_POSSIBLE_TO_SUPPORT = 8 * 16
    SAFETY_FACTOR = 5000
    MAX_DTCM_AVAILABLE = 59756 - SAFETY_FACTOR

    MISMATCHED_DELAY_PER_STAGE_ERROR_MESSAGE = (
        "The delay per stage is already set to {}, and therefore {} is not "
        "yet feasible. Please report it to Spinnaker user mail list.")

    def __init__(
            self, n_neurons, delay_per_stage, max_delay_to_support,
            source_vertex, constraints=None, label="DelayExtension"):
        """
        :param int n_neurons: the number of neurons
        :param int delay_per_stage: the delay per stage
        :param int max_delay_to_support: the max delay this will cover
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
        self.__n_delay_stages = 0
        self.__max_delay_needed_to_support = max_delay_to_support
        self.__delay_per_stage = delay_per_stage
        self.__delay_generator_data = defaultdict(list)
        self.__n_data_specs = 0
        self.set_new_n_delay_stages_and_delay_per_stage(
            self.__delay_per_stage, self.__max_delay_needed_to_support)

        # atom store
        self.__n_atoms = self.round_n_atoms(n_neurons, "n_neurons")

        # Dictionary of vertex_slice -> delay block for data specification
        self.__delay_blocks = dict()

        # Read the config for dropping late spikes
        config = globals_variables.get_simulator().config
        self.__drop_late_spikes = config.getboolean(
            "Simulation", "drop_late_spikes")

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def drop_late_spikes(self):
        return self.__drop_late_spikes

    @staticmethod
    def get_max_delay_ticks_supported(delay_ticks_at_post_vertex):
        max_slots = math.floor(
            DelayExtensionVertex.MAX_TICKS_POSSIBLE_TO_SUPPORT /
            delay_ticks_at_post_vertex)
        return max_slots * delay_ticks_at_post_vertex

    @property
    @overrides(AbstractHasDelayStages.n_delay_stages)
    def n_delay_stages(self):
        """ The maximum number of delay stages required by any connection\
            out of this delay extension vertex

        :rtype: int
        """
        return self.__n_delay_stages

    def set_new_n_delay_stages_and_delay_per_stage(
            self, new_post_vertex_n_delay, new_max_delay):
        if new_post_vertex_n_delay != self.__delay_per_stage:
            raise DelayExtensionException(
                self.MISMATCHED_DELAY_PER_STAGE_ERROR_MESSAGE.format(
                    self.__delay_per_stage, new_post_vertex_n_delay))

        new_n_stages = int(math.ceil(
            (new_max_delay - self.__delay_per_stage) /
            self.__delay_per_stage))

        if new_n_stages > self.__n_delay_stages:
            self.__n_delay_stages = new_n_stages

    @property
    def delay_per_stage(self):
        return self.__delay_per_stage

    @property
    def source_vertex(self):
        """
        :rtype: ~pacman.model.graphs.application.ApplicationVertex
        """
        return self.__source_vertex

    def add_delays(self, vertex_slice, source_ids, stages):
        """ Add delayed connections for a given vertex slice

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param list(int) source_ids:
        :param list(int) stages:
        """
        if vertex_slice not in self.__delay_blocks:
            self.__delay_blocks[vertex_slice] = DelayBlock(
                self.__n_delay_stages, self.__delay_per_stage, vertex_slice)
        for (source_id, stage) in zip(source_ids, stages):
            self.__delay_blocks[vertex_slice].add_delay(source_id, stage)

    def delay_blocks_for(self, vertex_slice):
        if vertex_slice in self.__delay_blocks:
            return self.__delay_blocks[vertex_slice]
        else:
            return DelayBlock(
                self.__n_delay_stages, self.__delay_per_stage, vertex_slice)

    def add_generator_data(
            self, max_row_n_synapses, max_delayed_row_n_synapses, pre_slices,
            post_slices, pre_vertex_slice, post_vertex_slice,
            synapse_information, max_stage, max_delay_per_stage,
            machine_time_step):
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
        :param int machine_time_step: sim machine time step
        :param int max_delay_per_stage: max delay per stage
        """
        self.__delay_generator_data[pre_vertex_slice].append(
            DelayGeneratorData(
                max_row_n_synapses, max_delayed_row_n_synapses,
                pre_slices, post_slices,
                pre_vertex_slice, post_vertex_slice,
                synapse_information, max_stage, max_delay_per_stage,
                machine_time_step))

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [ContiguousKeyRangeContraint()]

    def gen_on_machine(self, vertex_slice):
        """ Determine if the given slice needs to be generated on the machine

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: bool
        """
        return vertex_slice in self.__delay_generator_data

    def delay_generator_data(self, vertex_slice):
        return self.__delay_generator_data.get(vertex_slice, None)
