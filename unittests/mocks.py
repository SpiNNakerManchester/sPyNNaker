# Copyright (c) 2017 The University of Manchester
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

from typing import Optional
from numpy.typing import NDArray

from spinn_utilities.overrides import overrides

from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.models.neural_projections import (
        SynapseInformation)
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamics)
from spynnaker.pyNN.models.populations import Population


class MockPopulation(Population):

    def __init__(self, size, label, vertex=None):
        self._size = size
        self._label = label
        self._mock_vertex = vertex
        if vertex is None:
            self._mock_vertex = MockVertex()

    @property
    @overrides(Population.size)
    def size(self) -> int:
        return self._size

    def __repr__(self) -> str:
        return "Population {}".format(self._label)

    @property
    @overrides(Population._vertex)
    def _vertex(self) -> PopulationApplicationVertex:
        return self._mock_vertex


class MockVertex(PopulationApplicationVertex):

    @overrides(PopulationApplicationVertex.get_key_ordered_indices)
    def get_key_ordered_indices(
            self, indices: Optional[NDArray] = None) -> NDArray:
        assert indices is not None
        return indices

    @property
    @overrides(PopulationApplicationVertex.n_colour_bits)
    def n_colour_bits(self) -> int:
        raise NotImplementedError

    @property
    @overrides(PopulationApplicationVertex.n_atoms)
    def n_atoms(self) -> int:
        raise NotImplementedError


class MockSynapseDynamics(AbstractSynapseDynamics):

    @overrides(AbstractSynapseDynamics.merge)
    def merge(self, synapse_dynamics: AbstractSynapseDynamics
              ) -> AbstractSynapseDynamics:
        raise NotImplementedError

    @overrides(AbstractSynapseDynamics.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self) -> str:
        raise NotImplementedError

    @property
    @overrides(AbstractSynapseDynamics.changes_during_run)
    def changes_during_run(self) -> bool:
        raise NotImplementedError

    @property
    @overrides(AbstractSynapseDynamics.is_combined_core_capable)
    def is_combined_core_capable(self) -> bool:
        raise NotImplementedError


class MockConnector(AbstractConnector):

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(
            self, synapse_info: SynapseInformation) -> float:
        raise NotImplementedError

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(
            self, synapse_info: SynapseInformation) -> Optional[float]:
        raise NotImplementedError

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:
        raise NotImplementedError

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        raise NotImplementedError

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        raise NotImplementedError