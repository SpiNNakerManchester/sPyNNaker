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
import pickle
import numpy
import pytest
import shutil
from spinn_front_end_common.utilities.base_database import BaseDatabase
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase


def trim_spikes(spikes, indexes):
    return [[n, t] for [n, t] in spikes if n in indexes]


def copy_db(with_view):
    run_buffer = BaseDatabase.default_database_file()
    my_dir = os.path.dirname(os.path.abspath(__file__))
    if with_view:
        my_buffer = os.path.join(my_dir, "view_data.sqlite3")
    else:
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
    shutil.copyfile(my_buffer, run_buffer)
    SpynnakerDataView._mock_has_run()


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
            for i, row in enumerate(reader):
                row = list(map(lambda x: float(x), row))
                for spike in row:
                    spikes_expected.append([i, spike])
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
        assert 5 == len(spiketrains)

        #  gather False has not effect testing that here
        neo = pop.get_data("spikes", gather=False)
        spikes = neo_convertor.convert_spikes(neo)
        assert numpy.array_equal(spikes, self.spikes_expected)
        spiketrains = neo.segments[0].spiketrains
        assert 5 == len(spiketrains)

        neo = pop.get_data("v")
        v = neo.segments[0].filter(name='v')[0].magnitude
        assert numpy.array_equal(v,  self.v_expected)

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
        neo = view.get_data("spikes", gather=False)
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
        assert numpy.array_equal(v,  target)

    def test_get_spike_counts(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        with NeoBufferDatabase(my_buffer) as db:
            pop = db.get_population("pop_1")

        self.assertEqual({0: 3, 1: 3, 2: 3, 3: 3, 4: 3},
                         pop.get_spike_counts())

        view = pop[1:4]
        self.assertEqual({1: 3, 2: 3, 3: 3}, view.get_spike_counts())

        assert 3 == pop.mean_spike_count()
        assert 3 == view.mean_spike_count()

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

        v = pop.spinnaker_get_data("v")
        assert len(v) == 35 * 5

        with pytest.raises(ConfigurationException):
            pop.spinnaker_get_data(["v", "spikes"])
