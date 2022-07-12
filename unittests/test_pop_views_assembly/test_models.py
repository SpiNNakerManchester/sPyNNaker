
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


class TestPopulation(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_model_fail_to_set_synpase_param(self):
        n_neurons = 5
        value = 5
        label = "pop_1"
        sim.setup(timestep=1.0)
        model = sim.IF_curr_exp(tau_syn_I=value)
        pop_1 = sim.Population(n_neurons, model, label=label)
        self.assertEqual(model._model['tau_syn_I'], value)
        with self.assertRaises(TypeError):
            model._model['tau_syn_I'] = 6
        self.assertEqual(
            pop_1.get('tau_syn_I'), [value, value, value, value, value])

    def test_model_fail_to_set_neuron_param(self):
        n_neurons = 5
        value = 5
        label = "pop_1"
        sim.setup(timestep=1.0)
        model = sim.IF_curr_exp(i_offset=value)
        pop_1 = sim.Population(n_neurons, model, label=label)
        self.assertEqual(model._model['i_offset'], value)
        with self.assertRaises(TypeError):
            model._model['i_offset'] = 6
        self.assertEqual(
            pop_1.get('i_offset'), [value, value, value, value, value])

    def test_model_fail_to_set_neuron_param_array(self):
        n_neurons = 5
        value = 5
        new_value = 6
        label = "pop_1"
        sim.setup(timestep=1.0)
        model = sim.IF_curr_exp(i_offset=[value, value, value, value, value])
        pop_1 = sim.Population(n_neurons, model, label=label)
        self.assertEqual(
            model._model['i_offset'], [value, value, value, value, value])
        with self.assertRaises(TypeError):
            model._model['i_offset'] = [
                new_value, new_value, new_value, new_value, new_value]
        self.assertEqual(
            pop_1.get('i_offset'), [value, value, value, value, value])

    def test_model_fail_to_set_neuron_param_array_wrong_size(self):
        n_neurons = 5
        value = 5
        label = "pop_1"
        sim.setup(timestep=1.0)
        model = sim.IF_curr_exp(i_offset=[value, value, value, value])
        with self.assertRaises(Exception):
            sim.Population(n_neurons, model, label=label)

    def test_model_fail_to_set_neuron_param_random_distribution(self):
        n_neurons = 5
        range_low = -70
        range_high = -50
        value = sim.RandomDistribution('uniform', (range_low, range_high))
        label = "pop_1"
        sim.setup(timestep=1.0)
        model = sim.IF_curr_exp(i_offset=value)
        pop_1 = sim.Population(n_neurons, model, label=label)
        sim.run(0)
        values = pop_1.get('i_offset')
        for value in values:
            self.assertGreater(value, range_low)
            self.assertLess(value, range_high)

    def test_model_fail_to_set_neuron_param_function(self):
        n_neurons = 5

        def _silly_funct():
            return 5

        value = _silly_funct()
        label = "pop_1"
        sim.setup(timestep=1.0)
        model = sim.IF_curr_exp(i_offset=value)
        pop_1 = sim.Population(n_neurons, model, label=label)
        values = pop_1.get('i_offset')
        self.assertEqual([5, 5, 5, 5, 5], values)
