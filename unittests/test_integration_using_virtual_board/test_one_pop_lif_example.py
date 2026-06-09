#!/usr/bin/python

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


from parameterized import parameterized
import pyNN.spiNNaker as p

from spinn_utilities.config_holder import set_config

from spinn_machine.version import MANY_BOARD_TYPES

from spinnaker_testbase import BaseTestCase


def do_run(nNeurons: int, ver_num: str) -> None:

    p.setup(timestep=1.0, min_delay=1.0)
    set_config("Machine", "version", ver_num)

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
    assert neo is not None

    p.end()


class OnePopLifExample(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    @parameterized.expand(MANY_BOARD_TYPES)
    def test_run(self, _: str, ver_num: str) -> None:
        nNeurons = 255  # number of neurons in each population
        do_run(nNeurons, ver_num)
