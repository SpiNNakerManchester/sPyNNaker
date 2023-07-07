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

import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


class TestChangeSpikeSourcePoisson(BaseTestCase):

    def with_reset(self):
        p.setup(1.0)

        inp = p.Population(
            100, p.SpikeSourcePoisson(rate=100), label="input")
        inp.record("spikes")
        p.run(100)
        spikes1 = inp.spinnaker_get_data('spikes')
        p.reset()
        inp.set(rate=10)
        p.run(100)
        spikes2 = inp.spinnaker_get_data('spikes')
        p.end()
        assert len(spikes1) > len(spikes2) * 5

    def test_with_reset(self):
        self.runsafe(self.with_reset)

    def no_reset(self):
        p.setup(1.0)

        inp = p.Population(
            100, p.SpikeSourcePoisson(rate=100), label="input")
        inp.record("spikes")
        p.run(100)
        spikes1 = inp.spinnaker_get_data('spikes')
        inp.set(rate=10)
        p.run(100)
        spikes2 = inp.spinnaker_get_data('spikes')
        assert len(spikes1) > (len(spikes2)-len(spikes1)) * 5
        p.end()

    def test_no_reset(self):
        self.runsafe(self.no_reset)
