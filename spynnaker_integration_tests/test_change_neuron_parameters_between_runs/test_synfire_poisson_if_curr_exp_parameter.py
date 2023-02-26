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
import numpy
import spynnaker.plot_utils as plot_utils
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner

n_neurons = 200  # number of neurons in each population
neurons_per_core = n_neurons / 2
run_times = [5000, 5000]
# parameters for population 1 first run
input_class = p.SpikeSourcePoisson
start_time = 0
duration = 5000.0
rate = 2.0
# parameters for population 2 first run
set_between_runs = [(1, 'start', 5000),
                    (1, 'rate', 200.0),
                    (1, 'duration', 2000.0)]
extract_between_runs = False

synfire_run = SynfireRunner()


class TestSynfirePoissonIfCurrExpParameter(BaseTestCase):

    def synfire_poisson_if_curr_exp_parameter(self):
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           run_times=run_times, input_class=input_class,
                           start_time=start_time, duration=duration, rate=rate,
                           extract_between_runs=extract_between_runs,
                           set_between_runs=set_between_runs,
                           seed=12345)
        spikes = synfire_run.get_output_pop_spikes_numpy()
        # Check spikes increase in second half by at least a factor of ten
        hist = numpy.histogram(spikes[:, 1], bins=[0, 5000, 10000])
        self.assertLess(hist[0][0] * 10, hist[0][1])

    def test_synfire_poisson_if_curr_exp_parameter(self):
        self.runsafe(self.synfire_poisson_if_curr_exp_parameter)


if __name__ == '__main__':
    synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                       run_times=run_times, input_class=input_class,
                       start_time=start_time, duration=duration, rate=rate,
                       extract_between_runs=extract_between_runs,
                       set_between_runs=set_between_runs)
    spikes = synfire_run.get_output_pop_spikes_numpy()
    hist = numpy.histogram(spikes[:, 1], bins=[0, 5000, 10000])
    print(hist[0][0] * 10, hist[0][1])
    plot_utils.plot_spikes(spikes)
