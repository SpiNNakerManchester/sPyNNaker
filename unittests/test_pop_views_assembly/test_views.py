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

import pytest
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.models.populations import PopulationView
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class Test_IDMixin(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_simple(self):
        n_neurons = 5
        label = "pop_1"
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label=label)
        mask = [1, 3]
        view = PopulationView(pop_1, mask, label=label)
        self.assertEqual(2, view.size)
        self.assertEqual(2, view.local_size)

        random_view = pop_1.sample(3)
        self.assertEqual(3, random_view.size)

        self.assertEqual(label, view.label)
        self.assertEqual(pop_1.celltype, view.celltype)
        self.assertEqual(pop_1.celltype, random_view.celltype)

        view_initial_values = view.initial_values
        pop_initial_values = pop_1.initial_values
        self.assertEqual(len(view_initial_values), len(pop_initial_values))
        for key in pop_initial_values:
            self.assertEqual(
                pop_initial_values[key][3], view_initial_values[key][1])

        self.assertEqual(pop_1, view.parent)
        self.assertEqual(mask, view.mask)

        cells = view.all_cells
        self.assertEqual(2, len(cells))
        self.assertEqual(1, cells[0].id)
        self.assertEqual(3, cells[1].id)

        self.assertEqual(cells, view.local_cells)
        self.assertEqual(cells[0], view[1])

        iterator = iter(view)
        self.assertEqual(1, next(iterator).id)
        self.assertEqual(3, next(iterator).id)
        with pytest.raises(StopIteration):
            next(iterator)

        self.assertEqual(2, len(view))

        iterator = view.all()
        self.assertEqual(1, next(iterator).id)
        self.assertEqual(3, next(iterator).id)
        with pytest.raises(StopIteration):
            next(iterator)

        self.assertEqual(view.conductance_based, pop_1.conductance_based)

        describe = view.describe()
        self.assertIn('PopulationView "pop_1"', describe)
        self.assertIn('parent : "pop_1"', describe)
        self.assertIn('size   : 2', describe)
        self.assertIn('mask   : [1, 3]', describe)

        self.assertEqual(pop_1.find_units("v"), view.find_units("v"))

        sim.end()

    def test_get_set(self):
        n_neurons = 4
        label = "pop_1"
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label=label)
        view = PopulationView(pop_1, [1, 3], label="Odds")

        pop_1.set(tau_m=2)
        self.assertEqual([2, 2, 2, 2], pop_1.get("tau_m"))
        self.assertEqual([2, 2], view.get("tau_m", simplify=False))
        # This is not standard PyNN over a view
        self.assertEqual([2, 2], view.tau_m)
        view.set(tau_m=3)
        self.assertEqual([2, 3, 2, 3], pop_1.get("tau_m"))
        # This is not standard PyNN over a view
        view.tau_m = 4
        self.assertEqual([2, 4, 2, 4], pop_1.get("tau_m"))
        sim.end()

    def test_view_of_view(self):
        n_neurons = 10
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label="pop_1")
        view1 = PopulationView(pop_1, [1, 3, 5, 7, 9], label="Odds")
        view2 = PopulationView(view1, [1, 3], label="AlternativeOdds")
        # Not a normal way to access but good to test
        self.assertEqual((3, 7), view2._indexes)
        self.assertEqual(view2.parent, view1)
        self.assertEqual(view1.grandparent, pop_1)
        self.assertEqual(view2.grandparent, pop_1)
        cells = view2.all_cells
        self.assertEqual(3, cells[0].id)
        self.assertEqual(7, cells[1].id)
        self.assertEqual(3, view1.id_to_index(7))
        self.assertEqual([3, 0], view1.id_to_index([7, 1]))
        self.assertEqual(1, view2.id_to_index(7))
        view3 = view1[1:3]
        self.assertEqual((3, 5), view3._indexes)
        view4 = view1.sample(2)
        self.assertEqual(2, len(view4._indexes))
        sim.end()

    def test_initial_value(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
        self.assertEqual([-65, -65, -65, -65, -65], pop.initial_values["v"])
        view = PopulationView(pop, [1, 3], label="Odds")
        view2 = PopulationView(pop, [1, 2], label="OneTwo")
        view_iv = view.initial_values
        self.assertEqual(3, len(view_iv))
        self.assertEqual([-65, -65], view_iv["v"])
        view.initialize(v=-60)
        self.assertEqual([-65, -60, -65, -60, -65], pop.initial_values["v"])
        self.assertEqual([-60, -60], view.initial_values["v"])
        self.assertEqual([-60, -65], view2.initial_values["v"])
        view.initialize(v=lambda i: -65 + i / 10.0)
        self.assertEqual([-64.9, -64.7], view.initial_values["v"])
        sim.end()

    def test_projection(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
        view = PopulationView(pop, [1, 3], label="Odds")
        try:
            sim.Projection(pop, view, sim.OneToOneConnector())
        except NotImplementedError:
            pass  # Acceptable, but better if it worked
        with pytest.raises(ConfigurationException):
            sim.Projection(pop, "SOMETHING WIERD", sim.OneToOneConnector())
