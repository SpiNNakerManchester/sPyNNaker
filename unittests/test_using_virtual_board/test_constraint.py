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
from spinn_utilities.config_holder import set_config
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView


class TestConstraint(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_placement_constraint(self):
        """
        test the get_placements call.

        """
        sim.setup(timestep=1.0)
        set_config("Reports", "write_application_graph_placer_report", True)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 50)

        pop_1 = sim.Population(200, sim.IF_curr_exp(), label="pop_1")
        pop_1.add_placement_constraint(x=1, y=1)
        input = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]),
                               label="input")
        sim.Projection(input, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        simtime = 10
        sim.run(simtime)
        placements = [SpynnakerDataView.get_placement_of_vertex(vertex)
                      for vertex in pop_1._vertex.machine_vertices]
        sim.end()
        self.assertGreater(len(placements), 0)
        for pl in placements:
            self.assertEqual(1, pl.x)
            self.assertEqual(1, pl.y)
