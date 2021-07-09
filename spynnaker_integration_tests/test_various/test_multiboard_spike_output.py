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
import spynnaker8 as p
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinnaker_testbase import BaseTestCase


class TestMultiBoardSpikeOutput(BaseTestCase):

    counts = None

    @staticmethod
    def spike_receiver(label, time, neuron_ids):
        TestMultiBoardSpikeOutput.counts[label] += len(neuron_ids)

    def multi_board_spike_output(self):
        TestMultiBoardSpikeOutput.counts = dict()
        p.setup(1.0, n_chips_required=((48 * 2) + 1))
        try:
            machine = p.get_machine()
        except ConfigurationException as ex:
            raise SkipTest(ex)

        labels = list()
        pops = list()
        for chip in machine.ethernet_connected_chips:
            # print("Adding population on {}, {}".format(chip.x, chip.y))
            label = "{}, {}".format(chip.x, chip.y)
            spike_cells = {"spike_times": [i for i in range(100)]}
            pop = p.Population(10, p.SpikeSourceArray(**spike_cells),
                               label=label)
            pop.add_placement_constraint(chip.x, chip.y)
            labels.append(label)
            pops.append(pop)
            TestMultiBoardSpikeOutput.counts[label] = 0

        live_output = p.external_devices.SpynnakerLiveSpikesConnection(
            receive_labels=labels, local_port=None)
        for label, pop in zip(labels, pops):
            p.external_devices.activate_live_output_for(
                pop, database_notify_port_num=live_output.local_port)
            live_output.add_receive_callback(
                label, TestMultiBoardSpikeOutput.spike_receiver)

        p.run(1000)
        p.end()

        for label in labels:
            # print("Received {} of 1000 spikes from {}".format(
            #     TestMultiBoardSpikeOutput.counts[label], label))
            self.assertEqual(TestMultiBoardSpikeOutput.counts[label], 1000)

    def test_multi_board_spike_output(self):
        self.runsafe(self.multi_board_spike_output)


if __name__ == '__main__':
    unittest.main()
