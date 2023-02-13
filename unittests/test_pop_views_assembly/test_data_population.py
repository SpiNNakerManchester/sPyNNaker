# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import os
import pickle
import numpy
import pytest
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase
from .make_test_data import N_NEURONS


def trim_spikes(spikes, indexes):
    return [[n, t] for [n, t] in spikes if n in indexes]


class TestDataPopulation(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_v = os.path.join(my_dir, "v.csv")
        v_expected = []
        with open(my_v) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                row = list(map(lambda x: float(x), row))
                v_expected.append(row)
        cls.v_expected = numpy.array(v_expected)
        my_spikes = os.path.join(my_dir, "spikes.csv")
        spikes_expected = []
        with open(my_spikes) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                row = list(map(lambda x: float(x), row))
                spikes_expected.append((row[0], row[1]))
        cls.spikes_expected = numpy.array(spikes_expected)

    def test_simple_spikes(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        neo = pop.get_data("spikes")
        spikes = neo_convertor.convert_spikes(neo)
        assert numpy.array_equal(spikes, self.spikes_expected)
        spiketrains = neo.segments[0].spiketrains
        assert N_NEURONS == len(spiketrains)

        #  gather False has not effect testing that here
        neo = pop.get_data("spikes", gather=False)
        spikes = neo_convertor.convert_spikes(neo)
        assert numpy.array_equal(spikes, self.spikes_expected)
        spiketrains = neo.segments[0].spiketrains
        assert N_NEURONS == len(spiketrains)

        neo = pop.get_data("v")
        v = neo.segments[0].filter(name='v')[0]
        self.assertEqual(35, len(v.times))
        assert numpy.array_equal(v.magnitude,  self.v_expected)

    def test_get_spikes_by_index(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        neo = pop[1, 2].get_data("spikes")
        spikes = neo_convertor.convert_spikes(neo)
        target = trim_spikes(self.spikes_expected, [1, 2])
        assert numpy.array_equal(spikes, target)
        spiketrains = neo.segments[0].spiketrains
        assert 2 == len(spiketrains)

    def test_get_spikes_by_view(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        view = pop[1:3]
        neo = view.get_data("spikes")
        spikes = neo_convertor.convert_spikes(neo)
        target = trim_spikes(self.spikes_expected, [1, 2])
        assert numpy.array_equal(spikes, target)
        spiketrains = neo.segments[0].spiketrains
        assert 2 == len(spiketrains)

    def test_get_spikes_view_missing(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "view_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        view = pop[2:4]
        neo = view.get_data("spikes")
        spikes = neo_convertor.convert_spikes(neo)
        target = trim_spikes(self.spikes_expected, [2])
        assert numpy.array_equal(spikes, target)
        spiketrains = neo.segments[0].spiketrains
        assert 2 == len(spiketrains)
        assert 3 == len(spiketrains[0])
        assert 2 == spiketrains[0].annotations['source_index']
        assert 0 == len(spiketrains[1])
        assert 3 == spiketrains[1].annotations['source_index']

    def test_get_v_view(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        view = pop[1:3]
        neo = view.get_data("v")
        v = neo.segments[0].filter(name='v')[0].magnitude
        target = self.v_expected[:, 1:3]
        assert v.shape == target.shape
        assert numpy.array_equal(v,  target)

    def test_get_v_missing(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "view_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        view = pop[0:3]
        neo = view.get_data("v")
        v = neo.segments[0].filter(name='v')[0].magnitude
        target = self.v_expected[:, 1:3]
        assert numpy.array_equal(
            [1, 2], neo.segments[0].filter(name='v')[0].channel_index.index)
        assert v.shape == target.shape
        for i in range(35):
            print(i)
            print(v[1])
            print(target[i])
        assert numpy.array_equal(v,  target)

    def test_get_spike_counts(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        self.assertEqual(
            pop.get_spike_counts(),
            {0: 3, 1: 2, 2: 3, 3: 3, 4: 1, 5: 3, 6: 0, 7: 2, 8: 3})

        view = pop[1:4]
        self.assertEqual({1: 2, 2: 3, 3: 3}, view.get_spike_counts())

        assert 2.2222222222222223 == pop.mean_spike_count()
        assert 2.6666666666666665 == view.mean_spike_count()

    def test_write(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        # Note gather=False will be ignored just testing it can be
        pop.write_data("spikes.pkl", "spikes", gather=False)
        with open("spikes.pkl", "rb") as pkl:
            neo = pickle.load(pkl)
            spikes = neo_convertor.convert_spikes(neo)
            assert numpy.array_equal(spikes, self.spikes_expected)

        pop.write_data("spikes.pkl", 'spikes')
        with open("spikes.pkl", "rb") as pkl:
            neo = pickle.load(pkl)
            spikes = neo_convertor.convert_spikes(neo)
            assert numpy.array_equal(spikes, self.spikes_expected)

        pop.write_data("v.pkl", "v")
        with open("v.pkl", "rb") as pkl:
            neo = pickle.load(pkl)
            v = neo.segments[0].filter(name='v')[0].magnitude
            assert v.shape == self.v_expected.shape
            assert numpy.array_equal(v,  self.v_expected)

    def test_spinnaker_get_data(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        spikes = pop.spinnaker_get_data("spikes")
        assert numpy.array_equal(spikes, self.spikes_expected)

        v = pop.spinnaker_get_data("v")
        assert len(v) == 35 * N_NEURONS
        target = self.v_expected
        for neuron, time, val in v:
            self.assertEqual(val, target[int(time), int(neuron)],
                             f"{time}{neuron}")

        view = pop[4, 2]
        spikes = view.spinnaker_get_data("spikes")
        target = trim_spikes(self.spikes_expected, [4, 2])
        assert numpy.array_equal(spikes, target)

        spikes = pop.spinnaker_get_data("spikes", view_indexes=[4, 2])
        assert numpy.array_equal(spikes, target)

        with pytest.raises(ConfigurationException):
            # Only one type of data at a time is supported
            pop.spinnaker_get_data(["v", "spikes"])

    def test_spinnaker_get_data_view(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "view_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        spikes = pop.spinnaker_get_data("spikes")
        target = trim_spikes(self.spikes_expected, [1, 2])
        assert numpy.array_equal(spikes, target)

        v = pop.spinnaker_get_data("v")
        assert len(v) == 35 * 2
        target = self.v_expected
        for neuron, time, val in v:
            self.assertEqual(val, target[int(time), int(neuron)],
                             f"{time}{neuron}")
        with pytest.raises(ConfigurationException):
            # Only one type of data at a time is supported
            pop.spinnaker_get_data(["v", "spikes"])

    def test_rewiring(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "rewiring_data.sqlite3")
        my_labels = os.path.join(my_dir, "rewiring_labels.txt")

        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

            neo = pop.get_data("rewiring")
            formation_events = neo.segments[0].events[0]
            elimination_events = neo.segments[0].events[1]

            num_forms = len(formation_events.times)
            self.assertEqual(0, len(formation_events))
            num_elims = len(elimination_events.times)
            self.assertEqual(10, len(elimination_events))

            self.assertEqual(0, num_forms)
            self.assertEqual(10, num_elims)

            with open(my_labels, "r", encoding="UTF-8") as label_f:
                for i, line in enumerate(label_f.readlines()):
                    self.assertEqual(
                        line.strip(), elimination_events.labels[i])

            pop = db.get_population("pop_1")
            view = pop[2:4]
            #  rewiring can not be extracted using a view
            with self.assertRaises(SpynnakerException):
                neo = view.get_data("rewiring")

    def test_packets(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        neo = pop.get_data("packets-per-timestep")
        packets = neo.segments[0].filter(name='packets-per-timestep')[0]

        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_packets = os.path.join(my_dir, "packets-per-timestep.csv")
        packets_expected = []
        with open(my_packets) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                row = list(map(lambda x: float(x), row))
                packets_expected.append(row)

        assert numpy.array_equal(packets,  packets_expected)

    def test_bad_view(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        # Like normal slices/ views out of range is ignored
        pop[1:10]

        # Like index selections/ views and indexes raise an exception
        with self.assertRaises(TypeError):
            pop[1, 10]
