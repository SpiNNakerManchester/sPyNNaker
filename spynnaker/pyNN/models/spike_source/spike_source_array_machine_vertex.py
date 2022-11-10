# Copyright (c) 2022 The University of Manchester
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
from pacman.utilities.utility_calls import get_field_based_keys
from spinn_front_end_common.utility_models import (
    ReverseIPTagMulticastSourceMachineVertex)
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView


class SpikeSourceArrayMachineVertex(ReverseIPTagMulticastSourceMachineVertex):
    """ Extended to add colour
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
        keys = get_field_based_keys(
            key_base, self._vertex_slice, self.app_vertex.n_colour_bits)
        key_list = numpy.array(
            [keys[atom] for atom in range(self._vertex_slice.n_atoms)])
        colour_mask = (2 ** self.app_vertex.n_colour_bits) - 1
        for tick in sorted(self._send_buffer_times):
            if self._is_in_range(tick, first_time_step, end_time_step):
                self._send_buffer.add_keys(
                    tick, key_list + (tick & colour_mask))

    @overrides(ReverseIPTagMulticastSourceMachineVertex._fill_send_buffer_2d)
    def _fill_send_buffer_2d(self, key_base):
        first_time_step = SpynnakerDataView.get_first_machine_time_step()
        end_time_step = SpynnakerDataView.get_current_run_timesteps()
        if first_time_step == end_time_step:
            return
        keys = get_field_based_keys(
            key_base, self._vertex_slice, self.app_vertex.n_colour_bits)
        colour_mask = (2 ** self.app_vertex.n_colour_bits) - 1
        for atom in range(self._vertex_slice.n_atoms):
            for tick in sorted(self._send_buffer_times[atom]):
                if self._is_in_range(tick, first_time_step, end_time_step):
                    self._send_buffer.add_key(
                        tick, keys[atom] + (tick & colour_mask))
