import os
import sys
import unittest

import spinn_front_end_common.interface.abstract_spinnaker_base as base
from spinn_front_end_common.interface.abstract_spinnaker_base \
    import AbstractSpinnakerBase
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.utility_objs import ExecutableFinder
from spynnaker.pyNN.utilities.spynnaker_failed_state \
    import SpynnakerFailedState


class Close_Once(object):

    __slots__ = ("closed")

    def __init__(self):
        self.closed = False

    def close(self):
        if self.closed:
            raise Exception("Close called twice")
        else:
            self.closed = True


class TestSpinnakerMainInterface(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Normally this is done by spinnaker.py during import
        globals_variables.set_failed_state(SpynnakerFailedState())

    def test_min_init(self):
        class_file = sys.modules[self.__module__].__file__
        path = os.path.dirname(os.path.abspath(class_file))
        os.chdir(path)
        print path
        AbstractSpinnakerBase(base.CONFIG_FILE, ExecutableFinder())

    def test_stop_init(self):
        class_file = sys.modules[self.__module__].__file__
        path = os.path.dirname(os.path.abspath(class_file))
        os.chdir(path)

        interface = AbstractSpinnakerBase(base.CONFIG_FILE, ExecutableFinder())
        mock_contoller = Close_Once()
        interface._machine_allocation_controller = mock_contoller
        self.assertFalse(mock_contoller.closed)
        interface.stop(turn_off_machine=False, clear_routing_tables=False,
                       clear_tags=False)
        self.assertTrue(mock_contoller.closed)
        interface.stop(turn_off_machine=False, clear_routing_tables=False,
                       clear_tags=False)


if __name__ == "__main__":
    unittest.main()
