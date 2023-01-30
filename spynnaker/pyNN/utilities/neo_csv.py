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
import csv
from datetime import datetime
import logging
import neo
import numpy
import quantities
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.data import SpynnakerDataView

logger = FormatAdapter(logging.getLogger(__name__))


class NeoCsv(object):
    _POPULATION = "population"
    _DESCRIPTION = "description"
    _SIZE = "size"
    _FIRST_ID = "first_id"
    _SIMULATOR = "simulator"
    _DT = "dt"  # t_stop

    _INDEXES = "indexes"

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

    def _csv_variable_metdata(self, csv_writer, variable_type, variable,
                              t_start, t_stop, sampling_interval_ms, units):
        """
        Writes the metadata for a variable to csv

        :param ~csv.writer csv_writer: Open csv writer to write to
        :param str variable_type:
        :param str variable:
        :param float t_start:
        :param float t_stop:
        :param float sampling_interval_ms:
        :param str units:
        """
        csv_writer.writerow([variable_type, variable])
        csv_writer.writerow([self._T_START, t_start * quantities.ms])
        csv_writer.writerow([self._T_STOP, t_stop * quantities.ms])
        sampling_period = sampling_interval_ms * quantities.ms
        csv_writer.writerow([self._SAMPLING_PERIOD, sampling_period])
        if units is None:
            units = "dimensionless"
        csv_writer.writerow([self._UNITS, units])
        csv_writer.writerow([])

    def __quantify(self, as_str):
        """
        Converts a String into a quantities.Quantity

        The String should be a float, a space and a Quantities label

        :param str as_str: String representation of a quantity.
        :return: A Quantities object
        :rtype ~quantities.Quantity
        """
        parts = as_str.split(" ")
        return quantities.Quantity(float(parts[0]), units=parts[1])

    def __read_variable_metadata(self, csv_reader):
        """
        Reads a block of metadata, formats it and returns it as a dict

        A block is a number of rows each of exactly 2 values followed by an
        empty row

        :param ~csv.writer csv_writer: Open csv writer to read from
        :return: t_start, t_stop, sampling_period, units
        :rtype (~quantities.Quantity, ~quantities.Quantity,
            ~quantities.Quantity, str)
        """
        metadata = self.__read_metadata(csv_reader)
        return(
            self.__quantify(metadata[self._T_START]),
            self.__quantify(metadata[self._T_STOP]),
            self.__quantify(metadata[self._SAMPLING_PERIOD]),
            metadata[self._UNITS])

    def __read_signal_array(self, csv_reader):
        rows = []
        row = next(csv_reader)
        while len(row) > 0:
            rows.append(row)
            row = next(csv_reader)
        return numpy.asarray(rows, dtype=numpy.float64)

    def _insert_spike_data(
            self, view_indexes, segment, spikes, t_start, t_stop,
            sampling_rate):
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
        :param ~quantities.Quantity sampling_rate: Arte a neuron is recorded
        :param int first_id:
        """
        block = segment.block
        first_id = block.annotations[self._FIRST_ID]
        times = defaultdict(list)
        for neuron_id, time in spikes:
            times[int(neuron_id)].append(time)

        for index in view_indexes:
            spiketrain = neo.SpikeTrain(
                times=times[index],
                t_start=t_start,
                t_stop=t_stop,
                units='ms',
                sampling_rate=sampling_rate,
                source_population=block.name,
                source_id=index + first_id,
                source_index=index)
            segment.spiketrains.append(spiketrain)

    def _csv_spike_data(self, csv_writer, spikes):
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
        csv_writer.writerows(spikes)
        csv_writer.writerow([])

    def __read_spike_data(self, csv_reader, segment, view_indexes, variable):
        try:
            t_start, t_stop, sampling_period, units = \
                self.__read_variable_metadata(csv_reader)
            spikes = self.__read_signal_array(csv_reader)
            sampling_rate = 1000 / sampling_period
            self._insert_spike_data(
                view_indexes, segment, spikes, t_start, t_stop, sampling_rate)
        except KeyError as ex:
            logger.exception(f"Metadata for {variable} is missing {ex}. "
                             f"So this data will be skipped")
            return

    def __get_channel_index(self, ids, block):
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

    def _insert_matix_data(
            self, variable, segment, signal_array,
            indexes, t_start, sampling_rate, units):
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
        :param ~quantities.Quantity sampling_rate: Arte a neuron is recorded
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
        # pylint: disable=too-many-arguments, no-member, c-extension-no-member
        block = segment.block
        first_id = block.annotations[self._FIRST_ID]


        ids = list(map(lambda x: x+first_id, indexes))
        if units is None:
            units = "dimensionless"
        data_array = neo.AnalogSignal(
            signal_array,
            units=units,
            t_start=t_start,
            sampling_rate=sampling_rate,
            name=variable,
            source_population=block.name,
            source_ids=ids)
        channel_index = self.__get_channel_index(indexes, segment.block)
        data_array.channel_index = channel_index
        data_array.shape = (data_array.shape[0], data_array.shape[1])
        segment.analogsignals.append(data_array)
        channel_index.analogsignals.append(data_array)

    def _csv_matix_data(self, csv_writer, signal_array, indexes):
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
        # pylint: disable=too-many-arguments, no-member, c-extension-no-member
        csv_writer.writerow(indexes)
        csv_writer.writerows(signal_array)
        csv_writer.writerow([])

    def __read_matix_data(self, csv_reader, segment, variable):
        t_start, t_stop, sampling_period, units = \
            self.__read_variable_metadata(csv_reader)
        row = next(csv_reader)
        assert len(row) > 0
        indexes = numpy.asarray(row, dtype=int)
        signal_array = self.__read_signal_array(csv_reader)
        sampling_rate = 1000 / sampling_period
        self._insert_matix_data(
            variable, segment, signal_array, indexes,
            t_start, sampling_rate, units)

    def _insert_formation_events(
            self, segment, variable, formation_times, formation_labels):
        """ Adds data that is events to a neo segment.

        :param ~neo.core.Segment segment: Segment to add data to
        :param ~numpy.ndarray event_array: the raw "event" data
        :param str variable: the variable name
        :param recording_start_time: when recording started
        :type recording_start_time: float or int
        """
        # pylint: disable=too-many-arguments, no-member, c-extension-no-member
        formation_event_array = neo.Event(
            times=formation_times,
            labels=formation_labels,
            units="ms",
            name=variable + "_form",
            description="Synapse formation events",
            array_annotations={})
        segment.events.append(formation_event_array)

    def _insert_elimination_events(
            self, segment, variable, elimination_times, elimination_labels):
        """ Adds data that is events to a neo segment.

        :param ~neo.core.Segment segment: Segment to add data to
        :param ~numpy.ndarray event_array: the raw "event" data
        :param str variable: the variable name
        :param recording_start_time: when recording started
        :type recording_start_time: float or int
        """
        # pylint: disable=too-many-arguments, no-member, c-extension-no-member
        elimination_event_array = neo.Event(
            times=elimination_times,
            labels=elimination_labels,
            units="ms",
            name=variable + "_elim",
            description="Synapse elimination events",
            array_annotations={})
        segment.events.append(elimination_event_array)

    def _insert_neo_rewirings(
            self, segment, event_array, variable, recording_start_time):
        """ Adds data that is events to a neo segment.

        :param ~neo.core.Segment segment: Segment to add data to
        :param ~numpy.ndarray event_array: the raw "event" data
        :param str variable: the variable name
        :param recording_start_time: when recording started
        :type recording_start_time: float or int
        """
        # pylint: disable=too-many-arguments, no-member, c-extension-no-member
        t_start = recording_start_time * quantities.ms

        formation_times = []
        formation_labels = []
        elimination_times = []
        elimination_labels = []

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

        self._insert_formation_events(
            segment, variable, formation_times, formation_labels)
        self._insert_elimination_events(
            segment, variable, elimination_times, elimination_labels)

    def _csv_rewirings(self, csv_writer, event_array):
        """ Adds data that is events to a neo segment.

        :param ~neo.core.Segment segment: Segment to add data to
        :param ~numpy.ndarray event_array: the raw "event" data
        :param str variable: the variable name
        :param recording_start_time: when recording started
        :type recording_start_time: float or int
        """
        # pylint: disable=too-many-arguments, no-member, c-extension-no-member

        formation = []
        elimination = []

        for i in range(len(event_array)):
            event_time = event_array[i][0] * quantities.ms
            pre_id = int(event_array[i][1])
            post_id = int(event_array[i][2])
            if event_array[i][3] == 1:
                formation.append(
                    [event_time,
                     str(pre_id) + "_" + str(post_id) + "_formation"])
            else:
                elimination.append(
                    [event_time,
                     str(pre_id) + "_" + str(post_id) + "_elimination"])

        csv_writer.writerow([self._FORMATION])
        csv_writer.writerows(formation)
        csv_writer.writerow([])
        csv_writer.writerow([self._ELMINATION])
        csv_writer.writerows(elimination)
        csv_writer.writerow([])

    def __read_times_and_labels(self, csv_reader):
        times = []
        labels = []
        row = next(csv_reader)
        while len(row) > 0:
            assert len(row) == 2
            times.append(self.__quantify(row[0]))
            labels.append(row[1])
            row = next(csv_reader)
        return times, labels

    def __read_rewirings(self, csv_reader, segment, variable):
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

    def _insert_segment(self, block, segment_number, rec_datetime):
        segment = neo.Segment(
            name="segment{}".format(segment_number),
            description=block.description,
            rec_datetime=rec_datetime)
        for i in range(len(block.segments), segment_number):
            block.segments.append(neo.Segment(
                name="segment{}".format(i),
                description="empty"))
        if segment_number in block.segments:
            block.segments[segment_number] = segment
        else:
            block.segments.append(segment)
        segment.block = block
        if block.rec_datetime is None:
            block.rec_datetime = rec_datetime

        return segment

    def _csv_segment(self, csv_writer, segment_number, rec_datetime):
        csv_writer.writerow([self._SEGMENT_NUMBER, segment_number])
        csv_writer.writerow([self._REC_DATETIME, rec_datetime])
        csv_writer.writerow([])

    def __read_segment(self, csv_reader, block, segment_number_st):
        row = next(csv_reader)
        assert (row[0] == self._REC_DATETIME)
        rec_datetime = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f')
        # consume the empty line
        next(csv_reader)
        return self._insert_segment(
            block, int(segment_number_st), rec_datetime)

    def _csv_indexes(self, csv_writer, view_indexes):
        if view_indexes is not None:
            csv_writer.writerow([self._INDEXES])
            csv_writer.writerow(view_indexes)
            csv_writer.writerow([])

    def _insert_block(self, pop_label, description, size, first_id, dt,
                      simulator, annotations=None):
        block = neo.Block()
        block.name = pop_label
        block.description = description
        # pylint: disable=no-member
        metadata = {}
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

    def _csv_block(self, csv_writer, pop_label, t_stop,
                   pop_size, first_id, description):
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
        csv_writer.writerow([self._POPULATION, pop_label])
        csv_writer.writerow([self._DESCRIPTION, f"\"{description}\""])

        csv_writer.writerow([self._SIZE, pop_size])
        csv_writer.writerow([self._FIRST_ID, first_id])
        csv_writer.writerow(
            [self._SIMULATOR, SpynnakerDataView.get_sim_name()])
        csv_writer.writerow([self._DT, t_stop])
        # does not make sense on Spinnaker but oh well
        csv_writer.writerow([])

    def __read_block(self, metadata):
        return self._insert_block(
            pop_label=metadata[self._POPULATION],
            description=metadata[self._DESCRIPTION],
            size=int(metadata[self._SIZE]),
            first_id=int(metadata[self._FIRST_ID]),
            dt=float(metadata[self._DT]),
            simulator=metadata[self._SIMULATOR])

    def __read_metadata(self, csv_reader):
        metadata = {}
        row = next(csv_reader)
        while len(row) > 0:
            assert len(row) == 2
            metadata[row[0]] = row[1]
            row = next(csv_reader)
        return metadata

    def read_csv(self, csv_file):
        with open(csv_file, newline='') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            metadata = self.__read_metadata(csv_reader)
            block = self.__read_block(metadata)
            category = block
            indexes = range(block.annotations[self._SIZE])
            while True:
                try:
                    try:
                        row = next(csv_reader)
                        category = row[0]
                    except IndexError:
                        logger.warning(
                            f"Ignoring extra blank line after {category}")
                        row = next(csv_reader)
                        while len(row) == 0:
                            row = next(csv_reader)
                        category = row[0]

                    if row[0] == self._SEGMENT_NUMBER:
                        segment = self.__read_segment(
                            csv_reader, block, row[1])
                    elif row[0] == self._MATRIX:
                        self.__read_matix_data(
                            csv_reader, segment, row[1])
                    elif row[0] == self._SPIKES:
                        self.__read_spike_data(
                            csv_reader, segment, indexes, row[1])
                    elif row[0] == self._EVENT:
                        self.__read_rewirings(
                            csv_reader, segment, row[1])
                    elif row[0] == self._INDEXES:
                        row = next(csv_reader)
                        assert len(row) > 0
                        indexes = numpy.genfromtxt(row)
                        row = next(csv_reader)
                    else:
                        logger.error(
                            f"ignoring csv block starting with {row[0]}")
                        # ignore a block
                        row = next(csv_reader)
                        while len(row) > 0:
                            row = next(csv_reader)
                except StopIteration:
                    return block
