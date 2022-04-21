#!/usr/bin/python

# Copyright (c) 2017-2022 The University of Manchester
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

import pyNN.spiNNaker as p
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


def do_run(nNeurons):

    p.setup(timestep=1.0, min_delay=1.0)

    cell_params_lif_in = {'tau_m': 333.33, 'cm': 208.33,
                          'v': [0.0, 0.0146789550781, 0.029296875,
                                0.0438842773438, 0.0584106445312],
                          'v_rest': 0.1, 'v_reset': 0.0, 'v_thresh': 1.0,
                          'tau_syn_E': 1, 'tau_syn_I': 2, 'tau_refrac': 2.5,
                          'i_offset': 3.0}

    pop1 = p.Population(nNeurons, p.IF_curr_exp, cell_params_lif_in,
                        label='pop_0')

    pop1.record("v")
    pop1.record("gsyn_exc")
    pop1.record("spikes")

    p.run(100)

    neo = pop1.get_data(["v", "spikes", "gsyn_exc"])

    v = neo_convertor.convert_data(neo, name="v")
    gsyn = neo_convertor.convert_data(neo, name="gsyn_exc")
    spikes = neo_convertor.convert_spikes(neo)

    p.end()

    return (v, gsyn, spikes)


class OnePopLifExample(BaseTestCase):
    def do_run(self):
        nNeurons = 5  # number of neurons in each population
        (v, gsyn, spikes) = do_run(nNeurons)
        self.assertEqual(5, len(spikes))
        self.assertEqual(spikes[0][0], 0)
        self.assertEqual(spikes[0][1], 76)
        self.assertEqual(spikes[1][0], 1)
        self.assertEqual(spikes[1][1], 75)
        self.assertEqual(spikes[2][0], 2)
        self.assertEqual(spikes[2][1], 74)
        self.assertEqual(spikes[3][0], 3)
        self.assertEqual(spikes[3][1], 73)
        self.assertEqual(spikes[4][0], 4)
        self.assertEqual(spikes[4][1], 72)

    def test_run(self):
        self.runsafe(self.do_run)
