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
from spinn_front_end_common.utilities.database.database_connection import (
    DatabaseConnection)
from spynnaker.pyNN.spynnaker_external_device_plugin_manager import (
    SpynnakerExternalDevicePluginManager)
import time


def start_callback():
    print("Starting run for 3 seconds")
    time.sleep(3.0)
    print("Ending Simulation")
    sim.external_devices.request_stop()


def stop_callback():
    print("Stopping")


def run_forever_not_recorded():
    sim.setup(1.0)
    stim = sim.Population(1, sim.SpikeSourcePoisson(rate=10.0))
    pop = sim.Population(255, sim.IF_curr_exp(tau_syn_E=1.0), label="pop")
    sim.Projection(
        stim, pop, sim.AllToAllConnector(), sim.StaticSynapse(weight=20.0))
    conn = DatabaseConnection(
        start_resume_callback_function=start_callback,
        stop_pause_callback_function=stop_callback, local_port=None)
    SpynnakerExternalDevicePluginManager.add_database_socket_address(
        conn.local_ip_address, conn.local_port, None)
    sim.external_devices.run_forever()
    sim.end()


class MyTestCase(BaseTestCase):
    def test_run_forever_recorded(self):
        self.runsafe(run_forever_not_recorded)


if __name__ == '__main__':
    run_forever_not_recorded()
