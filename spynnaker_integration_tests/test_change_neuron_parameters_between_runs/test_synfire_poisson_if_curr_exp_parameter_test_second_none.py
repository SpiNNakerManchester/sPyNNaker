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
import spynnaker.spike_checker as spike_checker
import spynnaker.plot_utils as plot_utils
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner

n_neurons = 200  # number of neurons in each population
neurons_per_core = n_neurons / 2
run_times = [5000, 5000]
wrap_around = False
# parameters for population 1 first run
input_class = p.SpikeSourcePoisson
start_time = 0
duration = 5000.0
rate = 2.0
# parameters for population 2 first run
set_between_runs = [(1, 'duration', 0)]
extract_between_runs = False
record_input_spikes = True

synfire_run = SynfireRunner()


class TestSynfirePoissonIfCurrExpParameterTestSecondNone(BaseTestCase):

    def second_none(self):
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           run_times=run_times,
                           use_wrap_around_connections=wrap_around,
                           input_class=input_class,
                           start_time=start_time, duration=duration, rate=rate,
                           extract_between_runs=extract_between_runs,
                           set_between_runs=set_between_runs,
                           record_input_spikes=record_input_spikes)
        input_spikes = synfire_run.get_spike_source_spikes_numpy()
        spikes = synfire_run.get_output_pop_spikes_numpy()
        # Check input spikes stop
        hist = numpy.histogram(input_spikes[:, 1], bins=[0, 5000, 10000])
        self.assertEqual(0, hist[0][1])
        spike_checker.synfire_multiple_lines_spike_checker(spikes, n_neurons,
                                                           len(input_spikes),
                                                           wrap_around=False)

    def test_second_none(self):
        self.runsafe(self.second_none)


if __name__ == '__main__':
    synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                       run_times=run_times,
                       use_wrap_around_connections=wrap_around,
                       input_class=input_class, start_time=start_time,
                       duration=duration, rate=rate,
                       extract_between_runs=extract_between_runs,
                       set_between_runs=set_between_runs,
                       record_input_spikes=record_input_spikes)
    _gsyn = synfire_run.get_output_pop_gsyn_exc_numpy()
    _v = synfire_run.get_output_pop_voltage_numpy()
    _spikes_in = synfire_run.get_spike_source_spikes_numpy()
    _hist = numpy.histogram(_spikes_in[:, 1], bins=[0, 5000, 10000])
    print(_hist[0][0], _hist[0][1])
    _spikes_out = synfire_run.get_output_pop_spikes_numpy()
    plot_utils.plot_spikes([_spikes_in, _spikes_out])
    plot_utils.heat_plot(_v)
    plot_utils.heat_plot(_gsyn)
