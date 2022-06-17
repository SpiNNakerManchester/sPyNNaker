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

from pyNN.random import NumpyRNG
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


class ParamsUsingRandomDists(BaseTestCase):

    def do_run(self):
        nNeurons = 2
        p.setup(timestep=1.0, min_delay=1.0)

        rng = NumpyRNG(seed=85524)
        cm = p.RandomDistribution('uniform_int', [1, 4], rng=rng)
        i_off = p.RandomDistribution('poisson', lambda_=3, rng=rng)
        tau_m = p.RandomDistribution('gamma', [1.0, 1.0], rng=rng)
        tau_re = p.RandomDistribution('vonmises', [1.0, 1.0], rng=rng)
        tau_syn_E = p.RandomDistribution('exponential', [0.1], rng=rng)
        tau_syn_I = p.RandomDistribution('binomial', [1, 0.5], rng=rng)
        v_reset = p.RandomDistribution('lognormal', [1.0, 1.0], rng=rng)
        v_rest = p.RandomDistribution('normal_clipped',
                                      [-70.0, 1.0, -72.0, -68.0], rng=rng)
        v_thresh = p.RandomDistribution('normal_clipped_to_boundary',
                                        [-55.0, 2.0, -57.0, -53.0], rng=rng)
        v_init = p.RandomDistribution('normal', [-65.0, 1.0], rng=rng)

        cell_params_lif = {'cm': cm, 'i_offset': i_off, 'tau_m': tau_m,
                           'tau_refrac': tau_re, 'tau_syn_E': tau_syn_E,
                           'tau_syn_I': tau_syn_I, 'v_reset': v_reset,
                           'v_rest': v_rest, 'v_thresh': v_thresh}

        pop_1 = p.Population(
            nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_1')

        pop_1.initialize(v=v_init)

        p.run(1)

        # All this is really checking is that values get copied correctly
        self.assertEqual(nNeurons, len(pop_1.get("cm")))
        self.assertEqual(nNeurons, len(pop_1.get("i_offset")))
        self.assertEqual(nNeurons, len(pop_1.get("tau_m")))
        self.assertEqual(nNeurons, len(pop_1.get("tau_refrac")))
        self.assertEqual(nNeurons, len(pop_1.get("tau_syn_E")))
        self.assertEqual(nNeurons, len(pop_1.get("tau_syn_I")))
        self.assertEqual(nNeurons, len(pop_1.get("v_reset")))
        self.assertEqual(nNeurons, len(pop_1.get("v_rest")))
        self.assertEqual(nNeurons, len(pop_1.get("v_thresh")))
        p.end()

    def test_run(self):
        self.runsafe(self.do_run)
