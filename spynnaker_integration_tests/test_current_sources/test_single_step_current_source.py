# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as sim
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
            amplitudes.append(0.2 + (0.05 * n_step))

        # Test a single source injected into all neurons
        # Note the amplitudes are not large enough to cause spikes
        step_source = sim.StepCurrentSource(times=times, amplitudes=amplitudes)
        pop_lif.inject(step_source)

        # Test a single source injected into 5 neurons (across both cores)
        # with an amplitude large enough to cause spikes on these 5 neurons
        step_source2 = sim.StepCurrentSource(
            times=[300, 301], amplitudes=[10.1, -0.2])
        pop_lif[3:8].inject(step_source2)

        pop_lif.record(["spikes"])

        sim.run(runtime)

        lif_spikes = pop_lif.get_data('spikes')

        sim.end()

        spike_count = neo_convertor.convert_spikes(lif_spikes)

        self.assertEqual(len(spike_count), 5)

    def test_run(self):
        self.runsafe(self.do_run)
