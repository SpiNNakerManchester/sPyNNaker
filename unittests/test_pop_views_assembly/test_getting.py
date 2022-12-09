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
import pickle
from unittest import SkipTest
import numpy
import pytest
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.recorder import Recorder
import pyNN.spiNNaker as sim
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


def mock_spikes(_self, _variable):
    return numpy.array(
        [[0, 7], [0, 20], [0, 24], [0, 34], [0, 53], [0, 67], [0, 77],
         [1, 8], [1, 20], [1, 53],
         [2, 45], [2, 76]])


def mock_v_all(_self, _variable):
    indexes = [0, 1, 2, 3]
    data = numpy.empty((100, 4))
    for i in range(100):
        for j in indexes:
            data[i][j] = -65 + j + i/100
    return data


def mock_v_one_two(_self, _variable):
    indexes = [1, 2]
    data = numpy.empty((100, 2))
    for i in range(100):
        for j in range(len(indexes)):
            data[i][j] = -65 + indexes[j] + i/100
    return data


def trim_spikes(spikes, indexes):
    return [[n, t] for [n, t] in spikes if n in indexes]


class TestGetting(BaseTestCase):
    def setUp(self):
        """ Save the real methods that we mock out """
        # NO unittest_setup() as sim.setup is called
        self.__get_data = Recorder.get_data

    def tearDown(self):
        """ Restore the real methods that we may have mocked out """
        Recorder.get_data = self.__get_data

    def test_simple_spikes(self):
        view = SpynnakerDataView()
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp(), label="a label")
        Recorder.get_data = mock_spikes
        # Hack method not supported
        view._FecDataView__fec_data._first_machine_time_step = \
            view._FecDataView__fec_data._current_run_timesteps
        view._FecDataView__fec_data._current_run_timesteps += 100

        neo = pop.get_data("spikes")
        spikes = neo_convertor.convert_spikes(neo)
        assert numpy.array_equal(spikes,  mock_spikes(None, None))
        spiketrains = neo.segments[0].spiketrains
        assert 4 == len(spiketrains)

        #  gather False has not effect testing that here
        neo = pop.get_data("spikes", gather=False)
        spikes = neo_convertor.convert_spikes(neo)
        assert numpy.array_equal(spikes,  mock_spikes(None, None))
        spiketrains = neo.segments[0].spiketrains
        assert 4 == len(spiketrains)

        Recorder.get_data = mock_v_all
        neo = pop.get_data("v")
        v = neo.segments[0].filter(name='v')[0].magnitude
        target = mock_v_all(None, "any")
        assert numpy.array_equal(v,  target)

        neo = pop.get_data(['gsyn_exc', 'gsyn_inh'])
        exc = neo.segments[0].filter(name='gsyn_exc')[0].magnitude
        assert numpy.array_equal(exc,  target)
        inh = neo.segments[0].filter(name='gsyn_inh')[0].magnitude
        assert numpy.array_equal(inh,  target)

        sim.end()

    def test_get_spikes_by_index(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp(), label="a label")
        pop.record("spikes")

        Recorder.get_data = mock_spikes
        view = SpynnakerDataView()
        # Hack method not supported
        view._FecDataView__fec_data._first_machine_time_step = \
            view._FecDataView__fec_data._current_run_timesteps
        view._FecDataView__fec_data._current_run_timesteps += 100

        neo = pop[1, 2].get_data("spikes")
        spikes = neo_convertor.convert_spikes(neo)
        target = trim_spikes(mock_spikes(None, None), [1, 2])
        assert numpy.array_equal(spikes, target)
        spiketrains = neo.segments[0].spiketrains
        assert 2 == len(spiketrains)

        sim.end()

    def test_get_spikes_by_view(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp(), label="a label")
        Recorder.get_data = mock_spikes
        view = SpynnakerDataView()
        # Hack method not supported
        view._FecDataView__fec_data._first_machine_time_step = \
            view._FecDataView__fec_data._current_run_timesteps
        view._FecDataView__fec_data._current_run_timesteps += 100

        view = pop[1:3]
        view.record("spikes")
        neo = view.get_data("spikes", gather=False)
        spikes = neo_convertor.convert_spikes(neo)
        target = trim_spikes(mock_spikes(None, None), [1, 2])
        assert numpy.array_equal(spikes, target)
        spiketrains = neo.segments[0].spiketrains
        assert 2 == len(spiketrains)

        sim.end()

    def test_get_spikes_view_missing(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp(), label="a label")
        Recorder.get_data = mock_spikes
        view = SpynnakerDataView()
        # Hack method not supported
        view._FecDataView__fec_data._first_machine_time_step = \
            view._FecDataView__fec_data._current_run_timesteps
        view._FecDataView__fec_data._current_run_timesteps += 100

        view = pop[2:4]
        neo = view.get_data("spikes")
        spikes = neo_convertor.convert_spikes(neo)
        target = trim_spikes(mock_spikes(None, None), [2])
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
        pop = sim.Population(4, sim.IF_curr_exp(), label="a label")
        pop.record("spikes")
        Recorder.get_data = mock_v_all
        view = SpynnakerDataView()
        # Hack method not supported
        view._FecDataView__fec_data._first_machine_time_step = \
            view._FecDataView__fec_data._current_run_timesteps
        view._FecDataView__fec_data._current_run_timesteps += 100

        view = pop[1:3]
        neo = view.get_data("v")
        v = neo.segments[0].filter(name='v')[0].magnitude
        target = mock_v_one_two(None, "v")
        assert v.shape == target.shape
        assert numpy.array_equal(v,  target)

        sim.end()

    def test_get_v_missing(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp(), label="a label")
        pop[1:3].record("v")
        Recorder.get_data = mock_v_one_two
        data_view = SpynnakerDataView()
        # Hack method not supported
        data_view._FecDataView__fec_data._first_machine_time_step = \
            data_view._FecDataView__fec_data._current_run_timesteps
        data_view._FecDataView__fec_data._current_run_timesteps += 100

        view = pop[0:3]
        neo = view.get_data("v")
        v = neo.segments[0].filter(name='v')[0].magnitude
        target = mock_v_one_two(None, "v")
        assert numpy.array_equal(
            [1, 2], neo.segments[0].filter(name='v')[0].channel_index.index)
        assert v.shape == target.shape
        assert numpy.array_equal(v,  target)

        sim.end()

    def test_get_spike_counts(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp(), label="a label")
        pop.record("spikes")
        Recorder.get_data = mock_spikes
        view = SpynnakerDataView()
        # Hack method not supported
        view._FecDataView__fec_data._first_machine_time_step = \
            view._FecDataView__fec_data._current_run_timesteps
        view._FecDataView__fec_data._current_run_timesteps += 100

        assert {0: 7, 1: 3, 2: 2, 3: 0} == pop.get_spike_counts()

        view = pop[1:4]
        assert {1: 3, 2: 2, 3: 0} == view.get_spike_counts()

        assert 3 == pop.mean_spike_count()
        assert 5/3 == view.mean_spike_count()

        sim.end()

    def test_write(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp(), label="a label")
        pop.record(["spikes", "v"])
        Recorder.get_data = mock_spikes
        view = SpynnakerDataView()
        # Hack method not supported
        view._FecDataView__fec_data._first_machine_time_step = \
            view._FecDataView__fec_data._current_run_timesteps
        view._FecDataView__fec_data._current_run_timesteps += 100

        # Note gather=False will be ignored just testing it can be
        pop.write_data("spikes.pkl", "spikes", gather=False)
        try:
            with open("spikes.pkl", encoding="utf-8") as pkl:
                neo = pickle.load(pkl)
                spikes = neo_convertor.convert_spikes(neo)
                assert numpy.array_equal(spikes,  mock_spikes(None))
        except UnicodeDecodeError as e:
            raise SkipTest(
                "https://github.com/NeuralEnsemble/python-neo/issues/529"
                ) from e

        pop.write_data("spikes.pkl", 'spikes')
        try:
            with open("spikes.pkl", encoding="utf-8") as pkl:
                neo = pickle.load(pkl)
                spikes = neo_convertor.convert_spikes(neo)
                assert numpy.array_equal(spikes,  mock_spikes(None))
        except UnicodeDecodeError as e:
            raise SkipTest(
                "https://github.com/NeuralEnsemble/python-neo/issues/529"
                ) from e

        Recorder.get_data = mock_v_all
        (target, _, _) = mock_v_all(None, "any")

        pop.write_data("v.pkl", 'v')
        with open("v.pkl", encoding="utf-8") as pkl:
            neo = pickle.load(pkl)
            v = neo.segments[0].filter(name='v')[0].magnitude
            assert v.shape == target.shape
            assert numpy.array_equal(v,  target)

        pop.write_data("gsyn.pkl", ['gsyn_exc', 'gsyn_inh'])
        with open("gsyn.pkl", encoding="utf-8") as pkl:
            neo = pickle.load(pkl)
            exc = neo.segments[0].filter(name='gsyn_exc')[0].magnitude
            assert numpy.array_equal(exc,  target)
            inh = neo.segments[0].filter(name='gsyn_inh')[0].magnitude
            assert numpy.array_equal(inh,  target)

        sim.end()

    def test_spinnaker_get_data(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp(), label="a label")
        pop.record("v")
        Recorder.get_data = mock_v_all
        view = SpynnakerDataView()
        # Hack method not supported
        view._FecDataView__fec_data._first_machine_time_step = \
            view._FecDataView__fec_data._current_run_timesteps
        view._FecDataView__fec_data._current_run_timesteps += 100

        v = pop.spinnaker_get_data("v")
        assert 400 == len(v)

        v = pop.spinnaker_get_data(["v"])
        assert 400 == len(v)

        with pytest.raises(ConfigurationException):
            pop.spinnaker_get_data(["v", "spikes"])
        sim.end()
