# !/usr/bin/python

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

import spynnaker.plot_utils as plot_utils
import spynnaker8 as p
from spynnaker8.utilities import neo_convertor
from p8_integration_tests.base_test_case import BaseTestCase

# Shows https://github.com/SpiNNakerManchester/sPyNNaker/issues/335
# Does not happen on other neurons


def do_run(nNeurons):

    spike_list = {'spike_times': [float(x) for x in range(0, 599, 50)]}
    print(spike_list)
    p.setup(timestep=1.0, min_delay=1.0, max_delay=32.0)

    inpop = p.Population(nNeurons, p.SpikeSourceArray, spike_list,
                         label='input')
    pop = p.Population(nNeurons, p.IF_curr_exp(), label='rec')
    p.Projection(inpop, pop, p.OneToOneConnector(),
                 synapse_type=p.StaticSynapse(weight=5, delay=3),
                 receptor_type="excitatory")

    pop.record("spikes")

    p.run(1000)

    neo = pop.get_data("spikes")

    p.end()

    return neo


class Bug(BaseTestCase):

    def test_run_(self):
        nNeurons = 700  # number of neurons in each population
        neo = do_run(nNeurons)
        spike_count = neo_convertor.count_spikes(neo)
        self.assertEqual(7200, spike_count)


if __name__ == '__main__':
    nNeurons = 100  # number of neurons in each population
    neo = do_run(nNeurons)
    spikes = neo_convertor.convert_spikes(neo)
    plot_utils.plot_spikes(spikes)
    print(spikes)
