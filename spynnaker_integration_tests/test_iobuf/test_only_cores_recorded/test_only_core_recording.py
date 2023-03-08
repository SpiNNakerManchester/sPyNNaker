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
        input2.add_placement_constraint(0, 0, 3)
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
