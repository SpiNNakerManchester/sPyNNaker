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
from numpy import floating, int16, uint32
from numpy.typing import NDArray
from typing import (
    Dict, Iterable, List, NamedTuple, Optional, Sequence, Tuple, cast,
    TYPE_CHECKING)
from spinn_utilities.overrides import overrides
from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.common import Slice
from pacman.model.routing_info.vertex_routing_info import VertexRoutingInfo
from spinn_front_end_common.interface.ds import (
    DataType, DataSpecificationGenerator)
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_SHORT, BYTES_PER_WORD)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neural_projections.connectors import (
    ConvolutionConnector)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSupportsSignedWeights)
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from .abstract_local_only import AbstractLocalOnly
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neuron.abstract_population_vertex import (
        AbstractPopulationVertex)
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge)
    from spynnaker.pyNN.models.projection import Projection
    from spynnaker.pyNN.models.utility_models.delays import (
        DelayExtensionVertex)
    from spynnaker.pyNN.models.neuron import (
        PopulationMachineLocalOnlyCombinedVertex)
    from spynnaker.pyNN.models.common.population_application_vertex import (
        PopulationApplicationVertex)


class Source(NamedTuple):
    projection: Projection
    vertex_slice: Slice
    key: int
    mask: int


#: Number of shorts in the conv_config struct
CONV_CONFIG_N_SHORTS = 6

#: Number of words in the conv_config struct
CONV_CONFIG_N_WORDS = 2


class LocalOnlyConvolution(AbstractLocalOnly, AbstractSupportsSignedWeights):
    """
    A convolution synapse dynamics that can process spikes with only DTCM.
    """

    __slots__ = (
        "__cached_2d_overlaps",
        "__cached_n_incoming"
        "__delay")

    def __init__(self, delay: Optional[float] = None):
        """
        :param float delay:
            The delay used in the connection; by default 1 time step
        """
        # Store the overlaps between 2d vertices to avoid recalculation
        self.__cached_2d_overlaps: Dict[
            AbstractPopulationVertex,
            Dict[MachineVertex, List[Source]]] = {}

        # Store the n_incoming to avoid recalcaultion
        self.__cached_n_incoming: Dict[ProjectionApplicationEdge, int] = {}

        if delay is None:
            self.__delay = SpynnakerDataView.get_simulation_time_step_ms()
        elif not isinstance(delay, (float, int)):
            raise SynapticConfigurationException(
                "Only single value delays are supported")
        else:
            self.__delay = float(delay)

    @overrides(AbstractLocalOnly.merge)
    def merge(self, synapse_dynamics) -> LocalOnlyConvolution:
        if not isinstance(synapse_dynamics, LocalOnlyConvolution):
            raise SynapticConfigurationException(
                "All targets of this Population must have a synapse_type of"
                " Convolution")
        return synapse_dynamics

    @overrides(AbstractLocalOnly.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self) -> str:
        return "_conv"

    @property
    @overrides(AbstractLocalOnly.changes_during_run)
    def changes_during_run(self) -> bool:
        return False

    @overrides(AbstractLocalOnly.get_parameters_usage_in_bytes)
    def get_parameters_usage_in_bytes(
            self, n_atoms, incoming_projections: Iterable[Projection]) -> int:
        # pylint: disable=protected-access
        n_bytes = 0
        kernel_bytes = 0
        for incoming in incoming_projections:
            s_info = incoming._synapse_information
            if not isinstance(s_info.connector, ConvolutionConnector):
                raise SynapticConfigurationException(
                    "Only ConvolutionConnector can be used with a synapse type"
                    " of Convolution")
            app_edge = incoming._projection_edge

            if app_edge in self.__cached_n_incoming:
                n_incoming = self.__cached_n_incoming[app_edge]
            else:
                n_incoming = s_info.connector.get_max_n_incoming_slices(
                    app_edge.pre_vertex, app_edge.post_vertex)
                self.__cached_n_incoming[app_edge] = n_incoming
            n_bytes += s_info.connector.parameters_n_bytes * n_incoming
            kernel_bytes += s_info.connector.kernel_n_bytes

        if kernel_bytes % BYTES_PER_WORD != 0:
            kernel_bytes += BYTES_PER_SHORT

        return ((CONV_CONFIG_N_SHORTS * BYTES_PER_SHORT) +
                (CONV_CONFIG_N_WORDS * BYTES_PER_WORD) + n_bytes +
                kernel_bytes)

    @overrides(AbstractLocalOnly.write_parameters)
    def write_parameters(
            self, spec: DataSpecificationGenerator, region: int,
            machine_vertex: PopulationMachineLocalOnlyCombinedVertex,
            weight_scales: NDArray[floating]):
        # pylint: disable=unexpected-keyword-arg, protected-access

        # Get incoming sources for this machine vertex, and sort by key
        app_vertex = machine_vertex._pop_vertex
        sources_for_targets = self.__get_sources_for_target(app_vertex)
        sources_for_m_vertex = sources_for_targets[machine_vertex]
        sources_for_m_vertex.sort(key=lambda s: s.key)

        size = self.get_parameters_usage_in_bytes(
            machine_vertex.vertex_slice, app_vertex.incoming_projections)
        spec.reserve_memory_region(region, size, label="LocalOnlyConvolution")
        spec.switch_write_focus(region)

        # Get spec for each incoming source
        connector_weight_index: Dict[ConvolutionConnector, int] = {}
        unique_connectors: List[
            Tuple[ConvolutionConnector, ProjectionApplicationEdge]] = []
        next_weight_index = 0
        data: List[NDArray[uint32]] = []
        for source in sources_for_m_vertex:
            incoming = source.projection
            app_edge = incoming._projection_edge
            conn = self.__connector(incoming)
            if conn in connector_weight_index:
                weight_index = connector_weight_index[conn]
            else:
                unique_connectors.append((conn, app_edge))
                weight_index = next_weight_index
                connector_weight_index[conn] = weight_index
                next_weight_index += conn.kernel_n_weights

            data.extend(conn.get_local_only_data(
                app_edge, source.vertex_slice, source.key, source.mask,
                app_edge.pre_vertex.n_colour_bits, self.__delay, weight_index))
        n_weights = next_weight_index
        if next_weight_index % 2 != 0:
            n_weights += 1

        # Write the common spec
        post_slice = machine_vertex.vertex_slice
        post_start = numpy.array(post_slice.start)
        post_shape = numpy.array(post_slice.shape)
        post_end = (post_start + post_shape) - 1
        spec.write_value(post_start[1], data_type=DataType.INT16)
        spec.write_value(post_start[0], data_type=DataType.INT16)
        spec.write_value(post_end[1], data_type=DataType.INT16)
        spec.write_value(post_end[0], data_type=DataType.INT16)
        spec.write_value(post_shape[1], data_type=DataType.INT16)
        spec.write_value(post_shape[0], data_type=DataType.INT16)
        spec.write_value(next_weight_index)
        spec.write_value(len(sources_for_m_vertex), data_type=DataType.UINT32)

        # Write the data
        spec.write_array(numpy.concatenate(data, dtype=uint32))

        # Write weights where they are unique
        kernel_data = [
            conn.get_encoded_kernel_weights(app_edge, weight_scales)
            for conn, app_edge in unique_connectors]
        if next_weight_index % 2 != 0:
            kernel_data.append(numpy.array([0], dtype=int16))
        spec.write_array(
            numpy.concatenate(kernel_data, dtype=int16).view(uint32))

    @staticmethod
    def __merge_key_and_mask(key_a, mask_a, key_b, mask_b):
        new_xs = (~(key_a ^ key_b)) & 0xFFFFFFFF
        mask = mask_a & mask_b & new_xs
        key = (key_a | key_b) & mask
        return key, mask

    def __get_sources_for_target(
            self, app_vertex: AbstractPopulationVertex) -> Dict[
                MachineVertex, List[Source]]:
        """
        Get all the machine vertex sources that will hit the given
        application vertex.

        :param AbstractPopulationVertex app_vertex:
            The vertex being targeted
        :rtype: dict(~.MachineVertex, list(Sources))
        """
        sources_for_target = self.__cached_2d_overlaps.get(app_vertex)
        if sources_for_target is None:
            key_cache: Dict[
                Tuple[PopulationApplicationVertex, Slice], Source] = {}
            seen_pre_vertices = set()
            sources_for_target = defaultdict(list)
            for incoming in app_vertex.incoming_projections:
                # pylint: disable=protected-access
                app_edge = incoming._projection_edge
                s_info = incoming._synapse_information
                source_vertex = app_edge.pre_vertex
                if source_vertex not in seen_pre_vertices:
                    seen_pre_vertices.add(source_vertex)
                    for tgt, srcs in s_info.connector.get_connected_vertices(
                            s_info, source_vertex, app_vertex):
                        r_info = self.__get_rinfo_for_sources(
                            key_cache, cast(Sequence[MachineVertex], srcs),
                            incoming, app_edge, app_vertex)
                        sources_for_target[tgt].extend(r_info)
            self.__cached_2d_overlaps[app_vertex] = sources_for_target
        return sources_for_target

    def __get_rinfo_for_sources(
            self,
            key_cache: Dict[Tuple[PopulationApplicationVertex, Slice], Source],
            srcs: Sequence[MachineVertex], incoming: Projection,
            app_edge: ProjectionApplicationEdge,
            app_vertex: AbstractPopulationVertex) -> Iterable[Source]:
        """
        Get the routing information for sources, merging sources that have
        the same vertex slice.

        .. note::
            This happens in retinas from FPGAs.

        :param dict key_cache:
        :rtype: list(Source)
        """
        delay_vertex: Optional[DelayExtensionVertex] = None
        if self.__delay > app_vertex.splitter.max_support_delay():
            # pylint: disable=protected-access
            delay_edge = incoming._projection_edge.delay_edge
            assert delay_edge is not None
            delay_vertex = delay_edge.pre_vertex

        # Group sources by vertex slice
        sources: Dict[Slice, List[MachineVertex]] = defaultdict(list)
        for source in srcs:
            sources[source.vertex_slice].append(source)

        # For each slice, merge the keys
        for vertex_slice, slice_sources in sources.items():
            cache_key = (app_edge.pre_vertex, vertex_slice)
            key_source = key_cache.get(cache_key)
            if not key_source:
                key_source = self.__build_source(
                    slice_sources, delay_vertex, incoming, vertex_slice)
                key_cache[cache_key] = key_source
            yield key_source

    def __build_source(
            self, slice_sources: List[MachineVertex],
            delay_vertex: Optional[DelayExtensionVertex],
            incoming: Projection, vertex_slice: Slice) -> Source:
        r_info = self.__get_rinfo(slice_sources[0], delay_vertex)
        group_key = r_info.key
        group_mask = r_info.mask
        for source in slice_sources:
            r_info = self.__get_rinfo(source, delay_vertex)
            group_key, group_mask = self.__merge_key_and_mask(
                group_key, group_mask, r_info.key, r_info.mask)
        return Source(incoming, vertex_slice, group_key, group_mask)

    @staticmethod
    def __get_rinfo(
            source: MachineVertex,
            delay_vertex: Optional[DelayExtensionVertex]) -> VertexRoutingInfo:
        if delay_vertex:
            # pylint: disable=protected-access
            source = delay_vertex._delay_splitter.get_machine_vertex(
                source.vertex_slice)
        routing_info = SpynnakerDataView.get_routing_infos()
        r_info = routing_info.get_routing_info_from_pre_vertex(
            source, SPIKE_PARTITION_ID)
        if r_info is None:
            raise KeyError(f"unrouted source: {source}")
        return r_info

    @property
    @overrides(AbstractLocalOnly.delay)
    def delay(self) -> float:
        return self.__delay

    @property
    @overrides(AbstractLocalOnly.weight)
    def weight(self) -> int:
        # We don't have a weight here, it is in the connector
        return 0

    @staticmethod
    def __connector(projection: Projection) -> ConvolutionConnector:
        # pylint: disable=protected-access
        return cast(ConvolutionConnector,
                    projection._synapse_information.connector)

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
        max_weight = numpy.amax(conn.kernel_weights)
        return max_weight if max_weight > 0 else 0

    @overrides(AbstractSupportsSignedWeights.get_minimum_negative_weight)
    def get_minimum_negative_weight(
            self, incoming_projection: Projection) -> float:
        conn = self.__connector(incoming_projection)
        # This is different because the connector happens to support this
        min_weight = numpy.amin(conn.kernel_weights)
        return min_weight if min_weight < 0 else 0

    @overrides(AbstractSupportsSignedWeights.get_mean_positive_weight)
    def get_mean_positive_weight(
            self, incoming_projection: Projection) -> float:
        conn = self.__connector(incoming_projection)
        pos_weights = conn.kernel_weights[conn.kernel_weights > 0]
        if not len(pos_weights):
            return 0
        return numpy.mean(pos_weights)

    @overrides(AbstractSupportsSignedWeights.get_mean_negative_weight)
    def get_mean_negative_weight(
            self, incoming_projection: Projection) -> float:
        conn = self.__connector(incoming_projection)
        neg_weights = conn.kernel_weights[conn.kernel_weights < 0]
        if not len(neg_weights):
            return 0
        return numpy.mean(neg_weights)

    @overrides(AbstractSupportsSignedWeights.get_variance_positive_weight)
    def get_variance_positive_weight(
            self, incoming_projection: Projection) -> float:
        conn = self.__connector(incoming_projection)
        pos_weights = conn.kernel_weights[conn.kernel_weights > 0]
        if not len(pos_weights):
            return 0
        return numpy.var(pos_weights)

    @overrides(AbstractSupportsSignedWeights.get_variance_negative_weight)
    def get_variance_negative_weight(
            self, incoming_projection: Projection) -> float:
        conn = self.__connector(incoming_projection)
        neg_weights = conn.kernel_weights[conn.kernel_weights < 0]
        if not len(neg_weights):
            return 0
        return numpy.var(neg_weights)
