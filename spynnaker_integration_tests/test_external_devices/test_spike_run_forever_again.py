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


def sim_control(label, sender):
    global spike_send_count
    sleep(0.1)
    for _ in range(100):
        sender.send_spike(label, 0)
        sleep(0.01)
        spike_send_count += 1
    sim.external_devices.request_stop()


def receive_spikes(label, time, neuron_ids):
    global spike_receive_count
    spike_receive_count += len(neuron_ids)
    for neuron_id in neuron_ids:
        print("Received spike at time", time, "from", label, "-", neuron_id)


def do_run():

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

    for _ in range(5):
        sim.external_devices.run_forever()
    neo = pop.get_data("spikes")
    spikes = count_spikes(neo)
    pop.write_data("test.csv", "spikes")

    sim.end()
    print(spike_send_count, spike_receive_count, spikes)


class TestSpikeRunForeverAgain(BaseTestCase):

    def test_run(self):
        self.runsafe(do_run)


if __name__ == "__main__":
    do_run()
