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

from pyNN.random import RandomDistribution, NumpyRNG
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase
import numpy


class ParamsSetAsList(BaseTestCase):

    def do_run(self):
        nNeurons = 500
        p.setup(timestep=1.0, min_delay=1.0)

        p.set_number_of_neurons_per_core(p.IF_curr_exp, 100)

        cm = list()
        i_off = list()
        tau_m = list()
        tau_re = list()
        tau_syn_e = list()
        tau_syn_i = list()
        v_reset = list()
        v_rest = list()

        for atom in range(0, nNeurons):
            cm.append(0.25)
            i_off.append(0.0 + atom * 0.01)
            tau_m.append(10.0 + atom // 2 * 0.1)
            tau_re.append(2.0 + atom % 2 * 0.01)
            tau_syn_e.append(0.5)
            tau_syn_i.append(0.5 + atom * 0.01)
            v_reset.append(-65.0 + atom // 2 * 0.01)
            v_rest.append(-65.0 + atom % 2 * 0.01)

        gbar_na_distr = RandomDistribution('normal', (20.0, 2.0),
                                           rng=NumpyRNG(seed=85524))

        cell_params_lif = {'cm': 0.25, 'i_offset': i_off, 'tau_m': tau_m,
                           'tau_refrac': tau_re, 'v_thresh': gbar_na_distr}

        pop_1 = p.Population(
            nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_1')

        pop_1.set(tau_syn_E=0.5)
        pop_1.set(tau_syn_I=tau_syn_i)
        pop_1.set(v_reset=v_reset, v_rest=v_rest)
        p.run(1)

        assert numpy.allclose(cm, pop_1.get("cm"), rtol=1e-03)
        assert numpy.allclose(i_off, pop_1.get("i_offset"), rtol=1e-03)
        assert numpy.allclose(tau_m, pop_1.get("tau_m"), rtol=1e-03)
        assert numpy.allclose(tau_re, pop_1.get("tau_refrac"), rtol=1e-03)
        assert numpy.allclose(tau_syn_e, pop_1.get("tau_syn_E"), rtol=1e-03)
        assert numpy.allclose(tau_syn_i, pop_1.get("tau_syn_I"), rtol=1e-03)
        assert numpy.allclose(v_reset, pop_1.get("v_reset"), rtol=1e-03)
        assert numpy.allclose(v_rest, pop_1.get("v_rest"), rtol=1e-03)
        self.assertGreater(len(set(pop_1.get("v_thresh"))), nNeurons/2)
        p.end()

    def test_run(self):
        self.runsafe(self.do_run)
