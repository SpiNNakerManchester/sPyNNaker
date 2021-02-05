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

import unittest
from unittest import SkipTest
from spynnaker.pyNN.exceptions import ConfigurationException
import spynnaker8 as p
import spynnaker8.external_devices as e
from p8_integration_tests.base_test_case import BaseTestCase


class TestMultiBoardSpikeOutput(BaseTestCase):

    counts = None

    @staticmethod
    def spike_receiver(label, time, neuron_ids):
        TestMultiBoardSpikeOutput.counts[label] += len(neuron_ids)

    def multi_board_spike_output(self):
        TestMultiBoardSpikeOutput.counts = dict()
        try:
            p.setup(1.0, n_chips_required=((48 * 2) + 1))
            machine = p.get_machine()
        except ConfigurationException as oops:
            if "Failure to detect machine of " in str(oops):
                raise SkipTest("You Need at least 3 boards to run this test")

        labels = list()
        for chip in machine.ethernet_connected_chips:
            # print("Adding population on {}, {}".format(chip.x, chip.y))
            label = "{}, {}".format(chip.x, chip.y)
            labels.append(label)
            pop = p.Population(
                10, p.SpikeSourceArray(spike_times=[i for i in range(100)]),
                label=label)
            pop.add_placement_constraint(chip.x, chip.y)
            e.activate_live_output_for(pop)
            TestMultiBoardSpikeOutput.counts[label] = 0

        live_output = e.SpynnakerLiveSpikesConnection(
            receive_labels=labels, local_port=None)
        p.external_devices.add_database_socket_address(
            live_output.local_ip_address, live_output.local_port, None)
        for label in labels:
            live_output.add_receive_callback(
                label, TestMultiBoardSpikeOutput.spike_receiver)

        p.run(250)
        live_output.close()
        p.end()

        for label in labels:
            # print("Received {} of 1000 spikes from {}".format(
            #    TestMultiBoardSpikeOutput.counts[label], label))
            self.assertEqual(TestMultiBoardSpikeOutput.counts[label], 1000)

    def test_multi_board_spike_output(self):
        self.runsafe(self.multi_board_spike_output)


if __name__ == '__main__':
    unittest.main()
