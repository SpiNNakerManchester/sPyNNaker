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

"""
Synfirechain-like example
"""
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase
from spinn_front_end_common.utilities import globals_variables


class TestCoresAndBinariesRecording(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.SpikeSourceArray, 1)

        input = sim.Population(10, sim.SpikeSourceArray(spike_times=[0]),
                               label="input")
        pop_1 = sim.Population(100, sim.IF_curr_exp(), label="pop_1")
        sim.Projection(input, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=18))
        sim.run(500)

        app_iobuf_files = self.get_app_iobuf_files()
        placements = globals_variables.get_simulator()._placements
        sim.end()

        machine_verts = input._vertex.machine_vertices
        data = set()
        false_data = list()

        for machine_vertex in machine_verts:
            placement = placements.get_placement_of_vertex(machine_vertex)
            data.add(placement)

        for p in range(0, 16):
            if not placements.is_processor_occupied(0, 0, p):
                false_data.append(p)
            elif placements.get_placement_on_processor(0, 0, p) not in data:
                false_data.append(p)

        for placement in data:
            self.assertIn(
                "iobuf_for_chip_{}_{}_processor_id_{}.txt".format(
                    placement.x, placement.y, placement.p), app_iobuf_files)
        for processor in false_data:
            # extract_iobuf_from_cores = None
            self.assertNotIn(
                "iobuf_for_chip_0_0_processor_id_{}.txt".format(processor),
                app_iobuf_files)

    def test_do_run(self):
        self.runsafe(self.do_run)
