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

from enum import (auto, Enum)
import math
import numpy
import os
import struct
import re
from spinnman.messages.eieio.data_messages import EIEIODataHeader
from data_specification.enums import DataType
from pacman.model.graphs.common import Slice
from pacman.utilities.utility_calls import get_field_based_index
from spinn_front_end_common.interface.buffer_management.storage_objects \
    import BufferDatabase
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BITS_PER_WORD)
from spynnaker.pyNN.data import SpynnakerDataView


class RetrievalFunction(Enum):
    """
    Different functions to retrieve the data.

    This class is designed to used internally by NeoBufferDatabase
    """
    Neuron_spikes = (auto())
    EIEIO_spikes = (auto())
    Multi_spike = (auto())
    Matrix = (auto())
    Rewires = (auto())

    def __str__(self):
        return self.name


class NeoBufferDatabase(BufferDatabase):

    _N_BYTES_FOR_TIMESTAMP = BYTES_PER_WORD
    _TWO_WORDS = struct.Struct("<II")
    _NEO_DDL_FILE = os.path.join(os.path.dirname(__file__), "db.sql")
    #: rewiring: shift values to decode recorded value
    _PRE_ID_SHIFT = 9
    _POST_ID_SHIFT = 1
    _POST_ID_FACTOR = 2 ** 8
    _FIRST_BIT = 1
    #: number of words per rewiring entry
    _REWIRING_N_WORDS = 2

    def __init__(self, database_file=None):
        """
        Extra support for Neo on top of the Database for SQLite 3.

        This is the same database as used by BufferManager but with
        extra tables and access methods added.

        :param database_file:
            The name of a file that contains (or will contain) an SQLite
            database holding the data.
            If omitted the default location will be used.
        :type database_file: None or str
        """
        if database_file is None:
            database_file = self.default_database_file()

        super().__init__(database_file)
        with open(self._NEO_DDL_FILE, encoding="utf-8") as f:
            sql = f.read()

        # pylint: disable=no-member
        self._SQLiteDB__db.executescript(sql)

    def write_segement_data(self):
        """
        Writes the global information from the Views

        This writes information held in SpynnakerDataView so that the database
        is usable standalone

        """
        with self.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO segment
                (simulation_time_step_ms, segment_number)
                 VALUES (?, ?)
                """, [SpynnakerDataView.get_simulation_time_step_ms(),
                      SpynnakerDataView.get_segment_counter()])

    def _get_simulation_time_step_ms(self, cursor):
        """
        The simulation time step, in milliseconds

        The value that would be/have been returned by
        SpynnakerDataView.get_simulation_time_step_ms()

        :param ~sqlite3.Cursor cursor:
        :type: Float
        """
        for row in cursor.execute(
                """
                SELECT simulation_time_step_ms
                FROM segment
                LIMIT 1
                """):
            return row["simulation_time_step_ms"]

    def _get_population_recording_id(
            self, cursor, pop_label, variable, data_type, data_function,
            sampling_interval_ms, first_id):
        """
        Gets an id for this population and recording label combination.

        Will create a new population/recording record if required.

        For speed does not verify the additional fields if a record already
        exists.

        :param ~sqlite3.Cursor cursor:
        :param str pop_label:
        :param str variable:
        :type data_type: DataType or None
        :param RetrievalFunction data_function:
        :param sampling_interval: the simulation time in ms between sampling.
            Typically the sampling rate * simulation_timestep_ms
        :type sampling_interval_ms: float or None
        :param int first_id: The ID of the first member of the population.
        """
        for row in cursor.execute(
                """
                SELECT pop_rec_id FROM population_recording
                WHERE label = ? AND variable = ?
                LIMIT 1
                """, (pop_label, variable)):
            return row["pop_rec_id"]
        if data_type:
            data_type_name = data_type.name
        else:
            data_type_name = None
        cursor.execute(
            """
            INSERT INTO population_recording
            (label, variable, data_type, function, t_start, 
            sampling_interval_ms, first_id)
            VALUES (?, ?, ?, ?, 0, ?, ?)
            """, (pop_label, variable, data_type_name, str(data_function),
                  sampling_interval_ms, first_id))
        return cursor.lastrowid

    def _get_population_metadeta(
            self, cursor, pop_label, variable):
        """
        Gets the metadata id for this population and recording label
        combination.

        :param ~sqlite3.Cursor cursor:
        :param str pop_label:
        :param str variable:
        :return: id, datatype, retrieval function type
        :rtype: (int, DataType, RetrievalFunction)
        """
        for row in cursor.execute(
                """
                SELECT pop_rec_id,  data_type, function,  t_start, 
                       sampling_interval_ms, first_id
                FROM population_recording
                WHERE label = ? AND variable = ?
                LIMIT 1
                """, (pop_label, variable)):
            if row["data_type"]:
                data_type_st = str(row["data_type"], 'utf-8')
                data_type = DataType[data_type_st]
            else:
                data_type = None
            function = RetrievalFunction[str(row["function"], 'utf-8')]
            return (row["pop_rec_id"], data_type, function, row["t_start"],
                    row["sampling_interval_ms"], row["first_id"])
        raise Exception(f"No metedata for {variable} on {pop_label}")

    def _get_spikes_by_region(
            self, cursor, region_id, neurons, simulation_time_step_ms,
            selective_recording, spike_times, spike_ids):
        """
        Adds spike data for this region to the lists

        :param ~sqlite3.Cursor cursor:
        :param int region_id: Region data came from
        :param array(int) neurons: mapping of local id to global id
        :param float simulation_time_step_ms:
        :param bool selective_recording: flag to say if
        :param list(float) spike_times: List to add spike times to
        :param list(int) spike_ids: List to add spike ids to
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
        if selective_recording:
            for time_indice, local in zip(time_indices, local_indices):
                if local < neurons_recording:
                    spike_ids.append(neurons[local])
                    spike_times.append(record_time[time_indice])
        else:
            indices = neurons[local_indices]
            times = record_time[time_indices].reshape((-1))
            spike_ids.extend(indices)
            spike_times.extend(times)

    def _get_spikes(self, cursor, pop_rec_id):
        """
        Gets the spikes for this population/recording id

        :param ~sqlite3.Cursor cursor:
        :param int pop_rec_id:
        :return: numpy array of spike ids and spike times
        :rtype  ~numpy.ndarray
        """
        spike_times = list()
        spike_ids = list()
        simulation_time_step_ms = self._get_simulation_time_step_ms(cursor)
        rows = list(cursor.execute(
            """
            SELECT region_id, neurons_st, selective_recording
            FROM spikes_metadata
            WHERE pop_rec_id = ?
            """, [pop_rec_id]))
        for row in rows:
            neurons = numpy.array(self.string_to_array(row["neurons_st"]))

            self._get_spikes_by_region(
                cursor, row["region_id"], neurons, simulation_time_step_ms,
                row["selective_recording"], spike_times, spike_ids)

        result = numpy.column_stack((spike_ids, spike_times))
        return result[numpy.lexsort((spike_times, spike_ids))]

    def write_spikes_metadata(self, vertex, variable, region, neurons,
                              sampling_interval, first_id):
        """
        Write the metadata to retrieve spikes based on just the data

        :param MachineVertex vertex: vertex which will supply the data
        :param str variable: name of the variable. typically "spikes"
        :param int region: local region this vertex will write to
        :param list(int) neurons: mapping of global neuron ids to local one
            based on position in the list
        :param float sampling_interval:
            The simulation time in ms between sampling.
            Typically the sampling rate * simulation_timestep_ms
        :param int first_id: The ID of the first member of the population.

        """
        with self.transaction() as cursor:
            pop_rec_id = self._get_population_recording_id(
                cursor, vertex.app_vertex.label, variable, DataType.INT32,
                RetrievalFunction.Neuron_spikes, sampling_interval, first_id)
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            region_id = self._get_region_id(
                cursor, placement.x, placement.y, placement.p, region)
            neurons_st = self.array_to_string(neurons)
            selective_recording = (len(neurons) != vertex.vertex_slice.n_atoms)
            cursor.execute(
                """
                INSERT INTO spikes_metadata
                (pop_rec_id, region_id, neurons_st, selective_recording)
                 VALUES (?, ?, ?, ?)
                """, (pop_rec_id, region_id, neurons_st, selective_recording))

    def _get_eieio_spike_by_region(
            self, cursor, region_id, simulation_time_step_ms, base_key,
            vertex_slice, atoms_shape, n_colour_bits, results):
        """
        Adds spike data for this region to the list

        :param ~sqlite3.Cursor cursor:
        :param int region_id: Region data came from
        :param float simulation_time_step_ms:
        :param int base_key:
        :param Slice vertex_slice:
        :param tuple(int) atoms_shape:
        :return:
        """
        spike_data = self._read_contents(cursor, region_id)

        number_of_bytes_written = len(spike_data)
        offset = 0
        indices = get_field_based_index(base_key, vertex_slice, n_colour_bits)
        slice_ids = vertex_slice.get_raster_ids(atoms_shape)
        while offset < number_of_bytes_written:
            length, time = self._TWO_WORDS.unpack_from(spike_data, offset)
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

    def _get_eieio_spikes(self, cursor, pop_rec_id):
        """
        Gets the spikes for this population/recording id

        :param ~sqlite3.Cursor cursor:
        :param int pop_rec_id:
        :return: numpy array of spike ids and spike times
        :rtype  ~numpy.ndarray
        """
        simulation_time_step_ms = self._get_simulation_time_step_ms(cursor)
        results = []

        rows = list(cursor.execute(
            """
            SELECT region_id, base_key, vertex_slice, atoms_shape, 
                   n_colour_bits
            FROM eieio_spikes_metadata
            WHERE pop_rec_id = ?
            """, [pop_rec_id]))

        for row in rows:
            vertex_slice = Slice.from_string(str(row["vertex_slice"], "utf-8"))
            atoms_shape = self.string_to_array(row["atoms_shape"])
            self._get_eieio_spike_by_region(
                cursor, row["region_id"], simulation_time_step_ms,
                row["base_key"], vertex_slice, atoms_shape,
                row["n_colour_bits"], results)

        if not results:
            return numpy.empty(shape=(0, 2))
        result = numpy.vstack(results)
        return result[numpy.lexsort((result[:, 1], result[:, 0]))]

    def write_eieio_spikes_metadata(
            self, vertex, variable, region, base_key, n_colour_bits,
            sampling_interval_ms, first_id):
        """

         Write the metadata to retrieve spikes based on just the data

        :param MachineVertex vertex: vertex which will supply the data
        :param str variable: name of the variable. typically "spikes"
        :param int region: local region this vertex will write to
        :param int base_key:base key to add to each spike index
        :param int n_colour_bits:
            The number of colour bits sent by this vertex.
        :param sampling_interval: the simulation time in ms between sampling.
            Typically the sampling rate * simulation_timestep_ms
        :type sampling_interval_ms: float or None
        :param int first_id:
            First id of the population on a whole script level
         """
        with self.transaction() as cursor:
            pop_rec_id = self._get_population_recording_id(
                cursor, vertex.app_vertex.label, variable, DataType.INT32,
                RetrievalFunction.EIEIO_spikes, sampling_interval_ms, first_id)
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            region_id = self._get_region_id(
                cursor, placement.x, placement.y, placement.p, region)

            cursor.execute(
                """
                INSERT INTO eieio_spikes_metadata
                (pop_rec_id, region_id, base_key, vertex_slice, atoms_shape,
                 n_colour_bits)
                 VALUES (?, ?, ?, ?, ?, ?)
                """,
                (pop_rec_id, region_id, base_key, str(vertex.vertex_slice),
                 str(vertex.app_vertex.atoms_shape), n_colour_bits))

    def _get_multi_spikes_by_region(
            self, cursor, region_id, simulation_time_step_ms, vertex_slice,
            atoms_shape, spike_times, spike_ids):
        """
        Adds spike data for this region to the lists

        :param ~sqlite3.Cursor cursor:
        :param int region_id: Region data came from
        :param float simulation_time_step_ms:
        :param Slice vertex_slice:
        :param tuple(int, int) atoms_shape:
        :param list(float) spike_times: List to add spike times to
        :param list(int) spike_ids: List to add spike ids to
        """
        raw_data = self._read_contents(cursor, region_id)

        n_words = int(math.ceil(vertex_slice.n_atoms / BITS_PER_WORD))
        n_bytes_per_block = n_words * BYTES_PER_WORD
        offset = 0
        neurons = vertex_slice.get_raster_ids(atoms_shape)
        while offset < len(raw_data):
            time, n_blocks = self._TWO_WORDS.unpack_from(raw_data, offset)
            offset += self._TWO_WORDS.size
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

    def _get_multi_spikes(self, cursor, pop_rec_id):
        """
        Gets the spikes for this population/recording id

        :param ~sqlite3.Cursor cursor:
        :param int pop_rec_id:
        :return: numpy array of spike ids and spike times
        :rtype  ~numpy.ndarray
        """
        spike_times = list()
        spike_ids = list()
        simulation_time_step_ms = self._get_simulation_time_step_ms(cursor)
        rows = list(cursor.execute(
            """
            SELECT region_id, vertex_slice, atoms_shape
            FROM multi_spikes_metadata
            WHERE pop_rec_id = ?
            """, [pop_rec_id]))

        for row in rows:
            vertex_slice = Slice.from_string(str(row["vertex_slice"], "utf-8"))
            atoms_shape = self.string_to_array(row["atoms_shape"])

            self._get_multi_spikes_by_region(
                cursor, row["region_id"], simulation_time_step_ms,
                vertex_slice, atoms_shape, spike_times, spike_ids)

        if not spike_ids:
            return numpy.zeros((0, 2))

        spike_ids = numpy.hstack(spike_ids)
        spike_times = numpy.hstack(spike_times)
        result = numpy.dstack((spike_ids, spike_times))[0]
        return result[numpy.lexsort((spike_times, spike_ids))]

    def write_multi_spikes_metadata(self, vertex, variable, region,
                                    sampling_interval_ms, first_id):
        """
        Write the metadata to retrieve spikes based on just the data

        :param MachineVertex vertex: vertex which will supply the data
        :param str variable: name of the variable. typically "spikes"
        :param int region: local region this vertex will write to
        :param float sampling_interval_ms:
        :param int first_id: The ID of the first member of the population.
        """
        with self.transaction() as cursor:
            pop_rec_id = self._get_population_recording_id(
                cursor, vertex.app_vertex.label, variable, DataType.INT32,
                RetrievalFunction.Multi_spike, sampling_interval_ms, first_id)
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            region_id = self._get_region_id(
                cursor, placement.x, placement.y, placement.p, region)

            cursor.execute(
                """
                INSERT INTO multi_spikes_metadata
                (pop_rec_id, region_id, vertex_slice, atoms_shape)
                 VALUES (?, ?, ?, ?)
                """,
                (pop_rec_id, region_id, str(vertex.vertex_slice),
                 str(vertex.app_vertex.atoms_shape)))

    def _get_matrix_data_by_region(
            self, cursor, region_id, neurons, data_type):
        """
        Extracts data for this region

        :param ~sqlite3.Cursor cursor:
        :param int region_id: Region data came from
        :param array(int) neurons: mapping of local id to global id
        :param DataType data_type: type of data to extract
        :return:  neurons, times, data
        :rtype: (list(int), list(float ), numpy.array
        """

        # for buffering output info is taken form the buffer manager
        record_raw = self._read_contents(cursor, region_id)
        record_length = len(record_raw)

        # There is one column for time and one for each neuron recording
        data_row_length = len(neurons) * data_type.size
        full_row_length = data_row_length + self._N_BYTES_FOR_TIMESTAMP
        n_rows = record_length // full_row_length
        row_data = numpy.asarray(record_raw, dtype="uint8").reshape(
            n_rows, full_row_length)

        time_bytes = (
            row_data[:, 0: self._N_BYTES_FOR_TIMESTAMP].reshape(
                n_rows * self._N_BYTES_FOR_TIMESTAMP))
        times = time_bytes.view("<i4").reshape(n_rows, 1)
        var_data = (row_data[:, self._N_BYTES_FOR_TIMESTAMP:].reshape(
            n_rows * data_row_length))
        placement_data = data_type.decode_array(var_data).reshape(
            n_rows, len(neurons))

        return neurons, times, placement_data

    def _get_matrix_data(
            self, cursor, pop_rec_id, data_type, sampling_interval_ms):
        """
        Gets the matrix data  for this population/recording id

        :param ~sqlite3.Cursor cursor:
        :param int pop_rec_id:
        :param DataType data_type: type of data to extract
        :param sampling_interval_ms: the simulation time in ms between sampling.
        :return: numpy array of the data, neurons, sampling_interval in ms
        ;rtype: tuple(~numpy.ndarray,list(int), float)
        """
        pop_data = None
        pop_times = None
        pop_neurons = []

        rows = list(cursor.execute(
            """
            SELECT region_id, neurons_st
            FROM matrix_metadata
            WHERE pop_rec_id = ?
            """, [pop_rec_id]))

        for row in rows:
            neurons = numpy.array(self.string_to_array(row["neurons_st"]))

            neurons, times, data = \
                self._get_matrix_data_by_region(
                    cursor, row["region_id"], neurons, data_type)

            pop_neurons.extend(neurons)
            if pop_data is None:
                pop_data = data
                pop_times = times
            elif numpy.array_equal(pop_times, times):
                pop_data = numpy.append(
                    pop_data, data, axis=1)
            else:
                raise NotImplementedError("times differ")
        indexes = numpy.array(pop_neurons)
        order = numpy.argsort(indexes)
        return pop_data[:, order], indexes[order], sampling_interval_ms

    def write_matrix_metadata(self, vertex, variable, region, neurons,
                              data_type, sampling_rate, first_id):
        """
        Write the metadata to retrieve matrix data based on just the database

        :param MachineVertex vertex: vertex which will supply the data
        :param str variable: name of the variable.
        :param int region: local region this vertex will write to
        :param list(int) neurons: mapping of global neuron ids to local one
            based on position in the list
        :param DataType data_type: type of data being recorded
        :param int sampling_rate: Sampling rate in timesteps
        :param int first_id: The ID of the first member of the population.
        """
        if len(neurons) == 0:
            return
        sampling_interval = sampling_rate * \
                            SpynnakerDataView.get_simulation_time_step_ms()
        with self.transaction() as cursor:
            pop_rec_id = self._get_population_recording_id(
                cursor, vertex.app_vertex.label, variable, data_type,
                RetrievalFunction.Matrix, sampling_interval, first_id)
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            region_id = self._get_region_id(
                cursor, placement.x, placement.y, placement.p, region)
            neurons_st = self.array_to_string(neurons)
            cursor.execute(
                """
                INSERT INTO matrix_metadata
                (pop_rec_id, region_id, neurons_st)
                 VALUES (?, ?, ?)
                """, (pop_rec_id, region_id, neurons_st))

    def _get_rewires_by_region(
            self, cursor, region_id, vertex_slice, rewire_values,
            rewire_postids, rewire_preids, rewire_times):
        """
        Extracts rewires data for this region and adds it to the lists

        :param ~sqlite3.Cursor cursor:
        :param int region_id: Region data came from
        :param Slice vertex_slice: slice of this region
        :param list(int) rewire_values:
        :param list(int) rewire_postids:
        :param list(int) rewire_preids:
        :param list(int) rewire_times:
        """
        record_raw = self._read_contents(cursor, region_id)
        if len(record_raw) > 0:
            raw_data = (
                numpy.asarray(record_raw, dtype="uint8").view(
                    dtype="<i4")).reshape([-1, self._REWIRING_N_WORDS])
        else:
            return

        record_time = (raw_data[:, 0] *
                       SpynnakerDataView.get_simulation_time_step_ms())
        rewires_raw = raw_data[:, 1:]
        rew_length = len(rewires_raw)
        # rewires is 0 (elimination) or 1 (formation) in the first bit
        rewires = [rewires_raw[i][0] & self._FIRST_BIT
                   for i in range(rew_length)]
        # the post-neuron ID is stored in the next 8 bytes
        post_ids = [((int(rewires_raw[i]) >> self._POST_ID_SHIFT) %
                    self._POST_ID_FACTOR) + vertex_slice.lo_atom
                    for i in range(rew_length)]
        # the pre-neuron ID is stored in the remaining 23 bytes
        pre_ids = [int(rewires_raw[i]) >> self._PRE_ID_SHIFT
                   for i in range(rew_length)]

        rewire_values.extend(rewires)
        rewire_postids.extend(post_ids)
        rewire_preids.extend(pre_ids)
        rewire_times.extend(record_time)

    def _get_rewires(self, cursor, pop_rec_id):
        """
        Extracts rewires data for this region a

        :param ~sqlite3.Cursor cursor:
        :param int pop_rec_id:
        :return: (rewire_values, rewire_postids, rewire_preids, rewire_times)
        :rtype: ~numpy.ndarray(tuple(int, int, int, int))
        """
        rewire_times = list()
        rewire_values = list()
        rewire_postids = list()
        rewire_preids = list()

        rows = list(cursor.execute(
            """
            SELECT region_id, vertex_slice
            FROM rewires_metadata
            WHERE pop_rec_id = ?
            """, [pop_rec_id]))

        for row in rows:
            vertex_slice = Slice.from_string(str(row["vertex_slice"], "utf-8"))

            self._get_rewires_by_region(
                cursor, row["region_id"], vertex_slice, rewire_values,
                rewire_postids, rewire_preids, rewire_times)

            if len(rewire_values) == 0:
                return numpy.zeros((0, 4), dtype="float")

            result = numpy.column_stack(
                (rewire_times, rewire_preids, rewire_postids, rewire_values))
            return result[numpy.lexsort(
                (rewire_values, rewire_postids, rewire_preids, rewire_times))]

    def write_rewires_metadata(self, vertex, variable, region, first_id):
        """
        Write the metadata to retrieve rewires data based on just the database

        :param MachineVertex vertex: vertex which will supply the data
        :param str variable: name of the variable.
        :param int region: local region this vertex will write to
        :param int first_id: The ID of the first member of the population.
        """
        with self.transaction() as cursor:
            pop_rec_id = self._get_population_recording_id(
                cursor, vertex.app_vertex.label, variable, None,
                RetrievalFunction.Rewires, None, first_id)
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            region_id = self._get_region_id(
                cursor, placement.x, placement.y, placement.p, region)
            cursor.execute(
                """
                INSERT INTO rewires_metadata
                (pop_rec_id, region_id, vertex_slice)
                 VALUES (?, ?, ?)
                """, (pop_rec_id, region_id, str(vertex.vertex_slice)))

    def get_deta(self, pop_label, variable):
        """
        Gets the data as a Numpy array for one opulation and variable

        :param str pop_label:
        :param str variable:
        :return: a numpy array with data or this variable
        :rtype  ~numpy.ndarray
        """
        with self.transaction() as cursor:
            pop_rec_id, data_type, function, t_start, sampling_interval_ms,\
            first_id = self._get_population_metadeta(
                cursor, pop_label, variable)

            if function == RetrievalFunction.Neuron_spikes:
                return self._get_spikes(cursor, pop_rec_id)
            elif function == RetrievalFunction.EIEIO_spikes:
                return self._get_eieio_spikes(cursor, pop_rec_id)
            elif function == RetrievalFunction.Multi_spike:
                return self._get_multi_spikes(cursor, pop_rec_id)
            elif function == RetrievalFunction.Matrix:
                return self._get_matrix_data(
                    cursor, pop_rec_id, data_type, sampling_interval_ms)
            elif function == RetrievalFunction.Rewires:
                return self._get_rewires(cursor, pop_rec_id)
            else:
                raise NotImplementedError(function)

    @staticmethod
    def array_to_string(indexes):
        """
        Converts a list of ints into a compact string

        Works best if the list is sorted.

        Ids are comman seperate except when a series of ids is seqential when
        the start:end is used.

        :param list(int) indexes:
        :rtype str:
        """
        if indexes is None or len(indexes) == 0:
            return ""

        previous = indexes[0]
        results = str(previous)
        in_range = False
        for index in indexes[1:]:
            if index == previous + 1:
                if not in_range:
                    results += ":"
                    in_range = True
            else:
                if in_range:
                    results += str(previous)
                results += ","
                results += str(index)
                in_range = False
            previous = index
        if in_range:
            results += str(previous)
        return results

    @staticmethod
    def string_to_array(string):
        """
        Converts a string into a list of ints

        Assumes the wtring was created by array_to_string

        :param str string:
        :rtype: list(int
        """
        if not string:
            return []
        if not isinstance(string, str):
            string = str(string, "utf-8")
        results = []
        parts = re.findall(r"\d+[,:]*", string)
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
