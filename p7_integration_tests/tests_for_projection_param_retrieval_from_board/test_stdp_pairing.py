import spynnaker.pyNN as p
from p7_integration_tests.base_test_case import BaseTestCase
import spynnaker.plot_utils as plot_utils


def do_run():
    # SpiNNaker setup
    p.setup(timestep=1.0, min_delay=1.0, max_delay=10.0)

    # +-------------------------------------------------------------------+
    # | General Parameters                                                |
    # +-------------------------------------------------------------------+

    # Population parameters
    model = p.IF_curr_exp
    cell_params = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 10.0,
                   'tau_refrac': 2.0, 'tau_syn_E': 2.5, 'tau_syn_I': 2.5,
                   'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -55.4}

    delta_t = 10
    time_between_pairs = 150
    num_pre_pairs = 10
    num_pairs = 100
    num_post_pairs = 10
    pop_size = 1

    pairing_start_time = (num_pre_pairs * time_between_pairs) + delta_t
    pairing_end_time = pairing_start_time + (num_pairs * time_between_pairs)
    sim_time = pairing_end_time + (num_post_pairs * time_between_pairs)

    # +-------------------------------------------------------------------+
    # | Creation of neuron populations                                    |
    # +-------------------------------------------------------------------+
    # Neuron populations
    pre_pop = p.Population(pop_size, model, cell_params)
    post_pop = p.Population(pop_size, model, cell_params)

    # Stimulating populations
    spike_times = [[i for i in range(0, sim_time, time_between_pairs)], ]
    pre_stim = p.Population(pop_size, p.SpikeSourceArray,
                            {'spike_times': spike_times})
    spike_times = [[i for i in range(pairing_start_time, pairing_end_time,
                                     time_between_pairs)], ]
    post_stim = p.Population(pop_size, p.SpikeSourceArray,
                             {'spike_times': spike_times})

    # +-------------------------------------------------------------------+
    # | Creation of connections                                           |
    # +-------------------------------------------------------------------+
    # Connection type between noise poisson generator and
    # excitatory populations
    ee_connector = p.OneToOneConnector(weights=2)

    p.Projection(pre_stim, pre_pop, ee_connector, target='excitatory')
    p.Projection(post_stim, post_pop, ee_connector, target='excitatory')

    # Plastic Connections between pre_pop and post_pop
    stdp_model = p.STDPMechanism(
      timing_dependence=p.SpikePairRule(tau_plus=20.0, tau_minus=50.0),
      weight_dependence=p.AdditiveWeightDependence(w_min=0, w_max=1,
                                                   A_plus=0.02, A_minus=0.02))

    p.Projection(pre_pop, post_pop, p.OneToOneConnector(),
                 synapse_dynamics=p.SynapseDynamics(slow=stdp_model))

    # Record spikes
    pre_pop.record()
    post_pop.record()

    # Run simulation
    p.run(sim_time)

    # Dump data
    # pre_pop.printSpikes("results/stdp_pre.spikes")
    # post_pop.printSpikes("results/stdp_post.spikes")
    # pre_pop.print_v("results/stdp_pre.v")
    # post_pop.print_v("results/stdp_post.v")

    pre_spikes = pre_pop.getSpikes(compatible_output=True)
    post_spikes = post_pop.getSpikes(compatible_output=True)

    # End simulation on SpiNNaker
    p.end()

    return (pre_spikes, post_spikes)


class stdp_example(BaseTestCase):

    def test_run(self):
        (pre_spikes, post_spikes) = do_run()
        self.assertLess(110, len(pre_spikes))
        self.assertGreater(130, len(post_spikes))
        self.assertLess(90, len(post_spikes))
        self.assertGreater(110, len(post_spikes))


if __name__ == '__main__':
    (pre_spikes, post_spikes) = do_run()
    print len(pre_spikes)
    print len(post_spikes)
    plot_utils.plot_spikes(pre_spikes, title="pre-synaptic")
    plot_utils.plot_spikes(post_spikes, title="post-synaptic")
