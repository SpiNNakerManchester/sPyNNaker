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
from pacman.model.partitioner_splitters import SplitterSliceLegacy
from pacman.exceptions import PacmanConfigurationException
from spynnaker.pyNN.models.spike_source import SpikeSourcePoissonVertex
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector)
from .abstract_supports_one_to_one_sdram_input import (
    AbstractSupportsOneToOneSDRAMInput)


class SplitterPoissonDelegate(SplitterSliceLegacy):
    """ A splitter for Poisson sources that will ignore sources that are
        one-to-one connected to a single Population
    """

    INVALID_POP_ERROR_MESSAGE = (
        "The vertex {} cannot be supported by the SplitterPoissonDelegate as"
        " the only vertex supported by this splitter is a "
        "SpikeSourcePoissonVertex. Please use the correct splitter for "
        "your vertex and try again.")

    def __init__(self):
        super(SplitterPoissonDelegate, self).__init__(
            "SplitterPoissonDelegate")

    @overrides(SplitterSliceLegacy.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterCommon.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, SpikeSourcePoissonVertex):
            raise PacmanConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    @overrides(SplitterSliceLegacy.create_machine_vertices)
    def create_machine_vertices(self, resource_tracker, machine_graph):

        # Go through the outgoing projections and find cases where the Poisson
        # source will be split elsewhere to allow SDRAM connections
        for proj in self._governed_app_vertex.outgoing_projections:
            post_vertex = proj._projection_edge.post_vertex
            connector = proj._synapse_information.connector
            if (isinstance(post_vertex, AbstractPopulationVertex) and
                isinstance(post_vertex.splitter,
                           AbstractSupportsOneToOneSDRAMInput) and
                len(self._governed_app_vertex.outgoing_projections) == 1 and
                    isinstance(connector, OneToOneConnector)):
                return

        # If we passed this part, use the super class
        super(SplitterPoissonDelegate, self).create_machine_vertices(
            resource_tracker, machine_graph)
