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
import time
from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as sim
from spinn_front_end_common.utilities.database.database_connection import (
    DatabaseConnection)
from spynnaker.pyNN.spynnaker_external_device_plugin_manager import (
    SpynnakerExternalDevicePluginManager)


def start_callback() -> None:
    time.sleep(3.0)
    print("Ending Simulation")
    sim.external_devices.request_stop()


def stop_callback() -> None:
    print("Stopping")


def run_forever_recorded() -> None:
    sim.setup(1.0)
    source_spikes = range(0, 5000, 100)
    stim = sim.Population(1, sim.SpikeSourceArray(source_spikes))
    pop = sim.Population(255, sim.IF_curr_exp(tau_syn_E=1.0), label="pop")
    sim.Projection(
        stim, pop, sim.AllToAllConnector(), sim.StaticSynapse(weight=20.0))
    pop.record(["v", "spikes"])
    conn = DatabaseConnection(
        start_resume_callback_function=start_callback,
        stop_pause_callback_function=stop_callback, local_port=None)
    SpynnakerExternalDevicePluginManager.add_database_socket_address(
        conn.local_ip_address, conn.local_port, None)
    sim.external_devices.run_forever()

    spikes = pop.get_data("spikes").segments[0].spiketrains
    sim.end()
    for spiketrain in spikes:
        assert len(spiketrain) > 0
        for spike, source in zip(spiketrain, source_spikes[:len(spiketrain)]):
            assert spike > source
            assert spike < source + 10


class MyTestCase(BaseTestCase):
    def test_run_forever_recorded(self) -> None:
        self.runsafe(run_forever_recorded)


if __name__ == '__main__':
    run_forever_recorded()
