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
