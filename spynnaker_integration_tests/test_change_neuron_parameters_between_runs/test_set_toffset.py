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
    p.set_number_of_neurons_per_core(p.IF_curr_exp, n_neurons / n_cores)

    cell_params_lif = {'cm': 0.25,
                       'i_offset': 0.0,
                       'tau_m': 20.0,
                       'tau_refrac': 2.0,
                       'tau_syn_E': 5.0,
                       'tau_syn_I': 5.0,
                       'v_reset': -70.0,
                       'v_rest': -65.0,
                       'v_thresh': -50.0
                       }

    populations = list()

    populations.append(p.Population(n_neurons, p.IF_curr_exp, cell_params_lif,
                                    label='pop_1'))

    populations[0].record("spikes")

    p.run(100)

    populations[0].set(i_offset=i_offset2)

    p.run(100)

    populations[0].set(i_offset=i_offset3)

    p.run(100)

    neo = populations[0].get_data()

    p.end()

    return neo


class TestSetTOffset(BaseTestCase):
    expected = [104., 112., 120., 128., 136., 144., 152., 160., 168., 176.,
                184., 192., 200., 205., 210., 215., 220., 225., 230., 235.,
                240., 245., 250., 255., 260., 265., 270., 275., 280., 285.,
                290., 295.]

    def one_core(self):
        n_neurons = 6
        n_cores = 1
        neo = do_run(n_neurons, n_cores, 1, 2)
        spiketrains = neo.segments[0].spiketrains
        for spiketrain in spiketrains:
            assert numpy.array_equal(spiketrain.magnitude, self.expected)

    def test_one_core(self):
        self.runsafe(self.one_core)

    def three_cores(self):
        n_neurons = 6
        n_cores = 3
        neo = do_run(n_neurons, n_cores, 1, 2)
        spiketrains = neo.segments[0].spiketrains
        for spiketrain in spiketrains:
            assert numpy.array_equal(spiketrain.magnitude, self.expected)

    def test_three_cores(self):
        self.runsafe(self.three_cores)


if __name__ == '__main__':
    n_neurons = 40
    n_cores = 3
    neo = do_run(n_neurons, n_cores, 1, 2)
    spikes = neo_convertor.convert_spikes(neo)
    v = neo_convertor.convert_data(neo, "v")
    gsyn = neo_convertor.convert_data(neo, "gsyn_exc")

    print(spikes)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v)
    plot_utils.heat_plot(gsyn)

    times = set(spikes[:, 1])
    print(n_neurons * len(times), len(spikes))
