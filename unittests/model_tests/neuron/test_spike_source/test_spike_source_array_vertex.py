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

from testfixtures import LogCapture  # type: ignore[import]
import unittest
import pyNN.spiNNaker as sim
from spynnaker.pyNN.models.spike_source import (
    SpikeSourceArray, SpikeSourceArrayVertex)


class TestSpikeSourceArrayVertex(unittest.TestCase):

    def setUp(self) -> None:
        sim.setup()

    def test_no_spikes(self) -> None:
        with LogCapture() as lc:
            v = SpikeSourceArrayVertex(
                n_neurons=5, spike_times=[], label="test",
                max_atoms_per_core=10, model=SpikeSourceArray(),
                splitter=None, n_colour_bits=None)
        found = False
        for record in lc.records:
            if "no spike" in str(record.msg):
                found = True
        self.assertTrue(found)
        v.set_parameter_values("spike_times", [])
        v.set_parameter_values("spike_times", [1, 2, 3], [1, 3])
        self.assertSequenceEqual(
            [[], [1, 2, 3], [], [1, 2, 3], []],
            list(v.get_parameter_values("spike_times")))

    def test_singleton_list(self) -> None:
        v = SpikeSourceArrayVertex(
            n_neurons=5, spike_times=[1, 11, 22],
            label="test", max_atoms_per_core=10, model=SpikeSourceArray(),
            splitter=None, n_colour_bits=None)
        v.set_parameter_values("spike_times", [2, 12, 32])

    def test_double_list(self) -> None:
        SpikeSourceArrayVertex(
            n_neurons=3, spike_times=[[1], [11], [22]],
            label="test", max_atoms_per_core=10, model=SpikeSourceArray(),
            splitter=None, n_colour_bits=None)

    def test_big_double_list(self) -> None:
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
                label="test", max_atoms_per_core=10, model=SpikeSourceArray(),
                splitter=None, n_colour_bits=None)
            found = False
            for record in lc.records:
                msg = str(record.msg)
                if "too many spikes" in msg:
                    self.assertIn("110", msg)
                    self.assertIn("15", msg)
                    found = True
            self.assertTrue(found)

    def test_shared_list_big(self) -> None:
        with LogCapture() as lc:
            v = SpikeSourceArrayVertex(
                n_neurons=3, spike_times=[],
                label="test", max_atoms_per_core=10, model=SpikeSourceArray(),
                splitter=None, n_colour_bits=None,)
            v.set_parameter_values("spike_times", [34] * 35)
            found = False
            for record in lc.records:
                msg = str(record.msg)
                if "too many spikes" in msg:
                    self.assertIn("share", msg)
                    found = True
            self.assertTrue(found)

    def test_list_big(self) -> None:
        with LogCapture() as lc:
            SpikeSourceArrayVertex(
                n_neurons=1, spike_times=[37] * 109,
                label="test", max_atoms_per_core=10, model=SpikeSourceArray(),
                splitter=None, n_colour_bits=None)
            found = False
            for record in lc.records:
                msg = str(record.msg)
                if "too many spikes" in msg:
                    self.assertIn("37", msg)
                    self.assertIn("109", msg)
                    found = True
            self.assertTrue(found)
