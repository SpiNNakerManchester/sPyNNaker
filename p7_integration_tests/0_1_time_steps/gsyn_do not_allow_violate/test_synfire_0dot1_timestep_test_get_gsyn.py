"""
Synfirechain-like example
"""
# general imports
import unittest
import p7_integration_tests.scripts.synfire_run as synfire_run
from p7_integration_tests.base_test_case import BaseTestCase

from spinn_front_end_common.utilities.exceptions import ConfigurationException


class TestGsyn(BaseTestCase):
    """
    tests the printing of get gsyn given a simulation
    """

    def test_get_gsyn(self):
        n_neurons = 10  # number of neurons in each population
        runtime = 50
        with self.assertRaises(ConfigurationException):
            results = synfire_run.do_run(n_neurons, max_delay=14.4,
                                         timestep=0.1, neurons_per_core=5,
                                         delay=1.7, runtimes=[runtime])
            print results


if __name__ == '__main__':
    n_neurons = 10  # number of neurons in each population
    runtime = 50
    results = synfire_run.do_run(n_neurons, max_delay=14.4, timestep=0.1,
                                 neurons_per_core=5, delay=1.7,
                                 runtimes=[runtime])
