"""
Synfirechain-like example
"""
# general imports
from p7_integration_tests.scripts.synfire_run import TestRun
from p7_integration_tests.base_test_case import BaseTestCase

from spinn_front_end_common.utilities.exceptions import ConfigurationException

n_neurons = 10  # number of neurons in each population
runtime = 50
synfire_run = TestRun()


class TestGsyn(BaseTestCase):
    """
    tests the printing of get gsyn given a simulation
    """

    def test_get_gsyn(self):
        with self.assertRaises(ConfigurationException):
            synfire_run.do_run(n_neurons, max_delay=14.4, time_step=0.1,
                               neurons_per_core=5, delay=1.7,
                               run_times=[runtime])


if __name__ == '__main__':
    synfire_run.do_run(n_neurons, max_delay=14.4, time_step=0.1,
                       neurons_per_core=5, delay=1.7, run_times=[runtime])
