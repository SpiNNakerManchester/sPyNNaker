# Copyright (c) 2021 The University of Manchester
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
from collections import defaultdict
import numpy
from numpy import floating
from numpy.typing import NDArray
from typing import (
    Dict, Iterable, List, Optional, Set, Tuple, cast, TYPE_CHECKING)
from spinn_utilities.overrides import overrides
from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.common import Slice
from spinn_front_end_common.interface.ds import (
    DataType, DataSpecificationGenerator)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neural_projections.connectors import (
    PoolDenseConnector)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSupportsSignedWeights)
from spynnaker.pyNN.types import Weight_Delay_In_Types
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from .abstract_local_only import AbstractLocalOnly
from pacman.model.routing_info.vertex_routing_info import VertexRoutingInfo
if TYPE_CHECKING:
    from spynnaker.pyNN.models.projection import Projection
    from spynnaker.pyNN.models.neuron import (
        PopulationMachineLocalOnlyCombinedVertex)
    from spynnaker.pyNN.models.utility_models.delays import (
        DelayExtensionVertex)
    from spynnaker.pyNN.models.common.population_application_vertex import (
        PopulationApplicationVertex)


class LocalOnlyPoolDense(AbstractLocalOnly, AbstractSupportsSignedWeights):
    """
    A convolution synapse dynamics that can process spikes with only DTCM.
    """

    __slots__ = ()

    def __init__(self, delay: Weight_Delay_In_Types = None):
        """
        :param float delay:
            The delay used in the connection; by default 1 time step
        """
        super().__init__(delay)
        if not isinstance(delay, (float, int)):
            raise SynapticConfigurationException(
                "Only single value delays are supported")

    @overrides(AbstractLocalOnly.merge)
    def merge(self, synapse_dynamics) -> LocalOnlyPoolDense:
        if not isinstance(synapse_dynamics, LocalOnlyPoolDense):
            raise SynapticConfigurationException(
                "All Projections of this Population must have a synapse_type"
                " of LocalOnlyPoolDense")
        return synapse_dynamics

    @overrides(AbstractLocalOnly.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self) -> str:
        return "_pool_dense"

    @property
    @overrides(AbstractLocalOnly.changes_during_run)
    def changes_during_run(self) -> bool:
        return False

    @staticmethod
    def __connector(projection: Projection) -> PoolDenseConnector:
        # pylint: disable=protected-access
        return cast(PoolDenseConnector,
                    projection._synapse_information.connector)

    @overrides(AbstractLocalOnly.get_parameters_usage_in_bytes)
    def get_parameters_usage_in_bytes(
            self, n_atoms: int,
            incoming_projections: Iterable[Projection]) -> int:
        n_bytes = 0
        for incoming in incoming_projections:
            # pylint: disable=protected-access
            s_info = incoming._synapse_information
            if not isinstance(s_info.connector, PoolDenseConnector):
                raise SynapticConfigurationException(
                    "Only PoolDenseConnector can be used with a synapse type"
                    " of PoolDense")
            # pylint: disable=protected-access
            app_edge = incoming._projection_edge
            in_slices = app_edge.pre_vertex.splitter.get_out_going_slices()
            n_bytes += s_info.connector.local_only_n_bytes(
                in_slices, n_atoms)

        return (2 * BYTES_PER_WORD) + n_bytes

    @overrides(AbstractLocalOnly.write_parameters)
    def write_parameters(
            self, spec: DataSpecificationGenerator, region: int,
            machine_vertex: PopulationMachineLocalOnlyCombinedVertex,
            weight_scales: NDArray[floating]):
        # pylint: disable=protected-access
        app_vertex = machine_vertex._pop_vertex

        # Get all the incoming vertices and keys so we can sort
        incoming_info: List[
            Tuple[Projection, Slice, Tuple[int, int], int]] = []
        seen_pre_vertices: Set[PopulationApplicationVertex] = set()
        for incoming in app_vertex.incoming_projections:
            app_edge = incoming._projection_edge
            pre_vertex = app_edge.pre_vertex
            if pre_vertex in seen_pre_vertices:
                continue
            seen_pre_vertices.add(pre_vertex)

            delay_vertex: Optional[DelayExtensionVertex] = None
            if self.delay > app_vertex.splitter.max_support_delay():
                delay_edge = app_edge.delay_edge
                assert delay_edge is not None
                delay_vertex = delay_edge.pre_vertex

            # Keep track of all the same source squares, so they can be
            # merged; this will make sure the keys line up!
            edges_for_source: Dict[
                Tuple[PopulationApplicationVertex, Slice],
                List[VertexRoutingInfo]] = defaultdict(list)
            for pre_m_vertex in pre_vertex.splitter.get_out_going_vertices(
                    SPIKE_PARTITION_ID):
                edges_for_source[pre_vertex, pre_m_vertex.vertex_slice].append(
                    self.__get_rinfo(pre_m_vertex, delay_vertex))

            # Merge edges with the same source
            for (_, vertex_slice), edge_list in edges_for_source.items():
                incoming_info.append((
                    incoming, vertex_slice,
                    self.__group_key_and_mask(edge_list),
                    pre_vertex.n_colour_bits))

        size = self.get_parameters_usage_in_bytes(
            machine_vertex.vertex_slice.n_atoms,
            app_vertex.incoming_projections)
        spec.reserve_memory_region(region, size, label="LocalOnlyPoolDense")
        spec.switch_write_focus(region)

        # Write the common spec
        post_slice = machine_vertex.vertex_slice
        n_post = int(numpy.prod(post_slice.shape))
        spec.write_value(n_post, data_type=DataType.UINT32)
        spec.write_value(len(incoming_info), data_type=DataType.UINT32)

        # Write spec for each connector, sorted by key
        incoming_info.sort(key=lambda e: e[2][1])
        for incoming, vertex_slice, (key, mask), colour_bits in incoming_info:
            self.__connector(incoming).write_local_only_data(
                spec, incoming._projection_edge, vertex_slice, post_slice,
                key, mask, colour_bits, weight_scales)

    @staticmethod
    def __group_key_and_mask(
            r_info_list: List[VertexRoutingInfo]) -> Tuple[int, int]:
        """
        Compute the group key and mask for a list of routing infos.
        """
        # Start with the first item in the list
        # NB: the first iteration does nothing
        key, mask = r_info_list[0].key, r_info_list[0].mask
        for r_info in r_info_list:
            # Compute the new don't-care bits when we combine this route
            new_xs = ~(key ^ r_info.key)
            # New mask
            mask = mask & r_info.mask & new_xs
            # New key
            key = (key | r_info.key) & mask
        return key, mask

    @staticmethod
    def __get_rinfo(
            source: MachineVertex,
            delay_vertex: Optional[DelayExtensionVertex]) -> VertexRoutingInfo:
        # pylint: disable=protected-access
        routing_info = SpynnakerDataView.get_routing_infos()
        if delay_vertex is None:
            r_info = routing_info.get_routing_info_from_pre_vertex(
                source, SPIKE_PARTITION_ID)
        else:
            delay_source = delay_vertex._delay_splitter.get_machine_vertex(
                source.vertex_slice)
            r_info = routing_info.get_routing_info_from_pre_vertex(
                delay_source, SPIKE_PARTITION_ID)
        if r_info is None:
            raise SynapticConfigurationException(
                f"Missing r_info for {source}")
        return r_info

    @staticmethod
    def __get_synapse_type(proj: Projection, target: str) -> int:
        edge = proj._projection_edge  # pylint: disable=protected-access
        synapse_type = edge.post_vertex.get_synapse_id_by_target(target)
        # Checked during connection validation, assumed constant
        assert synapse_type is not None
        return synapse_type

    @overrides(AbstractSupportsSignedWeights.get_positive_synapse_index)
    def get_positive_synapse_index(
            self, incoming_projection: Projection) -> int:
        return self.__get_synapse_type(
            incoming_projection,
            self.__connector(incoming_projection).positive_receptor_type)

    @overrides(AbstractSupportsSignedWeights.get_negative_synapse_index)
    def get_negative_synapse_index(
            self, incoming_projection: Projection) -> int:
        return self.__get_synapse_type(
            incoming_projection,
            self.__connector(incoming_projection).negative_receptor_type)

    @overrides(AbstractSupportsSignedWeights.get_maximum_positive_weight)
    def get_maximum_positive_weight(
            self, incoming_projection: Projection) -> float:
        conn = self.__connector(incoming_projection)
        # We know the connector doesn't care about the argument
        max_weight = numpy.amax(conn.weights)
        return max_weight if max_weight > 0 else 0

    @overrides(AbstractSupportsSignedWeights.get_minimum_negative_weight)
    def get_minimum_negative_weight(
            self, incoming_projection: Projection) -> float:
        conn = self.__connector(incoming_projection)
        # This is different because the connector happens to support this
        min_weight = numpy.amin(conn.weights)
        return min_weight if min_weight < 0 else 0

    @overrides(AbstractSupportsSignedWeights.get_mean_positive_weight)
    def get_mean_positive_weight(
            self, incoming_projection: Projection) -> float:
        conn = self.__connector(incoming_projection)
        weights = conn.weights
        if isinstance(weights, (int, float)):
            return weights
        pos_weights = weights[weights > 0]
        if not len(pos_weights):
            return 0
        return numpy.mean(pos_weights)

    @overrides(AbstractSupportsSignedWeights.get_mean_negative_weight)
    def get_mean_negative_weight(
            self, incoming_projection: Projection) -> float:
        conn = self.__connector(incoming_projection)
        weights = conn.weights
        if isinstance(weights, (int, float)):
            return weights
        neg_weights = weights[weights < 0]
        if not len(neg_weights):
            return 0
        return numpy.mean(neg_weights)

    @overrides(AbstractSupportsSignedWeights.get_variance_positive_weight)
    def get_variance_positive_weight(
            self, incoming_projection: Projection) -> float:
        conn = self.__connector(incoming_projection)
        weights = conn.weights
        if isinstance(weights, (int, float)):
            return 0
        pos_weights = weights[weights > 0]
        if not len(pos_weights):
            return 0
        return numpy.var(pos_weights)

    @overrides(AbstractSupportsSignedWeights.get_variance_negative_weight)
    def get_variance_negative_weight(
            self, incoming_projection: Projection) -> float:
        conn = self.__connector(incoming_projection)
        weights = conn.weights
        if isinstance(weights, (int, float)):
            return 0
        neg_weights = weights[weights < 0]
        if not len(neg_weights):
            return 0
        return numpy.var(neg_weights)
