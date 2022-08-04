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

import os
import sys
import unittest
from spinn_utilities.exceptions import SimulatorShutdownException
from spinn_front_end_common.interface.abstract_spinnaker_base import (
    AbstractSpinnakerBase)
from spynnaker.pyNN.config_setup import unittest_setup
from spinn_front_end_common.abstract_models.impl import (
    MachineAllocationController)


class Close_Once(MachineAllocationController):
    __slots__ = ["closed"]

    def __init__(self):
        super().__init__("close-once")
        self.closed = False

    def _wait(self):
        return False

    def close(self):
        if self.closed:
            raise Exception("Close called twice")
        self.closed = True
        super().close()

    def extend_allocation(self, new_total_run_time):
        pass

    def where_is_machine(self, chip_x, chip_y):
        return (0, 0, 0)


class TestSpinnakerMainInterface(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_min_init(self):
        class_file = sys.modules[self.__module__].__file__
        path = os.path.dirname(os.path.abspath(class_file))
        os.chdir(path)
        print(path)
        AbstractSpinnakerBase()

    def test_stop_init(self):
        class_file = sys.modules[self.__module__].__file__
        path = os.path.dirname(os.path.abspath(class_file))
        os.chdir(path)

        interface = AbstractSpinnakerBase()
        mock_contoller = Close_Once()
        # pylint: disable=protected-access
        interface._data_writer.set_allocation_controller(mock_contoller)
        self.assertFalse(mock_contoller.closed)
        interface.stop()
        self.assertTrue(mock_contoller.closed)
        with self.assertRaises(SimulatorShutdownException):
            interface.stop()


if __name__ == "__main__":
    unittest.main()
