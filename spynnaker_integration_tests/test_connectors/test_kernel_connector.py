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

from typing import List, Tuple
import numpy as np
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestKernelConnector(BaseTestCase):

    def do_run(self, psh: int, psw: int, ksh: int, ksw: int,
               pre_start: Tuple[int, int] = (0, 0),
               post_start: Tuple[int, int] = (0, 0),
               pre_step: Tuple[int, int] = (1, 1),
               post_step: Tuple[int, int] = (1, 1)) -> List[List[int]]:
        sim.setup(timestep=1.0)

        # determine population size and runtime from the kernel sizes
        n_pop = psw*psh
        runtime = (n_pop*5)+1000

        spiking = [[n*5, (n_pop*5)-1-(n*5)] for n in range(n_pop)]
        input_pop = sim.Population(n_pop, sim.SpikeSourceArray(spiking),
                                   label="input")
        pop = sim.Population(n_pop // 4, sim.IF_curr_exp(), label="pop")

        weights = 5.0
        delays = 17.0

        shape_pre = [psh, psw]
        shape_post = [psh // 2, psw // 2]
        shape_kernel = [ksh, ksw]

        weight_list = [[7.0 if ((a + b) % 2 == 0) else 5.0
                        for a in range(ksw)] for b in range(ksh)]
        delay_list = [[20.0 if ((a + b) % 2 == 1) else 10.0
                       for a in range(ksw)] for b in range(ksh)]
        weight_kernel = np.asarray(weight_list)

        kernel_connector = sim.KernelConnector(
            shape_pre, shape_post, shape_kernel,
            weight_kernel=weight_kernel, delay_kernel=delay_list,
            pre_sample_steps_in_post=pre_step,
            post_sample_steps_in_pre=post_step,
            pre_start_coords_in_post=pre_start,
            post_start_coords_in_pre=post_start)

        c2 = sim.Projection(input_pop, pop, kernel_connector,
                            sim.StaticSynapse(weight=weights, delay=delays))

        pop.record(['v', 'spikes'])

        sim.run(runtime)

        weightsdelays = sorted(c2.get(['weight', 'delay'], 'list'),
                               key=lambda x: x[1])

        sim.end()

        return weightsdelays

    def test_oddsquarek_run(self) -> None:
        (psh, psw, ksh, ksw) = (4, 4, 3, 3)
        weightsdelays = self.do_run(psh, psw, ksh, ksw)
        # Checks go here
        self.assertEqual(25, len(weightsdelays))
        list10 = (1, 0, 5.0, 20.0)
        list11 = (1, 1, 7.0, 10.0)
        self.assertSequenceEqual(list10, weightsdelays[1])
        self.assertSequenceEqual(list11, weightsdelays[5])

    def test_evensquarek_run(self) -> None:
        (psh, psw, ksh, ksw) = (4, 4, 2, 2)
        weightsdelays = self.do_run(psh, psw, ksh, ksw)
        # Checks go here
        self.assertEqual(9, len(weightsdelays))
        list01 = (0, 1, 5.0, 20.0)
        list03 = (0, 3, 7.0, 10.0)
        self.assertSequenceEqual(list01, weightsdelays[1])
        self.assertSequenceEqual(list03, weightsdelays[5])

    def test_nonsquarek_run(self) -> None:
        (psh, psw, ksh, ksw) = (4, 4, 1, 3)
        weightsdelays = self.do_run(psh, psw, ksh, ksw)
        # Checks go here
        self.assertEqual(10, len(weightsdelays))
        list10 = (1, 0, 7.0, 10.0)
        list42 = (4, 2, 5.0, 20.0)
        self.assertSequenceEqual(list10, weightsdelays[1])
        self.assertSequenceEqual(list42, weightsdelays[5])

    def test_bigger_nonsquarep_run(self) -> None:
        (psh, psw, ksh, ksw) = (32, 16, 3, 3)
        weightsdelays = self.do_run(psh, psw, ksh, ksw)
        # Checks go here
        self.assertEqual(1081, len(weightsdelays))
        list10 = (1, 0, 5.0, 20.0)
        list11 = (1, 1, 7.0, 10.0)
        self.assertSequenceEqual(list10, weightsdelays[1])
        self.assertSequenceEqual(list11, weightsdelays[5])
