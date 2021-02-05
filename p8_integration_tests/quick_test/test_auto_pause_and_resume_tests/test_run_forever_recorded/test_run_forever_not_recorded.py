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

from p8_integration_tests.base_test_case import BaseTestCase
import spynnaker8 as sim
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
