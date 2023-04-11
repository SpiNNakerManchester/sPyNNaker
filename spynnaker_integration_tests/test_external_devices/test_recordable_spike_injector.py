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

from collections import defaultdict
from random import randint
import time
import unittest
import pyNN.spiNNaker as p
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
