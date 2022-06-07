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
from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as sim
import math
import time
from spinn_front_end_common.utilities.exceptions import ConfigurationException


class TestPoissonSpikeSource(BaseTestCase):

    def check_spikes(self, n_neurons, input, expected):
        neo = input.get_data("spikes")
        spikes = neo.segments[0].spiketrains
        count = sum(len(s) for s in spikes)
        tolerance = math.sqrt(expected)
        print(expected, float(count) / float(n_neurons))
        self.assertAlmostEqual(expected, float(count) / float(n_neurons),
                               delta=tolerance,
                               msg="Error on {}".format(input.label))

    def recording_poisson_spikes(self, run_zero):
        sim.setup(timestep=1.0, min_delay=1.0)
        n_neurons = 200  # number of neurons in each population
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, n_neurons / 2)

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

        pop_1 = sim.Population(
            n_neurons, sim.IF_curr_exp, cell_params_lif, label='pop_1')
        input = sim.Population(
            n_neurons, sim.SpikeSourcePoisson, {}, label='inputSpikes_1')

        sim.Projection(input, pop_1, sim.OneToOneConnector())

        input.record("spikes")

        if run_zero:
            sim.run(0)
        sim.run(5000)
        self.check_spikes(n_neurons, input, 5)

        sim.end()

    def recording_poisson_spikes_no_zero(self):
        self.recording_poisson_spikes(False)

    def test_recording_poisson_spikes_no_zero(self):
        self.runsafe(self.recording_poisson_spikes_no_zero)

    def recording_poisson_spikes_with_zero(self):
        self.recording_poisson_spikes(True)

    def test_recording_poisson_spikes_with_zero(self):
        self.runsafe(self.recording_poisson_spikes_with_zero)

    def recording_poisson_spikes_big(self):
        sim.setup(timestep=1.0, min_delay=1.0)
        n_neurons = 2560  # number of neurons in each population

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

        pop_1 = sim.Population(
            n_neurons, sim.IF_curr_exp, cell_params_lif, label='pop_1')
        input = sim.Population(
            n_neurons, sim.SpikeSourcePoisson, {}, label='inputSpikes_1')

        sim.Projection(input, pop_1, sim.OneToOneConnector())

        input.record("spikes")

        sim.run(5000)
        self.check_spikes(n_neurons, input, 5)

        sim.end()

    def test_recording_poisson_spikes_big(self):
        self.runsafe(self.recording_poisson_spikes_big)

    def recording_poisson_spikes_rate_0(self):
        sim.setup(timestep=1.0, min_delay=1.0)
        n_neurons = 256  # number of neurons in each population
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, n_neurons / 2)

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

        pop_1 = sim.Population(
            n_neurons, sim.IF_curr_exp, cell_params_lif, label='pop_1')
        input = sim.Population(
            n_neurons, sim.SpikeSourcePoisson, {'rate': 0}, label='input')

        sim.Projection(input, pop_1, sim.OneToOneConnector())

        input.record("spikes")

        sim.run(5000)
        self.check_spikes(n_neurons, input, 0)

        sim.end()

    def test_recording_poisson_spikes_rate_0(self):
        self.runsafe(self.recording_poisson_spikes_rate_0)

    def check_rates(self, rates, seconds, seed):
        n_neurons = 100
        sim.setup(timestep=1.0)
        inputs = {}
        for rate in rates:
            input = sim.Population(
                n_neurons, sim.SpikeSourcePoisson(rate),
                label='inputSpikes_{}'.format(rate),
                additional_parameters={"seed": seed})
            input.record("spikes")
            inputs[rate] = input
        sim.run(seconds * 1000)
        for rate in rates:
            self.check_spikes(n_neurons, inputs[rate], rate*seconds)
        sim.end()

    def recording_poisson_spikes_rate_fast(self):
        self.check_rates(
            [10.24, 20.48, 40.96, 81.92, 163.84, 327.68, 655.36, 1310.72], 10,
            0)

    def test_recording_poisson_spikes_rate_fast(self):
        self.runsafe(self.recording_poisson_spikes_rate_fast)

    def recording_poisson_spikes_rate_slow(self):
        self.check_rates(
            [0, 0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12],
            100, 0)

    def test_recording_poisson_spikes_rate_slow(self):
        self.runsafe(self.recording_poisson_spikes_rate_slow)

    def poisson_live_rates(self):

        self._saved_label_init = None
        self._saved_vertex_size = None
        self._saved_run_time_ms = None
        self._saved_machine_timestep_ms = None
        self._saved_label_set = None
        self._saved_label_stop = None

        def init(label, vertex_size, run_time_ms, machine_timestep_ms):
            self._saved_label_init = label
            self._saved_vertex_size = vertex_size
            self._saved_run_time_ms = run_time_ms
            self._saved_machine_timestep_ms = machine_timestep_ms

        def set_rates(label, conn):
            time.sleep(1.0)
            conn.set_rates(label, [(i, 50) for i in range(50)])
            self._saved_label_set = label

        def stop(label, _conn):
            self._saved_label_stop = label

        n_neurons = 100
        timestep = 1.0
        runtime = 2000
        sim.setup(timestep=timestep)
        sim.set_number_of_neurons_per_core(sim.SpikeSourcePoisson, 75)
        pop_label = "pop_to_control"
        pop = sim.Population(
            n_neurons, sim.SpikeSourcePoisson(rate=0.0),
            label=pop_label,
            additional_parameters={"max_rate": 50.0})
        pop.record("spikes")
        conn = sim.external_devices.SpynnakerPoissonControlConnection(
            poisson_labels=[pop_label], local_port=None)
        conn.add_start_resume_callback(pop_label, set_rates)
        conn.add_init_callback(pop_label, init)
        conn.add_pause_stop_callback(pop_label, stop)
        with self.assertRaises(ConfigurationException):
            conn.add_receive_callback(pop_label, stop)
        sim.external_devices.add_database_socket_address(
            conn.local_ip_address, conn.local_port, None)
        sim.external_devices.add_poisson_live_rate_control(pop)
        sim.run(runtime)
        neo = pop.get_data("spikes")
        spikes = neo.segments[0].spiketrains
        sim.end()
        count_0_49 = 0
        for a_spikes in spikes[0:50]:
            count_0_49 += len(a_spikes)
        count_50_99 = 0
        for a_spikes in spikes[50:100]:
            count_50_99 += len(a_spikes)
        tolerance = math.sqrt(50.0)
        self.assertAlmostEqual(50.0, count_0_49 / 50.0, delta=tolerance)
        self.assertEqual(count_50_99, 0.0)
        self.assertEqual(self._saved_label_set, pop_label)
        self.assertEqual(self._saved_label_init, pop_label)
        self.assertEqual(self._saved_label_stop, pop_label)
        self.assertEqual(self._saved_machine_timestep_ms, timestep)
        self.assertEqual(self._saved_vertex_size, n_neurons)
        self.assertEqual(self._saved_run_time_ms, runtime)

    def test_poisson_live_rates(self):
        self.runsafe(self.poisson_live_rates)
