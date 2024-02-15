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
from collections import defaultdict
import csv
from datetime import datetime
import logging
from neo import AnalogSignal, Block, Event, Segment, SpikeTrain
import numpy
from numpy import integer, float64
from numpy.typing import NDArray
from quantities import Quantity, ms
from typing import (
    Any, Dict, Iterable, List, Optional, Tuple, Union, TYPE_CHECKING)
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.data import SpynnakerDataView
if TYPE_CHECKING:
    from _csv import _writer as CSVWriter, _reader as CSVReader
    from spynnaker.pyNN.utilities.neo_buffer_database import Annotations

logger = FormatAdapter(logging.getLogger(__name__))


class NeoCsv(object):
    """
    Code to read a csv file and create a neo object.

    """
    # pylint: disable=c-extension-no-member, no-member

    _POPULATION = "population"
    _DESCRIPTION = "description"
    _SIZE = "size"
    _FIRST_ID = "first_id"
    _SIMULATOR = "simulator"
    _DT = "dt"  # t_stop

    _INDEXES = "indexes"
    _NO_INTERSECTION = "no intersection between recording and view indexes"

    _SEGMENT_NUMBER = 'segment_number'
    _REC_DATETIME = "rec_datetime"

    _T_START = "t_start"
    _T_STOP = "t_stop"
    _SAMPLING_PERIOD = "sampling_period"
    _UNITS = "units"

    _MATRIX = "matrix"

    _EVENT = "event"
    _ELMINATION = "elimination"
    _FORMATION = "formation"

    _SPIKES = "spikes"

    def _csv_variable_metdata(
            self, csv_writer: CSVWriter, variable_type: str, variable: str,
            t_start: float, t_stop: float, sampling_interval_ms: float,
            units: Optional[str]):
        """
        Writes the metadata for a variable to CSV

        :param ~csv.writer csv_writer: Open CSV writer to write to
        :param str variable_type:
        :param str variable:
        :param float t_start:
        :param float t_stop:
        :param float sampling_interval_ms:
        :param str units:
        """
        csv_writer.writerow([variable_type, variable])
        csv_writer.writerow([self._T_START, t_start * ms])
        csv_writer.writerow([self._T_STOP, t_stop * ms])
        sampling_period = sampling_interval_ms * ms
        csv_writer.writerow([self._SAMPLING_PERIOD, sampling_period])
        if units is None:
            units = "dimensionless"
        csv_writer.writerow([self._UNITS, units])
        csv_writer.writerow([])

    def __quantify(self, as_str: str) -> Quantity:
        """
        Converts a String into a quantities.Quantity

        The String should be a float, a space and a Quantities label

        :param str as_str: String representation of a quantity.
        :return: A Quantities object
        :rtype: ~quantities.Quantity
        """
        parts = as_str.split(" ")
        return Quantity(float(parts[0]), units=parts[1])

    def __read_variable_metadata(self, csv_reader: CSVReader) -> Tuple[
            Quantity, Quantity, Quantity, str]:
        """
        Reads a block of metadata, formats it and returns it as a dict

        A block is a number of rows each of exactly 2 values followed by an
        empty row

        :param ~csv.reader csv_reader: Open CSV writer to read from
        :return: t_start, t_stop, sampling_period, units
        :rtype: tuple(~quantities.Quantity, ~quantities.Quantity,
            ~quantities.Quantity, str)
        """
        metadata = self.__read_metadata(csv_reader)
        return (
            self.__quantify(metadata[self._T_START]),
            self.__quantify(metadata[self._T_STOP]),
            self.__quantify(metadata[self._SAMPLING_PERIOD]),
            metadata[self._UNITS])

    def __read_signal_array(self, csv_reader: CSVReader) -> NDArray[float64]:
        """
        Reads a block of data and converts it in a numpy array.

        A block is a number of rows followed by an empty row.
        All rows must have the same length.
        The assumption is that all values in the block represent floats.

        :param ~csv.writer csv_writer: Open CSV writer to read from
        :return: Numpy signal array of floats
        :rtype: ~numpy.array
        """
        rows = []
        row = next(csv_reader)
        while len(row) > 0:
            rows.append(row)
            row = next(csv_reader)
        return numpy.asarray(rows, dtype=float64)

    def __csv_indexes(self, indexes: NDArray[integer], csv_writer: CSVWriter):
        """
        Writes the indexes for which there could be data to the CSV.

        The indexes will be the intersection of the view used to record
        and the view used to write the CSV.

        If there is no indexes this will write the NO_INTERESTION string

        There may be a case where this writes indexes and then there is still
        no data below. This happens when the data is an empty array
        such as no spikes or rewires happened or the run was for time 0

        :param ~csv.writer csv_writer: Open CSV writer to write to
        :param list(int) indexes:
        """
        if len(indexes) > 0:
            csv_writer.writerow(indexes)
        else:
            csv_writer.writerow([self._NO_INTERSECTION])

    def __read_indexes(self, csv_reader: CSVReader) -> NDArray[integer]:
        """
        Reads the index or NO_INTERSECTION string from the CSV

        :param ~csv.writer csv_writer: Open CSV writer to read from
        :return: list of indexes
        :rtype: list(int)
        """
        row = next(csv_reader)
        assert len(row) > 0
        if len(row) == 1:
            if row[0] == self._NO_INTERSECTION:
                return numpy.array([], dtype=int)
        return numpy.asarray(row, dtype=int)

    def _insert_spike_data(
            self, view_indexes: Iterable[int], segment: Segment,
            spikes: NDArray, t_start: float, t_stop: float,
            sampling_rate: Quantity):
        """
        Creates the SpikeTrains and inserts then into the segment

        :param str pop_label: The label for the population of interest

            .. note::
                This is actually the label of the Application Vertex.
                Typically the Population label, corrected for `None` or
                duplicate values

        :param list(int) view_indexes:
        :param Segment segment:
        :param ~numpy.ndarray spikes:
        :param float t_start:
        :param float t_stop:
        :param ~quantities.Quantity sampling_rate: Rate a neuron is recorded
        """
        block = segment.block
        first_id = block.annotations[self._FIRST_ID]
        times = defaultdict(list)
        for neuron_id, time in spikes:
            times[int(neuron_id)].append(time)

        for index in view_indexes:
            spiketrain = SpikeTrain(
                times=times[index],
                t_start=t_start,
                t_stop=t_stop,
                units=ms,
                dtype=float64,
                sampling_rate=sampling_rate,
                source_population=block.name,
                source_id=index + first_id,
                source_index=index)
            segment.spiketrains.append(spiketrain)

    def _csv_spike_data(self, csv_writer: CSVWriter, spikes: NDArray,
                        indexes: NDArray[integer]):
        """
        Writes the spikes to the CSV file.

        :param ~csv.writer csv_writer: Open CSV writer to write to
        :param ~numpy.ndarray spikes:
        :param list(int) indexes: The indexes for which there could be data
        """
        self.__csv_indexes(indexes, csv_writer)
        csv_writer.writerows(spikes)
        csv_writer.writerow([])

    def __read_spike_data(
            self, csv_reader: CSVReader, segment: Segment, variable: str):
        """
        Reads spikes from the CSV file and add SpikeTrains to the segment.

        :param ~csv.reader csv_reader: Open CSV writer to read from
        :param Segment segment:
        :param str variable: Name of the variable being read
        """
        try:
            t_start, t_stop, sampling_period, _ = \
                self.__read_variable_metadata(csv_reader)
            indexes = self.__read_indexes(csv_reader)
            spikes = self.__read_signal_array(csv_reader)
            sampling_rate = 1000 / sampling_period
            self._insert_spike_data(
                indexes, segment, spikes, t_start, t_stop, sampling_rate)
        except KeyError as ex:
            logger.exception("Metadata for {} is missing {}. "
                             "So this data will be skipped", variable, ex)
            return

    def _insert_matrix_data(
            self, variable: str, segment: Segment, signal_array: NDArray,
            indexes: NDArray[integer], t_start: float, sampling_rate: Quantity,
            units: Union[Quantity, str, None]):
        """
        Adds a data item that is an analog signal to a neo segment.

        :param str variable: the variable name
        :param ~neo.core.Segment segment: Segment to add data to
        :param ~numpy.ndarray signal_array: the raw signal data
        :param list(int) indexes: The indexes for the data
        :type t_start: float or int
        :param ~quantities.Quantity sampling_rate: Rate a neuron is recorded
        :param units: the units of the recorded value
        :type units: quantities.quantity.Quantity or str
        """
        # pylint: disable=too-many-arguments
        block = segment.block

        first_id: int = block.annotations[self._FIRST_ID]

        ids = list(indexes + first_id)
        if units is None:
            units = "dimensionless"
        data_array = AnalogSignal(
            signal_array,
            units=units,
            t_start=t_start,
            sampling_rate=sampling_rate,
            name=variable,
            source_population=block.name,
            source_ids=ids,
            channel_names=indexes)
        data_array.shape = (data_array.shape[0], data_array.shape[1])
        segment.analogsignals.append(data_array)

    def _csv_matrix_data(
            self, csv_writer: CSVWriter, signal_array: NDArray,
            indexes: NDArray[integer]):
        """
        Writes data to a CSV file.

        :param ~csv.writer csv_writer: Open CSV writer to write to
        :param ~numpy.ndarray signal_array: the raw signal data
        :param list(int) indexes: The indexes for the data
        """
        self.__csv_indexes(indexes, csv_writer)
        csv_writer.writerows(signal_array)
        csv_writer.writerow([])

    def __read_matrix_data(self, csv_reader: CSVReader, segment: Segment,
                           variable: str):
        """
        Reads matrix data and adds it to the segment.

        :param ~csv.reader csv_reader: Open CSV writer to read from
        :param Segment segment:
        :param str variable:
        """
        t_start, _, sampling_period, units = \
            self.__read_variable_metadata(csv_reader)
        indexes = self.__read_indexes(csv_reader)
        signal_array = self.__read_signal_array(csv_reader)
        sampling_rate = 1000 / sampling_period
        self._insert_matrix_data(
            variable, segment, signal_array, indexes,
            t_start, sampling_rate, units)

    def _insert_formation_events(
            self, segment: Segment, variable: str,
            formation_times: List[Quantity], formation_labels: List[str]):
        """
        Adds formation data to a neo segment.

        :param ~neo.core.Segment segment: Segment to add data to
        :param str variable: the variable name
        :param list[~quantities.Quantity] formation_times:
        :param list[str] formation_labels:
        """
        formation_event_array = Event(
            times=formation_times,
            labels=formation_labels,
            units="ms",
            name=variable + "_form",
            description="Synapse formation events",
            array_annotations={})
        segment.events.append(formation_event_array)

    def _insert_elimination_events(
            self, segment: Segment, variable: str,
            elimination_times: List[Quantity], elimination_labels: List[str]):
        """
        Adds elimination data to a neo segment.

        :param ~neo.core.Segment segment: Segment to add data to
        :param str variable: the variable name
        :param list[~quantities.Quantity] elimination_times:
        :param list[str] elimination_labels:
        """
        elimination_event_array = Event(
            times=elimination_times,
            labels=elimination_labels,
            units="ms",
            name=variable + "_elim",
            description="Synapse elimination events",
            array_annotations={})
        segment.events.append(elimination_event_array)

    def _insert_neo_rewirings(
            self, segment: Segment, event_array: NDArray, variable: str):
        """
        Adds data that represent rewire events to a neo segment.

        :param ~neo.core.Segment segment: Segment to add data to
        :param ~numpy.ndarray event_array: the raw "event" data
        :param str variable: the variable name
        """
        formation_times: List[Quantity] = []
        formation_labels: List[str] = []
        elimination_times: List[Quantity] = []
        elimination_labels: List[str] = []

        for i in range(len(event_array)):
            event_time = event_array[i][0] * ms
            pre_id = int(event_array[i][1])
            post_id = int(event_array[i][2])
            if event_array[i][3] == 1:
                formation_times.append(event_time)
                formation_labels.append(f"{pre_id}_{post_id}_formation")
            else:
                elimination_times.append(event_time)
                elimination_labels.append(f"{pre_id}_{post_id}_elimination")

        self._insert_formation_events(
            segment, variable, formation_times, formation_labels)
        self._insert_elimination_events(
            segment, variable, elimination_times, elimination_labels)

    def _csv_rewirings(self, csv_writer: CSVWriter, event_array: NDArray):
        """
        Adds data that represent rewires events to a CSV file.

        :param ~csv.writer csv_writer: Open CSV writer to write to
        :param ~numpy.ndarray event_array: the raw "event" data
        """
        formation: List[Tuple[Quantity, str]] = []
        elimination: List[Tuple[Quantity, str]] = []

        for i in range(len(event_array)):
            event_time = event_array[i][0] * ms
            pre_id = int(event_array[i][1])
            post_id = int(event_array[i][2])
            if event_array[i][3] == 1:
                formation.append(
                    (event_time, f"{pre_id}_{post_id}_formation"))
            else:
                elimination.append(
                    (event_time, f"{pre_id}_{post_id}_elimination"))

        csv_writer.writerow([self._FORMATION])
        csv_writer.writerows(formation)
        csv_writer.writerow([])
        csv_writer.writerow([self._ELMINATION])
        csv_writer.writerows(elimination)
        csv_writer.writerow([])

    def __read_times_and_labels(self, csv_reader: CSVReader) -> Tuple[
            List[Quantity], List[str]]:
        """
        Reads formation or elimination data from the CSV file.

        :param ~csv.reader csv_reader: Open CSV writer to read from
        :return: A list of times and a list of labels
        :rtype: tuple(list[~quantities.Quantity], list[str])
        """
        times: List[Quantity] = []
        labels: List[str] = []
        row = next(csv_reader)
        while len(row) > 0:
            assert len(row) == 2
            times.append(self.__quantify(row[0]))
            labels.append(row[1])
            row = next(csv_reader)
        return times, labels

    def __read_rewirings(self, csv_reader: CSVReader, segment: Segment,
                         variable: str):
        """
        Reads rewiring data from a CSV file and adds it to the segment.

        :param ~csv.reader csv_reader: Open CSV writer to read from
        :param ~neo.core.Segment segment: Segment to add data to
        :param str variable:
        """
        self.__read_metadata(csv_reader)
        row = next(csv_reader)
        assert row == ["formation"]
        times, labels = self.__read_times_and_labels(csv_reader)
        self._insert_formation_events(
            segment, variable, times, labels)
        row = next(csv_reader)
        assert row == ["elimination"]
        times, labels = self.__read_times_and_labels(csv_reader)
        self._insert_elimination_events(
            segment, variable, times, labels)

    def _insert_empty_segment(self, block: Block, segment_number: int,
                              rec_datetime: datetime) -> Segment:
        """
        Creates an empty segment and adds it to the block.

        Unless other insert methods are called the segment will hold no data.

        :param ~neo.core.Block block:
        :param int segment_number:
        :param datetime rec_datetime:
        """
        segment = Segment(
            name=f"segment{segment_number}",
            description=block.description,
            rec_datetime=rec_datetime)
        for i in range(len(block.segments), segment_number):
            block.segments.append(Segment(
                name=f"segment{i}",
                description="empty"))
        if segment_number in block.segments:
            block.segments[segment_number] = segment
        else:
            block.segments.append(segment)
        segment.block = block
        if block.rec_datetime is None:
            block.rec_datetime = rec_datetime

        return segment

    def _csv_segment_metadata(self, csv_writer: CSVWriter, segment_number: int,
                              rec_datetime: datetime):
        """
        Writes only the segment's metadata to CSV.

        Unless other CSV methods are called the CSV will hold no data.

        :param ~csv.writer csv_writer: Open CSV writer to write to
        :param int segment_number:
        :param ~datetime.datetime rec_datetime:
        """
        csv_writer.writerow([self._SEGMENT_NUMBER, segment_number])
        csv_writer.writerow([self._REC_DATETIME, rec_datetime])
        csv_writer.writerow([])

    def __read_segment(self, csv_reader: CSVReader, block: Block,
                       segment_number_st: str) -> Segment:
        """
        Reads only segments metadata and inserts an empty segment.

        Unless other read methods are called the segment will hold no data

        :param ~csv.reader csv_reader: Open CSV writer to read from
        :param ~neo.core.Block block:
        :param str segment_number_st:
        """
        row = next(csv_reader)
        assert (row[0] == self._REC_DATETIME)
        rec_datetime = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f')
        # consume the empty line
        next(csv_reader)
        return self._insert_empty_segment(
            block, int(segment_number_st), rec_datetime)

    def _insert_empty_block(
            self, pop_label: str, description: str, size: int, first_id: int,
            dt: float, simulator: str,
            annotations: Annotations = None) -> Block:
        """
        Creates and empty Neo block object with just metadata.

        Unless other insert methods are called this block will hold no data

        Does not actually "insert" the block anywhere.
        The insert name is aligned with other methods to create a full block

        :param str pop_label:
        :param str description:
        :param int size:
        :param int first_id:
        :param float dt:
        :param str simulator:
        :param dict annotations:
        :return: a block with just metadata
        :rtype: ~neo.core.Block
        """
        block = Block()
        block.name = pop_label
        block.description = description
        # pylint: disable=no-member
        metadata: Dict[str, Any] = {}
        metadata[self._SIZE] = size
        metadata["first_index"] = 0
        metadata['last_index'] = size,
        metadata[self._FIRST_ID] = first_id
        metadata['last_id'] = first_id + size,
        metadata['label'] = pop_label
        metadata[self._SIMULATOR] = simulator
        metadata[self._DT] = dt
        block.annotate(**metadata)
        if annotations:
            block.annotate(**annotations)
        return block

    def _csv_block_metadata(
            self, csv_writer: CSVWriter, pop_label: str, t_stop: float,
            pop_size: int, first_id: int, description: str,
            annotations: Annotations):
        """
        :param ~csv.writer csv_writer: Open CSV writer to write to
        :param str pop_label:
        :param float t_stop:
        :param int pop_size:
        :param int first_id:
        :param str description:
        :param annotations: annotations to put on the neo block
        :type annotations: None or dict(str, ...)
        """
        csv_writer.writerow([self._POPULATION, pop_label])
        csv_writer.writerow([self._DESCRIPTION, f'"{description}"'])

        csv_writer.writerow([self._SIZE, pop_size])
        csv_writer.writerow([self._FIRST_ID, first_id])
        csv_writer.writerow(
            [self._SIMULATOR, SpynnakerDataView.get_sim_name()])
        csv_writer.writerow([self._DT, t_stop])
        # does not make sense on Spinnaker but oh well
        if annotations:
            for key, value in annotations.items():
                csv_writer.writerow([str(key), str(value)])
        csv_writer.writerow([])

    def __read_empty_block(self, csv_reader: CSVReader) -> Block:
        """
        Reads block metadata and uses it to create an empty block.

        :param ~csv.reader csv_reader: Open CSV writer to read from
        :return: empty block
        :rtype: ~neo.core.Block
        """
        metadata = self.__read_metadata(csv_reader)
        return self._insert_empty_block(
            pop_label=metadata.pop(self._POPULATION),
            description=metadata.pop(self._DESCRIPTION),
            size=int(metadata.pop(self._SIZE)),
            first_id=int(metadata.pop(self._FIRST_ID)),
            dt=float(metadata.pop(self._DT)),
            simulator=metadata.pop(self._SIMULATOR),
            annotations=metadata)

    def __read_metadata(self, csv_reader: CSVReader) -> Dict[str, str]:
        """
        Reads a block of metadata and converts it to a dict.

        A metadata block is zero or more lines of two columns followed by an
        empty line. the first column will be the keys the second the data

        :param ~csv.reader csv_reader: Open CSV writer to read from
        :return: a dict of the keys to unformatted values
        :rtype: dict(str, str)
        """
        metadata: Dict[str, str] = {}
        row = next(csv_reader)
        while len(row) > 0:
            assert len(row) == 2
            metadata[row[0]] = row[1]
            row = next(csv_reader)
        return metadata

    def read_csv(self, csv_file: str) -> Block:
        """
        Reads a whole CSV file and creates a block with data.

        :param str csv_file: Path of file to read
        :return: a block with all the data in the CSV file.
        :rtype: ~neo.core.Block
        """
        with open(csv_file, newline='',  encoding="utf-8") as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            block = self.__read_empty_block(csv_reader)
            category = block
            while True:
                try:
                    try:
                        row = next(csv_reader)
                        category = row[0]
                    except IndexError:
                        logger.warning("Ignoring extra blank line after {}",
                                       category)
                        row = next(csv_reader)
                        while len(row) == 0:
                            row = next(csv_reader)
                        category = row[0]

                    if row[0] == self._SEGMENT_NUMBER:
                        segment = self.__read_segment(
                            csv_reader, block, row[1])
                    elif row[0] == self._MATRIX:
                        self.__read_matrix_data(
                            csv_reader, segment, row[1])
                    elif row[0] == self._SPIKES:
                        self.__read_spike_data(
                            csv_reader, segment, row[1])
                    elif row[0] == self._EVENT:
                        self.__read_rewirings(
                            csv_reader, segment, row[1])
                    else:
                        logger.error("ignoring csv block starting with {}",
                                     row[0])
                        # ignore a block
                        row = next(csv_reader)
                        while len(row) > 0:
                            row = next(csv_reader)
                except StopIteration:
                    return block
