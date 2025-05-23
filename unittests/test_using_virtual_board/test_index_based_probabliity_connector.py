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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase

from spynnaker.pyNN.models.projection import Projection

WEIGHT = 5
DELAY = 2


class TestIndexBasedProbabilityConnector(BaseTestCase):

    def check_weights(self, projection: Projection, n: int, expression: str,
                      allow_self_connections: bool) -> None:
        weights = projection.get(["weight"], "list")
        pairs = [(s, d) for (s, d, _) in weights]
        must_count = 0
        maybe_count = 0
        for i in range(n):
            for j in range(n):
                if not allow_self_connections and (i == j):
                    self.assertNotIn((i, j), pairs)
                    continue
                kwargs = {"i": i, "j": j}
                prob = eval(expression, kwargs)
                if prob == 1:
                    self.assertIn((i, j), pairs)
                    must_count += 1
                elif prob == 0:
                    self.assertNotIn((i, j), pairs)
                else:
                    maybe_count += 1
        # Check at least one maybe connected
        self.assertLessEqual(len(weights), must_count + maybe_count)
        # Check not all the maybes connected
        self.assertGreaterEqual(len(weights), must_count)

    def check_connect(self, n: int, expression: str) -> None:
        sim.setup(1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 10)
        pop1 = sim.Population(
            n, sim.SpikeSourceArray(spike_times=[0]), label="input")
        pop2 = sim.Population(n, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=2)

        projection = sim.Projection(
            pop1, pop2, sim.IndexBasedProbabilityConnector(expression),
            synapse_type=synapse_type)
        sim.run(0)
        self.check_weights(projection, n, expression, True)
        sim.end()

    def check_connect_no_self(self, n: int, expression: str) -> None:
        sim.setup(1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 10)
        pop = sim.Population(n, sim.IF_curr_exp(), label="pop")
        synapse_type = sim.StaticSynapse(weight=5, delay=2)

        projection = sim.Projection(
            pop, pop, sim.IndexBasedProbabilityConnector(
                expression, allow_self_connections=False),
            synapse_type=synapse_type)
        sim.run(0)
        self.check_weights(projection, n, expression, False)
        sim.end()

    def test_self(self) -> None:
        self.check_connect(
            n=6, expression="(i+j)%3*0.5")

    def test_other(self) -> None:
        self.check_connect_no_self(
            n=6, expression="(i+j)%3*0.5")
