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

from unittest import SkipTest
import pytest
from pyNN.space import Sphere, RandomStructure
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestPopulation(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_properties(self):
        n_neurons = 5
        label = "pop_1"
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label=label)
        self.assertEqual(n_neurons, pop_1.size)
        self.assertEqual(label, pop_1.label)
        self.assertEqual(sim.IF_curr_exp, type(pop_1.celltype))
        v_init = -60
        pop_1.initialize(v=v_init)
        initial_values = pop_1.initial_values
        vs = initial_values["v"]
        assert [-60, -60, -60, -60, -60] == vs
        v_init = [-60 + index for index in range(n_neurons)]
        pop_1.initialize(v=v_init)
        initial_values = pop_1.initial_values
        vs = initial_values["v"]
        assert [-60, -59, -58, -57, -56] == vs

        _ = pop_1.all_cells
        _ = pop_1.local_cells

        self.assertEqual(n_neurons, pop_1.local_size)

        _ = pop_1.structure
        sim.end()

    def test_position_generator(self):
        n_neurons = 5
        label = "pop_1"
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label=label,
                               structure=RandomStructure(Sphere(5.0)))
        gen = pop_1.position_generator
        print(gen(0))
        sim.end()

    def test_set(self):
        n_neurons = 5
        label = "pop_1"
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label=label)
        pop_1.set(i_offset=2)
        sim.end()

    def test_set_multiple(self):
        n_neurons = 5
        label = "pop_1"
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label=label)
        pop_1.set(i_offset=[2, 3, 4, 5, 6])
        sim.end()

    def test_set_multiple_via_indirect(self):
        n_neurons = 5
        label = "pop_1"
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(
            n_neurons, sim.IF_curr_exp(i_offset=0), label=label)
        view = pop_1[0:3]
        view.set(i_offset=[2, 3, 4])
        sim.end()

    def test_selector(self):
        n_neurons = 5
        label = "pop_1"
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label=label)
        pop_1.set(tau_m=2)
        values = pop_1.get("tau_m")
        self.assertEqual([2, 2, 2, 2, 2], values)
        values = pop_1[1:3].get("tau_m")
        self.assertEqual([2, 2], values)
        pop_1[1:3].set(tau_m=3)
        values = pop_1.get("tau_m")
        self.assertEqual([2, 3, 3, 2, 2], values)
        values = pop_1.get(["cm", "v_thresh"])
        self.assertEqual([1.0, 1.0, 1.0, 1.0, 1.0], values['cm'])
        self.assertEqual(
            [-50.0, -50.0, -50.0, -50.0, -50.0], values["v_thresh"])
        values = pop_1[1, 3, 4].get(["cm", "v_thresh"])
        self.assertEqual([1.0, 1.0, 1.0], values['cm'])
        self.assertEqual(
            [-50.0, -50.0, -50.0], values["v_thresh"])
        sim.end()

    def test_init_by_in(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp())
        assert [-65.0, -65.0, -65.0, -65.0] == pop.initial_values["v"]
        pop[1:2].initialize(v=-60)
        assert [-65, -60, -65, -65] == pop.initial_values["v"]
        pop[2:3].initialize(v=12)
        assert -60 == pop[1].get_initial_value("v")
        sim.end()

    def test_init_bad(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp())
        with pytest.raises(Exception):
            pop.set_initial_value(variable="NOT_THERE", value="Anything")
        with pytest.raises(Exception):
            pop.get_initial_value(variable="NOT_THERE")
        sim.end()

    def test_no_init(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.SpikeSourceArray())
        with pytest.raises(KeyError):
            pop.initialize(v="Anything")
        with pytest.raises(KeyError):
            _ = pop.initial_values
        sim.end()

    def test_initial_values(self):
        sim.setup(timestep=1.0)
        pop = sim.Population.create(
            cellclass=sim.IF_curr_exp, cellparams=None, n=4)
        initial_values = pop.initial_values
        assert "v" in initial_values
        initial_values = pop[3:4].initial_values
        assert {"v": [-65], "isyn_exc": [0], "isyn_inh": [0]} == initial_values
        sim.end()

    def test_iter(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp(), label="a label")

        iterator = iter(pop)
        self.assertEqual(0, next(iterator).id)
        self.assertEqual(1, next(iterator).id)
        self.assertEqual(2, next(iterator).id)
        self.assertEqual(3, next(iterator).id)
        with pytest.raises(StopIteration):
            next(iterator)

        iterator = pop.all()
        self.assertEqual(0, next(iterator).id)
        self.assertEqual(1, next(iterator).id)
        self.assertEqual(2, next(iterator).id)
        self.assertEqual(3, next(iterator).id)
        with pytest.raises(StopIteration):
            next(iterator)

        sim.end()

    def test_base(self):
        n_neurons = 5
        label = "pop_1"
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label=label)
        assert n_neurons == pop_1.local_size
