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

from typing import Dict, List

import unittest
from spynnaker.pyNN.exceptions import ConfigurationException
import pyNN.spiNNaker as p
from spynnaker.pyNN.data import SpynnakerDataView
import spynnaker.pyNN.external_devices as e
from spinnaker_testbase import BaseTestCase


class TestMultiBoardSpikeOutput(BaseTestCase):

    counts: Dict[str, int] = dict()

    @staticmethod
    def spike_receiver(label: str, time: int, neuron_ids: List[int]) -> None:
        TestMultiBoardSpikeOutput.counts[label] += len(neuron_ids)

    def multi_board_spike_output(self) -> None:
        TestMultiBoardSpikeOutput.counts = dict()
        try:
            p.setup(1.0, n_chips_required=((48 * 2) + 1))
            machine = p.get_machine()
        except ConfigurationException as oops:
            if "Failure to detect machine of " in str(oops):
                SpynnakerDataView.raise_skiptest(
                    "You Need at least 3 boards to run this test", oops)

        labels = list()
        pops = list()
        for chip in machine.ethernet_connected_chips:
            # print("Adding population on {}, {}".format(chip.x, chip.y))
            label = "{}, {}".format(chip.x, chip.y)
            labels.append(label)
            pop = p.Population(
                10, p.SpikeSourceArray(spike_times=[i for i in range(100)]),
                label=label)
            pops.append(pop)
            pop.add_placement_constraint(chip.x, chip.y)
            TestMultiBoardSpikeOutput.counts[label] = 0

        live_output = p.external_devices.SpynnakerLiveSpikesConnection(
            receive_labels=labels, local_port=None)
        for pop in pops:
            e.activate_live_output_for(
                pop, database_notify_port_num=live_output.local_port)
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

    def test_multi_board_spike_output(self) -> None:
        self.runsafe(self.multi_board_spike_output)


if __name__ == '__main__':
    unittest.main()
