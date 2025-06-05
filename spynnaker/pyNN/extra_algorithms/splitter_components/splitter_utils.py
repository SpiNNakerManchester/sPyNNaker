# Copyright (c) 2025 The University of Manchester
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
from pacman.model.graphs.application import ApplicationVertex

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterPoissonDelegate)
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector, OneToOneConnector)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamics, SynapseDynamicsStatic)
from spynnaker.pyNN.models.spike_source import SpikeSourcePoissonVertex
from spynnaker.pyNN.types import DELAYS


def is_direct_poisson_source(
        post_vertex: ApplicationVertex, pre_vertex: ApplicationVertex,
        connector: AbstractConnector, dynamics: AbstractSynapseDynamics,
        delay: DELAYS) -> bool:
    """
    Determine if a given Poisson source can be created by this splitter.

    :param ~pacman.model.graphs.application.ApplicationVertex pre_vertex:
        The vertex sending into the Projection
    :param connector:
        The connector in use in the Projection
    :type connector:
        ~spynnaker.pyNN.models.neural_projections.connectors.AbstractConnector
    :param dynamics:
        The synapse dynamics in use in the Projection
    :type dynamics:
        ~spynnaker.pyNN.models.neuron.synapse_dynamics.AbstractSynapseDynamics
    :param delay:
        The delay in use in the Projection
    :rtype: bool
    """
    return (isinstance(pre_vertex, SpikeSourcePoissonVertex) and
            isinstance(pre_vertex.splitter, SplitterPoissonDelegate) and
            len(pre_vertex.outgoing_projections) == 1 and
            pre_vertex.n_atoms == post_vertex.n_atoms and
            isinstance(connector, OneToOneConnector) and
            isinstance(dynamics, SynapseDynamicsStatic) and
            delay == SpynnakerDataView().get_simulation_time_step_ms())
