"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase

import p7_integration_tests.scripts.synfire_run as synfire_run


class Synfire2RunNewPopIfCurrExpLower(BaseTestCase):
    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        try:
            results = synfire_run.do_run(nNeurons, spike_times=[[0, 1050]],
                                         run_times=[1000, 1000], reset=False,
                                         new_pop=True)
            (v1, gsyn1, spikes1, v2, gsyn2, spikes2) = results
        except NotImplementedError:
            # This is the current behavior but would not be wrong if changed.
            print "Adding populations without reset not yet supported"


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    results = synfire_run.do_run(nNeurons, spike_times=[[0, 1050]],
                                 run_times=[1000, 1000], reset=False,
                                 new_pop=True)
