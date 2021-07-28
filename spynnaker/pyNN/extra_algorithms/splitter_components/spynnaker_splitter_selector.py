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
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.graphs.application import (
    ApplicationSpiNNakerLinkVertex, ApplicationFPGAVertex)
from pacman.model.partitioner_splitters import SplitterExternalDevice
from spinn_front_end_common.interface.splitter_selectors import (
    SplitterSelector)
from spynnaker.pyNN.models.abstract_models import (
    AbstractAcceptsIncomingSynapses)
from .splitter_abstract_pop_vertex_slice import (
    SplitterAbstractPopulationVertexSlice)
from .splitter_abstract_pop_vertex_fixed import (
    SplitterAbstractPopulationVertexFixed)
from .spynnaker_splitter_slice_legacy import SpynnakerSplitterSliceLegacy
from .spynnaker_splitter_fixed_legacy import SpynnakerSplitterFixedLegacy
from .splitter_poisson_delegate import SplitterPoissonDelegate
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.spike_source.spike_source_array_vertex import (
    SpikeSourceArrayVertex)
from spynnaker.pyNN.models.spike_source.spike_source_poisson_vertex import (
    SpikeSourcePoissonVertex)
from spynnaker.pyNN.models.neuron.local_only import AbstractLocalOnly


def _is_multidimensional(app_vertex):
    return len(app_vertex.atoms_shape) > 1


class SpynnakerSplitterSelector(SplitterSelector):
    """ splitter object selector that allocates splitters to app vertices\
        that have not yet been given a splitter object.\
        default for APV is the SplitterAbstractPopulationVertexSlice\
        default for external device splitters are SplitterOneToOneLegacy\
        default for the rest is the SpynnakerSplitterSliceLegacy.

    :param ApplicationGraph app_graph: app graph
    :raises PacmanConfigurationException: If a bad configuration is set
    """

    PROGRESS_BAR_NAME = "Adding Splitter selectors where appropriate"

    def __call__(self, app_graph):
        """ Add a splitter to every vertex that doesn't already have one.

        :param ApplicationGraph app_graph: app graph
        :raises PacmanConfigurationException: If a bad configuration is set
        """

        progress_bar = ProgressBar(
            string_describing_what_being_progressed=self.PROGRESS_BAR_NAME,
            total_number_of_things_to_do=len(app_graph.vertices))

        for app_vertex in progress_bar.over(app_graph.vertices):
            if app_vertex.splitter is None:
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
            if isinstance(app_vertex, AbstractAcceptsIncomingSynapses):
                app_vertex.verify_splitter(app_vertex.splitter)

    @staticmethod
    def abstract_pop_heuristic(app_vertex):
        """ Assign the splitter for APV. Allows future overrides

        :param ~pacman.model.graphs.application.ApplicationGraph app_vertex:
            app vertex
        """
        if _is_multidimensional(app_vertex) or isinstance(
                app_vertex.synapse_dynamics, AbstractLocalOnly):
            app_vertex.splitter = SplitterAbstractPopulationVertexFixed()
        else:
            app_vertex.splitter = SplitterAbstractPopulationVertexSlice()

    @staticmethod
    def external_spinnaker_link_heuristic(app_vertex):
        """ Assign the splitter for SpiNNaker link vertices.\
            Allows future overrides

        :param ~pacman.model.graphs.application.ApplicationGraph app_vertex:
            app vertex
        """
        app_vertex.splitter = SplitterExternalDevice()

    @staticmethod
    def external_fpga_link_heuristic(app_vertex):
        """ Assign the splitter for FPGA link vertices. Allows future overrides

        :param ~pacman.model.graphs.application.ApplicationGraph app_vertex:
            app vertex
        """
        app_vertex.splitter = SplitterExternalDevice()

    @staticmethod
    def spike_source_array_heuristic(app_vertex):
        """ Assign the splitter for SSA. Allows future overrides

        :param ~pacman.model.graphs.application.ApplicationGraph app_vertex:
            app vertex
        """
        if _is_multidimensional(app_vertex):
            app_vertex.splitter = SpynnakerSplitterFixedLegacy()
        else:
            app_vertex.splitter = SpynnakerSplitterSliceLegacy()

    @staticmethod
    def spike_source_poisson_heuristic(app_vertex):
        """ Assign the splitter for SSP. Allows future overrides

        :param ~pacman.model.graphs.application.ApplicationGraph app_vertex:
            app vertex
        """
        if _is_multidimensional(app_vertex):
            app_vertex.splitter = SpynnakerSplitterFixedLegacy()
        else:
            app_vertex.splitter = SplitterPoissonDelegate()
