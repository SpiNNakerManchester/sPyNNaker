# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pyNN.spiNNaker as sim
from spynnaker.pyNN.exceptions import SpynnakerException
from spinnaker_testbase import BaseTestCase

SOURCES = 5
DESTINATIONS = 10


class TestFixedNumberPostConnector(BaseTestCase):

    def check_weights(self, projection, connections, with_replacement,
                      allow_self_connections):
        weights = projection.get(["weight"], "list")
        last_source = -1
        last_destination = -1
        count = connections
        for (source, destination, _) in weights:
            if source != last_source:
                self.assertEqual(connections, count)
                last_source = source
                count = 1
            else:
                count += 1
                if not with_replacement:
                    self.assertNotEqual(last_destination, destination)
            last_destination = destination
            if not allow_self_connections:
                self.assertNotEqual(source, destination)

        self.assertEqual(connections, count)

    def check_self_connect(
            self, connections, with_replacement, allow_self_connections):
        sim.setup(1.0)
        pop = sim.Population(DESTINATIONS, sim.IF_curr_exp(), label="pop")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop, pop, sim.FixedNumberPostConnector(
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
            pop1, pop2, sim.FixedNumberPostConnector(
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
            DESTINATIONS-3, with_replacement, allow_self_connections)

    def test_replace_no_self(self):
        with_replacement = True
        allow_self_connections = False
        self.check_self_connect(
            DESTINATIONS-3, with_replacement, allow_self_connections)

    def test_no_replace_self(self):
        with_replacement = True
        allow_self_connections = True
        self.check_self_connect(
            DESTINATIONS-3, with_replacement, allow_self_connections)

    def test_no_replace_no_self(self):
        with_replacement = True
        allow_self_connections = False
        self.check_self_connect(
            DESTINATIONS-3, with_replacement, allow_self_connections)

    def test_all_no_replace_self(self):
        with_replacement = False
        allow_self_connections = True
        self.check_self_connect(DESTINATIONS, with_replacement,
                                allow_self_connections)

    def test_all_no_replace_no_self(self):
        with_replacement = False
        allow_self_connections = False
        with self.assertRaises(SpynnakerException):
            self.check_self_connect(DESTINATIONS, with_replacement,
                                    allow_self_connections)

    def test_with_many_replace_self(self):
        with_replacement = True
        allow_self_connections = True
        self.check_self_connect(
            DESTINATIONS+5, with_replacement, allow_self_connections)

    def test_replace_other(self):
        with_replacement = True
        self.check_other_connect(DESTINATIONS-3, with_replacement)

    def test_no_replace_other(self):
        with_replacement = False
        self.check_other_connect(DESTINATIONS-3, with_replacement)

    def test_replace_other_many(self):
        with_replacement = True
        self.check_other_connect(DESTINATIONS+3, with_replacement)

    def test_no_replace_other_too_many(self):
        with_replacement = False
        with self.assertRaises(SpynnakerException):
            self.check_other_connect(DESTINATIONS+3, with_replacement)

    def test_get_before_run(self):
        sim.setup(1.0)
        pop1 = sim.Population(3, sim.IF_curr_exp(), label="pop1")
        pop2 = sim.Population(3, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop1, pop2, sim.FixedNumberPostConnector(2),
            synapse_type=synapse_type)
        weights = projection.get(["weight"], "list")
        sim.run(0)
        self.assertEqual(6, len(weights))
        sim.end()

    def test_check_connection_estimates(self):
        # Test that the estimates for connections per neuron/vertex work
        sim.setup(timestep=1.0)
        n_neurons = 25
        pop1 = sim.Population(n_neurons, sim.IF_curr_exp(), label="pop_1")
        pop2 = sim.Population(n_neurons, sim.IF_curr_exp(), label="pop_2")
        projection = sim.Projection(
            pop1, pop2, sim.FixedNumberPostConnector(n_neurons//2),
            synapse_type=sim.StaticSynapse(weight=5, delay=1))
        simtime = 10
        sim.run(simtime)
        weights = projection.get(["weight"], "list")
        self.assertEqual(n_neurons*int(n_neurons/2), len(weights))
        sim.end()
