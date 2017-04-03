import unittest
import p7_integration_tests.scripts.pynnBrunnelBrianNestSpinnaker as script

Neurons = 3000  # number of neurons in each population
sim_time = 1000
simulator_Name = 'spiNNaker'


class PynnBrunnelBrianNestSpinnaker(unittest.TestCase):

    def test_run(self):
        (esp, s, N_E) = script.do_run(Neurons, sim_time, False)


if __name__ == '__main__':
    (esp, s, N_E) = script.do_run(Neurons, sim_time, False)
