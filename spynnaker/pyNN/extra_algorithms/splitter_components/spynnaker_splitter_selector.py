# Copyright (c) 2020 The University of Manchester
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
from typing import cast
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.graphs.application import (
    ApplicationVertex, ApplicationSpiNNakerLinkVertex, ApplicationFPGAVertex)
from pacman.model.partitioner_splitters import (
    SplitterExternalDevice, SplitterFixedLegacy)
from spinn_front_end_common.interface.splitter_selectors import (
    vertex_selector)
from spynnaker.pyNN.models.abstract_models import (
    AbstractAcceptsIncomingSynapses)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron import PopulationVertex
from spynnaker.pyNN.models.spike_source import (
    SpikeSourceArrayVertex, SpikeSourcePoissonVertex)
from .splitter_population_vertex_fixed import (
    SplitterPopulationVertexFixed)
from .splitter_poisson_delegate import SplitterPoissonDelegate
from .splitter_population_vertex_neurons_synapses import (
    SplitterPopulationVertexNeuronsSynapses)
from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay

PROGRESS_BAR_NAME = "Adding Splitter selectors where appropriate"


def _is_multidimensional(app_vertex: ApplicationVertex) -> bool:
    return len(app_vertex.atoms_shape) > 1


def spynnaker_splitter_selector() -> None:
    """
    Add a splitter to every vertex that doesn't already have one.

    The default for :py:class:`PopulationVertex` is the
    :py:class:`SplitterPopulationVertexFixed`.
    The default for external device splitters are
    :py:class:`~pacman.model.partitioner_splitters.SplitterExternalDevice`.
    The default for the rest is the
    :py:class:`~pacman.model.partitioner_splitters.SplitterFixedLegacy`.

    :raises PacmanConfigurationException: If a bad configuration is set
    """
    progress_bar = ProgressBar(
        string_describing_what_being_progressed=PROGRESS_BAR_NAME,
        total_number_of_things_to_do=SpynnakerDataView.get_n_vertices())

    for app_vertex in progress_bar.over(SpynnakerDataView.iterate_vertices()):
        spynnaker_vertex_selector(app_vertex)


def spynnaker_vertex_selector(app_vertex: ApplicationVertex) -> None:
    """
    Main point for selecting a splitter object for a given application vertex.

    Will delegate to the non-sPyNNaker selector if no heuristic is known for
    the application vertex.

    :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
        application vertex to give a splitter object to
    """
    if not app_vertex.has_splitter:
        if isinstance(app_vertex, PopulationVertex):
            if app_vertex.combined_core_capable:
                app_vertex.splitter = SplitterPopulationVertexFixed()
            else:
                app_vertex.splitter = (
                    SplitterPopulationVertexNeuronsSynapses(
                        app_vertex.n_synapse_cores_required))
        elif isinstance(app_vertex, ApplicationSpiNNakerLinkVertex):
            app_vertex.splitter = SplitterExternalDevice()
        elif isinstance(app_vertex, ApplicationFPGAVertex):
            app_vertex.splitter = SplitterExternalDevice()
        elif isinstance(app_vertex, SpikeSourceArrayVertex):
            app_vertex.splitter = SplitterFixedLegacy()
        elif isinstance(app_vertex, SpikeSourcePoissonVertex):
            if _is_multidimensional(app_vertex):
                app_vertex.splitter = SplitterFixedLegacy()
            else:
                app_vertex.splitter = SplitterPoissonDelegate()
        else:  # go to basic selector. it might know what to do
            vertex_selector(app_vertex)
    if isinstance(app_vertex, AbstractAcceptsIncomingSynapses):
        s = cast(AbstractSpynnakerSplitterDelay, app_vertex.splitter)
        app_vertex.verify_splitter(s)
