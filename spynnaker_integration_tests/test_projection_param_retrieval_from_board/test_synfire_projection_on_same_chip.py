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

import numpy
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner

n_neurons = 20  # number of neurons in each population
runtimes = [0, 100]  # The zero uis to read data before a run
neurons_per_core = None
weight_to_spike = 1.0
delay = 1
placement_constraint = (0, 0)
get_weights = True
get_delays = True


class SynfireProjectionOnSameChip(BaseTestCase):

    def get_before_and_after(self):
        synfire_run = SynfireRunner()
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           weight_to_spike=weight_to_spike, delay=delay,
                           placement_constraint=placement_constraint,
                           run_times=runtimes, get_weights=get_weights,
                           get_delays=get_delays)
        weights = synfire_run.get_weights()
        self.assertEqual(n_neurons, len(weights[0]))
        self.assertEqual(n_neurons, len(weights[1]))
        self.assertTrue(numpy.allclose(weights[0][0][2], weights[1][0][2]))

        delays = synfire_run.get_delay()
        self.assertEqual(n_neurons, len(delays[0]))
        self.assertEqual(n_neurons, len(delays[1]))
        self.assertTrue(numpy.allclose(delays[0][0][2], delays[1][0][2]))

    def test_get_before_and_after(self):
        self.runsafe(self.get_before_and_after)


if __name__ == '__main__':
    synfire_run = SynfireRunner()
    synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                       weight_to_spike=weight_to_spike, delay=delay,
                       placement_constraint=placement_constraint,
                       run_times=runtimes, get_weights=get_weights,
                       get_delays=get_delays)
    weights = synfire_run.get_weights()
    delays = synfire_run.get_delay()
    print("weights[0]")
    print(weights[0])
    print(weights[0].shape)
    print("weights[1]")
    print(weights[1])
    print(weights[1].shape)
    print("delays[0]")
    print(delays[0])
    print(delays[0].shape)
    print("delays[1]")
    print(delays[1])
    print(delays[1].shape)
