# Copyright (c) 2021-2022 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import numpy
from collections import defaultdict
from spinn_utilities.overrides import overrides
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neural_projections.connectors import (
    PoolDenseConnector)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSupportsSignedWeights)
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from .abstract_local_only import AbstractLocalOnly


class LocalOnlyPoolDense(AbstractLocalOnly, AbstractSupportsSignedWeights):
    """ A convolution synapse dynamics that can process spikes with only DTCM
    """

    @overrides(AbstractLocalOnly.merge)
    def merge(self, synapse_dynamics):
        if not isinstance(synapse_dynamics, LocalOnlyPoolDense):
            raise SynapticConfigurationException(
                "All Projections of this Population must have a synapse_type"
                " of LocalOnlyPoolDense")
        return synapse_dynamics

    @overrides(AbstractLocalOnly.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self):
        return "_pool_dense"

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
    def write_parameters(self, spec, region, machine_vertex, weight_scales):

        # Get all the incoming vertices and keys so we can sort
        routing_info = SpynnakerDataView.get_routing_infos()
        incoming_info = list()
        seen_pre_vertices = set()
        for incoming in machine_vertex.app_vertex.incoming_projections:
            # pylint: disable=protected-access
            app_edge = incoming._projection_edge
            s_info = incoming._synapse_information

            if app_edge.pre_vertex in seen_pre_vertices:
                continue
            seen_pre_vertices.add(app_edge.pre_vertex)

            # Keep track of all the same source squares, so they can be
            # merged; this will make sure the keys line up!
            edges_for_source = defaultdict(list)
            for pre_m_vertex in app_edge.pre_vertex.machine_vertices:
                r_info = routing_info.get_routing_info_from_pre_vertex(
                    pre_m_vertex, SPIKE_PARTITION_ID)
                vertex_slice = pre_m_vertex.vertex_slice
                key = (app_edge.pre_vertex, vertex_slice)
                edges_for_source[key].append((pre_m_vertex, r_info))

            # Merge edges with the same source
            for (_, vertex_slice), edge_list in edges_for_source.items():
                group_key = edge_list[0][1].key
                group_mask = edge_list[0][1].mask
                for _, r_info in edge_list:
                    group_key, group_mask = self.__merge_key_and_mask(
                        group_key, group_mask, r_info.key, r_info.mask)
                incoming_info.append(
                    (incoming, vertex_slice, group_key, group_mask,
                     app_edge.pre_vertex.n_colour_bits))

        size = self.get_parameters_usage_in_bytes(
            machine_vertex.vertex_slice.n_atoms,
            machine_vertex.app_vertex.incoming_projections)
        spec.reserve_memory_region(region, size, label="LocalOnlyConvolution")
        spec.switch_write_focus(region)

        # Write the common spec
        post_slice = machine_vertex.vertex_slice
        n_post = numpy.prod(post_slice.shape)
        spec.write_value(n_post, data_type=DataType.UINT32)
        spec.write_value(len(incoming_info), data_type=DataType.UINT32)

        # Write spec for each connector, sorted by key
        incoming_info.sort(key=lambda e: e[3])
        for incoming, vertex_slice, key, mask, n_colour_bits in incoming_info:
            # pylint: disable=protected-access
            s_info = incoming._synapse_information
            app_edge = incoming._projection_edge
            s_info.connector.write_local_only_data(
                spec, app_edge, vertex_slice, post_slice, key, mask,
                n_colour_bits, weight_scales)

    def __merge_key_and_mask(self, key_a, mask_a, key_b, mask_b):
        new_xs = ~(key_a ^ key_b)
        mask = mask_a & mask_b & new_xs
        key = (key_a | key_b) & mask
        return key, mask

    @property
    @overrides(AbstractLocalOnly.delay)
    def delay(self):
        return SpynnakerDataView.get_simulation_time_step_ms()

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
        max_weight = numpy.amax(conn.weights)
        return max_weight if max_weight > 0 else 0

    @overrides(AbstractSupportsSignedWeights.get_minimum_negative_weight)
    def get_minimum_negative_weight(self, incoming_projection):
        # pylint: disable=protected-access
        conn = incoming_projection._synapse_information.connector
        # This is different because the connector happens to support this
        min_weight = numpy.amin(conn.weights)
        return min_weight if min_weight < 0 else 0

    @overrides(AbstractSupportsSignedWeights.get_mean_positive_weight)
    def get_mean_positive_weight(self, incoming_projection):
        # pylint: disable=protected-access
        conn = incoming_projection._synapse_information.connector
        weights = conn.weights
        if isinstance(weights, (int, float)):
            return weights
        pos_weights = weights[weights > 0]
        if not len(pos_weights):
            return 0
        return numpy.mean(pos_weights)

    @overrides(AbstractSupportsSignedWeights.get_mean_negative_weight)
    def get_mean_negative_weight(self, incoming_projection):
        # pylint: disable=protected-access
        conn = incoming_projection._synapse_information.connector
        weights = conn.weights
        if isinstance(weights, (int, float)):
            return weights
        neg_weights = weights[weights < 0]
        if not len(neg_weights):
            return 0
        return numpy.mean(neg_weights)

    @overrides(AbstractSupportsSignedWeights.get_variance_positive_weight)
    def get_variance_positive_weight(self, incoming_projection):
        # pylint: disable=protected-access
        conn = incoming_projection._synapse_information.connector
        weights = conn.weights
        if isinstance(weights, (int, float)):
            return 0
        pos_weights = weights[weights > 0]
        if not len(pos_weights):
            return 0
        return numpy.var(pos_weights)

    @overrides(AbstractSupportsSignedWeights.get_variance_negative_weight)
    def get_variance_negative_weight(self, incoming_projection):
        # pylint: disable=protected-access
        conn = incoming_projection._synapse_information.connector
        weights = conn.weights
        if isinstance(weights, (int, float)):
            return 0
        neg_weights = weights[weights < 0]
        if not len(neg_weights):
            return 0
        return numpy.var(neg_weights)
