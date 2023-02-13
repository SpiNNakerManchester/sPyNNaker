# Copyright (c) 2017-2023 The University of Manchester
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


def do_run():
    p.setup(0.1)
    runtime = 50
    populations = []

    pop_src1 = p.Population(1, p.SpikeSourceArray,
                            {'spike_times': [[5, 15, 20, 30]]}, label="src1")

    populations.append(p.Population(1, p.IF_curr_alpha, {}, label="test"))

    populations[0].set(tau_syn_E=2)
    populations[0].set(tau_syn_I=4)

    # define the projections
    p.Projection(
        pop_src1, populations[0], p.OneToOneConnector(),
        p.StaticSynapse(weight=1, delay=1), receptor_type="excitatory")
    p.Projection(
        pop_src1, populations[0], p.OneToOneConnector(),
        p.StaticSynapse(weight=1, delay=10), receptor_type="inhibitory")

    populations[0].record("all")
    p.run(runtime)
    p.end()


class TestAlpha(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_run(self):
        do_run()


if __name__ == '__main__':
    do_run()
