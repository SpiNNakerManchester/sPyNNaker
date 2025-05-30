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
from time import sleep
from typing import List
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.connections import SpynnakerLiveSpikesConnection
from spynnaker.pyNN.utilities.neo_convertor import count_spikes

spike_receive_count = 0
spike_send_count = 0


def sim_control(label: str, sender: SpynnakerLiveSpikesConnection) -> None:
    global spike_send_count
    sleep(0.1)
    for _ in range(100):
        sender.send_spike(label, 0)
        sleep(0.01)
        spike_send_count += 1
    sleep(1)
    sim.external_devices.request_stop()


def receive_spikes(label: str, time: int, neuron_ids: List[int]) -> None:
    global spike_receive_count
    spike_receive_count += len(neuron_ids)


class TestSpikeRunForeverAgain(BaseTestCase):

    def do_run(self) -> None:
        conn = sim.external_devices.SpynnakerLiveSpikesConnection(
            receive_labels=["pop_1"], send_labels=["sender"], local_port=None)
        conn.add_receive_callback("pop_1", receive_spikes)
        conn.add_start_resume_callback("sender", sim_control)

        # initial call to set up the front end (pynn requirement)
        sim.setup(timestep=1.0, min_delay=1.0)
        ssa = sim.Population(
            1, sim.external_devices.SpikeInjector(
                database_notify_port_num=conn.local_port),
            label="sender")
        pop = sim.Population(
            1, sim.IF_curr_exp(), label="pop_1")
        pop.record("spikes")
        sim.Projection(ssa, pop, sim.OneToOneConnector(),
                       sim.StaticSynapse(weight=5, delay=1))
        sim.external_devices.activate_live_output_for(
            pop, database_notify_port_num=conn.local_port)

        spike_times = range(0, 10000, 100)
        input_pop = sim.Population(
            1, sim.SpikeSourceArray(
                spike_times=spike_times),
            label="input")
        input_pop.record("spikes")
        pop2 = sim.Population(
            1, sim.IF_curr_exp(), label="pop_2")
        pop2.record("spikes")
        sim.Projection(input_pop, pop2, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        n_loops = 2
        for _ in range(n_loops):
            sim.external_devices.run_forever()

        neo = pop.get_data("spikes")
        pop_spikes = count_spikes(neo)

        neo = input_pop.get_data("spikes")
        n_input_spikes = count_spikes(neo)
        # input_spikes = neo.segments[0].spiketrains

        neo = pop2.get_data("spikes")
        n_pop2_spikes = count_spikes(neo)
        # pop2_spikes = neo.segments[0].spiketrains
        sim.end()

        # We can lose some spikes in the process of sending them or
        # receiving them, so we guess that 10 might be lost
        self.assertTrue((spike_send_count - spike_receive_count) < 10)
        self.assertTrue((spike_send_count - pop_spikes) < 10)

        # This can be out by one if the sender sends a spike just before the
        # end, especially as the end is externally controlled
        self.assertTrue((n_input_spikes - n_pop2_spikes) < 1)

    def test_run(self) -> None:
        self.runsafe(self.do_run)


if __name__ == '__main__':
    TestSpikeRunForeverAgain().do_run()
