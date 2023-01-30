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

import csv
import os
import numpy
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.utilities import neo_convertor
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase
from spynnaker.pyNN.utilities.neo_csv import NeoCsv


def trim_spikes(spikes, indexes):
    return [[n, t] for [n, t] in spikes if n in indexes]


class TestCSV(BaseTestCase):

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

    def test_write(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        my_csv = os.path.join(my_dir, "test.csv")
        my_packets = os.path.join(my_dir, "packets-per-timestep.csv")
        packets_expected = []
        with open(my_packets) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                row = list(map(lambda x: float(x), row))
                packets_expected.append(row)

        with NeoBufferDatabase(my_buffer) as db:
            db.write_csv(my_csv, "pop_1", variables="all")

        neo = NeoCsv().read_csv(my_csv)
        spikes = neo_convertor.convert_spikes(neo)
        assert numpy.array_equal(spikes, self.spikes_expected)

        v = neo.segments[0].filter(name='v')[0].magnitude
        assert v.shape == self.v_expected.shape
        assert numpy.array_equal(v,  self.v_expected)

        packets = neo.segments[0].filter(name='packets-per-timestep')[0]
        assert numpy.array_equal(packets,  packets_expected)

    def test_view(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        my_csv = os.path.join(my_dir, "test.csv")
        with NeoBufferDatabase(my_buffer) as db:
            #  packets-per-timestep data can not be extracted using a view
            db.write_csv(my_csv, "pop_1", variables=["spikes", "v"],
                         view_indexes=[2, 4, 7, 8])

        neo = NeoCsv().read_csv(my_csv)

        spikes = neo_convertor.convert_spikes(neo)
        target = trim_spikes(self.spikes_expected, [2, 4, 7, 8])
        assert numpy.array_equal(spikes, target)
        spiketrains = neo.segments[0].spiketrains
        assert 4 == len(spiketrains)

        v = neo.segments[0].filter(name='v')[0].magnitude
        target = self.v_expected[:, [2, 4, 7, 8]]
        assert v.shape == target.shape
        assert numpy.array_equal(v,  target)

    def test_rewiring(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "rewiring_data.sqlite3")
        my_labels = os.path.join(my_dir, "rewiring_labels.txt")

        my_csv = os.path.join(my_dir, "test.csv")
        with NeoBufferDatabase(my_buffer) as db:
            db.write_csv(my_csv, "pop_1", variables="all")
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
