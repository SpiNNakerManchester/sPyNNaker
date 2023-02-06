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
from data_specification.enums import DataType
from spynnaker.pyNN.models.common import NeuronRecorder
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestSetRecord(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_set_spikes(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(1, sim.IF_curr_exp())
        self.assertCountEqual(
            [], if_curr._vertex.get_recording_variables())
        ssa = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]))
        ssp = sim.Population(2, sim.SpikeSourcePoisson(rate=100.0),
                             additional_parameters={"seed": 1})
        if_curr.record("spikes")
        self.assertCountEqual(
            ["spikes"], if_curr._vertex.get_recording_variables())
        ssa.record("spikes")
        ssp.record("spikes")
        sim.end()

    def test_set_v(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(1, sim.IF_curr_exp())
        ssa = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]))
        ssp = sim.Population(2, sim.SpikeSourcePoisson(rate=100.0),
                             additional_parameters={"seed": 1})
        if_curr.record("v")

        # SpikeSourceArray must throw if asked to record voltage
        with self.assertRaises(Exception):
            ssa.record("v")

        # SpikeSourcePoisson must throw if asked to record voltage
        with self.assertRaises(Exception):
            ssp.record("v")

        sim.end()

    def test_set_all(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(1, sim.IF_curr_exp())
        ssa = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]))
        ssp = sim.Population(2, sim.SpikeSourcePoisson(rate=100.0),
                             additional_parameters={"seed": 1})
        if_curr.record("all")
        self.assertCountEqual(
            ["spikes", "v", "gsyn_inh", "gsyn_exc", "packets-per-timestep",
             "rewiring"],
            if_curr._vertex.get_recording_variables())
        ssa.record("all")
        self.assertCountEqual(
            ["spikes"], ssa._vertex.get_recording_variables())
        ssp.record("all")
        self.assertCountEqual(
            ["spikes"], ssp._vertex.get_recording_variables())
        sim.end()

    def test_set_spikes_interval(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(1, sim.IF_curr_exp())
        recorder = if_curr._vertex.neuron_recorder
        self.assertCountEqual(
            [], if_curr._vertex.get_recording_variables())
        ssa = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]))
        ssp = sim.Population(2, sim.SpikeSourcePoisson(rate=100.0),
                             additional_parameters={"seed": 1})
        if_curr.record("spikes", sampling_interval=2)
        ssa.record("spikes", sampling_interval=2)
        ssp.record("spikes", sampling_interval=2)
        self.assertCountEqual(
            ["spikes"], if_curr._vertex.get_recording_variables())
        assert recorder.get_sampling_interval_ms("spikes") == 2

    def test_set_spikes_interval2(self):
        sim.setup(timestep=0.5)
        if_curr = sim.Population(1, sim.IF_curr_exp())
        recorder = if_curr._vertex.neuron_recorder
        self.assertCountEqual(
            [], if_curr._vertex.get_recording_variables())
        if_curr.record("spikes", sampling_interval=2.5)
        self.assertCountEqual(
            ["spikes"], if_curr._vertex.get_recording_variables())
        assert recorder.get_sampling_interval_ms("spikes") == 2.5

    def test_set_spikes_indexes(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(5, sim.IF_curr_exp())
        recorder = if_curr._vertex.neuron_recorder
        ssa = sim.Population(
            5, sim.SpikeSourceArray(spike_times=[0]))
        ssp = sim.Population(5, sim.SpikeSourcePoisson(rate=100.0),
                             additional_parameters={"seed": 1})
        if_curr[1, 2, 4].record("spikes")
        ssa[1, 2, 4].record("spikes")
        ssp[1, 2, 4].record("spikes")
        self.assertCountEqual(
            ["spikes"], if_curr._vertex.get_recording_variables())
        assert recorder._indexes["spikes"] == [1, 2, 4]

    def test_set_spikes_indexes2(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(5, sim.IF_curr_exp())
        recorder = if_curr._vertex.neuron_recorder
        if_curr[1, 2, 4].record("spikes")
        if_curr[1, 3].record("spikes")
        self.assertCountEqual(
            ["spikes"], if_curr._vertex.get_recording_variables())
        assert recorder._indexes["spikes"] == [1, 2, 3, 4]

    def test_turn_off_spikes_indexes(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(5, sim.IF_curr_exp())
        if_curr.record("spikes")
        if_curr.record(None)
        self.assertCountEqual(
            [], if_curr._vertex.get_recording_variables())

    def test_set_spikes_indexes3(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(5, sim.IF_curr_exp())
        if_curr.record("spikes")
        self.assertCountEqual(
            ["spikes"], if_curr._vertex.get_recording_variables())

    # These test are currently directly on NeuronRecorder as no pynn way
    # to do this

    def test_turn_off_some_indexes(self):
        data_types = {
            "v": DataType.S1615,
            "gsyn_exc": DataType.S1615,
            "gsyn_inh": DataType.S1615}

        recorder = NeuronRecorder(
            ["v", "gsyn_exc", "gsyn_inh"], data_types, ["spikes"], 5, [], [],
            [], [])
        recorder.set_recording("spikes", True)
        self.assertCountEqual(["spikes"], recorder.recording_variables)
        recorder.set_recording("spikes", False, indexes=[2, 4])
        self.assertCountEqual([0, 1, 3], recorder._indexes["spikes"])
