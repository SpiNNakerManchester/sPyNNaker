import unittest
import spynnaker.pyNN as p
import pytest

cell_params_lif = {'cm': 0.25,
                   'i_offset': 0.0,
                   'tau_m': 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E': 5.0,
                   'tau_syn_I': 5.0,
                   'v_reset': -70.0,
                   'v_rest': -65.0,
                   'v_thresh': -50.0}


class TestPoissonSpikeSource(unittest.TestCase):
    def setUp(self):
        p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)

    def tearDown(self):
        p.end()

    @unittest.skip("Not implemented")
    def test_recording_poisson_spikes(self):
        n_neurons = 256  # number of neurons in each population
        p.set_number_of_neurons_per_core("IF_curr_exp", n_neurons / 2)

        populations = list()
        projections = list()
        populations.append(p.Population(n_neurons, p.IF_curr_exp,
                                        cell_params_lif, label='pop_1'))
        populations.append(p.Population(n_neurons, p.SpikeSourcePoisson,
                                        {}, label='inputSpikes_1'))
        projections.append(p.Projection(populations[1], populations[0],
                                        p.OneToOneConnector()))
        populations[1].record()

        p.run(5000)

        spikes = populations[1].getSpikes()
        # TODO: Correctness check for spikes
        print spikes

    @unittest.skip("Not implemented")
    def test_recording_poisson_large_spikes(self):
        n_neurons = 2560  # number of neurons in each population
        p.set_number_of_neurons_per_core("IF_curr_exp", n_neurons / 2)

        populations = list()
        projections = list()
        populations.append(p.Population(n_neurons, p.IF_curr_exp,
                                        cell_params_lif, label='pop_1'))
        populations.append(p.Population(n_neurons, p.SpikeSourcePoisson,
                                        {}, label='inputSpikes_1'))
        projections.append(p.Projection(populations[1], populations[0],
                                        p.OneToOneConnector()))
        populations[1].record()

        p.run(5000)

        spikes = populations[1].getSpikes()
        # TODO: Correctness check for spikes
        print spikes

    @pytest.mark.timeout(60)
    def test_recording_poisson_spikes_rate_0(self):
        n_neurons = 256  # number of neurons in each population
        p.set_number_of_neurons_per_core("IF_curr_exp", n_neurons / 2)

        populations = list()
        projections = list()
        populations.append(p.Population(n_neurons, p.IF_curr_exp,
                                        cell_params_lif, label='pop_1'))
        populations.append(p.Population(n_neurons, p.SpikeSourcePoisson,
                                        {'rate': 0}, label='inputSpikes_1'))
        projections.append(p.Projection(populations[1], populations[0],
                                        p.OneToOneConnector()))
        populations[1].record()

        p.run(5000)

        spikes = populations[1].getSpikes()
        # TODO: Correctness check for spikes
        print spikes


if __name__ == '__main__':
    unittest.main()
