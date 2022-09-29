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

from testfixtures import LogCapture
import unittest
from spynnaker.pyNN.models.spike_source import SpikeSourceArrayVertex
import pyNN.spiNNaker as sim


class TestSpikeSourceArrayVertex(unittest.TestCase):

    def setUp(cls):
        sim.setup()

    def test_no_spikes(self):
        with LogCapture() as lc:
            v = SpikeSourceArrayVertex(
                n_neurons=5, spike_times=[], label="test",
                max_atoms_per_core=None, model=None, splitter=None)
        found = False
        for record in lc.records:
            if "no spike" in record.msg.fmt:
                found = True
        self.assertTrue(found)
        v.spike_times = []
        v.set_value_by_selector([1, 3], "spike_times", [1, 2, 3])
        self.assertListEqual(
            [[], [1, 2, 3], [], [1, 2, 3], []], v.spike_times)

    def test_singleton_list(self):
        v = SpikeSourceArrayVertex(
            n_neurons=5, spike_times=[1, 11, 22],
            label="test", max_atoms_per_core=None, model=None, splitter=None)
        v.spike_times = [2, 12, 32]

    def test_double_list(self):
        SpikeSourceArrayVertex(
            n_neurons=3, spike_times=[[1], [11], [22]],
            label="test", max_atoms_per_core=None, model=None, splitter=None)

    def test_big_double_list(self):
        spike_list1 = [1, 2, 6, 8, 9]
        spike_list1.extend([15] * 40)
        spike_list2 = [3, 3, 7, 8, 9]
        spike_list2.extend([15] * 40)
        spike_list3 = [10, 13]
        spike_list3.extend([15] * 30)
        spike_list3.extend([21, 23, 45])
        spike_list = [spike_list1, spike_list2, spike_list3]
        with LogCapture() as lc:
            SpikeSourceArrayVertex(
                n_neurons=3, spike_times=spike_list,
                label="test", max_atoms_per_core=None, model=None,
                splitter=None)
            found = False
            for record in lc.records:
                if "too many spikes" in record.msg.fmt:
                    self.assertIn("110", record.msg.fmt)
                    self.assertIn("15", record.msg.fmt)
                    found = True
            self.assertTrue(found)

    def test_shared_list_big(self):
        with LogCapture() as lc:
            v = SpikeSourceArrayVertex(
                n_neurons=3, spike_times=None,
                label="test", max_atoms_per_core=None, model=None,
                splitter=None)
            v.spike_times = [34] * 35
            found = False
            for record in lc.records:
                if "too many spikes" in record.msg.fmt:
                    self.assertIn("share", record.msg.fmt)
                    found = True
            self.assertTrue(found)

    def test_list_big(self):
        with LogCapture() as lc:
            SpikeSourceArrayVertex(
                n_neurons=1, spike_times=[37] * 109,
                label="test", max_atoms_per_core=None, model=None,
                splitter=None)
            found = False
            for record in lc.records:
                if "too many spikes" in record.msg.fmt:
                    self.assertIn("37", record.msg.fmt)
                    self.assertIn("109", record.msg.fmt)
                    found = True
            self.assertTrue(found)
