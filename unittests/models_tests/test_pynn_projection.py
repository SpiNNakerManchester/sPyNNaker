#!/usr/bin/env python
import unittest
import spinn_front_end_common.utilities.exceptions as exc
import spynnaker.pyNN as pyNN
from spynnaker.pyNN.models.pynn_projection import Projection

projections = list()
populations = list()
no_neurons = 10
projection_details = list()
cell_params_lif = {
    'cm': 0.25,
    'i_offset': 0.0,
    'tau_m': 20.0,
    'tau_refrac': 2.0,
    'tau_syn_E': 5.0,
    'tau_syn_I': 5.0,
    'v_reset': -70.0,
    'v_rest': -65.0,
    'v_thresh': -50.0
}
cell_params_lif2exp = cell_params_lif
cell_params_lifexp = {
    'tau_refrac': 0.1,
    'cm': 1.0,
    'tau_syn_E': 5.0,
    'v_rest': -65.0,
    'tau_syn_I': 5.0,
    'tau_m': 20.0,
    'e_rev_E': 0.0,
    'i_offset': 0.0,
    'e_rev_I': -70.0,
    'v_thresh': -50.0,
    'v_reset': -65.0
}
cell_params_izk = {
    'a': 0.02,
    'c': -65.0,
    'b': 0.2,
    'd': 2.0,
    'i_offset': 0,
    'u_init': -14.0,
    'v_init': -70.0,
    'tau_syn_E': 5.0,
    'tau_syn_I': 5.0

}
spike_array = {'spike_times': [0]}
spike_array_poisson = {
    'duration': 10000000000.0,
    'start': 0.0,
    'rate': 1.0
}
cell_params_cochlea = {}
cell_params_retina = {}
cell_params_motor = {}
cell_params_multicast = {}


class TestProjection(unittest.TestCase):
    def setUp(self):
        pyNN.setup(timestep=1, min_delay=1, max_delay=15.0)

    def tearDown(self):
        pyNN.end()

    """
    Test the Projection class
    """

    def test_setup(self):
        global projections
        weight_to_spike = 2
        delay = 5
        populations.append(
            pyNN.Population(no_neurons, pyNN.IF_curr_exp, cell_params_lif,
                            label="LIF Pop"))
        populations.append(pyNN.Population(no_neurons, pyNN.IF_curr_dual_exp,
                                           cell_params_lif2exp,
                                           label="IF_curr_dual_exp Pop"))
        populations.append(
            pyNN.Population(no_neurons, pyNN.IF_cond_exp, cell_params_lifexp,
                            label="IF_cond_exp Pop"))
        populations.append(
            pyNN.Population(no_neurons, pyNN.IZK_curr_exp, cell_params_izk,
                            label="IZK_curr_exp Pop"))
        populations.append(
            pyNN.Population(no_neurons, pyNN.SpikeSourceArray, spike_array,
                            label="SpikeSourceArray Pop"))
        populations.append(pyNN.Population(no_neurons, pyNN.SpikeSourcePoisson,
                                           spike_array_poisson,
                                           label="SpikeSourcePoisson Pop"))
        for i in range(4):
            projection_details.append(
                {'presyn': populations[0], 'postsyn': populations[i],
                 'connector': pyNN.OneToOneConnector(weight_to_spike, delay)})
            projections.append(pyNN.Projection(
                populations[0], populations[i],
                pyNN.OneToOneConnector(weight_to_spike, delay)))

    def test_source_populations_as_postsynaptic(self):
        global projections
        weight_to_spike = 2
        delay = 5
        with self.assertRaises(exc.ConfigurationException):
            for i in range(4, 6):
                projections.append(pyNN.Projection(
                    populations[0], populations[i],
                    pyNN.OneToOneConnector(weight_to_spike, delay)))

    def test_delays(self):
        global projections
        for p in projections:
            self.assertEqual(p.getDelays(), 5)

    @unittest.skip("broken as unit test")
    def test_weights(self):
        # print projections[1].getWeights()
        for p in projections:
            self.assertEqual(list(p.getWeights()), [2] * no_neurons)

    def test_projection_params(self):
        populations = list()
        projection_details = list()
        populations = list()
        weight_to_spike = 2
        delay = 5
        populations.append(
            pyNN.Population(no_neurons, pyNN.IF_curr_exp, cell_params_lif,
                            label="LIF Pop"))
        populations.append(pyNN.Population(
            no_neurons, pyNN.IF_curr_dual_exp, cell_params_lif2exp,
            label="IF_curr_dual_exp Pop"))
        populations.append(pyNN.Population(
            no_neurons, pyNN.IF_cond_exp, cell_params_lifexp,
            label="IF_cond_exp Pop"))
        populations.append(pyNN.Population(
            no_neurons, pyNN.IZK_curr_exp, cell_params_izk,
            label="IZK_curr_exp Pop"))

        for i in range(4):
            for j in range(4):
                projection_details.append(
                    {'presyn': populations[i], 'postsyn': populations[j],
                     'connector': pyNN.OneToOneConnector(weight_to_spike,
                                                         delay)})
                projections.append(
                    pyNN.Projection(populations[i], populations[j],
                                    pyNN.OneToOneConnector(weight_to_spike,
                                                           delay)))

        for i in range(4):
            for j in range(4):
                self.assertEqual(
                    projections[i + j]._projection_edge._pre_vertex,
                    projection_details[i + j]['presyn']._vertex)
                self.assertEqual(
                    projections[i + j]._projection_edge._post_vertex,
                    projection_details[i + j]['postsyn']._vertex)

    def test_inhibitory_connector(self):
        weight_to_spike = 2
        delay = 5
        p1 = pyNN.Population(no_neurons, pyNN.IF_curr_exp, cell_params_lif,
                             label="LIF Pop")
        p2 = pyNN.Population(no_neurons, pyNN.IF_curr_exp, cell_params_lif,
                             label="LIF Pop")

        s12_2 = pyNN.Projection(p1, p2, pyNN.OneToOneConnector(
            weight_to_spike, delay), target='inhibitory')
        self.assertIsNotNone(s12_2)
        s21 = pyNN.Projection(p2, p1, pyNN.OneToOneConnector(
            weight_to_spike, delay), target='excitatory')
        self.assertIsNotNone(s21)

    def test_one_to_one_connector_from_low_to_high(self):
        weight_to_spike, delay = 2, 5
        first_population = pyNN.Population(no_neurons, pyNN.IF_curr_exp,
                                           cell_params_lif, label="LIF Pop")
        different_population = pyNN.Population(
            20, pyNN.IF_curr_exp, cell_params_lif,
            label="A random sized population")
        j = pyNN.Projection(first_population, different_population,
                            pyNN.OneToOneConnector(weight_to_spike, delay))
        self.assertIsNotNone(j)

    def test_one_to_one_connector_from_high_to_low(self):
        weight_to_spike, delay = 2, 5
        second_population = pyNN.Population(
            no_neurons, pyNN.IF_curr_exp, cell_params_lif, label="LIF Pop")
        different_population = pyNN.Population(
            20, pyNN.IF_curr_exp, cell_params_lif,
            label="A random sized population")
        j = pyNN.Projection(different_population, second_population,
                            pyNN.OneToOneConnector(weight_to_spike, delay))
        self.assertIsNotNone(j)

    def test_multiple_connections_between_same_populations(self):
        p1 = pyNN.Population(no_neurons, pyNN.IF_curr_exp, cell_params_lif,
                             label="LIF Pop")
        p2 = pyNN.Population(no_neurons, pyNN.IF_curr_exp, cell_params_lif,
                             label="LIF Pop")
        pyNN.Projection(p1, p2, pyNN.OneToOneConnector(1, 1))
        self.assertIsInstance(pyNN.Projection(p1, p2,
                                              pyNN.OneToOneConnector(1, 1)),
                              Projection,
                              "Failed to create multiple connections between"
                              " the same pair of populations")

    @unittest.skip("Not implemented")
    def test_all_to_all_connector(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("Not implemented")
    def test_fixed_probability_connector(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("Not implemented")
    def test_fixed_number_pre_connector(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("Not implemented")
    def test_from_list_connector(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("Not implemented")
    def test_from_file_connector(self):
        self.assertEqual(True, False, "Test not implemented yet")


if __name__ == "__main__":
    unittest.main()
