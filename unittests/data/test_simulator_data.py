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
from spinn_utilities.exceptions import DataNotYetAvialable
from spinn_front_end_common.data import FecDataView
from spinn_front_end_common.utilities.exceptions import (
    ConfigurationException)
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.data.spynnaker_data_writer import SpynnakerDataWriter


class TestSimulatorData(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_setup(self):
        view = SpynnakerDataView()
        # What happens before setup depends on the previous test
        # Use manual_check to verify this without dependency
        writer = SpynnakerDataWriter.setup()
        self.assertIn("run_1", SpynnakerDataView.get_run_dir_path())
        self.assertIn("provenance_data", view.provenance_dir_path)
        with self.assertRaises(DataNotYetAvialable):
            view.simulation_time_step_us
        with self.assertRaises(DataNotYetAvialable):
            view.min_delay
        self.assertFalse(view.has_min_delay())
        writer.set_up_timings(100, 10)
        self.assertTrue(view.has_min_delay())
        self.assertEqual(100, view.simulation_time_step_us)
        self.assertEqual(0.1, view.min_delay)

    def test_min_delay(self):
        writer = SpynnakerDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            writer.min_delay

        writer.set_up_timings_and_delay(500, 1, 0.5)
        self.assertEqual(0.5, writer.min_delay)

        writer.set_up_timings_and_delay(1000, 1, None)
        self.assertEqual(1, writer.min_delay)

        with self.assertRaises(ConfigurationException):
            writer.set_up_timings_and_delay(1000, 1, 0)

        with self.assertRaises(ConfigurationException):
            writer.set_up_timings_and_delay(1000, 1, 1.5)

        writer.set_up_timings_and_delay(1000, 1, 2)
        with self.assertRaises(ConfigurationException):
            writer.set_up_timings_and_delay(2000, 1, 1)

        with self.assertRaises(TypeError):
            writer.set_up_timings_and_delay(1000, 1, "baocn")

    def test_mock(self):
        view = SpynnakerDataView()
        # check there is a value not what it is
        self.assertIsNotNone(view.app_id)
        self.assertIsNotNone(view.min_delay)

    def test_multiple(self):
        view = SpynnakerDataView()
        writer = SpynnakerDataWriter.setup()
        view1 = SpynnakerDataView()
        view2 = FecDataView()
        writer.set_app_id(7)
        self.assertEqual(7, view.app_id)
        self.assertEqual(7, view2.app_id)
        self.assertEqual(7, view1.app_id)
        self.assertEqual(7, writer.app_id)
