import unittest
from p7_integration_tests.base_test_case import BaseTestCase
import p7_integration_tests.scripts.pynnBrunnelBrianNestSpinnaker as script

Neurons = 3000  # number of neurons in each population
sim_time = 1000
simulator_Name = 'spiNNaker'


class PynnBrunnelBrianNestSpinnaker(BaseTestCase):

    # Raises SpinnmanException: 30 cores have reached an error state
    # CPUState.RUN_TIME_EXCEPTION:
    # See prior_integration_tests/buffer_manager/
    # poission_without_recording/pynnBrunnelBrianNestSpinnaker.py
    @unittest.skip("Skipped buffer_manager/"
                   "poission_without_recording/"
                   "test_pynnBrunnelBrianNestSpinnaker")
    def test_run(self):
        (esp, s, N_E) = script.do_run(Neurons, sim_time, False)


if __name__ == '__main__':
    (esp, s, N_E) = script.do_run(Neurons, sim_time, False)
