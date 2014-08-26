#!/usr/bin/env python
import unittest
import spynnaker.pyNN as pyNN
import spynnaker.pyNN.models.neural_models as models
from spynnaker.pyNN.models.neural_models.izk_curr_exp import \
    IzhikevichCurrentExponentialPopulation
from spynnaker.pyNN.exceptions import ConfigurationException
populations = list()
cell_params_lif = {'cm': 0.25,
                   'i_offset': 0.0,
                   'tau_m': 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E': 5.0,
                   'tau_syn_I': 5.0,
                   'v_reset': -70.0,
                   'v_rest': -65.0,
                   'v_thresh': -50.0}
cell_params_izk = {
    'a': 0.02,
    'c': -65.0,
    'b': 0.2,
    'd': 2.0,
    'i_offset': 0,
    'u_init': -14.0,
    'v_init': -70.0,
    'tau_syn_E': 5.0,
    'tau_syn_I': 5.0}
pyNN.setup(timestep=1, min_delay=1, max_delay=10.0)


class TestingPopulation(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_if_curr_exp_population(self):
        pyNN.Population(1, pyNN.IF_curr_exp, cell_params_lif,
                        label="One population")

    def test_create_if_cond_exp_population(self):
        pyNN.Population(1, pyNN.IF_cond_exp, {}, label="One population")

    def test_create_izk_curr_exp_population(self):
        pyNN.Population(1, IzhikevichCurrentExponentialPopulation,
                        cell_params_izk, label="One population")

    def test_create_if_curr_dual_exp_population(self):
        pyNN.Population(1, pyNN.IF_curr_dual_exp, cell_params_lif,
                        label="One population")

    def test_create_if_curr_exp_population_zero(self):
        with self.assertRaises(ConfigurationException):
            pyNN.Population(0, pyNN.IF_curr_exp, cell_params_lif,
                            label="One population")

    def test_create_if_cond_exp_population_zero(self):
        with self.assertRaises(ConfigurationException):
            pyNN.Population(0, pyNN.IF_cond_exp, {}, label="One population")

    def test_create_izk_curr_exp_population_zero(self):
        with self.assertRaises(ConfigurationException):
            pyNN.Population(0, IzhikevichCurrentExponentialPopulation,
                            cell_params_izk, label="One population")

    def test_create_if_curr_dual_exp_population_zero(self):
        with self.assertRaises(ConfigurationException):
            pyNN.Population(0, pyNN.IF_curr_dual_exp, cell_params_lif,
                            label="One population")

    def test_population_size(self):
        populations = list()
        populations.append(pyNN.Population(1, pyNN.IF_curr_exp, cell_params_lif,
                                           label="One population"))
        populations.append(
            pyNN.Population(10, pyNN.IF_curr_exp, cell_params_lif,
                            label="Two population"))
        self.assertEqual(populations[0]._size, 1)
        self.assertEqual(populations[1]._size, 10)

    def test_get_spikes_from_virtual_spinnaker(self):
        self.assertEqual(True, False, "Test not implemented yet")

    def test_set_constraint_to_population(self):
        pop = pyNN.Population(10, pyNN.IF_curr_exp, cell_params_lif,
                              label="Constrained population")
        placer_constraint = pyNN.PlacerChipAndCoreConstraint(x=1, y=0)
        pop.set_constraint(placer_constraint)
        constraints = pop._get_vertex.constraints
        self.assertIn(placer_constraint, constraints)


if __name__ == "__main__":
    unittest.main()