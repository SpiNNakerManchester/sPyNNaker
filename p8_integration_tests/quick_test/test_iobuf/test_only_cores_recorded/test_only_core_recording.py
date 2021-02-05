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
from p8_integration_tests.base_test_case import BaseTestCase
from pacman.model.constraints.placer_constraints import ChipAndCoreConstraint
from spinn_front_end_common.utilities import globals_variables


class TestOnlyCoresRecording(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0, n_boards_required=1)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

        machine = globals_variables.get_simulator().machine

        input1 = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]), label="input1")
        input2 = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]), label="input2")
        pop_1 = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
        pop_2 = sim.Population(5, sim.IF_curr_exp(), label="pop_2")
        sim.Projection(input1, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        sim.Projection(input2, pop_2, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))

        # Make sure there is stuff at the cores specified in the cfg file
        input1.set_constraint(
            ChipAndCoreConstraint(0, 0, 1))
        input2.set_constraint(
            ChipAndCoreConstraint(0, 0, 3))
        # While there must be a chip 0,0  chip 1,1 could be missing
        if machine.is_chip_at(1, 1):
            pop_1.set_constraint(
                ChipAndCoreConstraint(1, 1, 1))
        # Make sure there is stuff at a core not specified in the cfg file
        pop_2.set_constraint(
            ChipAndCoreConstraint(0, 0, 2))

        sim.run(500)

        provenance_files = self.get_app_iobuf_files()
        sim.end()

        self.assertIn(
            "iobuf_for_chip_0_0_processor_id_1.txt", provenance_files)
        self.assertNotIn(
            "iobuf_for_chip_0_0_processor_id_2.txt", provenance_files)
        self.assertIn(
            "iobuf_for_chip_0_0_processor_id_3.txt", provenance_files)
        self.assertNotIn(
            "iobuf_for_chip_0_0_processor_id_4.txt", provenance_files)
        if machine.is_chip_at(1, 1):
            self.assertIn(
                "iobuf_for_chip_1_1_processor_id_1.txt", provenance_files)
        self.assertNotIn(
            "iobuf_for_chip_1_1_processor_id_2.txt", provenance_files)

    def test_do_run(self):
        self.runsafe(self.do_run)
