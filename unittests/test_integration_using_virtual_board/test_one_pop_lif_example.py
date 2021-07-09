#!/usr/bin/python

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

import spynnaker8 as p
from spinnaker_testbase import BaseTestCase


def do_run(nNeurons):

    p.setup(timestep=1.0, min_delay=1.0)

    cell_params_lif_in = {'tau_m': 333.33, 'cm': 208.33, 'v': 0.0,
                          'v_rest': 0.1, 'v_reset': 0.0, 'v_thresh': 1.0,
                          'tau_syn_E': 1, 'tau_syn_I': 2, 'tau_refrac': 2.5,
                          'i_offset': 3.0}

    pop1 = p.Population(nNeurons, p.IF_curr_exp, cell_params_lif_in,
                        label='pop_0')

    pop1.record("v")
    pop1.record("gsyn_exc")
    pop1.record("spikes")

    p.run(3000)

    neo = pop1.get_data()
    assert(neo is not None)

    p.end()


class OnePopLifExample(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_run(self):
        nNeurons = 255  # number of neurons in each population
        do_run(nNeurons)


if __name__ == '__main__':
    nNeurons = 255  # number of neurons in each population
    do_run(nNeurons)
