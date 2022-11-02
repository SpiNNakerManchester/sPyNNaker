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
import os
import struct
import re
from spinnman.messages.eieio.data_messages import EIEIODataHeader
from data_specification.enums import DataType
from pacman.utilities.utility_calls import get_field_based_index
from spinn_front_end_common.interface.buffer_management.storage_objects \
    import BufferDatabase
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BITS_PER_WORD)
from spynnaker.pyNN.data import SpynnakerDataView

_N_BYTES_FOR_TIMESTAMP = BYTES_PER_WORD
_TWO_WORDS = struct.Struct("<II")
_NEO_DDL_FILE = os.path.join(os.path.dirname(__file__), "db.sql")


class NeoBufferDatabase(BufferDatabase):

    def __init__(self, database_file=None):
        """
        :param str database_file:
            The name of a file that contains (or will contain) an SQLite
            database holding the data.
            If omitted the default location will be used.
        """
        if database_file is None:
            database_file = self.default_database_file()

        super().__init__(database_file)
        with open(_NEO_DDL_FILE, encoding="utf-8") as f:
            sql = f.read()

        self._SQLiteDB__db.executescript(sql)

    def set_segement_data(self):
        with self.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO segment 
                (simulation_time_step_ms)
                 VALUES (?)
                """, [SpynnakerDataView.get_simulation_time_step_ms()])

    def _get_simulation_time_step_ms(self, cursor):
        for row in cursor.execute(
                """
                SELECT simulation_time_step_ms 
                FROM segment
                LIMIT 1
                """):
            return row["simulation_time_step_ms"]

    def get_population_recording_id(
            self, cursor, pop_label, variable, data_type, data_function):
        for row in cursor.execute(
                """
                SELECT pop_rec_id FROM population_recording
                WHERE label = ? AND variable = ?
                LIMIT 1
                """, (pop_label, variable)):
            return row["pop_rec_id"]
        cursor.execute(
            """
            INSERT INTO population_recording 
            (label, variable, data_type, function)
             VALUES (?, ?, ?, ?)
            """, (pop_label, variable, data_type.name, data_function))
        return cursor.lastrowid

    def get_population_metadeta(
            self, cursor, pop_label, variable):
        for row in cursor.execute(
                """
                SELECT pop_rec_id,  data_type, function
                FROM population_recording
                WHERE label = ? AND variable = ?
                LIMIT 1
                """, (pop_label, variable)):
            data_type = DataType[str(row["data_type"], 'utf-8')]
            return (row["pop_rec_id"], data_type, row["function"])

    def _get_spikes_by_region(
            self, cursor, region_id, neurons, simulation_time_step_ms,
            no_indexes, spike_times, spike_ids):
        """

        :param int region_id:
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

        record_raw = self._read_contents(cursor, region_id)

        if len(record_raw) == 0:
            return

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

    def _get_spikes(self, cursor, pop_rec_id):
        spike_times = list()
        spike_ids = list()
        simulation_time_step_ms = self._get_simulation_time_step_ms(cursor)
        rows = list(cursor.execute(
            """
            SELECT region_id, neurons_st, simple_indexes
            FROM spikes_metadata 
            WHERE pop_rec_id = ?
            """, [pop_rec_id]))
        for row in rows:
            neurons_st = str(row["neurons_st"], "utf-8")
            neurons = numpy.array(self.string_to_array(neurons_st))

            self._get_spikes_by_region(
                cursor, row["region_id"], neurons, simulation_time_step_ms,
                row["simple_indexes"], spike_times, spike_ids)

        result = numpy.column_stack((spike_ids, spike_times))
        return result[numpy.lexsort((spike_times, spike_ids))]

    def set_spikes_metadata(self, vertex, variable, region, neurons):
        with self.transaction() as cursor:
            pop_rec_id = self.get_population_recording_id(
                cursor, vertex.app_vertex.label, variable, DataType.INT32,
                "get_spikes")
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            region_id = self._get_region_id(
                cursor, placement.x, placement.y, placement.p, region)
            neurons_st = self.array_to_string(neurons)
            simple_indexes = (len(neurons) == vertex.vertex_slice.n_atoms)
            cursor.execute(
                """
                INSERT INTO spikes_metadata 
                (pop_rec_id, region_id, neurons_st, simple_indexes)
                 VALUES (?, ?, ?, ?)
                """, (pop_rec_id, region_id, neurons_st, simple_indexes))

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
        spike_data, data_missing = self.get_region_data(x, y, p, region)

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
        raw_data, data_missing = self.get_region_data(x, y, p, region)
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

    def get_matrix_data(
            self, x, y, p, region, neurons, data_type,
            simulation_time_step_ms, sampling_rate):
        # for buffering output info is taken form the buffer manager
        record_raw, missing_data = self.get_region_data(x, y, p, region)
        record_length = len(record_raw)

        # There is one column for time and one for each neuron recording
        data_row_length = len(neurons) * data_type.size
        full_row_length = data_row_length + _N_BYTES_FOR_TIMESTAMP
        n_rows = record_length // full_row_length
        row_data = numpy.asarray(record_raw, dtype="uint8").reshape(
            n_rows, full_row_length)

        time_bytes = (
            row_data[:, 0: _N_BYTES_FOR_TIMESTAMP].reshape(
                n_rows * _N_BYTES_FOR_TIMESTAMP))
        times = time_bytes.view("<i4").reshape(n_rows, 1)
        var_data = (row_data[:, _N_BYTES_FOR_TIMESTAMP:].reshape(
            n_rows * data_row_length))
        placement_data = data_type.decode_array(var_data).reshape(
            n_rows, len(neurons))
        sampling_interval = sampling_rate * simulation_time_step_ms

        return neurons, times, placement_data, sampling_interval

    def get_deta(self, pop_label, variable):
        with self.transaction() as cursor:
            pop_rec_id, data_type, function = self.get_population_metadeta(
                cursor, pop_label, variable)
            return self._get_spikes(cursor, pop_rec_id)
        # assume funct = "get_spikes"

    @staticmethod
    def array_to_string(indexes):
        if indexes is None or len(indexes) == 0:
            return ""

        previous = indexes[0]
        results = str(previous)
        in_range = False
        for index in indexes[1:]:
            if index == previous + 1:
                if not in_range:
                    results+= ":"
                    in_range = True
            else:
                if in_range:
                    results+= str(previous)
                results+= ","
                results += str(index)
                in_range = False
            previous = index
        if in_range:
           results+= str(previous)
        return results

    @staticmethod
    def string_to_array(str):
        if not str:
            return []
        results = []
        parts = re.findall("\d+[,:]*", str)
        start = None
        for part in parts:
            if part.endswith(":"):
                start = int(part[:-1])
            else:
                if part.endswith(","):
                    val = int(part[:-1])
                else:
                    val = int(part)
                if start is not None:
                    results.extend(range(start, val+1))
                    start = None
                else:
                    results.append(val)

        return results
