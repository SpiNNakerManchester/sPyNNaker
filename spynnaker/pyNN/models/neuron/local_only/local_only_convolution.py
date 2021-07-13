# Copyright (c) 2021 The University of Manchester
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
from spinn_utilities.overrides import overrides
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_SHORT, BYTES_PER_WORD)
from spinn_front_end_common.utilities.globals_variables import (
    machine_time_step_ms)
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neural_projections.connectors import (
    ConvolutionConnector)
from .abstract_local_only import AbstractLocalOnly


class LocalOnlyConvolution(AbstractLocalOnly):
    """ A convolution synapse dynamics that can process spikes with only DTCM
    """

    @overrides(AbstractLocalOnly.merge)
    def merge(self, synapse_dynamics):
        if not isinstance(synapse_dynamics, LocalOnlyConvolution):
            raise SynapticConfigurationException(
                "All targets of this Population must have a synapse_type of"
                " Convolution")

    @overrides(AbstractLocalOnly.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self):
        return "_conv"

    @overrides(AbstractLocalOnly.are_weights_signed)
    def are_weights_signed(self):
        return False

    @overrides(AbstractLocalOnly.changes_during_run)
    def changes_during_run(self):
        return False

    @overrides(AbstractLocalOnly.get_parameters_usage_in_bytes)
    def get_parameters_usage_in_bytes(self, incoming_projections):
        n_bytes = 0
        for incoming in incoming_projections:
            s_info = incoming._synapse_information
            if not isinstance(s_info.connector, ConvolutionConnector):
                raise SynapticConfigurationException(
                    "Only ConvolutionConnector can be used with a synapse type"
                    " of Convolution")
            n_bytes += s_info.connector.local_only_n_bytes
        return 6 * BYTES_PER_SHORT + BYTES_PER_WORD

    @overrides(AbstractLocalOnly.write_parameters)
    def write_parameters(
            self, spec, region, routing_info, incoming_projections,
            machine_vertex, weight_scales):

        # Get all the incoming vertices and keys so we can sort
        edge_info = list()
        for incoming in incoming_projections:
            app_edge = incoming._projection_edge
            for edge in app_edge.machine_edges:
                if edge.post_vertex == machine_vertex:
                    r_info = routing_info.get_routing_info_for_edge(edge)
                    edge_info.append((edge, incoming, r_info))
        edge_info.sort(key=lambda e: e[1].first_key)

        size = self.get_parameters_usage_in_bytes(len(edge_info))
        spec.reserve_memory_region(region, size, label="LocalOnlyConvolution")
        spec.switch_write_focus(region)

        # Write the common spec
        post_slice = machine_vertex.vertex_slice
        post_start = numpy.array(post_slice.starts)
        post_shape = numpy.array(post_slice.shape)
        post_end = (post_start + post_shape) - 1
        spec.write_value(post_start[0], dtype=DataType.INT16)
        spec.write_value(post_start[1], dtype=DataType.INT16)
        spec.write_value(post_end[0], dtype=DataType.INT16)
        spec.write_value(post_end[1], dtype=DataType.INT16)
        spec.write_value(post_shape[0], dtype=DataType.INT16)
        spec.write_value(post_shape[1], dtype=DataType.INT16)
        spec.write_value(len(edge_info), dtype=DataType.UINT32)

        # Write spec for each connector
        for edge, incoming, r_info in edge_info:
            s_info = incoming._synapse_information
            s_info.connector.write_local_only_data(
                spec, edge, r_info, s_info, weight_scales)

    @property
    @overrides(AbstractLocalOnly.delay)
    def delay(self):
        return machine_time_step_ms()

    @overrides(AbstractLocalOnly.set_delay)
    def set_delay(self, delay):
        # We don't need no stinking delay
        pass

    @property
    @overrides(AbstractLocalOnly.weight)
    def weight(self):
        # We don't have a weight here, it is in the connector
        return 0
