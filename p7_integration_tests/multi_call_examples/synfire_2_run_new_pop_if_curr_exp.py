"""
Synfirechain-like example
"""
import unittest

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import p7_integration_tests.scripts.synfire_run_twice as synfire_run_twice

class Synfire2RunNewPopIfCurrExpLower(unittest.TestCase):
    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        try:
            results = synfire_run_twice.do_run(nNeurons, new_pop=True)
        except NotImplementedError:
            # This is the current behavior but would not be wrong if changed.
            print "Adding populations without reset not yet supported"


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    results = synfire_run_twice.do_run(nNeurons, new_pop=True)
