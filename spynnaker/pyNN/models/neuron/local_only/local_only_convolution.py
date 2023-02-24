# Copyright (c) 2021 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import numpy
from collections import defaultdict, namedtuple
from spinn_utilities.overrides import overrides
from data_specification.enums.data_type import DataType
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

Source = namedtuple("Source", ["projection", "vertex_slice", "key", "mask"])

#: Number of shorts in the conv_config struct
CONV_CONFIG_N_SHORTS = 6


class LocalOnlyConvolution(AbstractLocalOnly, AbstractSupportsSignedWeights):
    """ A convolution synapse dynamics that can process spikes with only DTCM
    """

    __slots__ = [
        "__cached_2d_overlaps",
        "__delay"
    ]

    def __init__(self, delay=None):
        """
        :param float delay:
            The delay used in the connection; by default 1 time step
        """
        # Store the overlaps between 2d vertices to avoid recalculation
        self.__cached_2d_overlaps = dict()
        self.__delay = delay
        if delay is None:
            self.__delay = SpynnakerDataView.get_simulation_time_step_ms()
        elif not isinstance(delay, (float, int)):
            raise SynapticConfigurationException(
                "Only single value delays are supported")

    @overrides(AbstractLocalOnly.merge)
    def merge(self, synapse_dynamics):
        if not isinstance(synapse_dynamics, LocalOnlyConvolution):
            raise SynapticConfigurationException(
                "All targets of this Population must have a synapse_type of"
                " Convolution")
        return synapse_dynamics

    @overrides(AbstractLocalOnly.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self):
        return "_conv"

    @property
    @overrides(AbstractLocalOnly.changes_during_run)
    def changes_during_run(self):
        return False

    @overrides(AbstractLocalOnly.get_parameters_usage_in_bytes)
    def get_parameters_usage_in_bytes(
            self, n_atoms, incoming_projections):
        n_bytes = 0
        for incoming in incoming_projections:
            # pylint: disable=protected-access
            s_info = incoming._synapse_information
            if not isinstance(s_info.connector, ConvolutionConnector):
                raise SynapticConfigurationException(
                    "Only ConvolutionConnector can be used with a synapse type"
                    " of Convolution")
            # pylint: disable=protected-access
            app_edge = incoming._projection_edge
            n_incoming = len(
                app_edge.pre_vertex.splitter.get_out_going_slices())
            n_bytes += s_info.connector.local_only_n_bytes * n_incoming

        return ((CONV_CONFIG_N_SHORTS * BYTES_PER_SHORT) + BYTES_PER_WORD +
                n_bytes)

    @overrides(AbstractLocalOnly.write_parameters)
    def write_parameters(self, spec, region, machine_vertex, weight_scales):

        # Get incoming sources for this machine vertex, and sort by key
        app_vertex = machine_vertex.app_vertex
        sources_for_targets = self.__get_sources_for_target(app_vertex)
        sources_for_m_vertex = sources_for_targets[machine_vertex]
        sources_for_m_vertex.sort(key=lambda s: s.key)

        size = self.get_parameters_usage_in_bytes(
            machine_vertex.vertex_slice, app_vertex.incoming_projections)
        spec.reserve_memory_region(region, size, label="LocalOnlyConvolution")
        spec.switch_write_focus(region)

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
        spec.write_value(len(sources_for_m_vertex), data_type=DataType.UINT32)

        # Write spec for each incoming source
        for source in sources_for_m_vertex:
            incoming = source.projection
            # pylint: disable=protected-access
            s_info = incoming._synapse_information
            app_edge = incoming._projection_edge
            s_info.connector.write_local_only_data(
                spec, app_edge, source.vertex_slice, source.key,
                source.mask, app_edge.pre_vertex.n_colour_bits, weight_scales)

    def __merge_key_and_mask(self, key_a, mask_a, key_b, mask_b):
        new_xs = ~(key_a ^ key_b)
        mask = mask_a & mask_b & new_xs
        key = (key_a | key_b) & mask
        return key, mask

    def __get_sources_for_target(self, app_vertex):
        """ Get all the machine vertex sources that will hit the given
            application vertex

        :param AbstractPopulationVertex app_vertex:
            The vertex being targeted
        :rtype: dict(MachineVertex, list(Sources))
        """
        sources_for_target = self.__cached_2d_overlaps.get(app_vertex)
        if sources_for_target is None:
            key_cache = dict()
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
                            key_cache, srcs, incoming, app_vertex)
                        sources_for_target[tgt].extend(r_info)
            self.__cached_2d_overlaps[app_vertex] = sources_for_target
        return sources_for_target

    def __get_rinfo_for_sources(self, key_cache, srcs, incoming, app_vertex):
        """ Get the routing information for sources, merging sources that have
            the same vertex slice (note this happens in retinas from FPGAs).

        :rtype: list(Source)
        """
        routing_info = SpynnakerDataView.get_routing_infos()
        delay_vertex = None
        if self.__delay > app_vertex.splitter.max_support_delay():
            # pylint: disable=protected-access
            delay_vertex = incoming._projection_edge.delay_edge.pre_vertex

        # Group sources by vertex slice
        sources = defaultdict(list)
        for source in srcs:
            sources[source.vertex_slice].append(source)

        # For each slice, merge the keys
        keys = list()
        for vertex_slice, slice_sources in sources.items():
            if vertex_slice in key_cache:
                keys.append(key_cache.get(vertex_slice))
            else:
                r_info = self.__get_rinfo(
                    routing_info, slice_sources[0], delay_vertex)
                group_key = r_info.key
                group_mask = r_info.mask
                for source in slice_sources:
                    r_info = self.__get_rinfo(
                        routing_info, source, delay_vertex)
                    group_key, group_mask = self.__merge_key_and_mask(
                        group_key, group_mask, r_info.key,
                        r_info.mask)
                key_source = Source(
                    incoming, vertex_slice, group_key, group_mask)
                key_cache[vertex_slice] = key_source
                keys.append(key_source)
        return keys

    def __get_rinfo(self, routing_info, source, delay_vertex):
        if delay_vertex is None:
            return routing_info.get_routing_info_from_pre_vertex(
                source, SPIKE_PARTITION_ID)
        delay_source = delay_vertex.splitter.get_machine_vertex(
            source.vertex_slice)
        return routing_info.get_routing_info_from_pre_vertex(
            delay_source, SPIKE_PARTITION_ID)

    @property
    @overrides(AbstractLocalOnly.delay)
    def delay(self):
        return self.__delay

    @property
    @overrides(AbstractLocalOnly.weight)
    def weight(self):
        # We don't have a weight here, it is in the connector
        return 0

    @overrides(AbstractSupportsSignedWeights.get_positive_synapse_index)
    def get_positive_synapse_index(self, incoming_projection):
        # pylint: disable=protected-access
        post = incoming_projection._projection_edge.post_vertex
        conn = incoming_projection._synapse_information.connector
        return post.get_synapse_id_by_target(conn.positive_receptor_type)

    @overrides(AbstractSupportsSignedWeights.get_negative_synapse_index)
    def get_negative_synapse_index(self, incoming_projection):
        # pylint: disable=protected-access
        post = incoming_projection._projection_edge.post_vertex
        conn = incoming_projection._synapse_information.connector
        return post.get_synapse_id_by_target(conn.negative_receptor_type)

    @overrides(AbstractSupportsSignedWeights.get_maximum_positive_weight)
    def get_maximum_positive_weight(self, incoming_projection):
        # pylint: disable=protected-access
        conn = incoming_projection._synapse_information.connector
        # We know the connector doesn't care about the argument
        max_weight = numpy.amax(conn.kernel_weights)
        return max_weight if max_weight > 0 else 0

    @overrides(AbstractSupportsSignedWeights.get_minimum_negative_weight)
    def get_minimum_negative_weight(self, incoming_projection):
        # pylint: disable=protected-access
        conn = incoming_projection._synapse_information.connector
        # This is different because the connector happens to support this
        min_weight = numpy.amin(conn.kernel_weights)
        return min_weight if min_weight < 0 else 0

    @overrides(AbstractSupportsSignedWeights.get_mean_positive_weight)
    def get_mean_positive_weight(self, incoming_projection):
        # pylint: disable=protected-access
        conn = incoming_projection._synapse_information.connector
        pos_weights = conn.kernel_weights[conn.kernel_weights > 0]
        if not len(pos_weights):
            return 0
        return numpy.mean(pos_weights)

    @overrides(AbstractSupportsSignedWeights.get_mean_negative_weight)
    def get_mean_negative_weight(self, incoming_projection):
        # pylint: disable=protected-access
        conn = incoming_projection._synapse_information.connector
        neg_weights = conn.kernel_weights[conn.kernel_weights < 0]
        if not len(neg_weights):
            return 0
        return numpy.mean(neg_weights)

    @overrides(AbstractSupportsSignedWeights.get_variance_positive_weight)
    def get_variance_positive_weight(self, incoming_projection):
        # pylint: disable=protected-access
        conn = incoming_projection._synapse_information.connector
        pos_weights = conn.kernel_weights[conn.kernel_weights > 0]
        if not len(pos_weights):
            return 0
        return numpy.var(pos_weights)

    @overrides(AbstractSupportsSignedWeights.get_variance_negative_weight)
    def get_variance_negative_weight(self, incoming_projection):
        # pylint: disable=protected-access
        conn = incoming_projection._synapse_information.connector
        neg_weights = conn.kernel_weights[conn.kernel_weights < 0]
        if not len(neg_weights):
            return 0
        return numpy.var(neg_weights)
