# Copyright (c) 2017 The University of Manchester
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

import csv
import os
from typing import List

import numpy
from numpy.typing import NDArray

from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.utilities import neo_convertor
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase
from spynnaker.pyNN.utilities.neo_csv import NeoCsv


def trim_spikes(spikes: NDArray[numpy.floating],
                indexes: List[int]) -> List[List[numpy.floating]]:
    return [[n, t] for [n, t] in spikes if n in indexes]


class TestCSV(BaseTestCase):

    spikes_expected: NDArray[numpy.floating] = numpy.array([])
    v_expected: NDArray

    @classmethod
    def setUpClass(cls) -> None:
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_v = os.path.join(my_dir, "v.csv")
        v_expected_l: List[List[float]] = []
        with open(my_v) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                row_f = list(map(lambda x: float(x), row))
                v_expected_l.append(row_f)
        cls.v_expected = numpy.array(v_expected_l)
        my_spikes = os.path.join(my_dir, "spikes.csv")
        spikes_expected_l = []
        with open(my_spikes) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                floats = list(map(lambda x: float(x), row))
                spikes_expected_l.append((floats[0], floats[1]))
        cls.spikes_expected = numpy.array(spikes_expected_l)

    def test_write(self) -> None:
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        my_csv = os.path.join(my_dir, "test_write.csv")
        my_packets = os.path.join(my_dir, "packets-per-timestep.csv")
        packets_expected = []
        with open(my_packets) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                floats = list(map(lambda x: float(x), row))
                packets_expected.append(floats)

        with NeoBufferDatabase(my_buffer) as db:
            db.csv_block_metadata(
                my_csv, "pop_1", annotations={"foo": 12, "bar": 34})
            db.csv_segment(my_csv, "pop_1", variables="all",
                           view_indexes=None, allow_missing=False)

        neo = NeoCsv().read_csv(my_csv)
        # All annotations converted to String and not back
        self.assertEqual(neo.annotations["foo"], "12")
        self.assertEqual(neo.annotations["bar"], "34")
        spikes = neo_convertor.convert_spikes(neo)
        assert numpy.array_equal(spikes, self.spikes_expected)

        v = neo.segments[0].filter(name='v')[0]
        assert v.shape == self.v_expected.shape
        assert numpy.array_equal(v,  self.v_expected)
        self.assertEqual(35, len(v.times))

        packets = neo.segments[0].filter(name='packets-per-timestep')[0]
        assert numpy.array_equal(packets,  packets_expected)

    def test_view(self) -> None:
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        my_csv = os.path.join(my_dir, "test_view.csv")
        with NeoBufferDatabase(my_buffer) as db:
            #  packets-per-timestep data can not be extracted using a view
            db.csv_block_metadata(my_csv, "pop_1", annotations=None)
            db.csv_segment(
                my_csv, "pop_1", variables=["spikes", "v"],
                view_indexes=[2, 4, 7, 8], allow_missing=False)

        neo = NeoCsv().read_csv(my_csv)

        spikes = neo_convertor.convert_spikes(neo)
        target_s = trim_spikes(self.spikes_expected, [2, 4, 7, 8])
        assert numpy.array_equal(spikes, target_s)
        spiketrains = neo.segments[0].spiketrains
        assert 4 == len(spiketrains)

        v = neo.segments[0].filter(name='v')[0]
        target_v = self.v_expected[:, [2, 4, 7, 8]]
        assert v.shape == target_v.shape
        assert numpy.array_equal(v.magnitude,  target_v)

    def test_over_view(self) -> None:
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "view_data.sqlite3")
        my_csv = os.path.join(my_dir, "test_over_view.csv")
        with NeoBufferDatabase(my_buffer) as db:
            db.csv_block_metadata(my_csv, "pop_1", annotations=None)
            db.csv_segment(my_csv, "pop_1", variables="all",
                           view_indexes=None, allow_missing=False)

        neo = NeoCsv().read_csv(my_csv)
        spikes = neo_convertor.convert_spikes(neo)
        target_s = trim_spikes(self.spikes_expected, [1, 2])
        assert numpy.array_equal(spikes, target_s)
        spiketrains = neo.segments[0].spiketrains
        assert 2 == len(spiketrains)

        v = neo.segments[0].filter(name='v')[0].magnitude
        target_v = self.v_expected[:, [1, 2]]
        assert v.shape == target_v.shape
        assert numpy.array_equal(v, target_v)

    def test_over_sub_view(self) -> None:
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "view_data.sqlite3")
        my_csv = os.path.join(my_dir, "test_over_sub_view.csv")
        with NeoBufferDatabase(my_buffer) as db:
            db.csv_block_metadata(my_csv, "pop_1", annotations=None)
            db.csv_segment(my_csv, "pop_1", variables="all",
                           view_indexes=[2, 4], allow_missing=False)

        neo = NeoCsv().read_csv(my_csv)
        spikes = neo_convertor.convert_spikes(neo)
        target_s = trim_spikes(self.spikes_expected, [2])
        assert numpy.array_equal(spikes, target_s)
        spiketrains = neo.segments[0].spiketrains
        assert 1 == len(spiketrains)

        v = neo.segments[0].filter(name='v')[0].magnitude
        target_v = self.v_expected[:, [2]]
        assert v.shape == target_v.shape
        assert numpy.array_equal(v, target_v)

    def test_no_intersection(self) -> None:
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "view_data.sqlite3")
        my_csv = os.path.join(my_dir, "test_no_intersection.csv")
        with NeoBufferDatabase(my_buffer) as db:
            db.csv_block_metadata(my_csv, "pop_1", annotations=None)
            db.csv_segment(my_csv, "pop_1", variables="all",
                           view_indexes=[4, 6], allow_missing=False)

        neo = NeoCsv().read_csv(my_csv)
        spikes = neo_convertor.convert_spikes(neo)
        self.assertEqual(0, len(spikes))
        spiketrains = neo.segments[0].spiketrains
        self.assertEqual(0, len(spiketrains))

        v = neo.segments[0].filter(name='v')[0].magnitude
        self.assertEqual(0, len(v))

    def test_rewiring(self) -> None:
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "rewiring_data.sqlite3")
        my_labels = os.path.join(my_dir, "rewiring_labels.txt")

        my_csv = os.path.join(my_dir, "test_rewiring.csv")
        with NeoBufferDatabase(my_buffer) as db:
            db.csv_block_metadata(my_csv, "pop_1", annotations=None)
            db.csv_segment(my_csv, "pop_1", variables="all",
                           view_indexes=None, allow_missing=False)
        neo = NeoCsv().read_csv(my_csv)
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
