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
import spynnaker.plot_utils as plot_utils
import spynnaker8 as p
from spynnaker8.utilities import neo_convertor
from p8_integration_tests.base_test_case import BaseTestCase

SPIKE_TIMES = [11, 22]


def do_run(nNeurons, timestep):

    spike_list = {'spike_times': SPIKE_TIMES}
    print(spike_list)
    p.setup(timestep=timestep, min_delay=timestep, max_delay=timestep*10)

    pop = p.Population(nNeurons, p.SpikeSourceArray, spike_list, label='input')

    pop.record("spikes")

    p.run(200)

    neo = pop.get_data("spikes")
    p.end()

    return neo


class SpikesTest(BaseTestCase):

    def test_many(self):
        nNeurons = 100  # number of neurons in each population
        neo = do_run(nNeurons, timestep=1.0)
        spikes = neo_convertor.convert_spikes(neo)
        spikes = neo_convertor.convert_spikes(neo)
        self.assertEqual(nNeurons * len(SPIKE_TIMES), len(spikes))
        for i in range(0, len(spikes), 2):
            self.assertEqual(i/2, spikes[i][0])
            self.assertEqual(11, spikes[i][1])
            self.assertEqual(i/2, spikes[i+1][0])
            self.assertEqual(22, spikes[i+1][1])

    def test_few(self):
        nNeurons = 10  # number of neurons in each population
        neo = do_run(nNeurons, timestep=1.0)
        spikes = neo_convertor.convert_spikes(neo)
        self.assertEqual(nNeurons * len(SPIKE_TIMES), len(spikes))
        for i in range(0, len(spikes), 2):
            self.assertEqual(i/2, spikes[i][0])
            self.assertEqual(11, spikes[i][1])
            self.assertEqual(i/2, spikes[i+1][0])
            self.assertEqual(22, spikes[i+1][1])

    def test_slow(self):
        nNeurons = 1  # number of neurons in each population
        neo = do_run(nNeurons, timestep=10.0)
        spikes = neo_convertor.convert_spikes(neo)
        self.assertEqual(nNeurons * len(SPIKE_TIMES), len(spikes))
        for i in range(0, len(spikes), 2):
            self.assertEqual(i/2, spikes[i][0])
            # Note spike times rounded up to next timestep
            self.assertEqual(20, spikes[i][1])
            self.assertEqual(i/2, spikes[i+1][0])
            self.assertEqual(30, spikes[i+1][1])

    def test_fast(self):
        nNeurons = 1  # number of neurons in each population
        neo = do_run(nNeurons, timestep=0.1)
        spikes = neo_convertor.convert_spikes(neo)
        self.assertEqual(nNeurons * len(SPIKE_TIMES), len(spikes))
        for i in range(0, len(spikes), 2):
            self.assertEqual(i/2, spikes[i][0])
            self.assertEqual(11, spikes[i][1])
            self.assertEqual(i/2, spikes[i+1][0])
            self.assertEqual(22, spikes[i+1][1])


if __name__ == '__main__':
    _n_neurons = 100  # number of neurons in each population
    _neo = do_run(_n_neurons, 0.1)
    _spikes = neo_convertor.convert_spikes(_neo)
    plot_utils.plot_spikes(_spikes)
    print(_spikes)
