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
from spinn_front_end_common.utility_models import \
    ReverseIPTagMulticastSourceMachineVertex
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron import PopulationMachineVertex

n_neurons = 200  # number of neurons in each population
simtime = 500
neurons_per_core = n_neurons // 2


class TestCoresAndBinariesRecording(BaseTestCase):

    def do_run(self) -> None:
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

        input = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]),
                               label="input")
        pop_1 = sim.Population(200, sim.IF_curr_exp(), label="pop_1")
        sim.Projection(input, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=18))
        sim.run(simtime)

        provenance_files = self.get_app_iobuf_files()
        # As outside of run we have to use unprotected method
        sim.end()

        data = set()

        for machine_vertex in SpynnakerDataView.iterate_machine_vertices():
            if (isinstance(machine_vertex, PopulationMachineVertex) or
                    isinstance(
                        machine_vertex,
                        ReverseIPTagMulticastSourceMachineVertex)):
                placement = SpynnakerDataView.get_placement_of_vertex(
                    machine_vertex)
                data.add(placement)

        false_data = list(range(0, 16))
        for placement in SpynnakerDataView.iterate_placements_on_core((0, 0)):
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

    def test_do_run(self) -> None:
        self.runsafe(self.do_run)
