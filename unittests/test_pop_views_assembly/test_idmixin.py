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

import numpy
import pytest
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase

N_NEURONS = 4
LABEL = "pop_1"


class TestIDMixin(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_cells(self):
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(N_NEURONS, sim.IF_curr_exp(), label=LABEL)
        cells = pop_1.all_cells
        assert 0 == cells[0].id
        assert pop_1 == cells[0]._population
        assert len(str(cells[0])) > 0
        assert len(repr(cells[0])) > 0
        assert not(cells[1].__eq__("Not the same object"))
        sim.end()

    def test_get_set(self):
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(N_NEURONS, sim.IF_curr_exp(), label=LABEL)
        cells = pop_1.all_cells
        p_tau_m = pop_1.get("tau_m")
        tau_m_3 = cells[3].tau_m
        assert p_tau_m[3] == tau_m_3
        cells[2].tau_m = 2
        p_tau_m = pop_1.get("tau_m")
        assert 2 == p_tau_m[2]
        params = cells[1].get_parameters()
        p_i_offset = pop_1.get("i_offset")
        assert params["i_offset"][0] == p_i_offset[1]
        cells[2].set_parameters(tau_m=3, i_offset=13)
        params = cells[2].get_parameters()
        assert 13 == params["i_offset"][0]
        sim.end()

    def test_bad(self):
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(4, sim.IF_curr_exp(), label=LABEL)
        cell = pop_1.all_cells[2]
        with pytest.raises(Exception):
            cell.variable_that_is_not_there
        with pytest.raises(Exception):
            cell.variable_that_is_not_there = "pop"
        sim.end()

    def test_is_local(self):
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(N_NEURONS, sim.IF_curr_exp(), label=LABEL)
        cells = pop_1.all_cells
        assert pop_1.is_local(2) == cells[2].local
        sim.end()

    """
    def test_positions(self):
        grid_structure = sim.Grid2D(dx=1.0, dy=1.0, x0=0.0, y0=0.0)
        positions = grid_structure.generate_positions(4)
        pos_T = positions.T
        sim.setup(timestep=1.0)
        pop_1 = sim.Population(N_NEURONS, sim.IF_curr_exp(), label=LABEL)
        cells = pop_1.all_cells
        assert "q" == pop_1.position[1]
    """

    def test_init_by_in(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label=LABEL)
        assert [-65.0, -65.0, -65.0, -65.0] == pop.initial_values["v"]
        cells = pop.all_cells
        cells[1].set_initial_value(variable="v", value=-60)
        assert [-60] == cells[1].get_initial_value("v")
        cells[2].initialize(v=-59)
        assert [-59] == cells[2].initial_values["v"]
        assert [-65.0, -60.0, -59.0, -65.0] == pop.initial_values["v"]
        sim.end()

    def test_initial_values(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(N_NEURONS, sim.IF_curr_exp(), label=LABEL)
        cells = pop.all_cells
        assert -65 == cells[1].v
        assert -65 == cells[1].v_init
        cells[1].v = -60
        assert [-65.0, -60.0, -65.0, -65.0] == pop.initial_values["v"]
        sim.end()

    def test_asview(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp(), label=LABEL)
        cell = pop[2]
        cell.as_view()

    def test_ssa_spike_times(self):
        n_atoms = 10
        set_id = 1
        set_value = [5]
        sim.setup(timestep=1.0)
        pop = sim.Population(n_atoms, sim.SpikeSourceArray([]))
        pop[set_id].set_parameters(spike_times=set_value)
        result = pop.get("spike_times")
        result_should_be = []
        for atom in range(n_atoms):
            if atom == set_id:
                result_should_be.append(numpy.array(set_value))
            else:
                result_should_be.append([])
        self.assertEqual(result, result_should_be)
