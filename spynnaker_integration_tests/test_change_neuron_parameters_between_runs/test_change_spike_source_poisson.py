# Copyright (c) 2017-2022 The University of Manchester
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
