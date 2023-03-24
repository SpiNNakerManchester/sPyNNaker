
# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
