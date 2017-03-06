#!/usr/bin/env python
import unittest
import spynnaker.pyNN as pyNN
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from pacman.model.constraints.placer_constraints.\
    placer_chip_and_core_constraint import PlacerChipAndCoreConstraint

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


class TestPyNNPopulation(unittest.TestCase):
    def setUp(self):
        pyNN.setup(timestep=1, min_delay=1, max_delay=10.0)

    def tearDown(self):
        pyNN.end()

    def test_create_if_curr_exp_population(self):
        pyNN.Population(1, pyNN.IF_curr_exp, cell_params_lif,
                        label="One population")

    def test_create_if_cond_exp_population(self):
        pyNN.Population(1, pyNN.IF_cond_exp, {}, label="One population")

    def test_create_izk_curr_exp_population(self):
        pyNN.Population(1, pyNN.IZK_curr_exp,
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
            pyNN.Population(0, pyNN.IZK_curr_exp,
                            cell_params_izk, label="One population")

    def test_create_if_curr_dual_exp_population_zero(self):
        with self.assertRaises(ConfigurationException):
            pyNN.Population(0, pyNN.IF_curr_dual_exp, cell_params_lif,
                            label="One population")

    def test_population_size(self):
        pop0 = pyNN.Population(
            1, pyNN.IF_curr_exp, cell_params_lif, label="One population")
        pop1 = pyNN.Population(
            10, pyNN.IF_curr_exp, cell_params_lif, label="Two population")
        self.assertEqual(pop0._size, 1)
        self.assertEqual(pop1._size, 10)

    @unittest.skip("Not implemented")
    def test_get_spikes_from_virtual_spinnaker(self):
        self.assertEqual(True, False, "Test not implemented yet")

    def test_set_constraint_to_population(self):
        pop = pyNN.Population(10, pyNN.IF_curr_exp, cell_params_lif,
                              label="Constrained population")
        placer_constraint = PlacerChipAndCoreConstraint(x=1, y=0)
        pop.set_constraint(placer_constraint)
        constraints = pop._get_vertex.constraints
        self.assertIn(placer_constraint, constraints)

    def test_t_set(self):
        pop = pyNN.Population(10, pyNN.IF_curr_exp, cell_params_lif,
                              label="Constrained population")
        data = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        pop.tset("cm", data)
        cm = pop.get("cm")
        for index in range(0, len(data)):
            self.assertEqual(cm[index], data[index])

    def test_t_set_invalid(self):
        pop = pyNN.Population(10, pyNN.IF_curr_exp, cell_params_lif,
                              label="Constrained population")
        data = [0, 1, 2, 3, 4, 5, 6, 7]
        with self.assertRaises(ConfigurationException):
            pop.tset("cm", data)

    def test_get_default_parameters_of_if_curr_exp(self):
        pop = pyNN.Population(10, pyNN.IF_curr_exp, cell_params_lif,
                              label="Constrained population")
        default_params = pop.default_parameters
        boxed_defaults = \
            {'tau_m': 20.0, 'cm': 1.0, 'v_rest': -65.0, 'v_reset': -65.0,
             'v_thresh': -50.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
             'tau_refrac': 0.1, 'i_offset': 0, 'v_init': -65.0}
        for param in default_params.keys():
            self.assertEqual(default_params[param], boxed_defaults[param])

    def test_get_default_parameters_of_if_curr_exp_no_instaniation(self):
        default_params = pyNN.IF_curr_exp.default_parameters
        boxed_defaults = \
            {'tau_m': 20.0, 'cm': 1.0, 'v_rest': -65.0, 'v_reset': -65.0,
             'v_thresh': -50.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
             'tau_refrac': 0.1, 'i_offset': 0, 'v_init': -65.0}
        for param in default_params.keys():
            self.assertEqual(default_params[param], boxed_defaults[param])

    def test_spikes_per_second_setting_in_a_pop(self):
        pop = pyNN.Population(
            10, pyNN.IF_curr_exp, {'spikes_per_second': 3333},
            label="Constrained population")
        spikes_per_second = pop._get_vertex.spikes_per_second
        self.assertEqual(spikes_per_second, 3333)

    def test_spikes_per_second_not_set_in_a_pop(self):
        pop = pyNN.Population(
            10, pyNN.IF_curr_exp, cell_params_lif,
            label="Constrained population")
        spikes_per_second = pop._get_vertex.spikes_per_second
        self.assertEqual(spikes_per_second, 30)

    def test_ring_buffer_sigma_setting_in_a_pop(self):
        pop = pyNN.Population(
            10, pyNN.IF_curr_exp, {'ring_buffer_sigma': 3333},
            label="Constrained population")
        ring_buffer_sigma = pop._get_vertex.ring_buffer_sigma
        self.assertEqual(ring_buffer_sigma, 3333)

    def test_ring_buffer_sigma_not_set_in_a_pop(self):
        pop = pyNN.Population(
            10, pyNN.IF_curr_exp, cell_params_lif,
            label="Constrained population")
        ring_buffer_sigma = pop._get_vertex.ring_buffer_sigma
        self.assertEqual(ring_buffer_sigma, 5.0)


if __name__ == "__main__":
    unittest.main()
