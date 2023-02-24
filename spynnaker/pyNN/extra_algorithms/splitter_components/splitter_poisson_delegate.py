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
from spinn_utilities.overrides import overrides
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from pacman.exceptions import PacmanConfigurationException
from pacman.model.partitioner_splitters import SplitterFixedLegacy
from spynnaker.pyNN.models.spike_source import SpikeSourcePoissonVertex
from .abstract_supports_one_to_one_sdram_input import (
    AbstractSupportsOneToOneSDRAMInput)


class SplitterPoissonDelegate(SplitterFixedLegacy):
    """ A splitter for Poisson sources that will ignore sources that are
        one-to-one connected to a single Population
    """

    # Message to display on error
    INVALID_POP_ERROR_MESSAGE = (
        "The vertex {} cannot be supported by the SplitterPoissonDelegate as"
        " the only vertex supported by this splitter is a "
        "SpikeSourcePoissonVertex. Please use the correct splitter for "
        "your vertex and try again.")

    @property
    def send_over_sdram(self):
        """ Determine if this vertex is to be sent using SDRAM

        :rtype: bool
        """
        # If there is only one outgoing projection, and it is one-to-one
        # connected to the target, and the target knows what to do, leave
        # it to the target
        if len(self._governed_app_vertex.outgoing_projections) != 1:
            return False
        proj = self._governed_app_vertex.outgoing_projections[0]
        # pylint: disable=protected-access
        post_vertex = proj._projection_edge.post_vertex
        if not isinstance(post_vertex.splitter,
                          AbstractSupportsOneToOneSDRAMInput):
            return False
        return post_vertex.splitter.handles_source_vertex(proj)

    @overrides(SplitterFixedLegacy.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterCommon.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, SpikeSourcePoissonVertex):
            raise PacmanConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    @overrides(SplitterFixedLegacy.create_machine_vertices)
    def create_machine_vertices(self, chip_counter):
        # If sending over SDRAM, let the target handle this
        if self.send_over_sdram:
            return

        # If we passed this part, use the super class
        return super(SplitterPoissonDelegate, self).create_machine_vertices(
            chip_counter)

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        if self.send_over_sdram:
            proj = self._governed_app_vertex.outgoing_projections[0]
            # pylint: disable=protected-access
            post_vertex = proj._projection_edge.post_vertex
            return post_vertex.splitter.get_in_coming_slices()
        return super(SplitterPoissonDelegate, self).get_in_coming_slices()

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        if self.send_over_sdram:
            proj = self._governed_app_vertex.outgoing_projections[0]
            # pylint: disable=protected-access
            post_vertex = proj._projection_edge.post_vertex
            return post_vertex.splitter.get_out_going_slices()
        return super(SplitterPoissonDelegate, self).get_out_going_slices()

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id):
        if self.send_over_sdram:
            return []
        return super(SplitterPoissonDelegate, self).get_out_going_vertices(
            partition_id)

    @overrides(AbstractSplitterCommon.get_same_chip_groups)
    def get_same_chip_groups(self):
        if self.send_over_sdram:
            return []
        return super(SplitterPoissonDelegate, self).get_same_chip_groups()
