# Copyright (c) 2017-2023 The University of Manchester
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

import unittest
from unittest import SkipTest
from spynnaker.pyNN.exceptions import ConfigurationException
import pyNN.spiNNaker as p
import spynnaker.pyNN.external_devices as e
from spinnaker_testbase import BaseTestCase


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
                raise SkipTest(
                    "You Need at least 3 boards to run this test") from oops

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

        live_output = p.external_devices.SpynnakerLiveSpikesConnection(
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
            # Lost packets might mean some get lost, but no more than 1000
            # can be received
            count = TestMultiBoardSpikeOutput.counts[label]
            self.assertGreaterEqual(count, 500)
            self.assertLessEqual(count, 1000)

    def test_multi_board_spike_output(self):
        self.runsafe(self.multi_board_spike_output)


if __name__ == '__main__':
    unittest.main()
