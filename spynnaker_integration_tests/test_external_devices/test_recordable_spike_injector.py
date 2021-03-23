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

from collections import defaultdict
from random import randint
import time
import unittest
import spynnaker8 as p
from spinnaker_testbase import BaseTestCase


class TestRecordableSpikeInjector(BaseTestCase):

    _n_spikes = defaultdict(lambda: 0)
    _n_neurons = 100

    def _inject(self, label, connection):
        time.sleep(0.1)
        for _ in range(5000):
            neuron_id = randint(0, self._n_neurons - 1)
            self._n_spikes[neuron_id] += 1
            connection.send_spike(label, neuron_id)
            time.sleep(0.001)

    def recordable_spike_injector(self):
        # pylint: disable=no-member
        p.setup(1.0)
        pop = p.Population(
            self._n_neurons, p.external_devices.SpikeInjector(), label="input")
        pop.record("spikes")

        connection = p.external_devices.SpynnakerLiveSpikesConnection(
            send_labels=["input"])
        connection.add_start_callback("input", self._inject)

        p.run(10000)
        spikes = pop.get_data("spikes").segments[0].spiketrains
        p.end()

        spike_trains = dict()
        for spiketrain in spikes:
            i = spiketrain.annotations['source_index']
            if __name__ == "__main__":
                if self._n_spikes[i] < len(spiketrain):
                    print("Incorrect number of spikes, expected {} but got {}:"
                          .format(self._n_spikes[i], len(spiketrain)))
                    print(spiketrain)
            else:
                # If too many things send spikes at the same time, some might
                # get dropped, so we have to use >= rather than ==; we
                # shouldn't see *more* than the sent number of spikes!
                assert self._n_spikes[i] >= len(spiketrain)
            spike_trains[i] = spiketrain

        # We expect to see at least one spike per neuron even with dropped
        # packets
        for (index, count) in self._n_spikes.items():
            if __name__ == "__main__":
                if index not in spike_trains:
                    print("Neuron {} should have spiked {} times but didn't"
                          .format(index, count))
            else:
                assert index in spike_trains

    def test_recordable_spike_injector(self):
        self.runsafe(self.recordable_spike_injector)


if __name__ == "__main__":
    unittest.main()
