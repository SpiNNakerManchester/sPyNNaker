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

"""
Synfirechain-like example
"""
from unittest import SkipTest
import spynnaker.plot_utils as plot_utils
import spynnaker8 as p
from spynnaker.pyNN.utilities import neo_convertor
from p8_integration_tests.base_test_case import BaseTestCase


def do_run(nNeurons, _neurons_per_core):

    spike_list = {'spike_times': [float(x) for x in range(0, 599, 50)]}
    p.setup(timestep=1.0, min_delay=1.0, max_delay=32.0)

    p.set_number_of_neurons_per_core(p.SpikeSourceArray, _neurons_per_core)

    pop = p.Population(nNeurons, p.SpikeSourceArray, spike_list, label='input')

    pop.record("spikes")

    p.run(1000)

    neo = pop.get_data("spikes")

    p.end()

    return neo


class BigManySpikes(BaseTestCase):

    def test_sixty_eight(self):
        nNeurons = 600  # number of neurons in each population
        neo = do_run(nNeurons, 68)
        try:
            spike_count = neo_convertor.count_spikes(neo)
            self.assertEqual(spike_count, 7200)
        except Exception as ex:
            # Just in case the range failed
            raise SkipTest(ex)

    def test_sixty_nine(self):
        nNeurons = 600  # number of neurons in each population
        neo = do_run(nNeurons, 69)
        try:
            spike_count = neo_convertor.count_spikes(neo)
            self.assertEqual(spike_count, 7200)
        except Exception as ex:
            # Just in case the range failed
            raise SkipTest(ex)


if __name__ == '__main__':
    nNeurons = 600  # number of neurons in each population
    spikes = do_run(nNeurons, 69)
    plot_utils.plot_spikes(spikes)
    print(spikes)
