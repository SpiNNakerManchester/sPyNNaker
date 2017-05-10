import unittest
import spynnaker.pyNN as sim
from p7_integration_tests.base_test_case import BaseTestCase


class SSANeuronClassNoEdgeTest(BaseTestCase):

    @unittest.skip("p7_integration_tests/"
                   "no_edge_tests/SSA_neuron_class_no_edge_test.py")
    def test_tun(self):
        sim.setup()

        sim.Population(3, sim.SpikeSourceArray,
                       {"spike_times": [1.0, 2.0, 3.0]})
        p2 = sim.Population(3, sim.SpikeSourceArray,
                            {"spike_times": [[10.0], [20.0], [30.0]]})
        p3 = sim.Population(4, sim.IF_cond_exp, {})

        sim.Projection(p2, p3, sim.FromListConnector([
            (0, 0, 0.1, 1.0), (1, 1, 0.1, 1.0), (2, 2, 0.1, 1.0)]))

        sim.run(100.0)

        sim.end()
