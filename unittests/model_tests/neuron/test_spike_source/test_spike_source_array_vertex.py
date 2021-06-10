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
from spynnaker.pyNN.models.spike_source import SpikeSourceArrayVertex
import spynnaker8  # noqa: F401


class TestSpikeSourceArrayVertex(unittest.TestCase):

    def setUp(cls):
        spynnaker8.setup()

    def test_no_spikes(self):
        v = SpikeSourceArrayVertex(
            n_neurons=5, spike_times=[], constraints=None, label="test",
            max_atoms_per_core=None, model=None, splitter=None)
        v.spike_times = []
        v.set_value_by_selector([1, 3], "spike_times", [1, 2, 3])
        self.assertListEqual(
            [[], [1, 2, 3], [], [1, 2, 3], []], v.spike_times)

    def test_singleton_list(self):
        v = SpikeSourceArrayVertex(
            n_neurons=5, spike_times=[1, 11, 22], constraints=None,
            label="test", max_atoms_per_core=None, model=None, splitter=None)
        v.spike_times = [2, 12, 32]

    def test_double_list(self):
        SpikeSourceArrayVertex(
            n_neurons=3, spike_times=[[1], [11], [22]], constraints=None,
            label="test", max_atoms_per_core=None, model=None, splitter=None)
