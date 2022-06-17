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

import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


def before_run(nNeurons):
    p.setup(timestep=1, min_delay=1)

    neuron_parameters = {'cm': 0.25, 'i_offset': 2, 'tau_m': 10.0,
                         'tau_refrac': 2.0, 'tau_syn_E': 0.5, 'tau_syn_I': 0.5,
                         'v_reset': -65.0, 'v_rest': -65.0, 'v_thresh': -50.0}

    pop = p.Population(nNeurons, p.IF_curr_exp, neuron_parameters,
                       label='pop_1')

    return pop.celltype


class Test_celltype(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_before_run(self):
        nNeurons = 20  # number of neurons in each population
        celltype = before_run(nNeurons)
        self.assertEqual(p.IF_curr_exp, type(celltype))


if __name__ == '__main__':
    nNeurons = 20  # number of neurons in each population
    celltype = before_run(nNeurons)
    print(celltype)
