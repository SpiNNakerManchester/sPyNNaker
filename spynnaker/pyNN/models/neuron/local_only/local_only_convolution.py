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
import numpy
from math import ceil
from numpy import floating, uint32
from numpy.typing import NDArray
from typing import (
    Dict, Iterable, List, cast, TYPE_CHECKING)
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationVertex
from spinn_front_end_common.interface.ds import (
    DataType, DataSpecificationGenerator)
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_SHORT, BYTES_PER_WORD)
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neural_projections.connectors import (
    ConvolutionConnector, AbstractConnector)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSupportsSignedWeights)
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.types import Weight_Delay_In_Types
from spynnaker.pyNN.models.common.local_only_2d_common import (
    get_div_const, get_rinfo_for_source, get_sources_for_target,
    BITS_PER_SHORT, N_COLOUR_BITS_BITS, KEY_INFO_SIZE,
    get_first_and_last_slice, Source)
from .abstract_local_only import AbstractLocalOnly
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neuron.abstract_population_vertex import (
        AbstractPopulationVertex)
    from spynnaker.pyNN.models.projection import Projection
    from spynnaker.pyNN.models.neuron import (
        PopulationMachineLocalOnlyCombinedVertex)


#: Size of convolution config main bytes
CONV_CONFIG_SIZE = (6 * BYTES_PER_SHORT) + (4 * BYTES_PER_WORD)

#: Size of source information
SOURCE_INFO_SIZE = KEY_INFO_SIZE + (6 * BYTES_PER_WORD)


class LocalOnlyConvolution(AbstractLocalOnly, AbstractSupportsSignedWeights):
    """
    A convolution synapse dynamics that can process spikes with only DTCM.
    """

    __slots__ = (
        "__cached_sources",
    )

    def __init__(self, delay: Weight_Delay_In_Types = None):

        """
        :param float delay:
            The delay used in the connection; by default 1 time step
        """
        super().__init__(delay)

        # Store the sources to avoid recalculation
        self.__cached_sources: Dict[ApplicationVertex, Dict[
                PopulationApplicationVertex, List[Source]]] = dict()

    @property
    def _delay(self) -> float:
        # Guaranteed by check in init
        return cast(float, self.delay)

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
        connectors_seen = set()
        edges_seen = set()
        for incoming in incoming_projections:
            s_info = incoming._synapse_information
            if not isinstance(s_info.connector, ConvolutionConnector):
                raise SynapticConfigurationException(
                    "Only ConvolutionConnector can be used with a synapse type"
                    " of Convolution")
            app_edge = incoming._projection_edge
            if app_edge not in edges_seen:
                edges_seen.add(app_edge)
                n_bytes += SOURCE_INFO_SIZE
            if s_info.connector not in connectors_seen:
                connectors_seen.add(s_info.connector)
                kernel_bytes += s_info.connector.kernel_n_bytes
            n_bytes += s_info.connector.parameters_n_bytes

        if kernel_bytes % BYTES_PER_WORD != 0:
            kernel_bytes += BYTES_PER_SHORT

        return CONV_CONFIG_SIZE + n_bytes + kernel_bytes

    @overrides(AbstractLocalOnly.write_parameters)
    def write_parameters(
            self, spec: DataSpecificationGenerator, region: int,
            machine_vertex: PopulationMachineLocalOnlyCombinedVertex,
            weight_scales: NDArray[floating]):
        # pylint: disable=unexpected-keyword-arg, protected-access

        # Get incoming sources for this vertex
        app_vertex = machine_vertex._pop_vertex
        sources = self.__get_sources_for_target(app_vertex)

        size = self.get_parameters_usage_in_bytes(
            machine_vertex.vertex_slice, app_vertex.incoming_projections)
        spec.reserve_memory_region(region, size, label="LocalOnlyConvolution")
        spec.switch_write_focus(region)

        # Get spec for each incoming source
        connector_weight_index: Dict[AbstractConnector, int] = dict()
        next_weight_index: int = 0
        source_data = list()
        connector_data: List[NDArray[uint32]] = list()
        weight_data = list()
        for pre_vertex, source_infos in sources.items():

            # Add connectors as needed
            first_conn_index = len(connector_data)
            for source in source_infos:
                # pylint: disable=protected-access
                conn = cast(
                    ConvolutionConnector,
                    source.projection._synapse_information.connector)
                app_edge = source.projection._projection_edge

                # Work out whether the connector needs a new weight index
                if conn in connector_weight_index:
                    weight_index = connector_weight_index[conn]
                else:
                    weight_index = next_weight_index
                    connector_weight_index[conn] = weight_index
                    next_weight_index += conn.kernel_n_weights
                    weight_data.append(conn.get_encoded_kernel_weights(
                        app_edge, weight_scales))

                connector_data.append(conn.get_local_only_data(
                    app_edge, source.local_delay, source.delay_stage,
                    weight_index))

            # Get the source routing information
            r_info, core_mask, mask_shift = get_rinfo_for_source(
                pre_vertex)

            # Get the width / height per core / last_core
            first_slice, last_slice = get_first_and_last_slice(pre_vertex)
            width_per_core = first_slice.shape[0]
            height_per_core = first_slice.shape[1]
            width_on_last_core = last_slice.shape[0]
            height_on_last_core = last_slice.shape[1]

            # Get cores per width / height
            pre_shape = list(pre_vertex.atoms_shape)
            cores_per_width = int(ceil(pre_shape[0] / width_per_core))
            cores_per_height = int(ceil(pre_shape[1] / height_per_core))

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
            # ... height / width per core ...
            source_data.append(
                (width_per_core << BITS_PER_SHORT) + height_per_core)
            # ... height / width last core ...
            source_data.append(
                (width_on_last_core << BITS_PER_SHORT) + height_on_last_core)
            # ... cores per height / width ...
            source_data.append(
                (cores_per_width << BITS_PER_SHORT) + cores_per_height)
            # ... 1 / width per core ...
            source_data.append(get_div_const(width_per_core))
            # ... 1 / width last core ...
            source_data.append(get_div_const(width_on_last_core))
            # ... 1 / cores_per_width
            source_data.append(get_div_const(cores_per_width))

        if next_weight_index % 2 != 0:
            weight_data.append(numpy.array([0], dtype="int16"))

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
        spec.write_value(len(sources))
        spec.write_value(len(connector_data))
        spec.write_value(next_weight_index)

        # Write the data
        # pylint: disable=unexpected-keyword-arg
        spec.write_array(numpy.array(source_data, dtype="uint32"))
        spec.write_array(numpy.concatenate(connector_data, dtype="uint32"))
        spec.write_array(
            numpy.concatenate(weight_data, dtype="int16").view("uint32"))

    def __get_sources_for_target(
            self, app_vertex: AbstractPopulationVertex) -> Dict[
                PopulationApplicationVertex, List[Source]]:
        """
        Get all the application vertex sources that will hit the given
        application vertex.

        :param AbstractPopulationVertex app_vertex: The vertex being targeted
        :return:
            A dict of source PopulationApplicationVertex to list of source
            information
        :rtype: dict(PopulationApplicationVertex, list(Source))
        """
        sources = self.__cached_sources.get(app_vertex)
        if sources is None:
            sources = get_sources_for_target(app_vertex)
            self.__cached_sources[app_vertex] = sources
        return sources

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
