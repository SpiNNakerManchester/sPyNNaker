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
from spynnaker.pyNN.exceptions import SpynnakerException
from spinnaker_testbase import BaseTestCase


class Test_Max_Cores(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_uncapped(self) -> None:
        sim.setup(timestep=1, min_delay=1)
        pop = sim.Population(500, sim.IF_curr_exp)
        vertex = pop._Population__vertex
        # Initially there is no limit because there are no projections
        self.assertEqual(256, vertex.get_max_atoms_per_core())

        pop_2 = sim.Population(500, sim.IF_curr_exp)
        sim.Projection(pop_2, pop, sim.OneToOneConnector(),
                       sim.StaticSynapse())
        # After adding a projection, we should get a new default value
        self.assertEqual(256, vertex.get_max_atoms_per_core())
        # go over the model cap
        with self.assertRaises(SpynnakerException):
            pop.set_max_atoms_per_core(500)
        # vertex unchanged
        self.assertEqual(256, vertex.get_max_atoms_per_core())
        pop.set_max_atoms_per_core(100)
        # vertex changed
        self.assertEqual(100, vertex.get_max_atoms_per_core())
        pop.set_max_atoms_per_core(200)
        # vertex changed up
        self.assertEqual(200, vertex.get_max_atoms_per_core())
        sim.end()

    def test_raise_sim_cap(self) -> None:
        sim.setup(timestep=1, min_delay=1)
        pop1 = sim.Population(500, sim.IF_curr_exp)
        with self.assertRaises(SpynnakerException):
            sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)
        vertex1 = pop1._Population__vertex
        self.assertEqual(256, vertex1.get_max_atoms_per_core())
        pop1.set_max_atoms_per_core(50)
        self.assertEqual(50, vertex1.get_max_atoms_per_core())
        pop1.set_max_atoms_per_core(100)
        self.assertEqual(100, vertex1.get_max_atoms_per_core())
        sim.end()
