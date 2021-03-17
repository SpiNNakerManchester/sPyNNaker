# Copyright (c) 2017-2019 The University of Manchester
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

from enum import Enum
import numpy
import os
import random
import sys
from spynnaker.pyNN.utilities.recorder_database import RecorderDatabase, DEFAULT_NAME
from spinnaker_testbase import BaseTestCase


class TimeStepType(Enum):
    TIMESTEP = 0
    IN_DATA = 1
    SEPARATE = 2


class TestRecorderDatabase(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls_file = sys.modules[cls.__module__].__file__
        path = os.path.dirname(cls_file)
        db_file = os.path.join(path, DEFAULT_NAME)
        if os.path.isfile(db_file):
            os.remove(db_file)

    def setUp(self):
        super().setUp()
        self.db = RecorderDatabase(os.getcwd())
        self.db.clear_ds()

    def tearDown(self):
        self.db.close()

    def random_matrix_data(self, timestamps, neuron_ids, timestamps_in_data):
        data = []
        for timestamp in timestamps:
            line = []
            if timestamps_in_data == TimeStepType.IN_DATA:
                line.append(timestamp)
            for _ in neuron_ids:
                line.append(random.randint(0, 100000000))
            data.append(line)
        return data

    def random_spike_data(self, timestamps, neuron_ids, as_numpy):
        spike_times = []
        data = []
        combined = []
        for timestamp in timestamps:
            for id in neuron_ids:
                if random.randint(0, 25) == 1:
                    data.append(id)
                    combined.append((timestamp, id))
                    spike_times.append(timestamp)
                if random.randint(0, 25) == 2:
                    spike_times.append(timestamp)
                    data.append(id)
                    combined.append((timestamp, id))

                    spike_times.append(timestamp)
                    data.append(id)
                    combined.append((timestamp, id))
        if as_numpy:
            return numpy.array(spike_times), numpy.array(data), \
                   numpy.array(combined)
        return spike_times, data, combined

    def simple_matrix(self, timestamps_in_data, sampling_interval, n_neurons):
        self.db.update_segment(0, 0, 100)
        source = "population1"
        variable = "voltage"
        self.db.register_matrix_source(
            source, variable, sampling_interval, description="foo",
            unit="v", n_neurons=n_neurons)
        ids = range(n_neurons)
        timestamps = [x * sampling_interval for x in range(0, 10)]
        data_in = self.random_matrix_data(timestamps, ids, timestamps_in_data)
        if timestamps_in_data == TimeStepType.TIMESTEP:
            ts = sampling_interval
        elif timestamps_in_data == TimeStepType.IN_DATA:
            ts = None
        else:
            ts = timestamps
        self.db.insert_matrix(source, variable, data_in, ids, ts)
        ids_out, timestamps_out, data_out = self.db.get_matrix_data(
            source, variable)
        if timestamps_in_data == TimeStepType.IN_DATA:
            data = list(map(lambda x: x[1:], data_in))
        else:
            data = data_in
        if data:
            self.assertEqual(data_out.shape, (len(data), len(data[0])))
        self.assertListEqual(data_out.tolist(), data)
        self.assertListEqual(ids_out.tolist(), list(ids))
        self.assertListEqual(timestamps_out.tolist(), list(timestamps))

    def test_simple_matrix_timestamps_timestep(self):
        self.simple_matrix(TimeStepType.TIMESTEP, 0.5, 4)

    def test_simple_matrix_timestamps_seperate(self):
        self.simple_matrix(TimeStepType.SEPARATE, 0.5, 4)

    def test_simple_matrix_timestamps_in_data(self):
        self.simple_matrix(TimeStepType.IN_DATA, 0.5, 4)

    def test_huge_matrix_timestamps_in_data(self):
        self.simple_matrix(TimeStepType.IN_DATA, 1, 4000)

    def events(self, timestamps_in_data, as_numpy):
        self.db.update_segment(0, 0, 100)
        source = "population1"
        variable = "spikes"
        sampling_interval = 1
        n_neurons = 4
        self.db.register_event_source(
            source, variable, sampling_interval, description="foo",
            unit="count", n_neurons=n_neurons)
        ids = range(n_neurons)
        timestamps1 = [x * sampling_interval for x in range(10)]
        spike_times1, spike_ids1, combined1 = self.random_spike_data(
            timestamps1, ids, as_numpy)
        if timestamps_in_data:
            self.db.insert_events(source, variable, combined1)
        else:
            self.db.insert_events(source, variable, spike_ids1, spike_times1)

        self.db.update_segment(0, 0, 200)
        timestamps2 = [x * sampling_interval for x in range(10, 20)]
        spike_times2, spike_ids2, combined2 = self.random_spike_data(
            timestamps2, ids, as_numpy)
        if as_numpy:
            if spike_ids1.size > 0:
                if spike_times2.size > 0:
                    spike_times = numpy.hstack([spike_times1, spike_times2])
                    spike_ids = numpy.hstack([spike_ids1, spike_ids2])
                    combined = numpy.vstack([combined1, combined2])
                else:
                    spike_times = spike_times1
                    spike_ids = spike_ids1
                    combined = combined1
            else:
                spike_times = spike_times2
                spike_ids = spike_ids2
                combined = combined2
        else:
            spike_times = spike_times1 + spike_times2
            spike_ids = spike_ids1 + spike_ids2
            combined = combined1 + combined2
        # Include repeat the same data
        if timestamps_in_data:
            self.db.insert_events(source, variable, combined)
        else:
            self.db.insert_events(source, variable, spike_ids, spike_times)

        data_out = self.db.get_events_data(
            source, variable)
        self.assertEqual(len(combined), len(data_out))
        print(data_out)
        print(spike_ids)
        print(spike_times)
        for i in range(len(combined)):
            self.assertEqual(data_out[i, 0], spike_times[i])
            self.assertEqual(data_out[i, 1], spike_ids[i])

    def test_event_timestamps_in_data_list(self):
        self.events(True, False)

    def test_event_timestamps_seperate_list(self):
        self.events(False, False)

    def test_event_timestamps_in_data_numpy(self):
        self.events(True, True)

    def test_event_timestamps_seperate_numpy(self):
        self.events(False, True)

    def test_no_events(self):
        self.db.update_segment(0, 0, 100)
        source = "population1"
        variable = "spikes"
        self.db.register_event_source(
            source, variable, sampling_interval=1, description="foo",
            unit="count", n_neurons=33)
        self.db.insert_events(source, variable, [])
        data_out = self.db.get_events_data(
            source, variable)
        self.assertEqual(0, len(data_out))

    def single(self, timestamps_in_data):
        self.db.update_segment(0, 0, 100)
        source = "population1"
        variable = "spikes_count"
        id = 4
        n_neurons = 5
        sampling_interval = 0.5
        self.db.register_single_source(
            source, variable, sampling_interval, description="foo",
            unit="v", n_neurons=n_neurons)
        timestamps = [row * sampling_interval for row in range(1, 10)]
        data_in = self.random_matrix_data(timestamps, [id], timestamps_in_data)
        if timestamps_in_data == TimeStepType.TIMESTEP:
            ts = 0.5
        elif timestamps_in_data == TimeStepType.IN_DATA:
            ts = None
        else:
            ts = timestamps
        self.db.insert_single(source, variable, data_in, id, ts)
        ids_out, timestamps_out, data_out = self.db.get_single_data(
            source, variable)
        if timestamps_in_data == TimeStepType.IN_DATA:
            data = list(map(lambda x: x[1:], data_in))
        else:
            data = data_in
        self.assertListEqual(data_out.tolist(), data)
        self.assertListEqual(ids_out.tolist(), list([id]))
        self.assertListEqual(timestamps_out.tolist(), list(timestamps))

    def test_single_timestamps_in_data(self):
        self.single(TimeStepType.IN_DATA)

    def test_singletime_stamps_seperate(self):
        self.single(TimeStepType.SEPARATE)

    def test_segments(self):
        self.db.update_segment(0, 0, 100)
        self.db.update_segment(0, 0, 200)
        self.db.update_segment(1, 0, 150)
        segments = self.db.get_segments()
        self.assertEqual(2, len(segments))
        self.assertEqual((0, 200), segments[0])
        self.assertEqual((0, 150), segments[1])
        self.assertEqual(1, self.db.current_segment())
