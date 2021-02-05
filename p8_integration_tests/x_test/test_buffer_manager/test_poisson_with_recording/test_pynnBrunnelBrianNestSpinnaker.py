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

import p8_integration_tests.scripts.pynnBrunnelPlot as pblt
from p8_integration_tests.base_test_case import BaseTestCase
import p8_integration_tests.scripts.pynnBrunnelBrianNestSpinnaker as script
from spynnaker8.utilities import neo_convertor

Neurons = 3000  # number of neurons in each population
sim_time = 1000
simulator_Name = 'spiNNaker'


def plot(esp, sim_time, N_E):
    import pylab  # deferred so unittest are not dependent on it
    if esp is not None:
        ts_ext = [x[1] for x in esp]
        ids_ext = [x[0] for x in esp]
        title = 'Raster Plot of the excitatory population in %s' \
                % simulator_Name,
        pblt._make_plot(ts_ext, ts_ext, ids_ext, ids_ext,
                        len(ts_ext) > 0, 5.0, False, title,
                        'Simulation Time (ms)', total_time=sim_time,
                        n_neurons=N_E)

        pylab.show()


class PynnBrunnelBrianNestSpinnaker(BaseTestCase):

    # AttributeError: 'SpikeSourcePoisson' object has no attribute 'describe'
    def test_run(self):
        self.assert_not_spin_three()
        (esp, s, N_E) = script.do_run(
            Neurons, sim_time, record=True, seed=1)
        esp_numpy = neo_convertor.convert_spikes(esp)
        s_numpy = neo_convertor.convert_spikes(s)
        self.assertEqual(2400, N_E)
        # Range required, because random delays are used, and although these
        # are seeded, the order of generation is not consistent
        self.assertLessEqual(210, len(esp_numpy))
        self.assertGreaterEqual(230, len(esp_numpy))
        self.assertEqual(23888, len(s_numpy))


if __name__ == '__main__':
    (esp, s, N_E) = script.do_run(Neurons, sim_time, record=True, seed=1)
    esp_numpy = neo_convertor.convert_spikes(esp)
    s_numpy = neo_convertor.convert_spikes(s)
    plot(esp_numpy, sim_time, N_E)
    print(len(esp_numpy))
    print(len(s_numpy))
    print(N_E)
