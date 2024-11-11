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
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.utilities.neo_convertor import count_spikes

spike_receive_count = 0
spike_send_count = 0
max_spike = 0

def sim_control(label, sender):
    global spike_send_count
    sleep(0.1)
    for _ in range(100):
        sender.send_spike(label, 0)
        sleep(0.01)
        spike_send_count += 1
    sim.external_devices.request_stop()


def receive_spikes(label, time, neuron_ids):
    global spike_receive_count, max_spike
    spike_receive_count += len(neuron_ids)
    max_spike = max(time, max_spike)
    # for neuron_id in neuron_ids:
    #    print("Received spike at time", time, "from", label, "-", neuron_id)



class TestSpikeRunForeverAgain(BaseTestCase):

    def do_run(self):
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

        self.assertEqual(spike_send_count, spike_receive_count)
        self.assertEqual(spike_send_count, pop_spikes)
        expected_ssa_spikes = list(filter(
            lambda spike: spike < max_spike, spike_times))
        # print(expected_ssa_spikes)
        # print(input_spikes)
        # print(pop2_spikes)
        self.assertEqual(len(expected_ssa_spikes), n_input_spikes)
        self.assertEqual(n_pop2_spikes, n_input_spikes)

    def test_run(self):
        self.runsafe(self.do_run)


if __name__ == '__main__':
    TestSpikeRunForeverAgain().do_run()
