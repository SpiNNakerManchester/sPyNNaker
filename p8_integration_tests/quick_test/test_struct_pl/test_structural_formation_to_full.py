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
import os
import sqlite3
from p8_integration_tests.base_test_case import BaseTestCase
import spynnaker8 as p


def structural_formation_to_full():
    p.setup(1.0)
    stim = p.Population(4, p.SpikeSourceArray(range(10)), label="stim")

    # These populations should experience formation
    pop = p.Population(4, p.IF_curr_exp(), label="pop")

    # Formation with random selection (0 probability elimination)
    proj = p.Projection(
        stim, pop, p.FromListConnector([]), p.StructuralMechanismStatic(
            partner_selection=p.LastNeuronSelection(),
            formation=p.DistanceDependentFormation([2, 2], 1.0),
            elimination=p.RandomByWeightElimination(4.0, 0, 0),
            f_rew=1000, initial_weight=4.0, initial_delay=3.0,
            s_max=4, seed=0, weight=0.0, delay=1.0))

    p.run(1000)

    # Get the final connections
    conns = list(proj.get(["weight", "delay"], "list"))

    num_rewires = None

    report_dir = p.globals_variables.get_simulator()._report_default_directory
    prov_file = os.path.join(
        report_dir, "provenance_data", "provenance.sqlite3")
    with sqlite3.connect(prov_file) as prov_db:
        prov_db.row_factory = sqlite3.Row
        rows = list(prov_db.execute(
            "SELECT the_value FROM provenance_view "
            "WHERE source_name LIKE '%pop%' "
            "AND description_name = 'Number_of_rewires' LIMIT 1"))
    for row in rows:
        num_rewires = row["the_value"]

    p.end()

    # Note: this will form 16 connections, but it will not strictly be
    # all-to-all as there is no way (at the moment) of ensuring duplicate
    # connections are not created.
    assert(len(conns) == 16)
    assert(num_rewires == 16)


class TestStructuralFormationToFull(BaseTestCase):

    def test_structural_formation_to_full(self):
        self.runsafe(structural_formation_to_full)


if __name__ == "__main__":
    structural_formation_to_full()
