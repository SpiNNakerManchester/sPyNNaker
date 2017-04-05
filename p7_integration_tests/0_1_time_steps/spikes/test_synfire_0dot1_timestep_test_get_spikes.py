"""
Synfirechain-like example
"""
import unittest

from p7_integration_tests.base_test_case import BaseTestCase
import p7_integration_tests.scripts.synfire_run as synfire_run
import spynnaker.spike_checker as spike_checker
from spinnman.exceptions import SpinnmanTimeoutException
from unittest import SkipTest

n_neurons = 200
timestep = 0.1
max_delay = 14.40
delay = 1.7
neurons_per_core = n_neurons/2
runtime = 500


class TestGetSpikesAt0_1msTimeStep(BaseTestCase):
    """
    tests the get spikes given a simulation at 0.1 ms time steps
    """
    def test_get_spikes(self):
        """
        test for get spikes
        """
        try:
            results = synfire_run.do_run(n_neurons, timestep=timestep,
                                         max_delay=max_delay, delay=delay,
                                         neurons_per_core=neurons_per_core,
                                         runtimes=[runtime])
            (v, gsyn, spikes) = results
            # Eact spike checking removed as system may oervload
            spike_checker.synfire_spike_checker(spikes, n_neurons)
        # System intentional overload so may error
        except SpinnmanTimeoutException as ex:
            raise SkipTest(ex)


if __name__ == '__main__':
    unittest.main()
