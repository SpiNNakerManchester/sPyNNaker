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
