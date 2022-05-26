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
from spynnaker.pyNN.exceptions import SpynnakerException
from spinnaker_testbase import BaseTestCase


def before_run(nNeurons):
    sim.setup(timestep=1, min_delay=1)

    neuron_parameters = {'cm': 0.25, 'i_offset': 2, 'tau_m': 10.0,
                         'tau_refrac': 2.0, 'tau_syn_E': 0.5, 'tau_syn_I': 0.5,
                         'v_reset': -65.0, 'v_rest': -65.0, 'v_thresh': -50.0}

    pop = sim.Population(nNeurons, sim.IF_curr_exp, neuron_parameters,
                         label='pop_1')

    return pop.celltype


class Test_Max_Cores(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_uncapped(self):
        sim.setup(timestep=1, min_delay=1)
        pop = sim.Population(500, sim.IF_curr_exp)
        vertex = pop._Population__vertex
        # 256 if the default
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

    def test_model_cap(self):
        sim.setup(timestep=1, min_delay=1)
        pop1 = sim.Population(500, sim.IF_curr_exp)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 50)
        pop2 = sim.Population(500, sim.IF_curr_exp)
        vertex1 = pop1._Population__vertex
        self.assertEqual(256, vertex1.get_max_atoms_per_core())
        vertex2 = pop2._Population__vertex
        self.assertEqual(50, vertex2.get_max_atoms_per_core())
        # go over the current model cap
        with self.assertRaises(SpynnakerException):
            pop1.set_max_atoms_per_core(100)
        sim.end()

    def test_raise_sim_cap(self):
        sim.setup(timestep=1, min_delay=1)
        with self.assertRaises(SpynnakerException):
            sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 500)
        pop1 = sim.Population(500, sim.IF_curr_exp)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)
        vertex1 = pop1._Population__vertex
        self.assertEqual(256, vertex1.get_max_atoms_per_core())
        with self.assertRaises(SpynnakerException):
            # This does not work because we have not programmed it
            pop1.set_max_atoms_per_core(200)
        pop1.set_max_atoms_per_core(50)
        self.assertEqual(50, vertex1.get_max_atoms_per_core())
        pop1.set_max_atoms_per_core(100)
        self.assertEqual(100, vertex1.get_max_atoms_per_core())
        with self.assertRaises(SpynnakerException):
            # This does not work because we have not programmed it
            sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 200)
        sim.end()
