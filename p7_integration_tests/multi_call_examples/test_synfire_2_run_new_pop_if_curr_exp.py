"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun

nNeurons = 200  # number of neurons in each population
spike_times = [[0, 1050]]
run_times = [1000, 1000]
reset = False
new_pop = True
synfire_run = TestRun()


class Synfire2RunNewPopIfCurrExpLower(BaseTestCase):
    def test_run(self):
        try:
            synfire_run.do_run(nNeurons, spike_times=spike_times,
                               run_times=run_times, reset=reset,
                               new_pop=new_pop)
        except NotImplementedError:
            # This is the current behavior but would not be wrong if changed.
            print "Adding populations without reset not yet supported"


if __name__ == '__main__':
    synfire_run.do_run(nNeurons, spike_times=spike_times, run_times=run_times,
                       reset=reset, new_pop=new_pop)
