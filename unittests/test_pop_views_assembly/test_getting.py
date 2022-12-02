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
from spinn_front_end_common.interface.buffer_management.storage_objects.\
    sqllite_database import DB_FILE_NAME
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.recorder import Recorder
import pyNN.spiNNaker as sim
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


def trim_spikes(spikes, indexes):
    return [[n, t] for [n, t] in spikes if n in indexes]


def copy_db(with_view):
    run_dir = SpynnakerDataView().get_run_dir_path()
    run_buffer = os.path.join(run_dir, DB_FILE_NAME)
    my_dir = os.path.dirname(os.path.abspath(__file__))
    if with_view:
        my_buffer = os.path.join(my_dir, "view_" + DB_FILE_NAME)
    else:
        my_buffer = os.path.join(my_dir, "all_" + DB_FILE_NAME)
    shutil.copyfile(my_buffer, run_buffer)


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
            for i, row in enumerate(reader):
                row = list(map(lambda x: float(x), row))
                for spike in row:
                    spikes_expected.append([i, spike])
        cls.spikes_expected = numpy.array(spikes_expected)

    #def tearDown(self):
    #    """ Restore the real methods that we may have mocked out """
    #    Recorder.get_data = self.__get_data

    def test_simple_spikes(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
        copy_db(False)

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

        neo = pop.get_v()
        v = neo.segments[0].filter(name='v')[0].magnitude
        assert numpy.array_equal(v,  self.v_expected)

        sim.end()

    def test_get_spikes_by_index(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
        pop.record("spikes")
        copy_db(False)

        neo = pop[1, 2].get_data("spikes")
        spikes = neo_convertor.convert_spikes(neo)
        target = trim_spikes(self.spikes_expected, [1, 2])
        assert numpy.array_equal(spikes, target)
        spiketrains = neo.segments[0].spiketrains
        assert 2 == len(spiketrains)

        sim.end()

    def test_get_spikes_by_view(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
        copy_db(False)

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
        pop = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
        copy_db(True)

        view = pop[2:4]
        neo = view.get_data("spikes")
        spikes = neo_convertor.convert_spikes(neo)
        target = trim_spikes(self.spikes_expected, [2])
        assert numpy.array_equal(spikes, target)
        spiketrains = neo.segments[0].spiketrains
        assert 2 == len(spiketrains)
        assert 2 == len(spiketrains[0])
        assert 2 == spiketrains[0].annotations['source_index']
        assert 0 == len(spiketrains[1])
        assert 3 == spiketrains[1].annotations['source_index']

        sim.end()

    def test_get_v_view(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
        pop.record("spikes")
        copy_db(False)

        view = pop[1:3]
        neo = view.get_data("v")
        v = neo.segments[0].filter(name='v')[0].magnitude
        target = self.v_expected()[:, 1:3]
        assert v.shape == target.shape
        assert numpy.array_equal(v,  target)

        sim.end()

    def test_get_v_missing(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
        pop[1:3].record("v")
        copy_db(True)

        view = pop[0:3]
        neo = view.get_data("v")
        v = neo.segments[0].filter(name='v')[0].magnitude
        target = self.v_expected[:, 0:3]
        assert numpy.array_equal(
            [1, 2], neo.segments[0].filter(name='v')[0].channel_index.index)
        assert v.shape == target.shape
        assert numpy.array_equal(v,  target)

        sim.end()

    def test_get_spike_counts(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp(), label="a label")
        pop.record("spikes")
        copy_db(False)

        assert {0: 7, 1: 3, 2: 2, 3: 0} == pop.get_spike_counts()

        view = pop[1:4]
        assert {1: 3, 2: 2, 3: 0} == view.get_spike_counts()

        assert 3 == pop.meanSpikeCount()
        assert 5/3 == view.mean_spike_count()

        sim.end()

    def test_write(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
        pop.record(["spikes", "v"])
        copy_db(False)

        # Note gather=False will be ignored just testing it can be
        pop.write_data("spikes.pkl", "spikes", gather=False)
        with open("spikes.pkl", "rb") as pkl:
            neo = pickle.load(pkl)
            spikes = neo_convertor.convert_spikes(neo)
            assert numpy.array_equal(spikes, self.spikes_expected)

        pop.printSpikes("spikes.pkl")
        with open("spikes.pkl", "rb") as pkl:
            neo = pickle.load(pkl)
            spikes = neo_convertor.convert_spikes(neo)
            assert numpy.array_equal(spikes, self.spikes_expected)

        pop.print_v("v.pkl")
        with open("v.pkl", "rb") as pkl:
            neo = pickle.load(pkl)
            v = neo.segments[0].filter(name='v')[0].magnitude
            assert v.shape == self.v_expected.shape
            assert numpy.array_equal(v,  self.v_expected)

        sim.end()

    def test_spinnaker_get_data(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
        pop.record("v")
        copy_db(False)
        SpynnakerDataView._mock_has_run()

        v = pop.spinnaker_get_data("v")
        assert len(v) == 35 * 5

        with pytest.raises(ConfigurationException):
            pop.spinnaker_get_data(["v", "spikes"])
        sim.end()
