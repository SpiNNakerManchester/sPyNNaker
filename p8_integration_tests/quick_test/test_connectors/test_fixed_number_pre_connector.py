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

import spynnaker8 as sim
from spynnaker.pyNN.exceptions import SpynnakerException
from p8_integration_tests.base_test_case import BaseTestCase

SOURCES = 5
DESTINATIONS = 10


class TestFixedNumberPreConnector(BaseTestCase):

    def check_weights(self, projection, connections, with_replacement,
                      allow_self_connections):
        weights = projection.get(["weight"], "list")
        print(weights)
        last_source = -1
        last_destination = -1
        for (source, destination, _) in weights:
            if source != last_source:
                last_source = source
            else:
                if not with_replacement:
                    self.assertNotEqual(last_destination, destination)
            last_destination = destination
            if not allow_self_connections:
                self.assertNotEqual(source, destination)

    def check_self_connect(self, connections, with_replacement,
                           allow_self_connections):
        sim.setup(1.0)
        pop = sim.Population(DESTINATIONS, sim.IF_curr_exp(), label="pop")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop, pop, sim.FixedNumberPreConnector(
                connections, with_replacement=with_replacement,
                allow_self_connections=allow_self_connections),
            synapse_type=synapse_type)
        sim.run(0)
        self.check_weights(projection, connections, with_replacement,
                           allow_self_connections)
        sim.end()

    def check_other_connect(self, connections, with_replacement):
        sim.setup(1.0)
        pop1 = sim.Population(SOURCES, sim.IF_curr_exp(), label="pop1")
        pop2 = sim.Population(DESTINATIONS, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop1, pop2, sim.FixedNumberPreConnector(
                connections, with_replacement=with_replacement),
            synapse_type=synapse_type)
        sim.run(0)
        self.check_weights(projection, connections, with_replacement,
                           allow_self_connections=True)
        sim.end()

    def test_replace_self(self):
        with_replacement = True
        allow_self_connections = True
        self.check_self_connect(
            DESTINATIONS-2, with_replacement, allow_self_connections)

    def test_replace_no_self(self):
        with_replacement = True
        allow_self_connections = False
        self.check_self_connect(
            DESTINATIONS-2, with_replacement, allow_self_connections)

    def test_no_replace_self(self):
        with_replacement = True
        allow_self_connections = True
        self.check_self_connect(
            DESTINATIONS-2, with_replacement, allow_self_connections)

    def test_no_replace_no_self(self):
        with_replacement = True
        allow_self_connections = False
        self.check_self_connect(
            SOURCES-2, with_replacement, allow_self_connections)

    def test_with_many_replace_self(self):
        with_replacement = True
        allow_self_connections = True
        self.check_self_connect(
            DESTINATIONS+2, with_replacement, allow_self_connections)

    def test_all_no_replace_self(self):
        with_replacement = False
        allow_self_connections = True
        self.check_self_connect(
            SOURCES, with_replacement, allow_self_connections)

    def test_all_no_replace_no_self(self):
        with_replacement = False
        allow_self_connections = False
        with self.assertRaises(SpynnakerException):
            self.check_self_connect(
                DESTINATIONS, with_replacement, allow_self_connections)

    def test_all_replace_no_self(self):
        with_replacement = False
        allow_self_connections = True
        self.check_self_connect(
            DESTINATIONS, with_replacement, allow_self_connections)

    def test_replace_other(self):
        with_replacement = True
        self.check_other_connect(SOURCES-2, with_replacement)

    def test_no_replace_other(self):
        with_replacement = False
        self.check_other_connect(SOURCES-2, with_replacement)

    def test_replace_other_many(self):
        with_replacement = True
        self.check_other_connect(SOURCES+3, with_replacement)

    def test_no_replace_other_too_many(self):
        with_replacement = False
        with self.assertRaises(SpynnakerException):
            self.check_other_connect(SOURCES+3, with_replacement)

    def test_get_before_run(self):
        sim.setup(1.0)
        pop1 = sim.Population(3, sim.IF_curr_exp(), label="pop1")
        pop2 = sim.Population(3, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop1, pop2, sim.FixedNumberPreConnector(2),
            synapse_type=synapse_type)
        weights = projection.get(["weight"], "list")
        sim.run(0)
        self.assertEqual(6, len(weights))
        sim.end()

    def test_with_delays(self):
        sim.setup(1.0)
        # Break up the pre population as that is where delays happen
        sim.set_number_of_neurons_per_core(sim.SpikeSourceArray, 50)
        pop1 = sim.Population(100, sim.SpikeSourceArray([1]), label="pop1")
        pop2 = sim.Population(10, sim.IF_curr_exp(), label="pop2")
        pop2.record("spikes")
        # Choose to use delay extensions
        synapse_type = sim.StaticSynapse(weight=0.5, delay=17)
        conn = sim.FixedNumberPreConnector(10)
        projection = sim.Projection(
            pop1, pop2, conn, synapse_type=synapse_type)
        delays = projection.get(["delay"], "list")
        sim.run(30)
        # There are 100 connections, as there are 10 for each post-neuron
        assert(len(delays) == 100)
        # If the delays are done right, all pre-spikes should arrive at the
        # same time causing each neuron in the post-population to spike
        spikes = pop2.get_data("spikes").segments[0].spiketrains
        for s in spikes:
            assert(len(s) == 1)
        sim.end()
