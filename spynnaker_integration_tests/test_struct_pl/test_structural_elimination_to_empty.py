# Copyright (c) 2017-2023 The University of Manchester
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
from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as p


def structural_eliminate_to_empty():
    p.setup(1.0)
    p.set_number_of_neurons_per_core(p.IF_curr_exp, 5)
    stim = p.Population(9, p.SpikeSourceArray(range(10)), label="stim")

    # These populations should experience elimination
    pop = p.Population(9, p.IF_curr_exp(), label="pop")

    # Make a full list

    # Elimination with random selection (0 probability formation)
    proj = p.Projection(
        stim, pop, p.AllToAllConnector(),
        p.StructuralMechanismStatic(
            partner_selection=p.RandomSelection(),
            formation=p.DistanceDependentFormation([3, 3], 0.0),
            elimination=p.RandomByWeightElimination(4.0, 1.0, 1.0),
            f_rew=1000, initial_weight=4.0, initial_delay=3.0,
            s_max=9, seed=0, weight=0.0, delay=1.0))

    pop.record("rewiring")

    p.run(1000)

    # Get the final connections
    conns = list(proj.get(["weight", "delay"], "list"))

    rewiring = pop.get_data("rewiring")
    formation_events = rewiring.segments[0].events[0]
    elimination_events = rewiring.segments[0].events[1]

    num_forms = len(formation_events.times)
    num_elims = len(elimination_events.times)

    first_elim = elimination_events.labels[0]

    p.end()

    # These should have no connections since all should be eliminated
    assert len(conns) == 0
    assert num_elims == 81
    assert num_forms == 0
    assert first_elim == "8_5_elimination"
    assert "7_5_elimination" in elimination_events.labels


class TestStructuralEliminateToEmpty(BaseTestCase):

    def test_structural_eliminate_to_empty(self):
        self.runsafe(structural_eliminate_to_empty)


if __name__ == "__main__":
    structural_eliminate_to_empty()
