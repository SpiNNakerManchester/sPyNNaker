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
import pyNN.spiNNaker as sim
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase
from .make_test_data import N_NEURONS


def trim_spikes(spikes, indexes):
    return [[n, t] for [n, t] in spikes if n in indexes]


_VIEW_DATA = "view_data.sqlite3"
_ALL_DATA = "all_data.sqlite3"


def copy_db(data_file):
    run_buffer = BaseDatabase.default_database_file()
    my_dir = os.path.dirname(os.path.abspath(__file__))
    my_buffer = os.path.join(my_dir, data_file)
    shutil.copyfile(my_buffer, run_buffer)
    SpynnakerDataView._mock_has_run()


class TestGetting(BaseTestCase):

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
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label="pop_1")
        copy_db(_ALL_DATA)

        neo = pop.get_data("spikes", annotations={"foo": 12, "bar": 34})
        self.assertEqual(neo.annotations["foo"], 12)
        self.assertEqual(neo.annotations["bar"], 34)
        spikes = neo_convertor.convert_spikes(neo)
        assert numpy.array_equal(spikes, self.spikes_expected)
        spiketrains = neo.segments[0].spiketrains
        assert N_NEURONS == len(spiketrains)

        #  gather False has not effect testing that here
        neo = pop.get_data(["spikes", "v"], gather=False)
        spikes = neo_convertor.convert_spikes(neo)
        assert numpy.array_equal(spikes, self.spikes_expected)
        spiketrains = neo.segments[0].spiketrains
        assert N_NEURONS == len(spiketrains)

        v = neo.segments[0].filter(name='v')[0].magnitude
        assert numpy.array_equal(v,  self.v_expected)

        sim.end()

    def test_get_spikes_by_index(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label="pop_1")
        pop.record("spikes")
        copy_db(_ALL_DATA)

        neo = pop[1, 2].get_data("spikes")
        spikes = neo_convertor.convert_spikes(neo)
        target = trim_spikes(self.spikes_expected, [1, 2])
        assert numpy.array_equal(spikes, target)
        spiketrains = neo.segments[0].spiketrains
        assert 2 == len(spiketrains)

        sim.end()

    def test_get_spikes_by_view(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label="pop_1")
        copy_db(_ALL_DATA)

        view = pop[1:3]
        view.record("spikes")
        neo = view.get_data("spikes", gather=False)
        spikes = neo_convertor.convert_spikes(neo)
        target = trim_spikes(self.spikes_expected, [1, 2])
        assert numpy.array_equal(spikes, target)
        spiketrains = neo.segments[0].spiketrains
        assert 2 == len(spiketrains)

        sim.end()

    def test_get_spikes_view_missing(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label="pop_1")
        copy_db(_VIEW_DATA)

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

        sim.end()

    def test_get_v_view(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label="pop_1")
        pop.record("spikes")
        copy_db(_ALL_DATA)

        view = pop[1:3]
        neo = view.get_data("v")
        v = neo.segments[0].filter(name='v')[0].magnitude
        target = self.v_expected[:, 1:3]
        assert v.shape == target.shape
        assert numpy.array_equal(v,  target)

        sim.end()

    def test_get_v_missing(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label="pop_1")
        pop[1:3].record("v")
        copy_db(_VIEW_DATA)

        view = pop[0:3]
        neo = view.get_data("v")
        v = neo.segments[0].filter(name='v')[0].magnitude
        target = self.v_expected[:, 1:3]
        assert numpy.array_equal(
            [1, 2], neo.segments[0].filter(name='v')[0].channel_index.index)
        assert v.shape == target.shape
        assert numpy.array_equal(v,  target)

        sim.end()

    def test_get_spike_counts(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label="pop_1")
        pop.record("spikes")
        copy_db(_ALL_DATA)

        assert {0: 3, 1: 2, 2: 3, 3: 3, 4: 1, 5: 3, 6: 0, 7: 2, 8: 3} == \
               pop.get_spike_counts()

        view = pop[1:4]
        assert {1: 2, 2: 3, 3: 3} == view.get_spike_counts()

        assert 2.2222222222222223 == pop.meanSpikeCount()
        assert 2.6666666666666665 == view.mean_spike_count()

        sim.end()

    def test_write(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label="pop_1")
        pop.record(["spikes", "v"])
        copy_db(_ALL_DATA)

        # Note gather=False will be ignored just testing it can be
        pop.write_data("spikes.pkl", "spikes", gather=False)
        with open("spikes.pkl", "rb") as pkl:
            neo = pickle.load(pkl)
            spikes = neo_convertor.convert_spikes(neo)
            assert numpy.array_equal(spikes, self.spikes_expected)

        pop.write_data("v.pkl", 'v')
        with open("v.pkl", "rb") as pkl:
            neo = pickle.load(pkl)
            v = neo.segments[0].filter(name='v')[0].magnitude
            assert v.shape == self.v_expected.shape
            assert numpy.array_equal(v,  self.v_expected)

        sim.end()

    def test_spinnaker_get_data(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label="pop_1")
        pop.record("v")
        copy_db(_ALL_DATA)

        v = pop.spinnaker_get_data("v")
        assert len(v) == 35 * 9

        with pytest.raises(ConfigurationException):
            pop.spinnaker_get_data(["v", "spikes"])
        sim.end()

    def test_rewiring(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label="pop_1")
        pop.record("rewiring")
        copy_db("rewiring_data.sqlite3")

        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_labels = os.path.join(my_dir, "rewiring_labels.txt")

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

        view = pop[2:4]
        #  rewiring can not be extracted using a view
        with self.assertRaises(SpynnakerException):
            neo = view.get_data("rewiring")

    def test_packets(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label="pop_1")
        pop.record("packets-per-timestep")
        copy_db(_ALL_DATA)

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
