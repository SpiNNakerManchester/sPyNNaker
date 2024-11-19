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

import os
from spinn_front_end_common.utilities.exceptions import ConfigurationException
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestRecordingLaterAdditions(BaseTestCase):

    def do_later_additions(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

        input_pop = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0, 7]), label="input")

        pop_a = sim.Population(1, sim.IF_curr_exp(), label="pop_a")
        sim.Projection(input_pop, pop_a, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop_a.record(["spikes", "v"])

        pop_b = sim.Population(1, sim.IF_curr_exp(), label="pop_b")
        sim.Projection(input_pop, pop_b, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))

        pop_c = sim.Population(1, sim.IF_curr_exp(), label="pop_c")
        sim.Projection(input_pop, pop_c, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop_c.record(["spikes"])

        sim.run(10)

        # Did not record all these should fail
        with self.assertRaises(ConfigurationException):
            pop_b.get_data(variables=["spikes", "v"])
        with self.assertRaises(ConfigurationException):
            pop_b.get_spike_counts()
        with self.assertRaises(ConfigurationException):
            pop_b.write_data("test_b_bad.csv", ["spikes", "v"])
        with self.assertRaises(ConfigurationException):
            pop_c.get_data(variables=["spikes", "v"])
        with self.assertRaises(ConfigurationException):
            pop_c.write_data("test_c_bad.csv", ["spikes", "v"])

        sim.reset()

        # No recording from previous segment so should fail
        with self.assertRaises(ConfigurationException):
            pop_b.get_data(variables=["spikes", "v"])
        with self.assertRaises(ConfigurationException):
            pop_b.write_data("test_b_bad.csv", ["spikes", "v"])
        # Only includes this segment so should fail
        with self.assertRaises(ConfigurationException):
            pop_b.get_spike_counts()
        # Some recording from previous will wok
        pop_c.get_data(variables=["spikes", "v"])
        pop_c.write_data("test_c_1.csv", ["spikes", "v"])

        pop_b.record(["spikes", "v"])
        pop_c.record(["v"])

        # No recording from previous segment so should fail
        with self.assertRaises(ConfigurationException):
            pop_b.get_data(variables=["spikes", "v"])
        with self.assertRaises(ConfigurationException):
            pop_b.write_data("test_b_bad.csv", ["spikes", "v"])
        # Only includes this segment so should fail
        with self.assertRaises(ConfigurationException):
            pop_b.get_spike_counts()
        # Some recording from previous will wok
        pop_c.get_data(variables=["spikes", "v"])
        pop_c.write_data("test_c_1.csv", ["spikes", "v"])

        sim.run(20)

        neo_a = pop_a.get_data(variables=["spikes", "v"])
        spikes_a_0 = neo_a.segments[0].spiketrains
        self.assertEqual(1, len(spikes_a_0),
                         "Expected 1 spiketrains for pop_a segment 0")
        self.assertEqual(1, len(spikes_a_0[0]),
                         "Expected 1 spike for pop_a segment 0")
        spikes_a_1 = neo_a.segments[1].spiketrains
        self.assertEqual(1, len(spikes_a_1),
                         "Expected 1 spiketrains for pop_a segment 1")
        self.assertEqual(2, len(spikes_a_1[0]),
                         "Expected 1 spike for pop_a segment 1")
        v_a_0 = neo_a.segments[0].filter(name='v')
        self.assertEqual(1, len(v_a_0),
                         "Expected 1 voltage array for pop_a segment 0")
        self.assertEqual(10, len(v_a_0[0]),
                         "Expected 10 volatge readings for pop_a segment 0")
        v_a_1 = neo_a.segments[1].filter(name='v')
        self.assertEqual(1, len(v_a_1),
                         "Expected 1 voltage array for pop_a segment 1")
        self.assertEqual(20, len(v_a_1[0]),
                         "Expected 20 voltage readings for pop_a segment 1")
        sc_a = pop_a.get_spike_counts()
        self.assertEqual({0: 2}, sc_a, "spike counts for pop_a ")
        pop_a.write_data("test_a.csv", ["spikes", "v"])

        neo_b = pop_b.get_data(variables=["spikes", "v"])
        spikes_b_0 = neo_b.segments[0].spiketrains
        self.assertEqual(0, len(spikes_b_0),
                         "Expected no spikes for pop_b segement 0")
        spikes_b_1 = neo_b.segments[1].spiketrains
        self.assertEqual(1, len(spikes_b_1),
                         "Expected 1 spiketrains for pop_b segment 1")
        self.assertEqual(2, len(spikes_b_1[0]),
                         "Expected 2 spikes for pop_b segment 1")
        v_b_0 = neo_b.segments[0].filter(name='v')
        self.assertEqual(0, len(v_b_0),
                         "Expected no voltage for pop_b segment 0")
        v_b_1 = neo_b.segments[1].filter(name='v')
        self.assertEqual(1, len(v_b_1),
                         "Expected 1 voltage array for pop_b segment 1")
        self.assertEqual(20, len(v_b_1[0]),
                         "Expected 20 voltage readings for pop_b segment 1")
        sc_b = pop_b.get_spike_counts()
        self.assertEqual({0: 2}, sc_b, "spike counts for pop_a ")
        pop_b.write_data("test_b.csv", ["spikes", "v"])

        neo_c = pop_c.get_data(variables=["spikes", "v"])
        spikes_c_0 = neo_c.segments[0].spiketrains
        self.assertEqual(1, len(spikes_c_0),
                         "Expected 1 spiketrains for pop_c segment 0")
        self.assertEqual(1, len(spikes_c_0[0]),
                         "Expected 1 spike for pop_c segment 0")
        spikes_c_1 = neo_c.segments[1].spiketrains
        self.assertEqual(1, len(spikes_c_1),
                         "Expected 1 spiketrains for pop_c segment 1")
        self.assertEqual(2, len(spikes_c_1[0]),
                         "Expected 1 spike for pop_c segment 1")
        v_c_0 = neo_c.segments[0].filter(name='v')
        self.assertEqual(0, len(v_c_0),
                         "Expected 0 voltage array for pop_c segment 0")
        v_c_1 = neo_c.segments[1].filter(name='v')
        self.assertEqual(1, len(v_c_1),
                         "Expected 1 voltage array for pop_c segment 1")
        self.assertEqual(20, len(v_c_1[0]),
                         "Expected 20 voltage readings for pop_c segment 1")
        sc_c = pop_c.get_spike_counts()
        self.assertEqual({0: 2}, sc_c, "spike counts for pop_c")
        pop_c.write_data("test_c.csv", ["spikes", "v"])
        sim.end()

    def cleanup(self, file):
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception:
            pass

    def test_later_additions(self):
        self.cleanup("test_a.csv")
        self.cleanup("test_b.csv")
        self.cleanup("test_b_bad.csv")
        self.cleanup("test_c.csv")
        self.cleanup("test_c_1.csv")
        self.cleanup("test_c_bad.csv")
        self.runsafe(self.do_later_additions)
