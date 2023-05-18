# Copyright (c) 2022 The University of Manchester
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
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utility_models import (
    ReverseIPTagMulticastSourceMachineVertex)
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView


class SpikeSourceArrayMachineVertex(ReverseIPTagMulticastSourceMachineVertex):
    """
    Extended to add colour.
    """

    @overrides(
        ReverseIPTagMulticastSourceMachineVertex.get_n_keys_for_partition)
    def get_n_keys_for_partition(self, partition_id):
        n_keys = super().get_n_keys_for_partition(partition_id)
        n_colours = 2 ** self.app_vertex.n_colour_bits
        return n_keys * n_colours

    @overrides(ReverseIPTagMulticastSourceMachineVertex._fill_send_buffer_1d)
    def _fill_send_buffer_1d(self, key_base):
        first_time_step = SpynnakerDataView.get_first_machine_time_step()
        end_time_step = SpynnakerDataView.get_current_run_timesteps()
        if first_time_step == end_time_step:
            return
        keys = numpy.arange(key_base, key_base + self._vertex_slice.n_atoms)
        keys = keys << self.app_vertex.n_colour_bits
        colour_mask = (2 ** self.app_vertex.n_colour_bits) - 1
        for tick in sorted(self._send_buffer_times):
            if self._is_in_range(tick, first_time_step, end_time_step):
                self._send_buffer.add_keys(
                    tick, keys + (tick & colour_mask))

    @overrides(ReverseIPTagMulticastSourceMachineVertex._fill_send_buffer_2d)
    def _fill_send_buffer_2d(self, key_base):
        first_time_step = SpynnakerDataView.get_first_machine_time_step()
        end_time_step = SpynnakerDataView.get_current_run_timesteps()
        if first_time_step == end_time_step:
            return
        keys = numpy.arange(key_base, key_base + self._vertex_slice.n_atoms)
        keys = keys << self.app_vertex.n_colour_bits
        colour_mask = (2 ** self.app_vertex.n_colour_bits) - 1
        for atom in range(self._vertex_slice.n_atoms):
            for tick in sorted(self._send_buffer_times[atom]):
                if self._is_in_range(tick, first_time_step, end_time_step):
                    self._send_buffer.add_key(
                        tick, keys[atom] + (tick & colour_mask))
