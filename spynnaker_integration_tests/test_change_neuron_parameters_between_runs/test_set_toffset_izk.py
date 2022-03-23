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
import spynnaker.plot_utils as plot_utils
import spynnaker8 as p
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


def do_run(n_neurons, n_cores, i_offset2, i_offset3):
    p.setup(timestep=1.0, min_delay=1.0)
    p.set_number_of_neurons_per_core(p.Izhikevich, n_neurons / n_cores)
    cell_params_izk = {'a': 0.02,
                       'b': 0.2,
                       'c': -65,
                       'd': 8,
                       'v': -75,
                       'u': 0,
                       'tau_syn_E': 2,
                       'tau_syn_I': 2,
                       'i_offset': 0
                       }
    populations = list()
    populations.append(p.Population(n_neurons, p.Izhikevich, cell_params_izk,
                                    label='pop_1'))
    populations[0].record("spikes")
    p.run(1000)
    populations[0].set(i_offset=i_offset2)
    p.run(1000)
    populations[0].set(i_offset=i_offset3)
    p.run(1000)
    neo = populations[0].get_data()

    p.end()

    return neo


class TestSetTOffset(BaseTestCase):
    expected = [2011., 2148., 2288., 2427., 2565., 2703., 2844., 2982.]

    def one_core(self):
        n_neurons = 32
        n_cores = 1
        neo = do_run(n_neurons, n_cores, 2, 4)
        spiketrains = neo.segments[0].spiketrains
        for spiketrain in spiketrains:
            assert numpy.array_equal(spiketrain.magnitude, self.expected)

    def test_one_core(self):
        self.runsafe(self.one_core)


if __name__ == '__main__':
    n_neurons = 40
    n_cores = 3
    neo = do_run(n_neurons, n_cores, 2, 4)
    spikes = neo_convertor.convert_spikes(neo)

    print(spikes)
    plot_utils.plot_spikes(spikes)

    times = set(spikes[:, 1])
    print(n_neurons * len(times), len(spikes))
