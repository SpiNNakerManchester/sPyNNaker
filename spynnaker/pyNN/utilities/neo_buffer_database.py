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

from collections import defaultdict
from datetime import datetime
from enum import (auto, Enum)
import logging
import math
import neo
import numpy
import os
import quantities
import struct
import re
from spinn_utilities.log import FormatAdapter
from spinnman.messages.eieio.data_messages import EIEIODataHeader
from data_specification.enums import DataType
from pacman.model.graphs.common import Slice
from pacman.utilities.utility_calls import get_field_based_index
from spinn_front_end_common.interface.buffer_management.storage_objects \
    import BufferDatabase
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BITS_PER_WORD)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.constants import SPIKES

logger = FormatAdapter(logging.getLogger(__name__))


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

    __N_BYTES_FOR_TIMESTAMP = BYTES_PER_WORD
    __TWO_WORDS = struct.Struct("<II")
    __NEO_DDL_FILE = os.path.join(os.path.dirname(__file__), "db.sql")
    #: rewiring: shift values to decode recorded value
    __PRE_ID_SHIFT = 9
    __POST_ID_SHIFT = 1
    __POST_ID_FACTOR = 2 ** 8
    __FIRST_BIT = 1
    #: number of words per rewiring entry
    __REWIRING_N_WORDS = 2

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
        with open(self.__NEO_DDL_FILE, encoding="utf-8") as f:
            sql = f.read()

        # pylint: disable=no-member
        self._SQLiteDB__db.executescript(sql)

    def write_segment_metadata(self):
        """
        Writes the global information from the Views

        This writes information held in SpynnakerDataView so that the database
        is usable standalone

        """
        with self.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO segment
                (simulation_time_step_ms, segment_number, rec_datetime)
                 VALUES (?, ?, ?)
                """, [SpynnakerDataView.get_simulation_time_step_ms(),
                      SpynnakerDataView.get_segment_counter(),
                      datetime.now()])

    def write_t_stop(self):
        """
        Records the current run time as t_Stop

        This writes information held in SpynnakerDataView so that the database
        is usable standalone
        """
        t_stop = SpynnakerDataView.get_current_run_time_ms()
        with self.transaction() as cursor:
            cursor.execute(
                """
                UPDATE segment
                SET t_stop = ?
                """, (t_stop, ))

    def __get_segment_info(self, cursor):
        """
        Gets the data for the whole segment

        :param ~sqlite3.Cursor cursor:
        :return: segment number, record time, and last run time recorded
        :rtype int, datatime, float
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        for row in cursor.execute(
                """
                SELECT segment_number, rec_datetime, t_stop
                FROM segment
                LIMIT 1
                """):
            t_str = str(row["rec_datetime"], "utf-8")
            time = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S.%f")
            if row["t_stop"] is None:
                t_stop = 0
                logger.warning("Data from a virtual run will be empty")
            else:
                t_stop = int(row["t_stop"])
            return row["segment_number"], time, t_stop
        raise ConfigurationException(
            "No recorded data. Did the simulation run?")

    def __get_simulation_time_step_ms(self, cursor):
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
        raise ConfigurationException("No segment data")

    def __get_population_id(
            self, cursor, pop_label, population):
        """
        Gets an id for this population label.

        Will create a new population if required.

        For speed does not verify the additional fields if a record already
        exists.

        :param ~sqlite3.Cursor cursor:
        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        """
        for row in cursor.execute(
                """
                SELECT pop_id FROM population
                WHERE label = ?
                LIMIT 1
                """, (pop_label,)):
            return row["pop_id"]
        cursor.execute(
            """
            INSERT INTO population
            (label, first_id, description, pop_size)
            VALUES (?, ?, ?, ?)
            """, (pop_label, population.first_id, population.describe(),
                  population.size))
        return cursor.lastrowid

    def __get_recording_id(
            self, cursor, pop_label, variable, population,
            sampling_interval_ms, data_type, data_function, units=None):
        """
        Gets an id for this population and recording label combination.

        Will create a new population/recording record if required.

        For speed does not verify the additional fields if a record already
        exists.

        :param ~sqlite3.Cursor cursor:
        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :param str variable:
        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        :type data_type: DataType or None
        :param RetrievalFunction data_function:
        :param sampling_interval: the simulation time in ms between sampling.
            Typically the sampling rate * simulation_timestep_ms
        :type sampling_interval_ms: float or None
        """
        for row in cursor.execute(
                """
                SELECT rec_id FROM recording_view
                WHERE label = ? AND variable = ?
                LIMIT 1
                """, (pop_label, variable)):
            return row["rec_id"]
        pop_id = self.__get_population_id(cursor, pop_label, population)
        if data_type:
            data_type_name = data_type.name
        else:
            data_type_name = None
        cursor.execute(
            """
            INSERT INTO recording
            (pop_id, variable, data_type, function, t_start,
            sampling_interval_ms, units)
            VALUES (?, ?, ?, ?, 0, ?, ?)
            """, (pop_id, variable, data_type_name, str(data_function),
                  sampling_interval_ms, units))
        return cursor.lastrowid

    def __get_population_metadata(self, cursor, pop_label):
        """
        Gets the metadata for the population with this label

        :param ~sqlite3.Cursor cursor:
        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :return: population size, first id and description
        :rtype: (int, int, str)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        for row in cursor.execute(
                """
                SELECT pop_size, first_id, description
                FROM population
                WHERE label = ?
                LIMIT 1
                """, (pop_label,)):
            return (int(row["pop_size"]), int(row["first_id"]),
                    str(row["description"], 'utf-8'))
        raise ConfigurationException(f"No metadata for {pop_label}")

    def get_population_metdadata(self, pop_label):
        """
        Gets the metadata for the population with this label

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :return: population size, first id and description
        :rtype: (int, int, str)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        with self.transaction() as cursor:
            return self.__get_population_metadata(cursor, pop_label)

    def get_recording_populations(self):
        """
        Gets a list of the labels of Populations recording.

        Or to be exact the ones with metadata saved so likely to be recording.

            .. note::
                These are actually the labels of the Application Vertices
                Typical the Population label corrected for None or
                duplicate values

        :return: List of population labels
        :rtype: list(str)
        """
        results = []
        with self.transaction() as cursor:
            for row in cursor.execute(
                    """
                    SELECT label
                    FROM population
                    """):
                results.append(str(row["label"], 'utf-8'))
        return results

    def get_population(self, pop_label):
        """
        Gets an Object with the same data retrieval API as a Population

        Retrievable is limited to recorded data and a little metadata needed to
        create a single Neo Segment wrapped in a neo Block

            .. note::
            As each database only includes

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :return: An Object which acts like a Population for getting neo data
        :rtype: DataPopulation
        """
        # delayed import due to circular dependencies
        from .data_population import DataPopulation
        # DataPopulation validates the pop_label so no need to do hre too
        return DataPopulation(self._database_file, pop_label)

    def get_recording_variables(self, pop_label):
        """
        List of the names of variables recording

        Or to be exact list of the names of variables with metadata so likely
        to be recording

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :return: List of variable names
        """
        with self.transaction() as cursor:
            return self.__get_recording_variables(pop_label, cursor)

    def __get_recording_variables(self, pop_label, cursor):
        """

        :param ~sqlite3.Cursor cursor:
        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :return: List of variable registered as recording.
        Even if there is no data
        :rtype: list(str)
        """
        results = []
        for row in cursor.execute(
                """
                SELECT variable
                FROM recording_view
                WHERE label = ?
                GROUP BY variable
                """, (pop_label,)):
            results.append(str(row["variable"], 'utf-8'))
        return results

    def get_recording_metadeta(self, pop_label, variable):
        """
        Gets the metadata id for this population and recording label
        combination.

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :param str variable:
        :return: datatype, t_start, sampling_interval_ms, first_id, pop_size,
            units
        :rtype: (DataType, float, float, int, int, str)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        with self.transaction() as cursor:
            info = self.__get_recording_metadeta(cursor, pop_label, variable)
            (_, datatype, _, _, sampling_interval_ms, _, _, units) = info
            return (datatype, sampling_interval_ms, units)

    def __get_recording_metadeta(
            self, cursor, pop_label, variable):
        """
        Gets the metadata id for this population and recording label
        combination.

        :param ~sqlite3.Cursor cursor:
        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :param str variable:
        :return: id, datatype, retrieval function type,  t_start,
                 sampling_interval_ms, first_id, pop_size, units
        :rtype: (int, DataType, RetrievalFunction, float, float, int, int, str)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        for row in cursor.execute(
                """
                SELECT rec_id,  data_type, function,  t_start,
                       sampling_interval_ms, first_id, pop_size, units
                FROM recording_view
                WHERE label = ? AND variable = ?
                LIMIT 1
                """, (pop_label, variable)):
            if row["data_type"]:
                data_type_st = str(row["data_type"], 'utf-8')
                data_type = DataType[data_type_st]
            else:
                data_type = None
            if row["units"]:
                units = str(row["units"], 'utf-8')
            else:
                units = None
            function = RetrievalFunction[str(row["function"], 'utf-8')]
            return (row["rec_id"], data_type, function, row["t_start"],
                    row["sampling_interval_ms"], row["first_id"],
                    row["pop_size"], units)
        raise ConfigurationException(
            f"No metadata for {variable} on {pop_label}")

    def __get_spikes_by_region(
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

    def __get_neuron_spikes(self, cursor, rec_id):
        """
        Gets the spikes for this population/recording id

        :param ~sqlite3.Cursor cursor:
        :param int rec_id:
        :return: numpy array of spike ids and spike times, all ids recording
        :rtype  ~numpy.ndarray, list(int)
        """
        spike_times = list()
        spike_ids = list()
        simulation_time_step_ms = self.__get_simulation_time_step_ms(cursor)
        rows = list(cursor.execute(
            """
            SELECT region_id, recording_neurons_st, selective_recording
            FROM region_metadata
            WHERE rec_id = ?
            """, [rec_id]))
        indexes = []
        for row in rows:
            neurons = numpy.array(self.string_to_array(
                row["recording_neurons_st"]))
            indexes.extend(neurons)

            self.__get_spikes_by_region(
                cursor, row["region_id"], neurons, simulation_time_step_ms,
                row["selective_recording"], spike_times, spike_ids)

        result = numpy.column_stack((spike_ids, spike_times))
        return result[numpy.lexsort((spike_times, spike_ids))], indexes

    def write_spikes_metadata(self, vertex, variable, region, population,
                              sampling_interval_ms, neurons):
        """
        Write the metadata to retrieve spikes based on just the data

        :param MachineVertex vertex: vertex which will supply the data
        :param str variable: name of the variable. typically "spikes"
        :param int region: local region this vertex will write to
        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        :param float sampling_interval_ms:
            The simulation time in ms between sampling.
            Typically the sampling rate * simulation_timestep_ms
        :param list(int) neurons: mapping of global neuron ids to local one
            based on position in the list
        """
        with self.transaction() as cursor:
            rec_id = self.__get_recording_id(
                cursor, vertex.app_vertex.label, variable, population,
                sampling_interval_ms, DataType.INT32,
                RetrievalFunction.Neuron_spikes)
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            region_id = self._get_region_id(
                cursor, placement.x, placement.y, placement.p, region)
            recording_neurons_st = self.array_to_string(neurons)
            selective_recording = (len(neurons) != vertex.vertex_slice.n_atoms)
            cursor.execute(
                """
                INSERT INTO region_metadata
                (rec_id, region_id, recording_neurons_st, selective_recording)
                 VALUES (?, ?, ?, ?)
                """,
                (rec_id, region_id, recording_neurons_st, selective_recording))

    def __get_eieio_spike_by_region(
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
        :return: all recording indexes spikes or not
        :rtype: list(int)
        """
        spike_data = self._read_contents(cursor, region_id)

        number_of_bytes_written = len(spike_data)
        offset = 0
        indices = get_field_based_index(base_key, vertex_slice, n_colour_bits)
        slice_ids = vertex_slice.get_raster_ids(atoms_shape)
        colour_mask = (2 ** n_colour_bits) - 1
        inv_colour_mask = ~colour_mask & 0xFFFFFFFF
        while offset < number_of_bytes_written:
            length, time = self.__TWO_WORDS.unpack_from(spike_data, offset)
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
            keys = numpy.bitwise_and(keys, inv_colour_mask)
            local_ids = numpy.array([indices[key] for key in keys])
            neuron_ids = slice_ids[local_ids]
            offset += length + 2 * BYTES_PER_WORD
            results.append(numpy.dstack((neuron_ids, timestamps))[0])

        return slice_ids

    def __get_eieio_spikes(self, cursor, rec_id):
        """
        Gets the spikes for this population/recording id

        :param ~sqlite3.Cursor cursor:
        :param int rec_id:
        :return: numpy array of spike ids and spike times, all ids recording
        :rtype  ~numpy.ndarray, lis(int)
        """
        simulation_time_step_ms = self.__get_simulation_time_step_ms(cursor)
        results = []
        indexes = []

        rows = list(cursor.execute(
            """
            SELECT region_id, base_key, vertex_slice, atoms_shape,
                   n_colour_bits
            FROM region_metadata
            WHERE rec_id = ?
            """, [rec_id]))

        for row in rows:
            vertex_slice = Slice.from_string(str(row["vertex_slice"], "utf-8"))
            atoms_shape = self.string_to_array(row["atoms_shape"])
            indexes.extend(self.__get_eieio_spike_by_region(
                cursor, row["region_id"], simulation_time_step_ms,
                row["base_key"], vertex_slice, atoms_shape,
                row["n_colour_bits"], results))

        if not results:
            return numpy.empty(shape=(0, 2)), indexes
        result = numpy.vstack(results)
        return result[numpy.lexsort((result[:, 1], result[:, 0]))], indexes

    def write_eieio_spikes_metadata(
            self, vertex, variable, region, population, sampling_interval_ms,
            base_key, n_colour_bits):
        """

         Write the metadata to retrieve spikes based on just the data

        :param MachineVertex vertex: vertex which will supply the data
        :param str variable: name of the variable. typically "spikes"
        :param int region: local region this vertex will write to
        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        :param sampling_interval_ms:
            the simulation time in ms between sampling.
            Typically the sampling rate * simulation_timestep_ms
        :type sampling_interval_ms: float or None
        :param int base_key:base key to add to each spike index
        :param int n_colour_bits:
            The number of colour bits sent by this vertex.
         """
        with self.transaction() as cursor:
            rec_id = self.__get_recording_id(
                cursor, vertex.app_vertex.label, variable, population,
                sampling_interval_ms, DataType.INT32,
                RetrievalFunction.EIEIO_spikes)
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            region_id = self._get_region_id(
                cursor, placement.x, placement.y, placement.p, region)

            cursor.execute(
                """
                INSERT INTO region_metadata
                (rec_id, region_id, base_key, vertex_slice, atoms_shape,
                 n_colour_bits)
                 VALUES (?, ?, ?, ?, ?, ?)
                """,
                (rec_id, region_id, base_key, str(vertex.vertex_slice),
                 str(vertex.app_vertex.atoms_shape), n_colour_bits))

    def __get_multi_spikes_by_region(
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
        :return: all recording indexes spikes or not
        :rtype: list(int)
        """
        raw_data = self._read_contents(cursor, region_id)

        n_words = int(math.ceil(vertex_slice.n_atoms / BITS_PER_WORD))
        n_bytes_per_block = n_words * BYTES_PER_WORD
        offset = 0
        neurons = vertex_slice.get_raster_ids(atoms_shape)
        while offset < len(raw_data):
            time, n_blocks = self.__TWO_WORDS.unpack_from(raw_data, offset)
            offset += self.__TWO_WORDS.size
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

        return neurons

    def __get_multi_spikes(self, cursor, rec_id):
        """
        Gets the spikes for this population/recording id

        :param ~sqlite3.Cursor cursor:
        :param int rec_id:
        :return: numpy array of spike ids and spike times, all ids recording
        :rtype  ~numpy.ndarray, list(int)
        """
        spike_times = list()
        spike_ids = list()
        indexes = []
        simulation_time_step_ms = self.__get_simulation_time_step_ms(cursor)
        rows = list(cursor.execute(
            """
            SELECT region_id, vertex_slice, atoms_shape
            FROM region_metadata
            WHERE rec_id = ?
            """, [rec_id]))

        for row in rows:
            vertex_slice = Slice.from_string(str(row["vertex_slice"], "utf-8"))
            atoms_shape = self.string_to_array(row["atoms_shape"])

            indexes.extend(self.__get_multi_spikes_by_region(
                cursor, row["region_id"], simulation_time_step_ms,
                vertex_slice, atoms_shape, spike_times, spike_ids))

        if not spike_ids:
            return numpy.zeros((0, 2)), indexes

        spike_ids = numpy.hstack(spike_ids)
        spike_times = numpy.hstack(spike_times)
        result = numpy.dstack((spike_ids, spike_times))[0]
        return result[numpy.lexsort((spike_times, spike_ids))], indexes

    def write_multi_spikes_metadata(
            self, vertex, variable, region, population, sampling_interval_ms):
        """
        Write the metadata to retrieve spikes based on just the data

        :param MachineVertex vertex: vertex which will supply the data
        :param str variable: name of the variable. typically "spikes"
        :param int region: local region this vertex will write to
        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        :param sampling_interval_ms:
            The simulation time in ms between sampling.
            Typically the sampling rate * simulation_timestep_ms
        :type sampling_interval_ms: float or None
        """
        with self.transaction() as cursor:
            rec_id = self.__get_recording_id(
                cursor, vertex.app_vertex.label, variable, population,
                sampling_interval_ms, DataType.INT32,
                RetrievalFunction.Multi_spike)
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            region_id = self._get_region_id(
                cursor, placement.x, placement.y, placement.p, region)

            cursor.execute(
                """
                INSERT INTO region_metadata
                (rec_id, region_id, vertex_slice, atoms_shape)
                 VALUES (?, ?, ?, ?)
                """,
                (rec_id, region_id, str(vertex.vertex_slice),
                 str(vertex.app_vertex.atoms_shape)))

    def __combine_indexes(self, view_indexes, data_indexes):
        # keep just the view indexes in the data
        indexes = [i for i in view_indexes if i in data_indexes]
        # check for missing and report
        view_set = set(view_indexes)
        missing = view_set.difference(data_indexes)
        if missing:
            missing_list = list(missing)
            missing_list.sort()
            logger.warning(f"No data available for neurons {missing_list}")
        return indexes

    def __get_spikes(self, cursor, rec_id, view_indexes, function):
        """
        Gets the data as a Numpy array for one opulation and variable

        :param ~sqlite3.Cursor cursor:
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        if function == RetrievalFunction.Neuron_spikes:
            spikes, data_indexes = self.__get_neuron_spikes(cursor, rec_id)
        elif function == RetrievalFunction.EIEIO_spikes:
            spikes, data_indexes = self.__get_eieio_spikes(cursor, rec_id)
        elif function == RetrievalFunction.Multi_spike:
            spikes, data_indexes = self.__get_multi_spikes(cursor, rec_id)
        else:
            raise NotImplementedError(function)

        if list(view_indexes) == list(data_indexes):
            indexes = numpy.array(data_indexes)
        else:
            # keep just the view indexes in the data
            indexes = self.__combine_indexes(view_indexes, data_indexes)
            # keep just data columns in the view
            spikes = spikes[numpy.isin(spikes[:, 0], indexes)]

        return spikes, indexes

    def __get_matrix_data_by_region(
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
        full_row_length = data_row_length + self.__N_BYTES_FOR_TIMESTAMP
        n_rows = record_length // full_row_length
        row_data = numpy.asarray(record_raw, dtype="uint8").reshape(
            n_rows, full_row_length)

        time_bytes = (
            row_data[:, 0: self.__N_BYTES_FOR_TIMESTAMP].reshape(
                n_rows * self.__N_BYTES_FOR_TIMESTAMP))
        times = time_bytes.view("<i4").reshape(n_rows, 1)
        var_data = (row_data[:, self.__N_BYTES_FOR_TIMESTAMP:].reshape(
            n_rows * data_row_length))
        placement_data = data_type.decode_array(var_data).reshape(
            n_rows, len(neurons))

        return neurons, times, placement_data

    def __get_matrix_data(self, cursor, rec_id, data_type, view_indexes):
        """
        Gets the matrix data  for this population/recording id

        :param ~sqlite3.Cursor cursor:
        :param int rec_id:
        :param DataType data_type: type of data to extract
        :param  list(int) view_indexes:
            The indexes for which data should be returned.
        :return: numpy array of the data, neurons
        :rtype: tuple(~numpy.ndarray, list(int))
        """
        signal_array = None
        pop_times = None
        pop_neurons = []

        rows = list(cursor.execute(
            """
            SELECT region_id, recording_neurons_st
            FROM region_metadata
            WHERE rec_id = ?
            """, [rec_id]))

        for row in rows:
            neurons = numpy.array(self.string_to_array(
                row["recording_neurons_st"]))

            neurons, times, data = \
                self.__get_matrix_data_by_region(
                    cursor, row["region_id"], neurons, data_type)

            pop_neurons.extend(neurons)
            if signal_array is None:
                signal_array = data
                pop_times = times
            elif numpy.array_equal(pop_times, times):
                signal_array = numpy.append(
                    signal_array, data, axis=1)
            else:
                raise NotImplementedError("times differ")
        data_indexes = numpy.array(pop_neurons)
        if signal_array is None:
            signal_array = []

        if list(view_indexes) == list(data_indexes):
            indexes = numpy.array(data_indexes)
        else:
            # keep just the view indexes in the data
            indexes = self.__combine_indexes(view_indexes, data_indexes)
            # keep just data columns in the view
            map_indexes = [list(data_indexes).index(i) for i in indexes]
            signal_array = signal_array[:, map_indexes]

        return signal_array, indexes

    def write_matrix_metadata(self, vertex, variable, region, population,
                              sampling_interval_ms, neurons, data_type):
        """
        Write the metadata to retrieve matrix data based on just the database

        :param MachineVertex vertex: vertex which will supply the data
        :param str variable: name of the variable.
        :param int region: local region this vertex will write to
        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        :param sampling_interval_ms:
            The simulation time in ms between sampling.
            Typically the sampling rate * simulation_timestep_ms
        :param list(int) neurons: mapping of global neuron ids to local one
            based on position in the list
        :param DataType data_type: type of data being recorded
        """
        if len(neurons) == 0:
            return
        with self.transaction() as cursor:
            rec_id = self.__get_recording_id(
                cursor, vertex.app_vertex.label, variable, population,
                sampling_interval_ms, data_type, RetrievalFunction.Matrix,
                vertex.app_vertex.get_units(variable))
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            region_id = self._get_region_id(
                cursor, placement.x, placement.y, placement.p, region)
            recording_neurons_st = self.array_to_string(neurons)
            cursor.execute(
                """
                INSERT INTO region_metadata
                (rec_id, region_id, recording_neurons_st)
                 VALUES (?, ?, ?)
                """, (rec_id, region_id, recording_neurons_st))

    def __get_rewires_by_region(
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
                    dtype="<i4")).reshape([-1, self.__REWIRING_N_WORDS])
        else:
            return

        record_time = (raw_data[:, 0] *
                       SpynnakerDataView.get_simulation_time_step_ms())
        rewires_raw = raw_data[:, 1:]
        rew_length = len(rewires_raw)
        # rewires is 0 (elimination) or 1 (formation) in the first bit
        rewires = [rewires_raw[i][0] & self.__FIRST_BIT
                   for i in range(rew_length)]
        # the post-neuron ID is stored in the next 8 bytes
        post_ids = [((int(rewires_raw[i]) >> self.__POST_ID_SHIFT) %
                     self.__POST_ID_FACTOR) + vertex_slice.lo_atom
                    for i in range(rew_length)]
        # the pre-neuron ID is stored in the remaining 23 bytes
        pre_ids = [int(rewires_raw[i]) >> self.__PRE_ID_SHIFT
                   for i in range(rew_length)]

        rewire_values.extend(rewires)
        rewire_postids.extend(post_ids)
        rewire_preids.extend(pre_ids)
        rewire_times.extend(record_time)

    def __get_rewires(self, cursor, rec_id):
        """
        Extracts rewires data for this region a

        :param ~sqlite3.Cursor cursor:
        :param int rec_id:
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
            FROM region_metadata
            WHERE rec_id = ?
            """, [rec_id]))

        for row in rows:
            vertex_slice = Slice.from_string(str(row["vertex_slice"], "utf-8"))

            self.__get_rewires_by_region(
                cursor, row["region_id"], vertex_slice, rewire_values,
                rewire_postids, rewire_preids, rewire_times)

            if len(rewire_values) == 0:
                return numpy.zeros((0, 4), dtype="float")

            result = numpy.column_stack(
                (rewire_times, rewire_preids, rewire_postids, rewire_values))
            return result[numpy.lexsort(
                (rewire_values, rewire_postids, rewire_preids, rewire_times))]

    def write_rewires_metadata(self, vertex, variable, region, population):
        """
        Write the metadata to retrieve rewires data based on just the database

        :param MachineVertex vertex: vertex which will supply the data
        :param str variable: name of the variable.
        :param int region: local region this vertex will write to
        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        """
        with self.transaction() as cursor:
            rec_id = self.__get_recording_id(
                cursor, vertex.app_vertex.label, variable, population, None,
                None, RetrievalFunction.Rewires)
            placement = SpynnakerDataView.get_placement_of_vertex(vertex)
            region_id = self._get_region_id(
                cursor, placement.x, placement.y, placement.p, region)
            cursor.execute(
                """
                INSERT INTO region_metadata
                (rec_id, region_id, vertex_slice)
                 VALUES (?, ?, ?)
                """, (rec_id, region_id, str(vertex.vertex_slice)))

    def get_data(self, pop_label, variable, view_indexes):
        """
        Gets the data as a Numpy array for one population and variable

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :param str variable: name of variable to get data for
        :return: a numpy array with data or this variable
        :rtype  ~numpy.ndarray
        """
        with self.transaction() as cursor:
            # called to trigger the virtual data warning if applicable
            self.__get_segment_info(cursor)
            (rec_id, data_type, function, t_start, sampling_interval_ms,
             first_id, pop_size, units) = self.__get_recording_metadeta(
                cursor, pop_label, variable)
            if view_indexes is None:
                view_indexes = range(pop_size)

            if function == RetrievalFunction.Matrix:
                data, indexes = self.__get_matrix_data(
                    cursor, rec_id, data_type, view_indexes)
                return data, indexes, sampling_interval_ms
            elif function == RetrievalFunction.Rewires:
                return self.__get_rewires(cursor, rec_id)
            else:
                return self.__get_spikes(
                    cursor, rec_id, view_indexes, function)[0]

    def __get_recorded_pynn7(
            self, cursor, rec_id, data_type, sampling_interval_ms,
            as_matrix, view_indexes):
        """ Get recorded data in PyNN 0.7 format. Must not be spikes.

        :param list(int) view_indexes:
            The indexes for which data should be returned.
        :rtype: ~numpy.ndarray
        """
        data, indexes = self.__get_matrix_data(
            cursor, rec_id, data_type, view_indexes)

        if as_matrix:
            return data

        # Convert to triples as Pynn 0,7 did
        n_machine_time_steps = len(data)
        n_neurons = len(indexes)
        column_length = n_machine_time_steps * n_neurons
        times = [i * sampling_interval_ms
                 for i in range(0, n_machine_time_steps)]
        return numpy.column_stack((
                numpy.repeat(indexes, n_machine_time_steps, 0),
                numpy.tile(times, n_neurons),
                numpy.transpose(data).reshape(column_length)))

    def spinnaker_get_data(
            self, pop_label, variable, as_matrix=False, view_indexes=None):
        if not isinstance(variable, str):
            if len(variable) != 1:
                raise ConfigurationException(
                    "Only one type of data at a time is supported")
            variable = variable[0]

        with self.transaction() as cursor:
            # called to trigger the virtual data warning if applicable
            self.__get_segment_info(cursor)
            (rec_id, data_type, function, t_start, sampling_interval_ms,
             first_id, pop_size, units) = self.__get_recording_metadeta(
                cursor, pop_label, variable)
            if view_indexes is None:
                view_indexes = range(pop_size)

            if function == RetrievalFunction.Matrix:
                return self.__get_recorded_pynn7(
                    cursor, rec_id, data_type, sampling_interval_ms,
                    as_matrix, view_indexes)
            # NO RetrievalFunction.Rewires get_spike will go boom
            else:
                if as_matrix:
                    logger.warning(f"Ignoring as matrix for {variable}")
                return self.__get_spikes(
                    cursor, rec_id, view_indexes, function)[0]

    def get_spike_counts(self, pop_label, view_indexes=None):
        with self.transaction() as cursor:
            # called to trigger the virtual data warning if applicable
            self.__get_segment_info(cursor)
            (rec_id, data_type, function, t_start, sampling_interval_ms,
             first_id, pop_size, units) = self.__get_recording_metadeta(
                cursor, pop_label, SPIKES)
            if view_indexes is None:
                view_indexes = range(pop_size)

            # get_spike will go boom if function not spikes
            spikes = self.__get_spikes(
                    cursor, rec_id, view_indexes, function)[0]
        counts = numpy.bincount(spikes[:, 0].astype(dtype=numpy.int32),
                                minlength=pop_size)
        return {i: counts[i] for i in view_indexes}

    def __add_spike_data(
            self, pop_label, view_indexes, segment, spikes, t_start, t_stop,
            sampling_interval_ms, first_id):
        """

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :param list(int) view_indexes:
        :param Segment segment:
        :param ~numpy.ndarray spikes:
        :param float t_start:
        :param float t_stop:
        :param float sampling_interval_ms:
        :param int first_id:
        """
        times = defaultdict(list)
        for neuron_id, time in spikes:
            times[int(neuron_id)].append(time)

        for index in view_indexes:
            spiketrain = neo.SpikeTrain(
                times=times[index],
                t_start=t_start,
                t_stop=t_stop,
                units='ms',
                sampling_interval=sampling_interval_ms,
                source_population=pop_label,
                source_id=index + first_id,
                source_index=index)
            segment.spiketrains.append(spiketrain)

    @staticmethod
    def __get_channel_index(ids, block):
        """

        :param list(int) ids:
        :param ~neo.core.Block block: neo block
        :rtype: ~neo.core.ChannelIndex
        """
        for channel_index in block.channel_indexes:
            if numpy.array_equal(channel_index.index, ids):
                return channel_index
        count = len(block.channel_indexes)
        channel_index = neo.ChannelIndex(
            name="Index {}".format(count), index=ids)
        block.channel_indexes.append(channel_index)
        return channel_index

    def __add_matix_data(
            self, pop_label, variable, block, segment, signal_array,
            indexes, t_start, sampling_interval_ms,
            units, first_id):
        """ Adds a data item that is an analog signal to a neo segment

         :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values
        :param str variable: the variable name
        :param ~neo.core.Block block: Block tdata is being added to
        :param ~neo.core.Segment segment: Segment to add data to
        :param ~numpy.ndarray signal_array: the raw signal data
        :param list(int) indexes: The indexes for the data
        :type t_start: float or int
        :param sampling_interval_ms: how often a neuron is recorded
        :type sampling_interval_ms: float or int
        :param units: the units of the recorded value
        :type units: quantities.quantity.Quantity or str
        :param int first_id:
        :return:
        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        """
        # pylint: disable=too-many-arguments, no-member
        t_start = t_start * quantities.ms
        sampling_period = sampling_interval_ms * quantities.ms

        ids = list(map(lambda x: x+first_id, indexes))
        if units is None:
            units = "dimensionless"
        data_array = neo.AnalogSignal(
            signal_array,
            units=units,
            t_start=t_start,
            sampling_period=sampling_period,
            name=variable,
            source_population=pop_label,
            source_ids=ids)
        channel_index = self.__get_channel_index(indexes, block)
        data_array.channel_index = channel_index
        data_array.shape = (data_array.shape[0], data_array.shape[1])
        segment.analogsignals.append(data_array)
        channel_index.analogsignals.append(data_array)

    def __add_neo_events(
            self, segment, event_array, variable, recording_start_time):
        """ Adds data that is events to a neo segment.

        :param ~neo.core.Segment segment: Segment to add data to
        :param ~numpy.ndarray event_array: the raw "event" data
        :param str variable: the variable name
        :param recording_start_time: when recording started
        :type recording_start_time: float or int
        """
        # pylint: disable=too-many-arguments, no-member
        t_start = recording_start_time * quantities.ms

        formation_times = []
        formation_labels = []
        formation_annotations = dict()
        elimination_times = []
        elimination_labels = []
        elimination_annotations = dict()

        for i in range(len(event_array)):
            event_time = t_start + event_array[i][0] * quantities.ms
            pre_id = int(event_array[i][1])
            post_id = int(event_array[i][2])
            if event_array[i][3] == 1:
                formation_times.append(event_time)
                formation_labels.append(
                    str(pre_id) + "_" + str(post_id) + "_formation")
            else:
                elimination_times.append(event_time)
                elimination_labels.append(
                    str(pre_id) + "_" + str(post_id) + "_elimination")

        formation_event_array = neo.Event(
            times=formation_times,
            labels=formation_labels,
            units="ms",
            name=variable + "_form",
            description="Synapse formation events",
            array_annotations=formation_annotations)

        elimination_event_array = neo.Event(
            times=elimination_times,
            labels=elimination_labels,
            units="ms",
            name=variable + "_elim",
            description="Synapse elimination events",
            array_annotations=elimination_annotations)

        segment.events.append(formation_event_array)
        segment.events.append(elimination_event_array)

    def __add_deta(self, cursor, pop_label, variable, block, segment,
                   view_indexes, t_stop):
        """
        Gets the data as a Numpy array for one opulation and variable

        :param ~sqlite3.Cursor cursor:
        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :param str variable:
        :param ~neo.core.Block block: neo block
        :param ~neo.core.Segment segment: Segment to add data to
        :param float t_stop
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        (rec_id, data_type, function, t_start, sampling_interval_ms,
         first_id, pop_size, units) = self.__get_recording_metadeta(
            cursor, pop_label, variable)

        if view_indexes is None:
            view_indexes = range(pop_size)

        if function == RetrievalFunction.Matrix:
            signal_array, indexes = self.__get_matrix_data(
                cursor, rec_id, data_type, view_indexes)
            self.__add_matix_data(
                pop_label, variable, block, segment, signal_array,
                indexes, t_start, sampling_interval_ms,
                units, first_id)
        elif function == RetrievalFunction.Rewires:
            event_array = self.__get_rewires(cursor, rec_id)
            self.__add_neo_events(segment, event_array, variable, t_start)
        else:
            spikes, indexes = self.__get_spikes(
                cursor, rec_id, view_indexes, function)
            self.__add_spike_data(
                pop_label, view_indexes, segment, spikes, t_start, t_stop,
                sampling_interval_ms, first_id)

    def get_block(self, pop_label, variables, view_indexes=None,
                  annotations=None):
        """

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :param variables: One or more variable names or None for all available
        :type variables: str, list(str) or None
        :param view_indexes: List of neurons ids to include or None for all
        :type view_indexes: None or list(int)
        :param annotations: annotations to put on the neo block
        :type annotations: None or dict(str, ...)
        :return: The Neo block
        :rtype: ~neo.core.Block
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        block = neo.Block()

        block.name = pop_label
        with self.transaction() as cursor:
            segment_number, rec_datetime, t_stop = \
                self.__get_segment_info(cursor)
            pop_size, first_id, description = \
                self.__get_population_metadata(cursor, pop_label)
            block.description = description
            # pylint: disable=no-member
            block.rec_datetime = rec_datetime

            metadata = {
                'size': pop_size,
                'first_index': 0,
                'last_index': pop_size,
                'first_id': first_id,
                'last_id': first_id + pop_size,
                'label': pop_label,
                'simulator': SpynnakerDataView.get_sim_name()
            }
            metadata['dt'] = t_stop
            metadata['mpi_processes'] = 1  # meaningless on Spinnaker
            block.annotate(**metadata)
            if annotations:
                block.annotate(**annotations)

        self.__add_segment(
            cursor, block, pop_label, variables, view_indexes)
        return block

    def add_segment(self, block, pop_label, variables, view_indexes=None):
        """
        Adds a segment to the block

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :param variables: One or more variable names or None for all available
        :type variables: str, list(str) or None
        :param view_indexes: List of neurons ids to include or None for all
        :type view_indexes: None or list(int)
        :return: Segment with the requested data
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        with self.transaction() as cursor:
            self.__add_segment(
                cursor, block, pop_label, variables, view_indexes)

    def __add_segment(self, cursor, block, pop_label, variables, view_indexes):
        """
        Adds a segment to the block

        :param ~sqlite3.Cursor cursor:
        :param  ~neo.core.Block block:
        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :param variables: One or more variable names or None for all available
        :type variables: str, list(str) or None
        :param view_indexes: List of neurons ids to include or None for all
        :type view_indexes: None or list(int)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        segment_number, rec_datetime, t_stop = \
            self.__get_segment_info(cursor)
        segment = neo.Segment(
            name="segment{}".format(segment_number),
            description=block.description,
            rec_datetime=rec_datetime)
        for i in range(len(block.segments), segment_number):
            block.segments.append(neo.Segment(
                name="segment{}".format(i),
                description="empty"))

        if isinstance(variables, str):
            variables = [variables]
        if 'all' in variables:
            variables = None
        if variables is None:
            variables = self.__get_recording_variables(pop_label, cursor)

        for variable in variables:
            self.__add_deta(cursor, pop_label, variable, block, segment,
                            view_indexes, t_stop)
        if segment_number in block.segments:
            block.segments[segment_number] = segment
        else:
            block.segments.append(segment)

    def clear_data(self, pop_label, variables):
        """
        Gets the data as a Numpy array for one population and variable

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex
                Typical the Population label corrected for None or
                duplicate values

        :param list(str) variables: names of variable to get data for
        """
        with self.transaction() as cursor:
            for variable in variables:
                cursor.execute(
                    """
                    UPDATE region SET
                        content = CAST('' AS BLOB), content_len = 0,
                        fetches = 0, append_time = NULL
                    WHERE region_id in
                        (SELECT region_id
                        FROM region_metadata NATURAL JOIN recording_view
                        WHERE label = ? AND variable = ?)
                    """, (pop_label, variable))
                cursor.execute(
                    """
                    DELETE FROM region_extra
                    WHERE region_id in
                        (SELECT region_id
                        FROM region_metadata NATURAL JOIN recording_view
                        WHERE label = ? AND variable = ?)
                    """, (pop_label, variable))

    @staticmethod
    def array_to_string(indexes):
        """
        Converts a list of ints into a compact string

        Works best if the list is sorted.

        Ids are comma separated except when a series of ids is sequential then
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

        Assumes the string was created by array_to_string

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
