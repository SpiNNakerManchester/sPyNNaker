"""
Synfirechain-like example
"""
import unittest

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import synfire_run_twice as synfire_run_twice

class Synfire2RunNewPopIfCurrExpLower(unittest.TestCase):
    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        with self.assertRaises(NotImplementedError):
            results = synfire_run_twice.do_run(nNeurons, new_pop=True)


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    results = synfire_run_twice.do_run(nNeurons, new_pop=True)
