# Copyright (c) 2017-2022 The University of Manchester
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

from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as sim
import random
from spynnaker.pyNN.utilities import neo_convertor


class TestSingleStepCurrentSource(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0)

        n_neurons = 10
        runtime = 400

        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 5)
        pop_lif = sim.Population(n_neurons, sim.IF_curr_exp(
            v_thresh=-55.0, tau_refrac=5.0, tau_m=10.0), label="lif")

        times = []
        amplitudes = []
        n_steps = 10
        for n_step in range(n_steps):
            times.append(50.0 + (10 * n_step))
            amplitudes.append(random.random())

        # Test a single source injected into all neurons
        # Note the amplitudes are not large enough to cause spikes
        step_source = sim.StepCurrentSource(times=times, amplitudes=amplitudes)
        pop_lif.inject(step_source)

        # Test a single source injected into 5 neurons (across both cores)
        # with an amplitude large enough to cause spikes on these 5 neurons
        step_source2 = sim.StepCurrentSource(
            times=[300, 301], amplitudes=[1.1, -0.2])
        pop_lif[3:8].inject(step_source2)

        pop_lif.record(["spikes"])

        sim.run(runtime)

        lif_spikes = pop_lif.get_data('spikes')

        sim.end()

        spike_count = neo_convertor.convert_spikes(lif_spikes)

        self.assertEqual(len(spike_count), 5)

    def test_run(self):
        self.runsafe(self.do_run)
