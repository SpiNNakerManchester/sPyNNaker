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
from spinn_front_end_common.utility_models import \
    ReverseIPTagMulticastSourceMachineVertex
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron import PopulationMachineVertex

n_neurons = 200  # number of neurons in each population
simtime = 500
neurons_per_core = n_neurons / 2


class TestCoresAndBinariesRecording(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

        input = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]),
                               label="input")
        pop_1 = sim.Population(200, sim.IF_curr_exp(), label="pop_1")
        sim.Projection(input, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=18))
        sim.run(simtime)

        provenance_files = self.get_app_iobuf_files()
        placements = SpynnakerDataView.get_placements()
        # As outside of run we have to use unprotected method
        app_graph = SpynnakerDataView.get_runtime_graph()
        sim.end()

        data = set()

        for vertex in app_graph.vertices:
            for machine_vertex in vertex.machine_vertices:
                if (isinstance(machine_vertex, PopulationMachineVertex) or
                        isinstance(
                            machine_vertex,
                            ReverseIPTagMulticastSourceMachineVertex)):
                    placement = placements.get_placement_of_vertex(
                        machine_vertex)
                    data.add(placement)

        false_data = list(range(0, 16))
        for placement in SpynnakerDataView.iterate_placements_on_core(0, 0):
            if placement in data:
                false_data.remove(placement.p)

        for placement in data:
            self.assertIn(
                "iobuf_for_chip_{}_{}_processor_id_{}.txt".format(
                    placement.x, placement.y, placement.p), provenance_files)
        for processor in false_data:
            # extract_iobuf_from_cores = None
            self.assertNotIn(
                "iobuf_for_chip_0_0_processor_id_{}.txt".format(processor),
                provenance_files)

    def test_do_run(self):
        self.runsafe(self.do_run)
