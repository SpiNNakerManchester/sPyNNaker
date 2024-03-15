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
from math import ceil
from typing import (
    Dict, List, Iterable, cast, TYPE_CHECKING)

import numpy
from numpy import floating, uint32
from numpy.typing import NDArray

from spinn_utilities.overrides import overrides

from pacman.model.graphs.application import ApplicationVertex

from spinn_front_end_common.interface.ds import (
    DataType, DataSpecificationGenerator)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neural_projections.connectors import (
    PoolDenseConnector)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSupportsSignedWeights)
from spynnaker.pyNN.types import Weight_Delay_In_Types
from spynnaker.pyNN.models.common.local_only_2d_common import (
    get_sources_for_target, get_rinfo_for_spike_source, BITS_PER_SHORT,
    get_div_const, N_COLOUR_BITS_BITS, KEY_INFO_SIZE, get_first_and_last_slice,
    Source)

from .abstract_local_only import AbstractLocalOnly

if TYPE_CHECKING:
    from spynnaker.pyNN.models.projection import Projection
    from spynnaker.pyNN.models.neuron import (
        PopulationMachineLocalOnlyCombinedVertex)
    from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
    from spynnaker.pyNN.models.neuron.synapse_dynamics import (
        AbstractSynapseDynamics)

#: Size of the source information
SOURCE_INFO_SIZE = KEY_INFO_SIZE + BYTES_PER_WORD

#: Size of the source info per-dimension info
SOURCE_INFO_DIM_SIZE = 9 * BYTES_PER_WORD

#: Size of information
CONFIG_SIZE = 3 * BYTES_PER_WORD


class LocalOnlyPoolDense(AbstractLocalOnly, AbstractSupportsSignedWeights):
    """
    A convolution synapse dynamics that can process spikes with only DTCM.
    """

    __slots__ = [
        "__cached_sources"]

    def __init__(self, delay: Weight_Delay_In_Types = None):
        """
        :param float delay:
            The delay used in the connection; by default 1 time step
        """
        # Store the sources to avoid recalculation
        self.__cached_sources: Dict[ApplicationVertex, Dict[
                ApplicationVertex, List[Source]]] = dict()

        super().__init__(delay)
        if not isinstance(self.delay, (float, int)):
            raise SynapticConfigurationException(
                "Only single value delays are supported")

    @property
    def _delay(self) -> float:
        # Guaranteed by check in init
        return cast(float, self.delay)

    @overrides(AbstractLocalOnly.merge)
    def merge(self, synapse_dynamics: AbstractSynapseDynamics
              ) -> LocalOnlyPoolDense:
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
        seen_edges = set()
        for incoming in incoming_projections:
            # pylint: disable=protected-access
            s_info = incoming._synapse_information
            if not isinstance(s_info.connector, PoolDenseConnector):
                raise SynapticConfigurationException(
                    "Only PoolDenseConnector can be used with a synapse type"
                    " of PoolDense")
            # pylint: disable=protected-access
            app_edge = incoming._projection_edge
            if app_edge not in seen_edges:
                seen_edges.add(app_edge)
                n_dims = len(app_edge.pre_vertex.atoms_shape)
                n_bytes += SOURCE_INFO_SIZE
                n_bytes += n_dims * SOURCE_INFO_DIM_SIZE
            n_bytes += s_info.connector.local_only_n_bytes(
                app_edge.pre_vertex.atoms_shape, n_atoms)

        return CONFIG_SIZE + n_bytes

    @overrides(AbstractLocalOnly.write_parameters)
    def write_parameters(
            self, spec: DataSpecificationGenerator, region: int,
            machine_vertex: PopulationMachineLocalOnlyCombinedVertex,
            weight_scales: NDArray[floating]):
        # Get incoming sources for this vertex
        app_vertex = cast('AbstractPopulationVertex',
                          machine_vertex.app_vertex)
        sources = self.__get_sources_for_target(app_vertex)

        size = self.get_parameters_usage_in_bytes(
            machine_vertex.vertex_slice.n_atoms,
            app_vertex.incoming_projections)
        spec.reserve_memory_region(region, size, label="LocalOnlyPoolDense")
        spec.switch_write_focus(region)

        connector_data: List[NDArray[uint32]] = list()
        source_data = list()
        n_connectors = 0
        for pre_vertex, source_infos in sources.items():
            first_conn_index = len(connector_data)
            for source in source_infos:
                # pylint: disable=protected-access
                conn = source.projection._synapse_information.connector
                app_edge = source.projection._projection_edge
                connector_data.append(conn.get_local_only_data(
                    app_edge, source.local_delay, source.delay_stage,
                    machine_vertex.vertex_slice, weight_scales))
                n_connectors += 1

            # Get the source routing information
            r_info, core_mask, mask_shift = get_rinfo_for_spike_source(
                pre_vertex)

            # Get the width / height per core / last_core
            first_slice, last_slice = get_first_and_last_slice(pre_vertex)
            n_dims = len(pre_vertex.atoms_shape)
            pre_shape = list(pre_vertex.atoms_shape)

            # Add the key and mask...
            source_data.extend([r_info.key, r_info.mask])
            # ... start connector index, n_colour_bits, count of connectors ...
            source_data.append(
                (len(source_infos) << BITS_PER_SHORT) +
                (pre_vertex.n_colour_bits <<
                 (BITS_PER_SHORT - N_COLOUR_BITS_BITS)) +
                first_conn_index)
            # ... core mask, mask shift ...
            source_data.append((mask_shift << BITS_PER_SHORT) + core_mask)
            # ... n_dims ...
            source_data.append(n_dims)

            # Add the dimensions; calculations are in reverse order!
            cum_size = 1
            cum_cores_per_dim = 1
            cum_last_size = 1
            all_dim_data = list()
            for i in range(n_dims):
                dim_data = list()
                # Size per core
                dim_data.append(first_slice.shape[i])
                dim_data.append(cum_size)
                dim_data.append(get_div_const(cum_size))
                cum_size *= first_slice.shape[i]

                # Cores
                cores_per_dim = int(ceil(pre_shape[i] / first_slice.shape[i]))
                dim_data.append(cores_per_dim)
                dim_data.append(cum_cores_per_dim)
                dim_data.append(get_div_const(cum_cores_per_dim))
                cum_cores_per_dim *= cores_per_dim

                # Last core
                dim_data.append(last_slice.shape[i])
                dim_data.append(cum_last_size)
                dim_data.append(get_div_const(cum_last_size))
                cum_last_size *= last_slice.shape[i]
                all_dim_data.append(dim_data)
            for dim_data in reversed(all_dim_data):
                source_data.extend(dim_data)

        # Write the spec
        n_post = int(numpy.prod(machine_vertex.vertex_slice.shape))
        spec.write_value(n_post, data_type=DataType.UINT32)
        spec.write_value(len(sources), data_type=DataType.UINT32)
        spec.write_value(n_connectors, data_type=DataType.UINT32)
        spec.write_array(numpy.array(source_data, dtype=numpy.uint32))
        spec.write_array(numpy.concatenate(connector_data))

    def __get_sources_for_target(self, app_vertex: AbstractPopulationVertex):
        """
        Get all the application vertex sources that will hit the given
        application vertex.

        :param AbstractPopulationVertex app_vertex: The vertex being targeted
        :return:
            A dict of source ApplicationVertex to list of source information
        :rtype: dict(ApplicationVertex, list(Source))
        """
        sources = self.__cached_sources.get(app_vertex)
        if sources is None:
            sources = get_sources_for_target(app_vertex)
            self.__cached_sources[app_vertex] = sources
        return sources

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
        if len(pos_weights) == 0:
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
        if len(neg_weights) == 0:
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
        if len(pos_weights) == 0:
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
        if len(neg_weights) == 0:
            return 0
        return numpy.var(neg_weights)
