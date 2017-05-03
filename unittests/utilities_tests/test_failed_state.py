import unittest

from spynnaker.pyNN.utilities.failed_state import FailedState
from spynnaker.pyNN.utilities import globals_variables


class TestFailedState(unittest.TestCase):

    def test_init(self):
        fs = FailedState()
        self.assertIsNotNone(fs)

    def test_globals_variable(self):
        sim = globals_variables.get_simulator()
        self.assertTrue(isinstance(sim, FailedState))
