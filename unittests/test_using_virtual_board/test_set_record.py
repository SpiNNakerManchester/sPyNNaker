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

import six

from data_specification.enums import DataType
from spynnaker.pyNN.models.common import NeuronRecorder
import spynnaker8 as sim
from p8_integration_tests.base_test_case import BaseTestCase


class TestSetRecord(BaseTestCase):
    assertListEq = six.assertCountEqual

    def test_set_spikes(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(1, sim.IF_curr_exp())
        self.assertListEq([], if_curr._get_all_recording_variables())
        ssa = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]))
        ssp = sim.Population(2, sim.SpikeSourcePoisson(rate=100.0),
                             additional_parameters={"seed": 1})
        if_curr.record("spikes")
        self.assertListEq(["spikes"], if_curr._get_all_recording_variables())
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

        try:
            ssa.record("v")
        except Exception as e:
            self.assertEqual(
                "This population does not support the recording of v!",
                str(e))
        try:
            ssp.record("v")
        except Exception as e:
            self.assertEqual(
                "This population does not support the recording of v!",
                str(e))

        sim.end()

    def test_set_all(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(1, sim.IF_curr_exp())
        ssa = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]))
        ssp = sim.Population(2, sim.SpikeSourcePoisson(rate=100.0),
                             additional_parameters={"seed": 1})
        if_curr.record("all")
        self.assertListEq(
            ["spikes", "v", "gsyn_inh", "gsyn_exc", "packets-per-timestep"],
            if_curr._get_all_recording_variables())
        ssa.record("all")
        self.assertListEq(["spikes"], ssa._get_all_recording_variables())
        ssp.record("all")
        self.assertListEq(["spikes"], ssp._get_all_recording_variables())
        sim.end()

    def test_set_spikes_interval(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(1, sim.IF_curr_exp())
        recorder = if_curr._vertex.neuron_recorder
        self.assertListEq([], if_curr._get_all_recording_variables())
        ssa = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]))
        ssp = sim.Population(2, sim.SpikeSourcePoisson(rate=100.0),
                             additional_parameters={"seed": 1})
        if_curr.record("spikes", sampling_interval=2)
        ssa.record("spikes", sampling_interval=2)
        ssp.record("spikes", sampling_interval=2)
        self.assertListEq(["spikes"], if_curr._get_all_recording_variables())
        assert recorder.get_neuron_sampling_interval("spikes") == 2

    def test_set_spikes_interval2(self):
        sim.setup(timestep=0.5)
        if_curr = sim.Population(1, sim.IF_curr_exp())
        recorder = if_curr._vertex.neuron_recorder
        self.assertListEq([], if_curr._get_all_recording_variables())
        if_curr.record("spikes", sampling_interval=2.5)
        self.assertListEq(["spikes"], if_curr._get_all_recording_variables())
        assert recorder.get_neuron_sampling_interval("spikes") == 2.5

    def test_set_spikes_indexes(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(5, sim.IF_curr_exp())
        recorder = if_curr._vertex.neuron_recorder
        ssa = sim.Population(
            5, sim.SpikeSourceArray(spike_times=[0]))
        ssp = sim.Population(5, sim.SpikeSourcePoisson(rate=100.0),
                             additional_parameters={"seed": 1})
        if_curr.record("spikes", indexes=[1, 2, 4])
        ssa.record("spikes", indexes=[1, 2, 4])
        ssp.record("spikes", indexes=[1, 2, 4])
        self.assertListEq(["spikes"], if_curr._get_all_recording_variables())
        assert recorder._indexes["spikes"] == [1, 2, 4]

    def test_set_spikes_indexes2(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(5, sim.IF_curr_exp())
        recorder = if_curr._vertex.neuron_recorder
        if_curr.record("spikes", indexes=[1, 2, 4])
        if_curr.record("spikes", indexes=[1, 3])
        self.assertListEq(["spikes"], if_curr._get_all_recording_variables())
        assert recorder._indexes["spikes"] == [1, 2, 3, 4]

    def test_turn_off_spikes_indexes(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(5, sim.IF_curr_exp())
        if_curr.record("spikes")
        if_curr.record(None)
        self.assertListEq([], if_curr._get_all_recording_variables())

    def test_set_spikes_indexes3(self):
        sim.setup(timestep=1)
        if_curr = sim.Population(5, sim.IF_curr_exp())
        if_curr.record("spikes")
        self.assertListEq(["spikes"], if_curr._get_all_recording_variables())

    # These test are currently directly on NeuronRecorder as no pynn way
    # to do this

    def test_turn_off_some_indexes(self):
        data_types = {
            "v": DataType.S1615,
            "gsyn_exc": DataType.S1615,
            "gsyn_inh": DataType.S1615}

        recorder = NeuronRecorder(
            ["v", "gsyn_exc", "gsyn_inh"], data_types, ["spikes"], 5, [], [])
        recorder.set_recording("spikes", True)
        self.assertListEq(["spikes"], recorder.recording_variables)
        recorder.set_recording("spikes", False, indexes=[2, 4])
        self.assertListEq([0, 1, 3], recorder._indexes["spikes"])
