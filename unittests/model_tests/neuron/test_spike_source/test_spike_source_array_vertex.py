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
                max_atoms_per_core=None, model=None, splitter=None,
                n_colour_bits=None)
        found = False
        for record in lc.records:
            if "no spike" in record.msg.fmt:
                found = True
        self.assertTrue(found)
        v.set_parameter_values("spike_times", [])
        v.set_parameter_values("spike_times", [1, 2, 3], [1, 3])
        self.assertSequenceEqual(
            [[], [1, 2, 3], [], [1, 2, 3], []],
            v.get_parameter_values("spike_times"))

    def test_singleton_list(self):
        v = SpikeSourceArrayVertex(
            n_neurons=5, spike_times=[1, 11, 22],
            label="test", max_atoms_per_core=None, model=None, splitter=None,
            n_colour_bits=None)
        v.set_parameter_values("spike_times", [2, 12, 32])

    def test_double_list(self):
        SpikeSourceArrayVertex(
            n_neurons=3, spike_times=[[1], [11], [22]],
            label="test", max_atoms_per_core=None, model=None, splitter=None,
            n_colour_bits=None)

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
                splitter=None, n_colour_bits=None)
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
                splitter=None, n_colour_bits=None)
            v.set_parameter_values("spike_times", [34] * 35)
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
                splitter=None, n_colour_bits=None)
            found = False
            for record in lc.records:
                if "too many spikes" in record.msg.fmt:
                    self.assertIn("37", record.msg.fmt)
                    self.assertIn("109", record.msg.fmt)
                    found = True
            self.assertTrue(found)
