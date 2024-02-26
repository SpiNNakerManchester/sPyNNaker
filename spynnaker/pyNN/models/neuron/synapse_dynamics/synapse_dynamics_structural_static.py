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
from typing import (
    Any, Dict, Iterable, Optional, Tuple, TYPE_CHECKING, Sequence, Union)

import numpy

from pyNN.standardmodels.synapses import StaticSynapse

from spinn_utilities.overrides import overrides

from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.common import Slice

from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.types import Weight_Types
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.utilities.utility_calls import create_mars_kiss_seeds

from .abstract_synapse_dynamics_structural import (
    AbstractSynapseDynamicsStructural)
from .synapse_dynamics_structural_common import (
    DEFAULT_F_REW, DEFAULT_INITIAL_WEIGHT, DEFAULT_INITIAL_DELAY,
    DEFAULT_S_MAX, SynapseDynamicsStructuralCommon as
    _Common)
from .abstract_static_synapse_dynamics import AbstractStaticSynapseDynamics
from .synapse_dynamics_static import SynapseDynamicsStatic
from .synapse_dynamics_stdp import SynapseDynamicsSTDP
from .synapse_dynamics_structural_stdp import SynapseDynamicsStructuralSTDP
from .abstract_synapse_dynamics import AbstractSynapseDynamics

if TYPE_CHECKING:
    from pacman.model.graphs import AbstractVertex
    from pacman.model.graphs.machine import MachineVertex
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)
    from spynnaker.pyNN.models.neural_projections.connectors import (
        AbstractConnector)
    from spynnaker.pyNN.models.neuron.synapse_dynamics.\
        abstract_synapse_dynamics_structural import (
            InitialDelay)
    from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis.\
        partner_selection.abstract_partner_selection import (
            AbstractPartnerSelection)
    from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis.\
        formation.abstract_formation import (
            AbstractFormation)
    from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis.\
        elimination.abstract_elimination import (
            AbstractElimination)
    from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
        ConnectionsArray)
    from .synapse_dynamics_structural_common import ConnectionsInfo


class SynapseDynamicsStructuralStatic(SynapseDynamicsStatic, _Common):
    """
    Class that enables synaptic rewiring in the absence of STDP.

    It acts as a wrapper around SynapseDynamicsStatic, meaning that rewiring
    can operate in parallel with static synapses.

    Written by Petrut Bogdan.
    """
    __slots__ = (
        # Frequency of rewiring (Hz)
        "__f_rew",
        # Initial weight assigned to a newly formed connection
        "__initial_weight",
        # Delay assigned to a newly formed connection
        "__initial_delay",
        # Maximum fan-in per target layer neuron
        "__s_max",
        # The seed
        "__seed",
        # Holds initial connectivity as defined via connector
        "__connections",
        # The actual type of weights: static through the simulation or those
        # that can be change through STDP
        "__weight_dynamics",
        # Shared RNG seed to be written on all cores
        "__seeds",
        # The RNG used with the seed that is passed in
        "__rng",
        # The partner selection rule
        "__partner_selection",
        # The formation rule
        "__formation",
        # The elimination rule
        "__elimination",
        "__with_replacement")

    def __init__(
            self, partner_selection: AbstractPartnerSelection,
            formation: AbstractFormation, elimination: AbstractElimination,
            f_rew: float = DEFAULT_F_REW,
            initial_weight: float = DEFAULT_INITIAL_WEIGHT,
            initial_delay: InitialDelay = DEFAULT_INITIAL_DELAY,
            s_max: int = DEFAULT_S_MAX,
            with_replacement: bool = True, seed: Optional[int] = None,
            weight: float = StaticSynapse.default_parameters['weight'],
            delay: Optional[float] = None):
        """
        :param AbstractPartnerSelection partner_selection:
            The partner selection rule
        :param AbstractFormation formation: The formation rule
        :param AbstractElimination elimination: The elimination rule
        :param float f_rew: How many rewiring attempts will be done per second.
        :param float initial_weight:
            Weight assigned to a newly formed connection
        :param initial_delay:
            Delay assigned to a newly formed connection; a single value means
            a fixed delay value, or a tuple of two values means the delay will
            be chosen at random from a uniform distribution between the given
            values
        :type initial_delay: float or (float, float)
        :param int s_max: Maximum fan-in per target layer neuron
        :param bool with_replacement:
            If set to True (default), a new synapse can be formed in a
            location where a connection already exists; if False, then it must
            form where no connection already exists
        :param int seed: seed the random number generators
        :param float weight: The weight of connections formed by the connector
        :param delay: The delay of connections formed by the connector
            Use ``None`` to get the simulator default minimum delay.
        :type delay: float or None
        """
        super().__init__(weight=weight, delay=delay, pad_to_length=s_max)

        self.__partner_selection = partner_selection
        self.__formation = formation
        self.__elimination = elimination
        self.__f_rew = f_rew
        self.__initial_weight = initial_weight
        self.__initial_delay = initial_delay
        self.__s_max = s_max
        self.__with_replacement = with_replacement
        self.__seed = seed
        self.__connections: ConnectionsInfo = dict()

        self.__rng = numpy.random.RandomState(seed)
        self.__seeds: Dict[Any, Tuple[int, ...]] = dict()

    @overrides(AbstractStaticSynapseDynamics.merge)
    def merge(self, synapse_dynamics: AbstractSynapseDynamics
              ) -> AbstractSynapseDynamics:
        # If the dynamics is structural, check if same as this
        if isinstance(synapse_dynamics, AbstractSynapseDynamicsStructural):
            if not self.is_same_as(synapse_dynamics):
                raise SynapticConfigurationException(
                    "Synapse dynamics must match exactly when using multiple"
                    " edges to the same population")

            # If structural part matches, return other as it might also be STDP
            return synapse_dynamics

        # If the dynamics is STDP but not Structural (as here), merge
        if isinstance(synapse_dynamics, SynapseDynamicsSTDP):
            return SynapseDynamicsStructuralSTDP(
                self.partner_selection, self.formation,
                self.elimination,
                synapse_dynamics.timing_dependence,
                synapse_dynamics.weight_dependence,
                # voltage dependence is not supported
                None, synapse_dynamics.dendritic_delay_fraction,
                self.f_rew, self.initial_weight, self.initial_delay,
                self.s_max, self.with_replacement, self.seed,
                backprop_delay=synapse_dynamics.backprop_delay)

        # Otherwise, it is static, so return ourselves
        return self

    def set_projection_parameter(self, param: str, value):
        """
        :param str param:
        :param value:
        """
        for item in (self.partner_selection, self.__formation,
                     self.__elimination):
            if hasattr(item, param):
                setattr(item, param, value)
                break
        else:
            raise ValueError(f"Unknown parameter {param}")

    @overrides(AbstractStaticSynapseDynamics.is_same_as)
    @overrides(_Common.is_same_as)
    def is_same_as(self, synapse_dynamics: Union[
            AbstractSynapseDynamics,
            AbstractSynapseDynamicsStructural]) -> bool:
        if not (isinstance(synapse_dynamics, SynapseDynamicsStructuralStatic)):
            return False
        if not AbstractStaticSynapseDynamics.is_same_as(
                self, synapse_dynamics):
            return False
        return _Common.is_same_as(self, synapse_dynamics)

    @overrides(AbstractStaticSynapseDynamics.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self) -> str:
        return (super().get_vertex_executable_suffix() +
                _Common.get_vertex_executable_suffix(self))

    @overrides(AbstractSynapseDynamicsStructural.set_connections)
    def set_connections(
            self, connections: ConnectionsArray, post_vertex_slice: Slice,
            app_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation):
        if not isinstance(synapse_info.synapse_dynamics,
                          AbstractSynapseDynamicsStructural):
            return
        collector = self.__connections.setdefault(
            (app_edge.post_vertex, post_vertex_slice.lo_atom), [])
        collector.append((connections, app_edge, synapse_info))

    @overrides(AbstractStaticSynapseDynamics.get_parameter_names)
    def get_parameter_names(self) -> Iterable[str]:
        yield from super().get_parameter_names()
        yield from _Common.get_parameter_names(self)

    @property
    @overrides(SynapseDynamicsStatic.changes_during_run)
    def changes_during_run(self) -> bool:
        return True

    @property
    @overrides(AbstractSynapseDynamicsStructural.f_rew)
    def f_rew(self) -> float:
        return self.__f_rew

    @property
    @overrides(AbstractSynapseDynamicsStructural.seed)
    def seed(self) -> Optional[int]:
        return self.__seed

    @property
    @overrides(AbstractSynapseDynamicsStructural.s_max)
    def s_max(self) -> int:
        return self.__s_max

    @property
    @overrides(AbstractSynapseDynamicsStructural.with_replacement)
    def with_replacement(self) -> bool:
        return self.__with_replacement

    @property
    @overrides(AbstractSynapseDynamicsStructural.initial_weight)
    def initial_weight(self) -> float:
        return self.__initial_weight

    @property
    @overrides(AbstractSynapseDynamicsStructural.initial_delay)
    def initial_delay(self) -> InitialDelay:
        return self.__initial_delay

    @property
    @overrides(AbstractSynapseDynamicsStructural.partner_selection)
    def partner_selection(self) -> AbstractPartnerSelection:
        return self.__partner_selection

    @property
    @overrides(AbstractSynapseDynamicsStructural.formation)
    def formation(self) -> AbstractFormation:
        return self.__formation

    @property
    @overrides(AbstractSynapseDynamicsStructural.elimination)
    def elimination(self) -> AbstractElimination:
        return self.__elimination

    @property
    @overrides(_Common.connections)
    def connections(self) -> ConnectionsInfo:
        return self.__connections

    @overrides(SynapseDynamicsStatic.get_weight_mean)
    def get_weight_mean(self, connector: AbstractConnector,
                        synapse_info: SynapseInformation) -> float:
        return self.get_weight_maximum(connector, synapse_info)

    @overrides(SynapseDynamicsStatic.get_weight_variance)
    def get_weight_variance(
           self, connector: AbstractConnector, weights: Weight_Types,
           synapse_info: SynapseInformation) -> float:
        return 0.0

    @overrides(SynapseDynamicsStatic.get_weight_maximum)
    def get_weight_maximum(self, connector: AbstractConnector,
                           synapse_info: SynapseInformation) -> float:
        w_m = super().get_weight_maximum(connector, synapse_info)
        return max(w_m, self.__initial_weight)

    @overrides(SynapseDynamicsStatic.get_delay_maximum)
    def get_delay_maximum(self, connector: AbstractConnector,
                          synapse_info: SynapseInformation) -> Optional[float]:
        d_m = super().get_delay_maximum(connector, synapse_info)
        if d_m is None:
            return self.__initial_delay
        return max(d_m, self.__initial_delay)

    @overrides(SynapseDynamicsStatic.get_delay_minimum)
    def get_delay_minimum(
            self, connector: AbstractConnector,
            synapse_info: SynapseInformation) -> Optional[float]:
        d_m = super().get_delay_minimum(connector, synapse_info)
        if d_m is None:
            return self.__initial_delay
        return min(d_m, self.__initial_delay)

    @overrides(SynapseDynamicsStatic.get_delay_variance)
    def get_delay_variance(
            self, connector: AbstractConnector, delays: numpy.ndarray,
            synapse_info: SynapseInformation) -> float:
        return 0.0

    @overrides(_Common._get_seeds)
    def _get_seeds(
            self, app_vertex: Union[None, ApplicationVertex, Slice] = None
            ) -> Sequence[int]:
        if app_vertex:
            if app_vertex not in self.__seeds:
                self.__seeds[app_vertex] = (
                    create_mars_kiss_seeds(self.__rng))
            return self.__seeds[app_vertex]
        else:
            return create_mars_kiss_seeds(self.__rng)

    @overrides(SynapseDynamicsStatic.generate_on_machine)
    def generate_on_machine(self) -> bool:
        # Never generate structural connections on the machine
        return False

    @overrides(AbstractSynapseDynamics.get_connected_vertices)
    def get_connected_vertices(
            self, s_info: SynapseInformation, source_vertex: ApplicationVertex,
            target_vertex: ApplicationVertex) -> Sequence[
            Tuple[MachineVertex, Sequence[AbstractVertex]]]:

        # Things change, so assume all connected
        return [(m_vertex, [source_vertex])
                for m_vertex in target_vertex.splitter.get_in_coming_vertices(
                    SPIKE_PARTITION_ID)]

    @property
    @overrides(AbstractSynapseDynamics.is_combined_core_capable)
    def is_combined_core_capable(self) -> bool:
        return False
