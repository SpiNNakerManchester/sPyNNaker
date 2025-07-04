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
from __future__ import annotations
from typing import Iterable, Optional, TYPE_CHECKING

from numpy import floating
from numpy.typing import NDArray
from typing_extensions import TypeAlias

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.model.graphs.common import Slice
from spinn_front_end_common.interface.ds import DataSpecificationBase

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
        ConnectionsArray)
    from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
        .partner_selection import AbstractPartnerSelection
    from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
        .formation import AbstractFormation
    from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
        .elimination import AbstractElimination
    from spynnaker.pyNN.models.projection import Projection
    from spynnaker.pyNN.models.neuron.synaptic_matrices import SynapticMatrices
    from spynnaker.pyNN.models.neuron import PopulationVertex
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)

# see https://github.com/SpiNNakerManchester/sPyNNaker/issues/1427
#: :meta private:
InitialDelay: TypeAlias = float


class AbstractSynapseDynamicsStructural(object, metaclass=AbstractBase):
    """
    Base class for synapse dynamics that structural plasticity understands.
    """
    __slots__ = ()

    @abstractmethod
    def get_structural_parameters_sdram_usage_in_bytes(
            self, incoming_projections: Iterable[Projection],
            n_neurons: int) -> int:
        """
        Get the size of the structural parameters.

        .. note::
            At the Application level this will be an estimate.

        :param incoming_projections:
            The projections that target the vertex in question
        :param n_neurons:
        :return: the size of the parameters, in bytes
        :raises PacmanInvalidParameterException:
            If the parameters make no sense.
        """
        raise NotImplementedError

    @abstractmethod
    def write_structural_parameters(
            self, spec: DataSpecificationBase, region: int,
            weight_scales: NDArray[floating],
            app_vertex: PopulationVertex,
            vertex_slice: Slice, synaptic_matrices: SynapticMatrices) -> None:
        """
        Write structural plasticity parameters.

        :param spec: The data specification to write to
        :param region: region ID
        :param weight_scales: Weight scaling for each synapse type
        :param app_vertex: The target application vertex
        :param vertex_slice: The slice of the target vertex to generate for
        :param synaptic_matrices: The synaptic matrices for this vertex
        """
        raise NotImplementedError

    @abstractmethod
    def set_connections(
            self, connections: ConnectionsArray, post_vertex_slice: Slice,
            app_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation) -> None:
        """
        Set connections for structural plasticity.

        :param connections:
        :param post_vertex_slice:
        :param app_edge:
        :param synapse_info:
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def f_rew(self) -> float:
        """
        The frequency of rewiring.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def s_max(self) -> int:
        """
        The maximum number of synapses.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def with_replacement(self) -> bool:
        """
        Whether to allow replacement when creating synapses.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def seed(self) -> Optional[int]:
        """
        The seed to control the randomness.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def initial_weight(self) -> float:
        """
        The weight of a formed connection.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def initial_delay(self) -> InitialDelay:
        """
        The delay of a formed connection.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def partner_selection(self) -> AbstractPartnerSelection:
        """
        The partner selection rule.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def formation(self) -> AbstractFormation:
        """
        The formation rule.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def elimination(self) -> AbstractElimination:
        """
        The elimination rule.
        """
        raise NotImplementedError

    @abstractmethod
    def check_initial_delay(self, max_delay_ms: int) -> None:
        """
        Check that delays can be done without delay extensions.

        :param max_delay_ms: The maximum delay supported, in milliseconds
        :raises Exception: if the delay is out of range
        """
        raise NotImplementedError

    @abstractmethod
    def get_max_rewires_per_ts(self) -> int:
        """
        Get the max number of rewires per timestep.
        """
        raise NotImplementedError
