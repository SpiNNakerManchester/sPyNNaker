# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import math
import time
from typing import List
from neo import Block
import pyNN.spiNNaker as sim

from spinnaker_testbase import BaseTestCase
from spinn_front_end_common.utilities.connections import LiveEventConnection
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.connections import SpynnakerPoissonControlConnection


class TestPoissonSpikeSource(BaseTestCase):

    def check_spikes(self, n_neurons: int, neo: Block, expected: float) -> None:
        spikes = neo.segments[0].spiketrains
        count = sum(len(s) for s in spikes)
        tolerance = math.sqrt(expected)
        self.assertAlmostEqual(expected, float(count) / float(n_neurons),
                               delta=tolerance)

    def recording_poisson_spikes(self, run_zero: bool) -> None:
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
        ssp = sim.Population(
            n_neurons, sim.SpikeSourcePoisson(rate=1), label='inputSpikes_1')

        sim.Projection(ssp, pop_1, sim.OneToOneConnector())

        ssp.record("spikes")

        if run_zero:
            sim.run(0)
        sim.run(5000)
        neo = ssp.get_data("spikes")
        sim.end()

        self.check_spikes(n_neurons, neo, 5)

    def recording_poisson_spikes_no_zero(self) -> None:
        self.recording_poisson_spikes(False)

    def test_recording_poisson_spikes_no_zero(self) -> None:
        self.runsafe(self.recording_poisson_spikes_no_zero)

    def recording_poisson_spikes_with_zero(self) -> None:
        self.recording_poisson_spikes(True)

    def test_recording_poisson_spikes_with_zero(self) -> None:
        self.runsafe(self.recording_poisson_spikes_with_zero)

    def recording_poisson_spikes_big(self) -> None:
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
        ssp = sim.Population(
            n_neurons, sim.SpikeSourcePoisson(rate=1), label='inputSpikes_1')

        sim.Projection(ssp, pop_1, sim.OneToOneConnector())

        ssp.record("spikes")

        sim.run(5000)
        neo = ssp.get_data("spikes")
        sim.end()

        self.check_spikes(n_neurons, neo, 5)

    def test_recording_poisson_spikes_big(self) -> None:
        self.runsafe(self.recording_poisson_spikes_big)

    def recording_poisson_spikes_rate_0(self) -> None:
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
        ssp = sim.Population(
            n_neurons, sim.SpikeSourcePoisson, {'rate': 0}, label='ssp')

        sim.Projection(ssp, pop_1, sim.OneToOneConnector())

        ssp.record("spikes")

        sim.run(5000)
        neo = ssp.get_data("spikes")
        sim.end()

        self.check_spikes(n_neurons, neo, 0)

    def test_recording_poisson_spikes_rate_0(self) -> None:
        self.runsafe(self.recording_poisson_spikes_rate_0)

    def check_rates(self, rates: List[float], seconds: int, seed: int) -> None:
        n_neurons = 100
        sim.setup(timestep=1.0)
        ssps = {}
        for rate in rates:
            ssp = sim.Population(
                n_neurons, sim.SpikeSourcePoisson(rate),
                label='inputSpikes_{}'.format(rate),
                additional_parameters={"seed": seed})
            ssp.record("spikes")
            ssps[rate] = ssp
        sim.run(seconds * 1000)
        spikes = {}
        for rate in rates:
            neo = ssps[rate].get_data("spikes")
            spikes[rate] = neo
        sim.end()
        for rate in rates:
            self.check_spikes(n_neurons, spikes[rate], rate*seconds)

    def recording_poisson_spikes_rate_fast(self) -> None:
        self.check_rates(
            [10.24, 20.48, 40.96, 81.92, 163.84, 327.68, 655.36, 1310.72], 10,
            0)

    def test_recording_poisson_spikes_rate_fast(self) -> None:
        self.runsafe(self.recording_poisson_spikes_rate_fast)

    def recording_poisson_spikes_rate_slow(self) -> None:
        self.check_rates(
            [0, 0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12],
            100, 0)

    def test_recording_poisson_spikes_rate_slow(self) -> None:
        self.runsafe(self.recording_poisson_spikes_rate_slow)

    def poisson_live_rates(self) -> None:

        self._saved_label_init = None
        self._saved_vertex_size = None
        self._saved_run_time_ms = None
        self._saved_machine_timestep_ms = None
        self._saved_label_set = None
        self._saved_label_stop = None

        def init(label: str, vertex_size: int, run_time_ms: float,
                 machine_timestep_ms: float) -> None:
            self._saved_label_init = label
            self._saved_vertex_size = vertex_size
            self._saved_run_time_ms = run_time_ms
            self._saved_machine_timestep_ms = machine_timestep_ms

        def set_rates(
                label: str, conn: SpynnakerPoissonControlConnection) -> None:
            time.sleep(1.0)
            conn.set_rates(label, [(i, 50) for i in range(50)])
            self._saved_label_set = label

        def stop(label: str, _conn: LiveEventConnection) -> None:
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
        self.assertGreater(count_0_49, 0.0)
        self.assertEqual(count_50_99, 0.0)
        self.assertEqual(self._saved_label_set, pop_label)
        self.assertEqual(self._saved_label_init, pop_label)
        self.assertEqual(self._saved_label_stop, pop_label)
        self.assertEqual(self._saved_machine_timestep_ms, timestep)
        self.assertEqual(self._saved_vertex_size, n_neurons)
        self.assertEqual(self._saved_run_time_ms, runtime)

    def test_poisson_live_rates(self) -> None:
        self.runsafe(self.poisson_live_rates)

    def poisson_multi_run_change_rate(self) -> None:

        n_p = 2
        sim.setup(timestep=1.0)

        simtime = 1000

        init_rate = [50, 50]
        pop_src = sim.Population(
            n_p, sim.SpikeSourcePoisson(rate=init_rate), label="src")

        sim.run(simtime)

        pop_src.set(rate=[1, 100])

        sim.run(simtime)

        sim.end()

    def test_poisson_multi_run_change_rate(self) -> None:
        self.runsafe(self.poisson_multi_run_change_rate)

    def poisson_higher_rate(self) -> None:
        sim.setup(timestep=1.0)
        pop_src = sim.Population(
            100, sim.SpikeSourcePoisson(rate=1000), label="src")
        pop_src.record("spikes")
        sim.run(10000)
        neo = pop_src.get_data("spikes")
        sim.end()
        self.check_spikes(100, neo, 10000)

    def test_poisson_higher_rate(self) -> None:
        self.runsafe(self.poisson_higher_rate)
