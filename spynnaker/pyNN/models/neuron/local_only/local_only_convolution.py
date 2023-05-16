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
import numpy
from math import ceil, log2, floor
from collections import namedtuple, defaultdict
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
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from .abstract_local_only import AbstractLocalOnly

Source = namedtuple(
    "Source", ["projection", "local_delay", "delay_stage"])

#: Number of shorts in the conv_config struct
CONV_CONFIG_N_SHORTS = 6

#: Number of words in the conv_config struct
CONV_CONFIG_N_WORDS = 2

#: The number of bits in a short value
BITS_PER_SHORT = 16

#: The number of bits in a byte value
BITS_PER_BYTE = 8

#: The number of bits to represent n_colour_bits
N_COLOUR_BITS_BITS = 3


class LocalOnlyConvolution(AbstractLocalOnly, AbstractSupportsSignedWeights):
    """
    A convolution synapse dynamics that can process spikes with only DTCM.
    """

    __slots__ = [
        "__cached_sources",
        "__cached_n_incoming"
        "__delay"
    ]

    def __init__(self, delay=None):
        """
        :param float delay:
            The delay used in the connection; by default 1 time step
        """
        # Store the sources to avoid recalculation
        self.__cached_sources = dict()

        # Store the n_incoming to avoid recalcaultion
        self.__cached_n_incoming = dict()

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
        kernel_bytes = 0
        for incoming in incoming_projections:
            # pylint: disable=protected-access
            s_info = incoming._synapse_information
            if not isinstance(s_info.connector, ConvolutionConnector):
                raise SynapticConfigurationException(
                    "Only ConvolutionConnector can be used with a synapse type"
                    " of Convolution")
            # pylint: disable=protected-access
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
    def write_parameters(self, spec, region, machine_vertex, weight_scales):

        # Get incoming sources for this vertex
        app_vertex = machine_vertex.app_vertex
        sources = self.__get_sources_for_target(app_vertex)

        size = self.get_parameters_usage_in_bytes(
            machine_vertex.vertex_slice, app_vertex.incoming_projections)
        spec.reserve_memory_region(region, size, label="LocalOnlyConvolution")
        spec.switch_write_focus(region)

        # Get spec for each incoming source
        connector_weight_index = dict()
        next_weight_index = 0
        source_data = list()
        connector_data = list()
        weight_data = list()
        for pre_vertex, source_infos in sources.items():

            # Add connectors as needed
            first_conn_index = len(connector_data)
            for source in source_infos:
                # pylint: disable=protected-access
                conn = source.projection._synapse_information.connector
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
            r_info, core_mask, mask_shift = self.__get_rinfo_for_source(
                pre_vertex)

            # Calculate the parameters to do 1 / source width
            source_width = pre_vertex.atoms_shape[0]
            log_sw = int(ceil(log2(source_width)))
            log_m_sw = ((2 ** log_sw) - source_width) / source_width
            source_width_m = int(floor((2 ** BYTES_PER_SHORT) * log_m_sw) + 1)
            source_width_sh1 = min(log_sw, 1)
            source_width_sh2 = max(log_sw - 1, 0)

            # Add the key and mask...
            source_data.extend([r_info.key, r_info.mask])
            # ... start connector index, n colour bits, count of connectors ...
            source_data.append(
                (first_conn_index << (BITS_PER_SHORT + N_COLOUR_BITS_BITS)) +
                (pre_vertex.n_colour_bits << BITS_PER_SHORT) +
                len(source_infos))
            # ... core mask, mask shift ...
            source_data.append((core_mask << BITS_PER_SHORT) + mask_shift)
            # ... n neurons, source width ...
            source_data.append(
                (pre_vertex.n_atoms << BITS_PER_SHORT) +
                pre_vertex.atoms_shape[0])
            # ... 1 / source width parameters
            source_data.append(
                (source_width_m << BITS_PER_SHORT) +
                (source_width_sh1 << BITS_PER_BYTE) + source_width_sh2)

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
        spec.write_array(numpy.concatenate(source_data, dtype="uint32"))
        spec.write_array(numpy.concatenate(connector_data, dtype="uint32"))
        spec.write_array(
            numpy.concatenate(weight_data, dtype="int16").view("uint32"))

    def __get_sources_for_target(self, app_vertex):
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
            sources = defaultdict(list)
            for incoming in app_vertex.incoming_projections:
                pre_vertex, local_delay, delay_stage = \
                    self.__get_delay_for_source(incoming)
                source = Source(incoming, local_delay, delay_stage)
                sources[pre_vertex].append(source)
            self.__cached_sources[app_vertex] = sources
        return sources

    def __get_delay_for_source(self, incoming):
        # pylint: disable=protected-access
        app_edge = incoming._projection_edge
        delay = incoming._synapse_information.synapse_dynamics.delay
        steps = delay * SpynnakerDataView.get_simulation_time_step_per_ms()
        max_delay = app_edge.post_vertex.splitter.max_support_delay()
        local_delay = steps % max_delay
        delay_stage = 0
        pre_vertex = app_edge.pre_vertex
        if steps > max_delay:
            delay_stage = (steps // max_delay) - 1
            pre_vertex = app_edge.delay_edge.pre_vertex
        return pre_vertex, local_delay, delay_stage

    def __get_rinfo_for_source(self, pre_vertex):
        """
        Get the routing information for the source of a projection.

        :param ApplicationVertex pre_vertex: The source of incoming data
        :return: Routing information, core mask, core mask shift
        :rtype: AppVertexRoutingInfo, int, int
        """
        routing_info = SpynnakerDataView.get_routing_infos()

        # Find the routing information
        r_info = routing_info.get_routing_info_from_pre_vertex(
                pre_vertex, SPIKE_PARTITION_ID)

        mask_shift = r_info.n_bits_atoms
        core_mask = (2 ** get_n_bits(
            len(r_info.vertex.splitter.get_out_going_vertices(
                SPIKE_PARTITION_ID)))) - 1
        return r_info, core_mask, mask_shift

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
