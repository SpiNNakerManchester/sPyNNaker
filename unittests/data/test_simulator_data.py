# Copyright (c) 2021 The University of Manchester
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
from spinn_front_end_common.utilities.exceptions import (
    SimulatorDataNotYetAvialable)
from spynnaker.pyNN.data import SpynnakerDataView, SpynnakerDataWriter


class TestSimulatorData(unittest.TestCase):

    def test_setup(self):
        view = SpynnakerDataView()
        writer = SpynnakerDataWriter()
        # What happens before setup depends on the previous test
        # Use manual_check to verify this without dependency
        writer.setup()
        self.assertIn("run_1", view.report_default_directory)
        self.assertIn("provenance_data", view.provenance_file_path)
        with self.assertRaises(SimulatorDataNotYetAvialable):
            view.machine_time_step
        with self.assertRaises(SimulatorDataNotYetAvialable):
            view.min_delay
        self.assertFalse(view.has_min_delay())
        writer.set_machine_time_step(100)
        self.assertTrue(view.has_min_delay())
        self.assertEqual(100, view.machine_time_step)
        self.assertEqual(100, view.min_delay)
        writer.set_min_delay(200)
        self.assertEqual(200, view.min_delay)

    def test_dict(self):
        view = SpynnakerDataView()
        writer = SpynnakerDataWriter()
        writer.setup()

        self.assertFalse(view.has_min_delay())
        self.assertFalse("MinDelay" in view)
        with self.assertRaises(KeyError):
            view["MinDelay"]
        with self.assertRaises(SimulatorDataNotYetAvialable):
            view.min_delay
        writer.set_min_delay(400)
        writer.set_app_id(8)
        self.assertTrue(view.has_min_delay())
        self.assertEqual(400, view.min_delay)
        self.assertEqual(400, view["MinDelay"])
        self.assertTrue("MinDelay" in view)
        self.assertEqual(8, view["APPID"])
