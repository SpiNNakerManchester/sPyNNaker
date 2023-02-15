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
from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as p


def structural_formation_to_full():
    p.setup(1.0)
    stim = p.Population(4, p.SpikeSourceArray(range(10)), label="stim")

    # These populations should experience formation
    pop = p.Population(4, p.IF_curr_exp(), label="pop")

    # Formation with random selection (0 probability elimination), setting
    # with_replacement=False means an all-to-all connection will be the result
    proj = p.Projection(
        stim, pop, p.FromListConnector([]), p.StructuralMechanismStatic(
            partner_selection=p.LastNeuronSelection(),
            formation=p.DistanceDependentFormation([2, 2], 1.0),
            elimination=p.RandomByWeightElimination(4.0, 0, 0),
            f_rew=1000, initial_weight=4.0, initial_delay=3.0,
            s_max=4, seed=0, weight=0.0, delay=1.0, with_replacement=False))

    pop.record("rewiring")

    p.run(1000)

    # Get the final connections
    conns = proj.get(["weight", "delay"], "list")

    rewiring = pop.get_data("rewiring")

    formation_events = rewiring.segments[0].events[0]
    elimination_events = rewiring.segments[0].events[1]

    num_forms = len(formation_events.times)
    num_elims = len(elimination_events.times)

    first_f = formation_events.labels[0]

    p.end()

    return conns, num_forms, num_elims, first_f


def structural_formation_to_full_with_reset():
    p.setup(1.0)
    stim = p.Population(4, p.SpikeSourceArray(range(10)), label="stim")

    # These populations should experience formation
    pop = p.Population(4, p.IF_curr_exp(), label="pop")

    # Formation with random selection (0 probability elimination), setting
    # with_replacement=False means an all-to-all connection will be the result
    proj = p.Projection(
        stim, pop, p.FromListConnector([]), p.StructuralMechanismStatic(
            partner_selection=p.LastNeuronSelection(),
            formation=p.DistanceDependentFormation([2, 2], 1.0),
            elimination=p.RandomByWeightElimination(4.0, 0, 0),
            f_rew=1000, initial_weight=4.0, initial_delay=3.0,
            s_max=4, seed=0, weight=0.0, delay=1.0, with_replacement=False))

    pop.record("rewiring")

    p.run(1000)

    p.Population(4, p.IF_curr_exp(), label="pop2")
    p.reset()

    p.run(1000)

    # Get the final connections
    conns = proj.get(["weight", "delay"], "list")

    rewiring = pop.get_data("rewiring")

    formation_events = rewiring.segments[0].events[0]
    formation_events2 = rewiring.segments[1].events[0]

    num_forms = len(formation_events.times)
    num_forms2 = len(formation_events2.times)

    first_f = formation_events.labels[0]
    first_f2 = formation_events2.labels[0]

    p.end()

    return conns, num_forms, num_forms2, first_f, first_f2


class TestStructuralFormationToFull(BaseTestCase):
    def do_run(self):
        conns, num_forms, num_elims, first_f = structural_formation_to_full()
        # Should have built all-to-all connectivity
        all_to_all_conns = [
            [0, 0, 4., 3.], [0, 1, 4., 3.], [0, 2, 4., 3.], [0, 3, 4., 3.],
            [1, 0, 4., 3.], [1, 1, 4., 3.], [1, 2, 4., 3.], [1, 3, 4., 3.],
            [2, 0, 4., 3.], [2, 1, 4., 3.], [2, 2, 4., 3.], [2, 3, 4., 3.],
            [3, 0, 4., 3.], [3, 1, 4., 3.], [3, 2, 4., 3.], [3, 3, 4., 3.]]
        first_formation = "3_3_formation"

        self.assertCountEqual(all_to_all_conns, conns)
        self.assertEqual(len(conns), 16)
        self.assertEqual(num_forms, 16)
        self.assertEqual(num_elims, 0)
        self.assertEqual(first_f, first_formation)

    def do_run_with_reset(self):
        conns, num_forms, num_forms2, first_f, first_f2 = \
            structural_formation_to_full_with_reset()
        # Should have built all-to-all connectivity
        all_to_all_conns = [
            [0, 0, 4., 3.], [0, 1, 4., 3.], [0, 2, 4., 3.], [0, 3, 4., 3.],
            [1, 0, 4., 3.], [1, 1, 4., 3.], [1, 2, 4., 3.], [1, 3, 4., 3.],
            [2, 0, 4., 3.], [2, 1, 4., 3.], [2, 2, 4., 3.], [2, 3, 4., 3.],
            [3, 0, 4., 3.], [3, 1, 4., 3.], [3, 2, 4., 3.], [3, 3, 4., 3.]]
        first_formation = "3_3_formation"

        self.assertCountEqual(all_to_all_conns, conns)
        self.assertEqual(num_forms, num_forms2)
        self.assertEqual(first_f, first_f2)
        self.assertEqual(first_f, first_formation)

    def test_structural_formation_to_full(self):
        self.runsafe(self.do_run)

    def test_structural_formation_to_full_with_reset(self):
        self.runsafe(self.do_run_with_reset)


if __name__ == "__main__":
    structural_formation_to_full()
