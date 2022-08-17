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
from pacman.model.partitioner_splitters.splitter_one_to_one_legacy import (
    SplitterOneToOneLegacy)
from spinn_front_end_common.interface.splitter_selectors import (
    vertex_selector)
from spynnaker.pyNN.models.abstract_models import (
    AbstractAcceptsIncomingSynapses)
from .splitter_abstract_pop_vertex_fixed import (
    SplitterAbstractPopulationVertexFixed)
from .spynnaker_splitter_fixed_legacy import SpynnakerSplitterFixedLegacy
from .splitter_poisson_delegate import SplitterPoissonDelegate
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.spike_source import (
    SpikeSourceArrayVertex, SpikeSourcePoissonVertex)
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexNeuronsSynapses)

PROGRESS_BAR_NAME = "Adding Splitter selectors where appropriate"


def spynnaker_splitter_selector():
    """ Add a splitter to every vertex that doesn't already have one.

        default for APV is the SplitterAbstractPopulationVertexFixed\
        default for external device splitters are SplitterOneToOneLegacy\
        default for the rest is the SpynnakerSplitterFixedLegacy.

    :raises PacmanConfigurationException: If a bad configuration is set
    """
    progress_bar = ProgressBar(
        string_describing_what_being_progressed=PROGRESS_BAR_NAME,
        total_number_of_things_to_do=SpynnakerDataView.get_n_vertices())

    for app_vertex in progress_bar.over(SpynnakerDataView.iterate_vertices()):
        spynakker_vertex_selector(app_vertex)


def spynakker_vertex_selector(app_vertex):
    """ main point for selecting a splitter object for a given app vertex.

    Will delegate to the none spynakker slector if no heuristic is known for
    the app vertex.

    :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
        app vertex to give a splitter object to
    :rtype: None
    """
    if app_vertex.splitter is None:
        if isinstance(app_vertex, AbstractPopulationVertex):
            if app_vertex.single_core_capable:
                app_vertex.splitter = SplitterAbstractPopulationVertexFixed()
            else:
                app_vertex.splitter = (
                    SplitterAbstractPopulationVertexNeuronsSynapses(
                        app_vertex.n_synapse_cores_required))
        elif isinstance(app_vertex, ApplicationSpiNNakerLinkVertex):
            app_vertex.splitter = SplitterOneToOneLegacy()
        elif isinstance(app_vertex, ApplicationFPGAVertex):
            app_vertex.splitter = SplitterOneToOneLegacy()
        elif isinstance(app_vertex, SpikeSourceArrayVertex):
            app_vertex.splitter = SpynnakerSplitterFixedLegacy()
        elif isinstance(app_vertex, SpikeSourcePoissonVertex):
            app_vertex.splitter = SplitterPoissonDelegate()
        else:  # go to basic selector. it might know what to do
            vertex_selector(app_vertex)
    if isinstance(app_vertex, AbstractAcceptsIncomingSynapses):
        app_vertex.verify_splitter(app_vertex.splitter)
