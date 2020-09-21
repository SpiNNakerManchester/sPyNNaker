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
from pacman.model.graphs.application import (
    ApplicationSpiNNakerLinkVertex, ApplicationFPGAVertex)
from spinn_front_end_common.interface.partitioner_splitters.splitter_one_to_one_legacy import SplitterOneToOneLegacy
from spinn_front_end_common.interface.partitioner_splitters.\
    splitter_slice_legacy import SplitterSliceLegacy
from spinn_front_end_common.interface.splitter_selectors import (
    SplitterSelector)
from spynnaker.pyNN.extra_algorithms.splitter_components.\
    splitter_abstract_pop_vertex_slice import (
        SplitterAbstractPopulationVertexSlice)
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.spike_source.spike_source_array_vertex import (
    SpikeSourceArrayVertex)
from spynnaker.pyNN.models.spike_source.spike_source_poisson_vertex import (
    SpikeSourcePoissonVertex)


class SpynnakerSplitterSelector(SplitterSelector):
        """
        splitter object selector that allocates splitters to app vertices
        that have not yet been given a splitter object.
        default for APV is the SplitterAbstractPopulationVertexSlice
        default for external device splitters are SplitterOneToOneLegacy
        default for the rest is the SpynnakerSplitterSliceLegacy.

        :param ApplicationGraph app_graph: app graph
        :rtype: None
        """

        def __call__(self, app_graph):
            """ basic selector which puts the legacy splitter object on
            everything without a splitter object

            :param ApplicationGraph app_graph: app graph
            :rtype: None
            """
            for app_vertex in app_graph.vertices:
                if app_vertex.splitter_object is None:
                    if isinstance(app_vertex, AbstractPopulationVertex):
                        self.abstract_pop_heuristic(app_vertex)
                    elif isinstance(app_vertex, ApplicationSpiNNakerLinkVertex):
                        self.external_spinnaker_link_heuristic(app_vertex)
                    elif isinstance(app_vertex, ApplicationFPGAVertex):
                        self.external_fpga_link_heuristic(app_vertex)
                    elif isinstance(app_vertex, SpikeSourceArrayVertex):
                        self.spike_source_array_heuristic(app_vertex)
                    elif isinstance(app_vertex, SpikeSourcePoissonVertex):
                        self.spike_source_poisson_heuristic(app_vertex)
                    else:  # go to basic selector. it might know what to do
                        self.vertex_selector(app_vertex)

        @staticmethod
        def abstract_pop_heuristic(app_vertex):
            app_vertex.splitter_object = (
                SplitterAbstractPopulationVertexSlice())

        @staticmethod
        def external_spinnaker_link_heuristic(app_vertex):
            app_vertex.splitter_object = SplitterOneToOneLegacy()

        @staticmethod
        def external_fpga_link_heuristic(app_vertex):
            app_vertex.splitter_object = SplitterOneToOneLegacy()

        @staticmethod
        def spike_source_array_heuristic(app_vertex):
            app_vertex.splitter_object = SplitterSliceLegacy()

        @staticmethod
        def spike_source_poisson_heuristic(app_vertex):
            app_vertex.splitter_object = SplitterSliceLegacy()
