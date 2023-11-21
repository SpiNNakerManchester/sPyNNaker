# Copyright (c) 2014 The University of Manchester
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
from typing import List, Optional, Type, cast, TYPE_CHECKING
from typing_extensions import TypeGuard
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationEdge
from spinn_front_end_common.interface.provenance import (
    AbstractProvidesLocalProvenanceData)
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
from spynnaker.pyNN.models.common.population_application_vertex import (
    PopulationApplicationVertex)
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neuron.synapse_dynamics import (
        AbstractSynapseDynamics, AbstractSynapseDynamicsStructural,
        SynapseDynamicsSTDP, SynapseDynamicsNeuromodulation)
    from spynnaker.pyNN.models.neural_projections import (
        SynapseInformation, DelayedApplicationEdge)
    from spynnaker.pyNN.models.neuron import AbstractPopulationVertex


class _Dynamics:
    """
    Holds late-initialized class references.
    """
    _Structural: Optional[Type[AbstractSynapseDynamicsStructural]] = None
    _STDP: Optional[Type[SynapseDynamicsSTDP]] = None
    _Neuromodulation: Optional[Type[SynapseDynamicsNeuromodulation]] = None

    @classmethod
    def Structural(cls) -> Type[AbstractSynapseDynamicsStructural]:
        if cls._Structural is None:
            # Avoid import loop by postponing this import
            from spynnaker.pyNN.models.neuron.synapse_dynamics import (
                AbstractSynapseDynamicsStructural as StructuralDynamics)
            cls._Structural = StructuralDynamics
        return cls._Structural

    @classmethod
    def STDP(cls) -> Type[SynapseDynamicsSTDP]:
        if cls._STDP is None:
            # Avoid import loop by postponing this import
            from spynnaker.pyNN.models.neuron.synapse_dynamics import (
                SynapseDynamicsSTDP as STDPDynamics)
            cls._STDP = STDPDynamics
        return cls._STDP

    @classmethod
    def Neuromodulation(cls) -> Type[SynapseDynamicsNeuromodulation]:
        if cls._Neuromodulation is None:
            # Avoid import loop by postponing this import
            from spynnaker.pyNN.models.neuron.synapse_dynamics import (
                SynapseDynamicsNeuromodulation as Neuromodulation)
            cls._Neuromodulation = Neuromodulation
        return cls._Neuromodulation


def are_dynamics_structural(
        synapse_dynamics: AbstractSynapseDynamics) -> TypeGuard[
            AbstractSynapseDynamicsStructural]:
    # pylint: disable=isinstance-second-argument-not-valid-type
    return isinstance(synapse_dynamics, _Dynamics.Structural())


def are_dynamics_stdp(synapse_dynamics: AbstractSynapseDynamics) -> TypeGuard[
        SynapseDynamicsSTDP]:
    # pylint: disable=isinstance-second-argument-not-valid-type
    return isinstance(synapse_dynamics, _Dynamics.STDP())


def are_dynamics_neuromodulation(
        synapse_dynamics: AbstractSynapseDynamics) -> TypeGuard[
            SynapseDynamicsNeuromodulation]:
    # pylint: disable=isinstance-second-argument-not-valid-type
    return isinstance(synapse_dynamics, _Dynamics.Neuromodulation())


class ProjectionApplicationEdge(
        ApplicationEdge, AbstractProvidesLocalProvenanceData):
    """
    An edge which terminates on an :py:class:`AbstractPopulationVertex`.
    """
    __slots__ = (
        "__delay_edge",
        "__synapse_information",
        "__is_neuromodulation")

    def __init__(
            self, pre_vertex: PopulationApplicationVertex,
            post_vertex: AbstractPopulationVertex,
            synapse_information: SynapseInformation,
            label: Optional[str] = None):
        """
        :param PopulationApplicationVertex pre_vertex:
        :param AbstractPopulationVertex post_vertex:
        :param SynapseInformation synapse_information:
            The synapse information on this edge
        :param str label:
        """
        super().__init__(pre_vertex, post_vertex, label=label)

        # A list of all synapse information for all the projections that are
        # represented by this edge
        self.__synapse_information = [synapse_information]
        self.__is_neuromodulation = are_dynamics_neuromodulation(
            synapse_information.synapse_dynamics)

        # The edge from the delay extension of the pre_vertex to the
        # post_vertex - this might be None if no long delays are present
        self.__delay_edge: Optional[DelayedApplicationEdge] = None

    def add_synapse_information(self, synapse_information: SynapseInformation):
        """
        :param SynapseInformation synapse_information:
        """
        dynamics = synapse_information.synapse_dynamics
        is_neuromodulation = are_dynamics_neuromodulation(dynamics)
        if is_neuromodulation != self.__is_neuromodulation:
            raise SynapticConfigurationException(
                "Cannot mix neuromodulated and non-neuromodulated synapses "
                f"between the same source Population {self._pre_vertex} and "
                f"target Population {self._post_vertex}")
        self.__synapse_information.append(synapse_information)

    @property
    def synapse_information(self) -> List[SynapseInformation]:
        """
        :rtype: list(SynapseInformation)
        """
        return self.__synapse_information

    @property
    def delay_edge(self) -> Optional[DelayedApplicationEdge]:
        """
        Settable.

        :rtype: DelayedApplicationEdge or None
        """
        return self.__delay_edge

    @delay_edge.setter
    def delay_edge(self, delay_edge: DelayedApplicationEdge):
        self.__delay_edge = delay_edge

    @property
    def is_neuromodulation(self) -> bool:
        """
        Whether this edge is providing neuromodulation.

        :rtype: bool
        """
        return self.__is_neuromodulation

    @property
    def n_delay_stages(self) -> int:
        """
        :rtype: int
        """
        if self.__delay_edge is None:
            return 0
        return cast(DelayExtensionVertex,
                    self.__delay_edge.pre_vertex).n_delay_stages

    @overrides(AbstractProvidesLocalProvenanceData.get_local_provenance_data)
    def get_local_provenance_data(self) -> None:
        for synapse_info in self.synapse_information:
            synapse_info.connector.get_provenance_data(synapse_info)

    @property
    @overrides(ApplicationEdge.pre_vertex)
    def pre_vertex(self) -> PopulationApplicationVertex:
        return cast(PopulationApplicationVertex, super().pre_vertex)

    @property
    @overrides(ApplicationEdge.post_vertex)
    def post_vertex(self) -> AbstractPopulationVertex:
        return cast('AbstractPopulationVertex', super().post_vertex)
