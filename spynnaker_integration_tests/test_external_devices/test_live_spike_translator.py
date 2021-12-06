# Copyright (c) 2021 The University of Manchester
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
import pyNN.spiNNaker as p

from spinnman.connections import ConnectionListener
from spinnman.messages.eieio.create_eieio_data import read_eieio_data_message
from spinnman.connections.udp_packet_connections import SCAMPConnection
from spinnman.utilities.utility_functions import reprogram_tag
from spinn_front_end_common.utilities.database import DatabaseConnection
from spinnman.messages.eieio.eieio_prefix import EIEIOPrefix
from spinnaker_testbase.base_test_case import BaseTestCase
import unittest


class UDPSCAMPConnection(SCAMPConnection):

    def get_receive_method(self):
        return self.receive


class TestLiveGatherTranslator(BaseTestCase):

    PREFIX = 0x1234

    def recv(self, data):
        message = read_eieio_data_message(data, 0)
        while message.is_next_element:
            element = message.next_element
            time = element.payload
            key = element.key
            self.stored_data.append((key, time))
            print(f"Received key {hex(key)} at time {time}")

    def database_callback(self, db_reader):
        ip_addr = db_reader.get_ip_address(0, 0)
        self.conn = UDPSCAMPConnection(remote_host=ip_addr)
        print(f"Listening on port {self.conn.local_port}")
        self.listener = ConnectionListener(self.conn)
        self.listener.add_callback(self.recv)
        reprogram_tag(self.conn, tag=1, strip=True)
        self.listener.start()

    def live_spike_receive_translated(self):
        self.stored_data = list()

        db_conn = DatabaseConnection(local_port=None)
        db_conn.add_database_callback(self.database_callback)

        p.setup(1.0)
        p.set_number_of_neurons_per_core(p.SpikeSourceArray, 5)

        pop = p.Population(
            25, p.SpikeSourceArray([[1000 + (i * 10)] for i in range(25)]))
        p.external_devices.activate_live_output_for(
            pop, translate_keys=True,
            database_notify_port_num=db_conn.local_port, tag=1,
            use_prefix=True, key_prefix=self.PREFIX,
            prefix_type=EIEIOPrefix.UPPER_HALF_WORD)

        p.run(1500)

        p.end()
        self.listener.close()
        self.conn.close()

        self.assertGreater(len(self.stored_data), 0)
        for key, time in self.stored_data:
            self.assertEqual(key >> 16, self.PREFIX)
            self.assertEqual(1000 + ((key & 0xFFFF) * 10), time)

    def test_live_spike_receive_translated(self):
        self.runsafe(self.live_spike_receive_translated)


if __name__ == '__main__':
    unittest.main()
