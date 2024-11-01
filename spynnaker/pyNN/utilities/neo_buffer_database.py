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
from __future__ import annotations
import csv
from datetime import datetime
import logging
import math
import os
import re
import struct
from typing import (
    Any, Collection, Dict, Iterable, List, Optional, Sequence, Tuple, Union,
    TYPE_CHECKING)

import numpy
from numpy import floating, integer, uint8, uint32
from numpy.typing import NDArray
import quantities
import neo  # type: ignore[import]

from spinn_utilities.log import FormatAdapter
from spinn_utilities.logger_utils import warn_once

from spinnman.messages.eieio.data_messages import EIEIODataHeader


from pacman.model.graphs.common import Slice, MDSlice
from pacman.utilities.utility_calls import get_keys

from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utility_models import (
    ReverseIPTagMulticastSourceMachineVertex)
from spinn_front_end_common.interface.buffer_management.storage_objects \
    import BufferDatabase
from spinn_front_end_common.utilities.base_database import _SqliteTypes
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BITS_PER_WORD)
from spinn_front_end_common.utilities.exceptions import ConfigurationException

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.utilities.buffer_data_type import BufferDataType
from spynnaker.pyNN.utilities.constants import SPIKES
from spynnaker.pyNN.utilities.neo_csv import NeoCsv

if TYPE_CHECKING:
    from _csv import _writer as CSVWriter
    from spynnaker.pyNN.models.common.types import Names as ConcreteNames
    from spynnaker.pyNN.models.populations.population import Population
    from .data_population import DataPopulation
    #: :meta private:
    Names = Optional[ConcreteNames]
    #: :meta private:
    ViewIndices = Union[None, Sequence[int], NDArray[integer]]
    #: :meta private:
    Annotations = Optional[Dict[str, Any]]

logger = FormatAdapter(logging.getLogger(__name__))


class NeoBufferDatabase(BufferDatabase, NeoCsv):
    """
    Extra support for Neo on top of the Database for SQLite 3.

    This is the same database as used by BufferManager but with
    extra tables and access methods added.
    """
    # pylint: disable=c-extension-no-member

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

    @staticmethod
    def _string(value: _SqliteTypes) -> str:
        if isinstance(value, (bytes, memoryview)):
            return str(value, 'utf-8')
        else:
            return str(value)

    def __init__(self, database_file: Optional[str] = None,
                 read_only: Optional[bool] = None):
        """
        :param database_file:
            The name of a file that contains (or will contain) an SQLite
            database holding the data.
            If omitted the default location will be used.
        :type database_file: None or str
        :param bool read_only:
            By default the database is read-only if given a database file.
            This allows to override that (mainly for clear)
        """
        if database_file is None:
            database_file = self.default_database_file()
            if read_only is None:
                read_only = False
        else:
            if read_only is None:
                read_only = True

        super().__init__(database_file, read_only=read_only)
        with open(self.__NEO_DDL_FILE, encoding="utf-8") as f:
            sql = f.read()

        # pylint: disable=no-member
        self._SQLiteDB__db.executescript(sql)  # type: ignore[attr-defined]

    def write_segment_metadata(self) -> None:
        """
        Writes the global information from the Views.

        This writes information held in :py:class:`SpynnakerDataView` so that
        the database is usable stand-alone.

        .. note::
            The database must be writable for this to work!
        """
        # t_stop intentionally left None to show no run data
        self.execute(
            """
            INSERT INTO segment(
                simulation_time_step_ms, segment_number, rec_datetime,
                dt, simulator)
            VALUES (?, ?, ?, ?, ?)
            """, (SpynnakerDataView.get_simulation_time_step_ms(),
                  SpynnakerDataView.get_segment_counter(),
                  datetime.now(),
                  SpynnakerDataView.get_simulation_time_step_ms(),
                  SpynnakerDataView.get_sim_name()))

    def write_t_stop(self) -> None:
        """
        Records the current run time as `t_Stop`.

        This writes information held in :py:class:`SpynnakerDataView` so that
        the database is usable stand-alone.

        .. note::
            The database must be writable for this to work!
        """
        t_stop = SpynnakerDataView.get_current_run_time_ms()
        if t_stop == 0:
            if SpynnakerDataView.get_current_run_timesteps() is None:
                return
        self.execute(
            """
            UPDATE segment
            SET t_stop = ?
            """, (t_stop,))

    def __get_segment_info(
            self) -> Tuple[int, datetime, Optional[float], float, str]:
        """
        Gets the metadata for the segment.

        :return: segment number, record time, last run time recorded,
            simulator timestep in ms, simulator name
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        for row in self.execute(
                """
                SELECT segment_number, rec_datetime, t_stop, dt, simulator
                FROM segment
                LIMIT 1
                """):
            t_str = self._string(row[self._REC_DATETIME])
            time = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S.%f")
            return (row[self._SEGMENT_NUMBER], time, row[self._T_STOP],
                    row[self._DT], self._string(row[self._SIMULATOR]))
        raise ConfigurationException(
            "No recorded data. Did the simulation run?")

    def __get_simulation_time_step_ms(self) -> float:
        """
        The simulation time step, in milliseconds.

        The value that would be/have been returned by
        SpynnakerDataView.get_simulation_time_step_ms()

        :rtype: float
        :return: The timestep
        """
        for row in self.execute(
                """
                SELECT simulation_time_step_ms
                FROM segment
                LIMIT 1
                """):
            return row["simulation_time_step_ms"]
        raise ConfigurationException("No segment data")

    def __get_population_id(
            self, pop_label: str, population: Population) -> int:
        """
        Gets an ID for this population label.
        Will create a new population if required.

        For speed does not verify the additional fields if a record already
        exists.

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        :return: The ID
        """
        for row in self.execute(
                """
                SELECT pop_id FROM population
                WHERE label = ?
                LIMIT 1
                """, (pop_label,)):
            return row["pop_id"]
        self.execute(
            """
            INSERT INTO population(
                label, first_id, description, pop_size)
            VALUES (?, ?, ?, ?)
            """, (pop_label, population.first_id, population.describe(),
                  population.size))
        rowid = self.lastrowid
        assert rowid is not None, "population must have been inserted"
        return rowid

    def __get_recording_id(
            self, pop_label: str, variable: str,
            population: Population, sampling_interval_ms: Optional[float],
            data_type: Optional[DataType], buffered_type: BufferDataType,
            units: Optional[str], n_colour_bits: int) -> int:
        """
        Gets an ID for this population and recording label combination.
        Will create a new population/recording record if required.

        For speed does not verify the additional fields if a record already
        exists.

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :param str variable:
        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        :param sampling_interval:
            The simulation time in milliseconds between sampling.
            Typically the sampling rate * simulation_timestep_ms
        :type sampling_interval_ms: float or None
        :type data_type: DataType or None
        :param BufferDataType buffered_type:
        :param str units:
        :param int n_colour_bits:
        :return: The ID
        """
        for row in self.execute(
                """
                SELECT rec_id FROM recording_view
                WHERE label = ? AND variable = ?
                LIMIT 1
                """, (pop_label, variable)):
            return row["rec_id"]
        pop_id = self.__get_population_id(pop_label, population)
        if data_type:
            data_type_name = data_type.name
        else:
            data_type_name = None
        self.execute(
            """
            INSERT INTO recording(
                pop_id, variable, data_type, buffered_type, t_start,
                sampling_interval_ms, units, n_colour_bits)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
            """, (pop_id, variable, data_type_name, str(buffered_type),
                  sampling_interval_ms, units, n_colour_bits))
        rowid = self.lastrowid
        assert rowid is not None, "recording must have been inserted"
        return rowid

    def __get_population_metadata(
            self, pop_label: str) -> Tuple[int, int, str]:
        """
        Gets the metadata for the population with this label

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :return: population size, first ID and description
        :rtype: (int, int, str)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        for row in self.execute(
                """
                SELECT pop_size, first_id, description
                FROM population
                WHERE label = ?
                LIMIT 1
                """, (pop_label,)):
            return (int(row["pop_size"]), int(row["first_id"]),
                    self._string(row["description"]))
        raise ConfigurationException(f"No metadata for {pop_label}")

    def get_population_metadata(self, pop_label: str) -> Tuple[int, int, str]:
        """
        Gets the metadata for the population with this label

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :return: population size, first id and description
        :rtype: (int, int, str)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        return self.__get_population_metadata(pop_label)

    def get_recording_populations(self) -> Tuple[str, ...]:
        """
        Gets a list of the labels of Populations recording.
        Or to be exact the ones with metadata saved so likely to be recording.

        .. note::
            These are actually the labels of the Application Vertices.
            Typically the Population label, corrected for `None` or
            duplicate values

        :return: List of population labels
        :rtype: list(str)
        """
        results = []
        for row in self.execute(
                """
                SELECT label
                FROM population
                """):
            results.append(self._string(row["label"]))
        return tuple(results)

    def get_population(self, pop_label: str) -> DataPopulation:
        """
        Gets an Object with the same data retrieval API as a Population.

        Retrieval is limited to recorded data and a little metadata needed to
        create a single Neo Segment wrapped in a Neo Block.

        .. note::
            As each database only includes data for one run (with resets
            creating another database) the structure is relatively simple.

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :return: An Object which acts like a Population for getting neo data
        :rtype: DataPopulation
        """
        # delayed import due to circular dependencies
        # pylint: disable=import-outside-toplevel
        from .data_population import DataPopulation as DataPop
        # DataPopulation validates the pop_label so no need to do here too
        return DataPop(self._database_file, pop_label)

    def get_recording_variables(self, pop_label: str) -> Tuple[str, ...]:
        """
        List of the names of variables recording.
        Or, to be exact, list of the names of variables with metadata so likely
        to be recording.

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :return: List of variable names
        """
        results: List[str] = []
        for row in self.execute(
                """
                SELECT variable
                FROM recording_view
                WHERE label = ?
                GROUP BY variable
                """, (pop_label,)):
            results.append(self._string(row["variable"]))
        return tuple(results)

    def get_recording_metadata(self, pop_label: str, variable: str) -> Tuple[
            Optional[DataType], float, Optional[str]]:
        """
        Gets the metadata ID for this population and recording label
        combination.

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :param str variable:
        :return: data_type, sampling_interval_ms, units
        :rtype: tuple(DataType, float, str)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        info = self.__get_recording_metadata(pop_label, variable)
        (_, datatype, _, _, sampling_interval_ms, _, units, _) = info
        return (datatype, sampling_interval_ms, units)

    def __get_recording_metadata(
            self, pop_label: str, variable: str) -> Tuple[
                int, Optional[DataType], BufferDataType, float, float, int,
                Optional[str], int]:
        """
        Gets the metadata id for this population and recording label
        combination.

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typical the Population label, corrected for `None` or
                duplicate values

        :param str variable:
        :return:
            id, data_type, buffered_type, t_start,
            sampling_interval_ms, pop_size, units, n_colour_bits
        :rtype:
            tuple(int, DataType, BufferedDataType, float, float, int, str, int)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        for row in self.execute(
                """
                SELECT rec_id,  data_type, buffered_type,  t_start,
                       sampling_interval_ms, pop_size, units, n_colour_bits
                FROM recording_view
                WHERE label = ? AND variable = ?
                LIMIT 1
                """, (pop_label, variable)):
            if row["data_type"]:
                data_type = DataType[self._string(row["data_type"])]
            else:
                data_type = None
            if row["units"]:
                units = self._string(row["units"])
            else:
                units = None
            buffered_type = BufferDataType[self._string(row["buffered_type"])]
            return (row["rec_id"], data_type, buffered_type, row["t_start"],
                    row["sampling_interval_ms"], row["pop_size"], units,
                    row["n_colour_bits"])
        raise ConfigurationException(
            f"No metadata for {variable} on {pop_label}")

    def __get_region_metadata(self, rec_id: int) -> Iterable[Tuple[
            int, Optional[NDArray[integer]], Slice, Optional[bool], int, int]]:
        """
        :param int rec_id:
        :return:
            region_id, neurons, vertex_slice, selective_recording, base_key,
            index
        :rtype: iterable(tuple(int, ~numpy.ndarray, Slice, bool, int, int))
        """
        index = 0
        # Need to put the rows in a list to get them to persist.
        for row in list(self.execute(
                """
                SELECT region_id, recording_neurons_st, vertex_slice, base_key
                FROM region_metadata
                WHERE rec_id = ?
                ORDER BY region_id, recording_neurons_st, vertex_slice,
                    base_key
                """, (rec_id,))):
            vertex_slice = MDSlice.from_string(
                self._string(row["vertex_slice"]))
            recording_neurons_st = row["recording_neurons_st"]
            if recording_neurons_st:
                neurons = numpy.array(
                    self.string_to_array(recording_neurons_st))
                yield (row["region_id"], neurons, vertex_slice,
                       len(neurons) != vertex_slice.n_atoms,
                       row["base_key"], index)
            else:
                yield (row["region_id"], None, vertex_slice, None,
                       row["base_key"], index)
            index += 1

    def __get_spikes_by_region(
            self, region_id: int, neurons: NDArray[integer],
            simulation_time_step_ms: float, selective_recording: bool,
            spike_times: List[float], spike_ids: List[int]) -> None:
        """
        Adds spike data for this region to the lists.

        :param int region_id: Region data came from
        :param array(int) neurons: mapping of local ID to global ID
        :param float simulation_time_step_ms:
        :param bool selective_recording: flag to say if
        :param list(float) spike_times: List to add spike times to
        :param list(int) spike_ids: List to add spike IDs to
        """
        neurons_recording = len(neurons)
        if neurons_recording == 0:
            return
        n_words = int(math.ceil(neurons_recording / BITS_PER_WORD))
        n_bytes = n_words * BYTES_PER_WORD
        n_words_with_timestamp = n_words + 1

        record_raw = self._read_recording(region_id)

        if len(record_raw) == 0:
            return

        raw_data = (
            numpy.asarray(record_raw, dtype=uint8).view(
                dtype="<i4")).reshape([-1, n_words_with_timestamp])

        record_time = (raw_data[:, 0] * simulation_time_step_ms)
        spikes = raw_data[:, 1:].byteswap().view(uint8)
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

    def __get_neuron_spikes(self, rec_id: int) -> Tuple[
            NDArray, List[int]]:
        """
        Gets the spikes for this population/recording ID.

        :param int rec_id:
        :return: numpy array of spike IDs and spike times, all IDs recording
        :rtype: tuple(~numpy.ndarray, list(int))
        """
        spike_times: List[float] = []
        spike_ids: List[int] = []
        simulation_time_step_ms = self.__get_simulation_time_step_ms()
        indexes: List[int] = []
        for region_id, neurons, _, selective_recording, _, _ in \
                self.__get_region_metadata(rec_id):
            if neurons is None or selective_recording is None:
                continue
            indexes.extend(neurons)
            self.__get_spikes_by_region(
                region_id, neurons, simulation_time_step_ms,
                selective_recording, spike_times, spike_ids)

        result = numpy.column_stack((spike_ids, spike_times))
        return result[numpy.lexsort(result.T[::-1])], indexes

    def __get_eieio_spike_by_region(
            self, region_id: int,
            simulation_time_step_ms: float, base_key: int,
            vertex_slice: Slice, n_colour_bits: int,
            results: List[NDArray]) -> NDArray[integer]:
        """
        Adds spike data for this region to the list.

        :param int region_id: Region data came from
        :param float simulation_time_step_ms:
        :param int base_key:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param int n_colour_bits:
        :param results: Where to add spike data to
        :return: all recording indexes spikes or not
        :rtype: list(int)
        """
        spike_data = self._read_recording(region_id)

        number_of_bytes_written = len(spike_data)
        offset = 0
        indices = {
            key: index for index, key in enumerate(
                get_keys(base_key, vertex_slice, n_colour_bits))}
        slice_ids = vertex_slice.get_raster_ids()
        colour_mask = (2 ** n_colour_bits) - 1
        inv_colour_mask = ~colour_mask & 0xFFFFFFFF
        while offset < number_of_bytes_written:
            length, time = self.__TWO_WORDS.unpack_from(spike_data, offset)
            time *= simulation_time_step_ms
            data_offset = offset + 2 * BYTES_PER_WORD

            eieio_header = EIEIODataHeader.from_bytestring(
                spike_data, data_offset)
            if eieio_header.eieio_type.payload_bytes > 0:
                raise ValueError("Can only read spikes as keys")

            data_offset += eieio_header.size
            timestamps = numpy.repeat([time], eieio_header.count)
            key_bytes = eieio_header.eieio_type.key_bytes
            keys = numpy.frombuffer(
                spike_data, dtype=f"<u{key_bytes}",
                count=eieio_header.count, offset=data_offset).astype(uint32)
            keys = numpy.bitwise_and(keys, inv_colour_mask)
            local_ids = numpy.array([indices[key] for key in keys])
            neuron_ids = slice_ids[local_ids]
            offset += length + 2 * BYTES_PER_WORD
            results.append(numpy.dstack((neuron_ids, timestamps))[0])

        return slice_ids

    def __get_eieio_spikes(
            self, rec_id: int, n_colour_bits: int) -> Tuple[
                NDArray, List[int]]:
        """
        Gets the spikes for this population/recording ID.

        :param int rec_id:
        :param int n_colour_bits:
        :return: numpy array of spike IDs and spike times, all IDs recording
        :rtype: tuple(~numpy.ndarray, list(int))
        """
        simulation_time_step_ms = self.__get_simulation_time_step_ms()
        results: List[NDArray] = []
        indexes: List[int] = []

        for region_id, _, vertex_slice, selective_recording, base_key, _ in \
                self.__get_region_metadata(rec_id):
            if selective_recording:
                raise NotImplementedError(
                    "Unable to handle selective recording")
            indexes.extend(self.__get_eieio_spike_by_region(
                region_id, simulation_time_step_ms,
                base_key, vertex_slice, n_colour_bits, results))

        if not results:
            return numpy.empty(shape=(0, 2)), indexes
        result = numpy.vstack(results)
        return result[numpy.lexsort((result[:, 1], result[:, 0]))], indexes

    def __get_multi_spikes_by_region(
            self, region_id: int, neurons: NDArray[integer],
            simulation_time_step_ms: float,
            spike_times: List[NDArray[floating]],
            spike_ids: List[NDArray[integer]]):
        """
        Adds spike data for this region to the lists.

        :param int region_id: Region data came from
        :param ~numpy.ndarray neurons:
        :param float simulation_time_step_ms:
        :param list(float) spike_times: List to add spike times to
        :param list(int) spike_ids: List to add spike IDs to
        """
        raw_data = self._read_recording(region_id)

        n_words = int(math.ceil(len(neurons) / BITS_PER_WORD))
        n_bytes_per_block = n_words * BYTES_PER_WORD
        offset = 0
        while offset < len(raw_data):
            time, n_blocks = self.__TWO_WORDS.unpack_from(raw_data, offset)
            offset += self.__TWO_WORDS.size
            spike_data = numpy.frombuffer(
                raw_data, dtype=uint8,
                count=n_bytes_per_block * n_blocks, offset=offset)
            offset += n_bytes_per_block * n_blocks

            spikes = spike_data.view("<i4").byteswap().view(uint8)
            bits = numpy.fliplr(numpy.unpackbits(spikes).reshape(
                (-1, 32))).reshape((-1, n_bytes_per_block * 8))
            local_indices = numpy.nonzero(bits)[1]
            indices = neurons[local_indices]
            times = numpy.repeat(
                [time * simulation_time_step_ms],
                len(indices))
            spike_ids.append(indices)
            spike_times.append(times)

    def __get_multi_spikes(self, rec_id: int) -> Tuple[
            NDArray, List[int]]:
        """
        Gets the spikes for this population/recording ID.

        :param int rec_id:
        :return: numpy array of spike IDs and spike times, all IDs recording
        :rtype: tuple(~numpy.ndarray, list(int))
        """
        spike_times_l: List[NDArray[floating]] = []
        spike_ids_l: List[NDArray[integer]] = []
        indexes: List[int] = []
        simulation_time_step_ms = self.__get_simulation_time_step_ms()
        for region_id, neurons, _, selective_recording, _, _ in \
                self.__get_region_metadata(rec_id):
            if selective_recording:
                raise NotImplementedError(
                    "Unable to handle selective recording")
            assert neurons is not None
            indexes.extend(neurons)
            self.__get_multi_spikes_by_region(
                region_id, neurons, simulation_time_step_ms,
                spike_times_l, spike_ids_l)

        if not spike_ids_l:
            return numpy.zeros((0, 2)), indexes

        spike_ids_a = numpy.hstack(spike_ids_l)
        spike_times_a = numpy.hstack(spike_times_l)
        result = numpy.dstack((spike_ids_a, spike_times_a))[0]
        return result[numpy.lexsort((spike_times_a, spike_ids_a))], indexes

    @staticmethod
    def __combine_indexes(
            view_indexes: Union[Sequence[int], NDArray[integer]],
            data_indexes: Union[Sequence[int], NDArray[integer]],
            variable: str) -> NDArray[integer]:
        """
        :param view_indexes:
        :param data_indexes:
        :param str variable:
        :return: indices
        :rtype: list
        """
        # keep just the view indexes in the data
        data_set = set(data_indexes)
        indexes = [i for i in view_indexes if i in data_set]
        # check for missing and report
        view_set = set(view_indexes)
        missing = view_set.difference(data_indexes)
        if missing:
            logger.warning("No {} available for neurons {}",
                           variable, sorted(missing))
        return numpy.array(indexes)

    def __get_spikes(
            self, rec_id: int, view_indexes: ViewIndices,
            buffer_type: BufferDataType, n_colour_bits: int,
            variable: str) -> Tuple[NDArray, NDArray[integer]]:
        """
        Gets the data as a Numpy array for one population and variable.

        :param int rec_id:
        :param list(int) view_indexes:
        :param buffer_type:
        :param int n_colour_bits:
        :param str variable:
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        :rtype: tuple(~numpy.ndarray, list(int))
        """
        if buffer_type == BufferDataType.NEURON_SPIKES:
            spikes, data_indexes = self.__get_neuron_spikes(rec_id)
        elif buffer_type == BufferDataType.EIEIO_SPIKES:
            spikes, data_indexes = self.__get_eieio_spikes(
                rec_id, n_colour_bits)
        elif buffer_type == BufferDataType.MULTI_SPIKES:
            spikes, data_indexes = self.__get_multi_spikes(rec_id)
        else:
            raise NotImplementedError(buffer_type)

        if view_indexes is None or list(view_indexes) == list(data_indexes):
            indexes = numpy.array(data_indexes)
        else:
            # keep just the view indexes in the data
            indexes = self.__combine_indexes(
                view_indexes, data_indexes, variable)
            # keep just data columns in the view
            spikes = spikes[numpy.isin(spikes[:, 0], indexes)]

        return spikes, indexes

    def __get_matrix_data_by_region(
            self, region_id: int, neurons: NDArray[integer],
            data_type: DataType) -> Tuple[
                NDArray[floating], NDArray[floating]]:
        """
        Extracts data for this region.

        :param int region_id: Region data came from
        :param array(int) neurons: mapping of local ID to global ID
        :param DataType data_type: type of data to extract
        :return: times, data
        :rtype: tuple(~numpy.ndarray, ~numpy.ndarray)
        """
        # for buffering output info is taken form the buffer manager
        record_raw = self._read_recording(region_id)
        record_length = len(record_raw)

        # There is one column for time and one for each neuron recording
        data_row_length = len(neurons) * data_type.size
        full_row_length = data_row_length + self.__N_BYTES_FOR_TIMESTAMP
        n_rows = record_length // full_row_length
        row_data = numpy.asarray(record_raw, dtype=uint8).reshape(
            n_rows, full_row_length)

        time_bytes = (
            row_data[:, 0: self.__N_BYTES_FOR_TIMESTAMP].reshape(
                n_rows * self.__N_BYTES_FOR_TIMESTAMP))
        times = time_bytes.view("<i4").reshape(n_rows, 1)
        var_data = (row_data[:, self.__N_BYTES_FOR_TIMESTAMP:].reshape(
            n_rows * data_row_length))
        placement_data = data_type.decode_array(var_data).reshape(
            n_rows, len(neurons))

        return times, placement_data

    def __get_matrix_data(
            self, rec_id: int, data_type: DataType,
            view_indexes: ViewIndices, pop_size: int,
            variable: str) -> Tuple[NDArray[floating], NDArray[integer]]:
        """
        Gets the matrix data  for this population/recording ID.

        :param int rec_id:
        :param DataType data_type: type of data to extract
        :param view_indexes:
            The indexes for which data should be returned. Or `None` for all
        :type view_indexes: list(int) or None
        :param int pop_size:
        :param str variable:
        :return: numpy array of the data, neurons
        :rtype: tuple(~numpy.ndarray, ~numpy.ndarray)
        """
        signal_array: Optional[NDArray[floating]] = None
        pop_times: Optional[NDArray[floating]] = None
        pop_neurons: List[None] = []
        indexes: List[int] = []

        for region_id, neurons, _, _, _, index in \
                self.__get_region_metadata(rec_id):
            if neurons is not None:
                pop_neurons.extend(neurons)
            else:
                indexes.append(index)
                neurons = numpy.array([index], dtype=integer)
            times, data = self.__get_matrix_data_by_region(
                region_id, neurons, data_type)
            if signal_array is None or pop_times is None:
                signal_array = data
                pop_times = times
            elif numpy.array_equal(pop_times, times):
                signal_array = numpy.append(
                    signal_array, data, axis=1)
            else:
                raise NotImplementedError("times differ")
        if signal_array is None:
            signal_array = numpy.zeros((0,), dtype=floating)

        if len(indexes) > 0:
            assert (len(pop_neurons) == 0)
            if view_indexes is not None:
                raise SpynnakerException(
                    f"{variable} data can not be extracted using a view")
            return signal_array, numpy.array(indexes)

        data_indexes = numpy.array(pop_neurons)
        if view_indexes is None:
            view_indexes = range(pop_size)
        if list(view_indexes) == list(data_indexes):
            indexes_a = numpy.array(data_indexes)
        else:
            # keep just the view indexes in the data
            indexes_a = self.__combine_indexes(
                view_indexes, data_indexes, variable)
            # keep just data columns in the view
            map_indexes = [list(data_indexes).index(i) for i in indexes_a]
            signal_array = signal_array[:, map_indexes]

        return signal_array, indexes_a

    def __get_rewires_by_region(
            self, region_id: int, vertex_slice: Slice,
            rewire_values: List[int], rewire_postids: List[int],
            rewire_preids: List[int], rewire_times: List[int],
            sampling_interval_ms: float):
        """
        Extracts rewires data for this region and adds it to the lists.

        :param int region_id: Region data came from
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            slice of this region
        :param list(int) rewire_values:
        :param list(int) rewire_postids:
        :param list(int) rewire_preids:
        :param list(int) rewire_times:
        """
        record_raw = self._read_recording(region_id)
        if len(record_raw) < 1:
            return

        raw_data = numpy.asarray(record_raw, dtype=uint8).view(
            dtype="<i4").reshape([-1, self.__REWIRING_N_WORDS])

        record_time = (raw_data[:, 0] * sampling_interval_ms)
        rewires_raw = raw_data[:, 1:]
        rew_length = len(rewires_raw)
        # rewires is 0 (elimination) or 1 (formation) in the first bit
        rewires = (rewires_raw[i][0] & self.__FIRST_BIT
                   for i in range(rew_length))
        # the post-neuron ID is stored in the next 8 bytes
        post_ids = (((int(rewires_raw[i]) >> self.__POST_ID_SHIFT) %
                     self.__POST_ID_FACTOR) + vertex_slice.lo_atom
                    for i in range(rew_length))
        # the pre-neuron ID is stored in the remaining 23 bytes
        pre_ids = (int(rewires_raw[i]) >> self.__PRE_ID_SHIFT
                   for i in range(rew_length))

        rewire_values.extend(rewires)
        rewire_postids.extend(post_ids)
        rewire_preids.extend(pre_ids)
        rewire_times.extend(record_time)

    def __get_rewires(self, rec_id: int,
                      sampling_interval_ms: float) -> NDArray[integer]:
        """
        Extracts rewires data for this region.

        :param int rec_id:
        :return: (rewire_values, rewire_postids, rewire_preids, rewire_times)
        :rtype: ~numpy.ndarray(tuple(int, int, int, int))
        """
        rewire_times: List[int] = []
        rewire_values: List[int] = []
        rewire_postids: List[int] = []
        rewire_preids: List[int] = []

        for region_id, _, vertex_slice, _, _, _ in \
                self.__get_region_metadata(rec_id):
            # as no neurons for "rewires" selective_recording will be true

            self.__get_rewires_by_region(
                region_id, vertex_slice, rewire_values, rewire_postids,
                rewire_preids, rewire_times, sampling_interval_ms)

            if len(rewire_values) == 0:
                return numpy.zeros((0, 4), dtype=integer)

        result = numpy.column_stack(
            (rewire_times, rewire_preids, rewire_postids, rewire_values))
        return result[numpy.lexsort(
            (rewire_values, rewire_postids, rewire_preids, rewire_times))]

    def __get_recorded_pynn7(
            self, rec_id: int, data_type: DataType,
            sampling_interval_ms: float, as_matrix: bool,
            view_indexes: ViewIndices, pop_size: int,
            variable: str) -> NDArray[floating]:
        """
        Get recorded data in PyNN 0.7 format. Must not be spikes.

        :param int rec_id:
        :param DataType data_type: type of data to extract
        :param float sampling_interval_ms:
        :param bool as_matrix:
        :param view_indexes:
            The indexes for which data should be returned. Or `None` for all
        :type view_indexes: list(int) or None
        :param int pop_size:
        :param str variable:
        :rtype: ~numpy.ndarray
        """
        data, indexes = self.__get_matrix_data(
            rec_id, data_type, view_indexes, pop_size, variable)

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
            self, pop_label: str, variable: str, as_matrix: bool = False,
            view_indexes: ViewIndices = None) -> NDArray[floating]:
        """
        SsPyNNaker specific method for getting data as a numpy array,
        instead of the Neo-based object

        :param str pop_label: label for the Population
        :param variable: Single variable name.
        :type variable: str or list(str)
        :param as_matrix: If set True the data is returned as a 2d matrix
        :param view_indexes: The indexes for which data should be returned.
            If ``None``, all data (view_index = data_indexes)
        :type view_indexes: None or iter(int)
        :return: array of the data
        :rtype: ~numpy.ndarray
        :raises ConfigurationException:
            If variable is a list of a length other than 1
        """
        if not isinstance(variable, str):
            if len(variable) != 1:
                raise ConfigurationException(
                    "Only one type of data at a time is supported")
            variable = variable[0]

        # called to trigger the virtual data warning if applicable
        self.__get_segment_info()
        (rec_id, data_type, buffered_type, _, sampling_interval_ms,
         pop_size, _, n_colour_bits) = \
            self.__get_recording_metadata(pop_label, variable)
        if buffered_type == BufferDataType.MATRIX:
            assert data_type is not None
            return self.__get_recorded_pynn7(
                rec_id, data_type, sampling_interval_ms,
                as_matrix, view_indexes, pop_size, variable)
        # NO BufferedDataType.REWIRES get_spike will go boom
        else:
            if as_matrix:
                logger.warning("Ignoring as matrix for {}", variable)
            return self.__get_spikes(
                rec_id, view_indexes, buffered_type,
                n_colour_bits, variable)[0]

    def get_spike_counts(
            self, pop_label: str,
            view_indexes: ViewIndices = None) -> Dict[int, int]:
        """
        Gets the spike counts for the population with this label.

        :param str pop_label: label for the Population
        :param view_indexes: If supplied indexes to retrieve.
        :type view_indexes: None or iter(int)
        :return: dict of index to count
        :rtype: dict(int, int)
        """
        # called to trigger the virtual data warning if applicable
        self.__get_segment_info()
        (rec_id, _, buffered_type, _, _, pop_size, _, n_colour_bits) = \
            self.__get_recording_metadata(pop_label, SPIKES)
        if view_indexes is None:
            view_indexes = range(pop_size)

        # get_spike will go boom if buffered_type not spikes
        spikes = self.__get_spikes(
            rec_id, view_indexes, buffered_type,
            n_colour_bits, SPIKES)[0]
        counts = numpy.bincount(spikes[:, 0].astype(dtype=numpy.int32),
                                minlength=pop_size)
        return {i: counts[i] for i in view_indexes}

    def __add_data(
            self, pop_label: str, variable: str,
            segment: neo.Segment, view_indexes: ViewIndices,
            t_stop: Optional[float]):
        """
        Gets the data as a Numpy array for one population and variable.

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :param str variable:
        :param ~neo.core.Segment segment: Segment to add data to
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        (rec_id, data_type, buffer_type, t_start, sampling_interval_ms,
         pop_size, units, n_colour_bits) = \
            self.__get_recording_metadata(pop_label, variable)

        if buffer_type == BufferDataType.MATRIX:
            assert data_type is not None
            signal_array, indexes = self.__get_matrix_data(
                rec_id, data_type, view_indexes, pop_size, variable)
            sampling_rate = 1000/sampling_interval_ms * quantities.Hz
            t_start = t_start * quantities.ms
            self._insert_matrix_data(
                variable, segment, signal_array,
                indexes, t_start, sampling_rate, units)
        elif buffer_type == BufferDataType.REWIRES:
            if view_indexes is not None:
                raise SpynnakerException(
                    f"{variable} can not be extracted using a view")
            event_array = self.__get_rewires(
                rec_id, sampling_interval_ms)
            self._insert_neo_rewirings(segment, event_array, variable)
        else:
            if view_indexes is None:
                view_indexes = range(pop_size)
            spikes, indexes = self.__get_spikes(
                rec_id, view_indexes, buffer_type,
                n_colour_bits, variable)
            sampling_rate = 1000 / sampling_interval_ms * quantities.Hz
            if t_stop is None:
                if len(spikes) == 0:
                    t_stop = 0
                    warn_once(logger, "No spike data. Setting end time to 0")
                else:
                    t_stop = numpy.amax(spikes, 0)[1]
                    warn_once(logger, "Unknown how long the simulation ran. "
                                      "So using max spike as stop time")
            self._insert_spike_data(
                view_indexes, segment, spikes, t_start, t_stop,
                sampling_rate)

    def __read_and_csv_data(
            self, pop_label: str, variable: str, csv_writer: CSVWriter,
            view_indexes: ViewIndices, t_stop: Optional[float]):
        """
        Reads the data for one variable and adds it to the CSV file.

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :param str variable:
        :param ~csv.writer csv_writer: Open CSV writer to write to
        :param view_indexes:
        :type view_indexes: None, ~numpy.array or list(int)
        """
        (rec_id, data_type, buffer_type, t_start, sampling_interval_ms,
         pop_size, units, n_colour_bits) = \
            self.__get_recording_metadata(pop_label, variable)

        if buffer_type == BufferDataType.MATRIX:
            assert data_type is not None
            self._csv_variable_metdata(
                csv_writer, self._MATRIX, variable, t_start, t_stop,
                sampling_interval_ms, units)
            signal_array, indexes = self.__get_matrix_data(
                rec_id, data_type, view_indexes, pop_size, variable)
            self._csv_matrix_data(csv_writer, signal_array, indexes)
        elif buffer_type == BufferDataType.REWIRES:
            self._csv_variable_metdata(
                csv_writer, self._EVENT, variable, t_start, t_stop,
                sampling_interval_ms, units)
            if view_indexes is not None:
                raise SpynnakerException(
                    f"{variable} can not be extracted using a view")
            event_array = self.__get_rewires(rec_id, sampling_interval_ms)
            self._csv_rewirings(csv_writer, event_array)
        else:
            self._csv_variable_metdata(
                csv_writer, self._SPIKES, variable, t_start, t_stop,
                sampling_interval_ms, units)
            spikes, indexes = self.__get_spikes(
                rec_id, view_indexes, buffer_type, n_colour_bits, variable)
            self._csv_spike_data(csv_writer, spikes, indexes)

    def __get_empty_block(
            self, pop_label: str, annotations: Annotations) -> neo.Block:
        """
        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :param variables:
            One or more variable names or `None` for all available
        :type variables: str, list(str) or None
        :param view_indexes: List of neurons IDs to include or `None` for all
        :type view_indexes: None or list(int)
        :param annotations: annotations to put on the neo block
        :type annotations: None or dict(str, ...)
        :return: The Neo block
        :rtype: ~neo.core.Block
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        _, _, _, dt, simulator = self.__get_segment_info()
        pop_size, first_id, description = \
            self.__get_population_metadata(pop_label)
        return self._insert_empty_block(
            pop_label, description, pop_size, first_id, dt, simulator,
            annotations)

    def get_empty_block(self, pop_label: str,
                        annotations: Annotations = None) -> neo.Block:
        """
        Creates a block with just metadata but not data segments.

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :param annotations: annotations to put on the neo block
        :type annotations: None or dict(str, ...)
        :return: The Neo block
        :rtype: ~neo.core.Block
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        return self.__get_empty_block(pop_label, annotations)

    def get_full_block(
            self, pop_label: str, variables: Names, view_indexes: ViewIndices,
            annotations: Annotations) -> neo.Block:
        """
        Creates a block with metadata and data for this segment.
        Any previous segments will be empty.

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :param variables:
            One or more variable names or `None` for all available
        :type variables: str, list(str) or None
        :param view_indexes: List of neurons IDs to include or `None` for all
        :type view_indexes: None or list(int)
        :param annotations: annotations to put on the neo block
        :type annotations: None or dict(str, ...)
        :return: The Neo block
        :rtype: ~neo.core.Block
        """
        block = self.__get_empty_block(pop_label, annotations)
        self.__add_segment(block, pop_label, variables, view_indexes)
        return block

    def csv_segment(
            self, csv_file: str, pop_label: str, variables: Names,
            view_indexes: ViewIndices = None):
        """
        Writes the data including metadata to a CSV file.

        :param str csv_file: Path to file to write block metadata to
        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typical the Population label, corrected for `None` or
                duplicate values

        :param variables:
            One or more variable names or `None` for all available
        :type variables: str, list(str) or None
        :param view_indexes: List of neurons IDs to include or `None` for all
        :type view_indexes: None or list(int)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        if not os.path.isfile(csv_file):
            raise SpynnakerException("PLease call csv_block_metadata first")
        with open(csv_file, 'a', newline='', encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)

            segment_number, rec_datetime, t_stop, _, _ = \
                self.__get_segment_info()
            self._csv_segment_metadata(
                csv_writer, segment_number, rec_datetime)

            for variable in self.__clean_variables(variables, pop_label):
                self.__read_and_csv_data(
                    pop_label, variable, csv_writer, view_indexes, t_stop)

    def csv_block_metadata(
            self, csv_file: str, pop_label: str,
            annotations: Annotations = None):
        """
        Writes the data including metadata to a CSV file.
        Overwrites any previous data in the file.

        :param str csv_file: Path to file to write block metadata to
        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :param annotations: annotations to put on the neo block
        :type annotations: None or dict(str, ...)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        with open(csv_file, 'w', newline='',  encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)

            _, _, _, dt, _ = self.__get_segment_info()
            pop_size, first_id, description = \
                self.__get_population_metadata(pop_label)
            self._csv_block_metadata(
                csv_writer, pop_label, dt, pop_size, first_id, description,
                annotations)

    def add_segment(
            self, block: neo.Block, pop_label: str, variables: Names,
            view_indexes: ViewIndices = None):
        """
        Adds a segment to the block.

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :param variables:
            One or more variable names or `None` for all available
        :type variables: str, list(str) or None
        :param view_indexes: List of neurons IDs to include or `None` for all
        :type view_indexes: None or list(int)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        self.__add_segment(block, pop_label, variables, view_indexes)

    def __clean_variables(
            self, variables: Names, pop_label: str) -> Tuple[str, ...]:
        if variables is None:
            vs: Tuple[str, ...] = ("all", )
        elif isinstance(variables, str):
            vs = (variables, )
        else:
            vs = tuple(variables)
        if 'all' in vs:
            return self.get_recording_variables(pop_label)
        else:
            return vs

    def __add_segment(
            self, block: neo.Block, pop_label: str,
            variables: Names, view_indexes: ViewIndices):
        """
        Adds a segment to the block.

        :param  ~neo.core.Block block:
        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :param variables:
            One or more variable names or `None` for all available
        :type variables: str, list(str) or None
        :param view_indexes: List of neurons IDs to include or `None` for all
        :type view_indexes: None or list(int)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording metadata not setup correctly
        """
        segment_number, rec_datetime, t_stop, _, _ = \
            self.__get_segment_info()
        segment = self._insert_empty_segment(
            block, segment_number, rec_datetime)

        for variable in self.__clean_variables(variables, pop_label):
            self.__add_data(
                pop_label, variable, segment, view_indexes, t_stop)

    def clear_data(self, pop_label: str, variables: Names):
        """
        Clears the data for one population and given variables.

        .. note:::
            The database must be writable for this to work!

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typical the Population label, corrected for `None` or
                duplicate values

        :param list(str) variables: names of variable to get data for
        """
        t_start = SpynnakerDataView.get_current_run_time_ms()
        variables = self.__clean_variables(variables, pop_label)
        region_ids = []
        for variable in variables:
            self.execute(
                """
                UPDATE recording SET
                    t_start = ?
                WHERE rec_id in (
                    SELECT rec_id
                    FROM recording_view
                    WHERE label = ? AND variable = ?)
                """, (t_start, pop_label, variable))

            for row in self.execute(
               """
                    SELECT region_id
                    FROM region_metadata NATURAL JOIN recording_view
                    WHERE label = ? AND variable = ?
                    """, (pop_label, variable)):
                region_ids.append(int((row["region_id"])))

        for region_id in region_ids:
            self._clear_recording_region(region_id)

    def write_metadata(self) -> None:
        """
        Write the current metadata to the database.

        The underlying call does not guarantee order
        so there order the metadata is added is not consistent,

        .. note::
            The database must be writable for this to work!
        """
        for population in SpynnakerDataView.iterate_populations():
            # pylint: disable=protected-access
            for variable in population._vertex.get_recording_variables():
                self.__write_metadata(population, variable)

    def __write_metadata(self, population: Population, variable: str):
        # pylint: disable=protected-access
        app_vertex = population._vertex
        assert app_vertex.label is not None
        buffered_data_type = \
            app_vertex.get_buffer_data_type(variable)
        data_type = app_vertex.get_data_type(variable)
        sampling_interval_ms = \
            app_vertex.get_sampling_interval_ms(variable)

        units = app_vertex.get_units(variable)
        n_colour_bits = app_vertex.n_colour_bits
        rec_id = self.__get_recording_id(
            app_vertex.label, variable,
            population, sampling_interval_ms, data_type,
            buffered_data_type, units, n_colour_bits)
        region = app_vertex.get_recording_region(variable)
        machine_vertices = app_vertex.splitter.machine_vertices_for_recording(
            variable)
        for vertex in machine_vertices:
            placement = SpynnakerDataView.get_placement_of_vertex(
                vertex)
            region_id = self._get_recording_region_id(
                placement.x, placement.y, placement.p, region)
            vertex_slice = vertex.vertex_slice
            neurons = app_vertex.get_neurons_recording(
                variable, vertex_slice)
            if neurons is None:
                recording_neurons_st = None
            elif len(neurons) == 0:
                continue
            else:
                recording_neurons_st = self.array_to_string(neurons)
            if buffered_data_type == BufferDataType.EIEIO_SPIKES:
                # Sneaky! An undeclared interface...
                assert isinstance(
                    vertex, ReverseIPTagMulticastSourceMachineVertex)
                base_key = vertex.get_virtual_key()
            else:
                base_key = None
            self.execute(
                """
                INSERT INTO region_metadata(
                    rec_id, region_id, recording_neurons_st,
                    base_key, vertex_slice)
                VALUES (?, ?, ?, ?, ?)
                """,
                (rec_id, region_id, recording_neurons_st,
                 base_key, str(vertex.vertex_slice)))

    @staticmethod
    def array_to_string(indexes: Collection[int]) -> str:
        """
        Converts a list of non-negative integers into a compact string.
        Works best if the list is sorted.

        IDs are comma separated, except when a series of IDs is sequential then
        the start:end is used.

        :param list(int) indexes:
        :rtype: str
        """
        if indexes is None or len(indexes) == 0:
            return ""

        previous = -1
        results = ""
        in_range = False
        for index in indexes:
            if previous < 0:
                previous = index
                results = str(previous)
            else:
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

    @classmethod
    def string_to_array(cls, string: str) -> List[int]:
        """
        Converts a string into a list of integers.
        Assumes the string was created by :py:meth:`array_to_string`

        :param str string:
        :rtype: list(int)
        """
        if not string:
            return []
        string = cls._string(string)
        results: List[int] = []
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
