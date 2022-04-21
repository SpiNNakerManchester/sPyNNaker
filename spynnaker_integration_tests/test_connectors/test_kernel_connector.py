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

import numpy as np
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestKernelConnector(BaseTestCase):
    # pylint: disable=expression-not-assigned

    def do_run(self, psh, psw, ksh, ksw, pre_start=(0, 0), post_start=(0, 0),
               pre_step=(1, 1), post_step=(1, 1)):
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
        delay_kernel = np.asarray(delay_list)

        kernel_connector = sim.KernelConnector(
            shape_pre, shape_post, shape_kernel,
            weight_kernel=weight_kernel, delay_kernel=delay_kernel,
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

    def test_oddsquarek_run(self):
        (psh, psw, ksh, ksw) = (4, 4, 3, 3)
        weightsdelays = self.do_run(psh, psw, ksh, ksw)
        # Checks go here
        self.assertEqual(25, len(weightsdelays))
        list10 = (1, 0, 5.0, 20.0)
        list11 = (1, 1, 7.0, 10.0)
        [self.assertEqual(list10[i], weightsdelays[1][i]) for i in range(4)]
        [self.assertEqual(list11[i], weightsdelays[5][i]) for i in range(4)]
        # NOTE: you can probably replace the above in later versions of python3
        #       with the following, but in 3.5 it generates a FutureWarning
#         self.assertSequenceEqual(list10, weightsdelays[1])
#         self.assertSequenceEqual(list11, weightsdelays[5])

    def test_evensquarek_run(self):
        (psh, psw, ksh, ksw) = (4, 4, 2, 2)
        weightsdelays = self.do_run(psh, psw, ksh, ksw)
        # Checks go here
        self.assertEqual(9, len(weightsdelays))
        list01 = (0, 1, 5.0, 20.0)
        list03 = (0, 3, 7.0, 10.0)
        [self.assertEqual(list01[i], weightsdelays[1][i]) for i in range(4)]
        [self.assertEqual(list03[i], weightsdelays[5][i]) for i in range(4)]

    def test_nonsquarek_run(self):
        (psh, psw, ksh, ksw) = (4, 4, 1, 3)
        weightsdelays = self.do_run(psh, psw, ksh, ksw)
        # Checks go here
        self.assertEqual(10, len(weightsdelays))
        list10 = (1, 0, 7.0, 10.0)
        list42 = (4, 2, 5.0, 20.0)
        [self.assertEqual(list10[i], weightsdelays[1][i]) for i in range(4)]
        [self.assertEqual(list42[i], weightsdelays[5][i]) for i in range(4)]

    def test_bigger_nonsquarep_run(self):
        (psh, psw, ksh, ksw) = (32, 16, 3, 3)
        weightsdelays = self.do_run(psh, psw, ksh, ksw)
        # Checks go here
        self.assertEqual(1081, len(weightsdelays))
        list10 = (1, 0, 5.0, 20.0)
        list11 = (1, 1, 7.0, 10.0)
        [self.assertEqual(list10[i], weightsdelays[1][i]) for i in range(4)]
        [self.assertEqual(list11[i], weightsdelays[5][i]) for i in range(4)]
