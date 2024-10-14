#!/usr/bin/python

# Copyright (c) 2024 The University of Manchester
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

from time import sleep
import numpy
from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as sim


class TestSendMultiplePartitions(BaseTestCase):

    def send_spike(self, label, conn):
        sleep(0.1)
        conn.send_spike(label, 0)

    # Added to check that the delay expander runs; a previous fix
    # for a related issue inadvertently turned it off for this type of case
    def do_run(self):
        conn = sim.external_devices.SpynnakerLiveSpikesConnection(
            send_labels=["Inject"], local_port=None)
        conn.add_start_resume_callback("Inject", self.send_spike)

        sim.setup(1.0)
        source_1 = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]))
        source_2 = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[5]))
        injector = sim.Population(
            1, sim.external_devices.SpikeInjector(
                database_notify_port_num=conn.local_port), label="Inject")
        target = sim.Population(3, sim.IF_curr_exp())
        target.record("spikes")
        proj_1 = sim.Projection(
            source_1, target, sim.FromListConnector([(0, 0)]),
            synapse_type=sim.StaticSynapse(weight=5.0))
        proj_2 = sim.Projection(
            source_2, target, sim.FromListConnector([(0, 1)]),
            synapse_type=sim.StaticSynapse(weight=5.0), partition_id="Test")
        proj_3 = sim.Projection(
            injector, target, sim.FromListConnector([(0, 2)]),
            synapse_type=sim.StaticSynapse(weight=5.0), partition_id="Inject")

        sim.run(1000)

        spikes = target.get_data("spikes").segments[0].spiketrains
        weights_1 = proj_1.get("weight", format="list")
        weights_2 = proj_2.get("weight", format="list")
        weights_3 = proj_3.get("weight", format="list")

        sim.end()

        print(spikes)
        print(weights_1)
        print(weights_2)
        print(weights_3)

        # There should be a spike to each neuron
        self.assertEqual(len(spikes[0]), 1)
        self.assertEqual(len(spikes[1]), 1)
        self.assertEqual(len(spikes[2]), 1)

        self.assertListEqual(list(weights_1), [[0, 0, 5.0]])
        self.assertListEqual(list(weights_2), [[0, 1, 5.0]])
        self.assertListEqual(list(weights_3), [[0, 2, 5.0]])

    def test_run(self):
        self.runsafe(self.do_run)
