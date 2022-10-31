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

import math
import numpy
import struct
from spinnman.messages.eieio.data_messages import EIEIODataHeader
from pacman.utilities.utility_calls import get_field_based_index
from spinn_front_end_common.interface.buffer_management.storage_objects \
    import BufferDatabase
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BITS_PER_WORD)

_TWO_WORDS = struct.Struct("<II")


class NeoBufferDatabase(object):

    def __init__(self):
        # storage area for received data from cores
        self._db = BufferDatabase()

    def get_spikes(self, x, y, p, region, neurons, simulation_time_step_ms,
                   no_indexes):
        """

        :param int x:
        :param int y:
        :param int p:
        :param int region:
        :param array(int) neurons:
        :param float simulation_time_step_ms:
        :param bool no_indexes:
        :return:
        """
        neurons_recording = len(neurons)
        if neurons_recording == 0:
            return [], []
        n_words = int(math.ceil(neurons_recording / BITS_PER_WORD))
        n_bytes = n_words * BYTES_PER_WORD
        n_words_with_timestamp = n_words + 1

        record_raw, data_missing = self._db.get_region_data(
            x, y, p, region)

        if len(record_raw) == 0:
            return [], []

        spike_times = list()
        spike_ids = list()
        raw_data = (
            numpy.asarray(record_raw, dtype="uint8").view(
                dtype="<i4")).reshape([-1, n_words_with_timestamp])

        record_time = (raw_data[:, 0] * simulation_time_step_ms)
        spikes = raw_data[:, 1:].byteswap().view("uint8")
        bits = numpy.fliplr(numpy.unpackbits(spikes).reshape(
            (-1, 32))).reshape((-1, n_bytes * 8))
        time_indices, local_indices = numpy.where(bits == 1)
        if no_indexes:
            indices = neurons[local_indices]
            times = record_time[time_indices].reshape((-1))
            spike_ids.extend(indices)
            spike_times.extend(times)
        else:
            for time_indice, local in zip(time_indices, local_indices):
                if local < neurons_recording:
                    spike_ids.append(neurons[local])
                    spike_times.append(record_time[time_indice])
        return spike_times, spike_ids

    def get_eieio_spikes(
            self, x, y, p, region, simulation_time_step_ms,
            base_key, vertex_slice, atoms_shape):
        """

        :param int x:
        :param int y:
        :param int p:
        :param int region:
        :param float simulation_time_step_ms:
        :param int base_key:
        :param Slice vertex_slice:
        :param tuple(int) atoms_shape:
        :return:
        """
        spike_data, data_missing = self._db.get_region_data(
            x, y, p, region)

        number_of_bytes_written = len(spike_data)
        offset = 0
        indices = get_field_based_index(base_key, vertex_slice)
        slice_ids = vertex_slice.get_raster_ids(atoms_shape)
        results = []
        while offset < number_of_bytes_written:
            length, time = _TWO_WORDS.unpack_from(spike_data, offset)
            time *= simulation_time_step_ms
            data_offset = offset + 2 * BYTES_PER_WORD

            eieio_header = EIEIODataHeader.from_bytestring(
                spike_data, data_offset)
            if eieio_header.eieio_type.payload_bytes > 0:
                raise Exception("Can only read spikes as keys")

            data_offset += eieio_header.size
            timestamps = numpy.repeat([time], eieio_header.count)
            key_bytes = eieio_header.eieio_type.key_bytes
            keys = numpy.frombuffer(
                spike_data, dtype="<u{}".format(key_bytes),
                count=eieio_header.count, offset=data_offset)
            local_ids = numpy.array([indices[key] for key in keys])
            neuron_ids = slice_ids[local_ids]
            offset += length + 2 * BYTES_PER_WORD
            results.append(numpy.dstack((neuron_ids, timestamps))[0])
        return results

    def get_multi_spikes(
            self, x, y, p, region, simulation_time_step_ms, vertex_slice,
            atoms_shape):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param tuple(int) atoms_shape:
        """
        raw_data, data_missing = self._db.get_region_data(
            x, y, p, region)
        spike_ids = []
        spike_times = []

        n_words = int(math.ceil(vertex_slice.n_atoms / BITS_PER_WORD))
        n_bytes_per_block = n_words * BYTES_PER_WORD
        offset = 0
        neurons = vertex_slice.get_raster_ids(atoms_shape)
        while offset < len(raw_data):
            time, n_blocks = _TWO_WORDS.unpack_from(raw_data, offset)
            offset += _TWO_WORDS.size
            spike_data = numpy.frombuffer(
                raw_data, dtype="uint8",
                count=n_bytes_per_block * n_blocks, offset=offset)
            offset += n_bytes_per_block * n_blocks

            spikes = spike_data.view("<i4").byteswap().view("uint8")
            bits = numpy.fliplr(numpy.unpackbits(spikes).reshape(
                (-1, 32))).reshape((-1, n_bytes_per_block * 8))
            local_indices = numpy.nonzero(bits)[1]
            indices = neurons[local_indices]
            times = numpy.repeat(
                [time * simulation_time_step_ms],
                len(indices))
            spike_ids.append(indices)
            spike_times.append(times)

        return spike_times, spike_ids
