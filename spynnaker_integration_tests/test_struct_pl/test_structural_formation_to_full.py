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
from spinnaker_testbase import BaseTestCase
import spynnaker8 as p


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


class TestStructuralFormationToFull(BaseTestCase):
    def do_run(self):
        conns, num_forms, num_elims, first_f = structural_formation_to_full()
        # Should have built all-to-all connectivity
        all_to_all_conns = [
            (0, 0, 4., 3.), (0, 1, 4., 3.), (0, 2, 4., 3.), (0, 3, 4., 3.),
            (1, 0, 4., 3.), (1, 1, 4., 3.), (1, 2, 4., 3.), (1, 3, 4., 3.),
            (2, 0, 4., 3.), (2, 1, 4., 3.), (2, 2, 4., 3.), (2, 3, 4., 3.),
            (3, 0, 4., 3.), (3, 1, 4., 3.), (3, 2, 4., 3.), (3, 3, 4., 3.)]
        first_formation = "3_3_formation"

        self.assertEqual(all_to_all_conns, conns.tolist())
        self.assertEqual(len(conns), 16)
        self.assertEqual(num_forms, 16)
        self.assertEqual(num_elims, 0)
        self.assertEqual(first_f, first_formation)

    def test_structural_formation_to_full(self):
        self.runsafe(self.do_run)


if __name__ == "__main__":
    structural_formation_to_full()
