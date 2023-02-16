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
