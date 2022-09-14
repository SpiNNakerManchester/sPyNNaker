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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.data import SpynnakerDataView


class TestOnlyCoresRecording(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0, n_boards_required=1)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

        machine = SpynnakerDataView.get_machine()
        input1 = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]), label="input1")
        input2 = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]), label="input2")
        input3 = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]), label="input3")
        input4 = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]), label="input4")

        # Make sure there is stuff at the cores specified in the cfg file
        input1.add_placement_constraint(0, 0, 4)
        input2.add_placement_constrain(0, 0, 3)
        # While there must be a chip 0,0  chip 1,1 could be missing
        if machine.is_chip_at(1, 1):
            input3.add_placement_constraint(1, 1, 5)
        # Make sure there is stuff at a core not specified in the cfg file
        input4.add_placement_constraint(0, 0, 10)

        sim.run(500)

        provenance_files = self.get_app_iobuf_files()
        sim.end()

        self.assertNotIn(
            "iobuf_for_chip_0_0_processor_id_1.txt", provenance_files)
        self.assertNotIn(
            "iobuf_for_chip_0_0_processor_id_2.txt", provenance_files)
        self.assertIn(
            "iobuf_for_chip_0_0_processor_id_3.txt", provenance_files)
        self.assertIn(
            "iobuf_for_chip_0_0_processor_id_4.txt", provenance_files)
        if machine.is_chip_at(1, 1):
            self.assertIn(
                "iobuf_for_chip_1_1_processor_id_5.txt", provenance_files)
        self.assertNotIn(
            "iobuf_for_chip_1_1_processor_id_2.txt", provenance_files)

    def test_do_run(self):
        self.runsafe(self.do_run)
