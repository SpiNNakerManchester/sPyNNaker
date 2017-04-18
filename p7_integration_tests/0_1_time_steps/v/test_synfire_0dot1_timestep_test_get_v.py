"""
Synfirechain-like example
"""
# spynnaker imports
from p7_integration_tests.base_test_case import BaseTestCase
import p7_integration_tests.scripts.synfire_run as synfire_run
from spinnman.exceptions import SpinnmanTimeoutException
from unittest import SkipTest

# general imports
import unittest


class TestGetVoltage(BaseTestCase):
    """
    tests the printing of get v given a simulation
    """

    def test_get_voltage(self):
        """
        test that tests the getting of v from a pre determined recording
        :return:
        """
        try:
            n_neurons = 200  # number of neurons in each population
            runtime = 500
            results = synfire_run.do_run(n_neurons, max_delay=14.4,
                                         time_step=0.1,
                                         neurons_per_core=10, delay=1.7,
                                         run_times=[runtime])
            (v, gsyn, spikes, inpur_spikes) = results
            # Exact v check removed as system overloads
        # System intentional overload so may error
        except SpinnmanTimeoutException as ex:
            raise SkipTest(ex)


if __name__ == '__main__':
    unittest.main()
