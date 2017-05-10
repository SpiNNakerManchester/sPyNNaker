#!/usr/bin/env python
"""
Simple test for STDP :

   Reproduces a classical plasticity experiment of plasticity induction by
pre/post synaptic pairing specifically :

 * At the begining of the simulation,
   "n_stim_test" external stimulations of the
   "pre_pop" (presynaptic) population do not trigger activity in the "post_pop"
   (postsynaptic) population.

 * Then the presynaptic and postsynaptic populations are stimulated together
   "n_stim_pairing" times by an external source so that the
   "post_pop" population spikes 10ms after the "pre_pop" population.

 * Ater that period, only the "pre_pop" population is externally stimulated
   "n_stim_test" times, but now it should trigger activity in the "post_pop"
   population (due to STDP learning)

Run as :

   $ ./stdp_example

This example requires that the NeuroTools package is installed
(http://neuralensemble.org/trac/NeuroTools)

Authors : Catherine Wacongne < catherine.waco@gmail.com >
          Xavier Lagorce < Xavier.Lagorce@crans.org >

April 2013
"""

import spynnaker.pyNN as p
import unittest
import spynnaker.plot_utils as plot_utils
from p7_integration_tests.base_test_case import BaseTestCase


def do_run():
    # SpiNNaker setup
    p.setup(timestep=1.0, min_delay=1.0, max_delay=10.0)

    # +-------------------------------------------------------------------+
    # | General Parameters                                                |
    # +-------------------------------------------------------------------+

    # Population parameters
    model = p.IF_curr_exp
    # model = sim.IF_cond_exp
    """
    cell_params = {'i_offset' : .1,    'tau_refrac' : 3.0, 'v_rest' : -65.0,
                   'v_thresh' : -51.0,  'tau_syn_E'  : 2.0,
                   'tau_syn_I': 5.0,    'v_reset'    : -70.0}
    """
    cell_params = {'cm': 0.25,  # nF
                   'i_offset': 0.0,
                   'tau_m': 10.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E': 2.5,
                   'tau_syn_I': 2.5,
                   'v_reset': -70.0,
                   'v_rest': -65.0,
                   'v_thresh': -55.4}

    # Other simulation parameters
    e_rate = 200
    in_rate = 350

    n_stim_test = 5
    n_stim_pairing = 10
    dur_stim = 20

    pop_size = 40

    ISI = 150.
    start_test_pre_pairing = 200.
    start_pairing = 1500.
    start_test_post_pairing = 700.

    simtime = start_pairing + start_test_post_pairing + \
        ISI * (n_stim_pairing + n_stim_test) + 550.  # let's make it 5000

    # Initialisations of the different types of populations
    IAddPre = []
    IAddPost = []

    # +-------------------------------------------------------------------+
    # | Creation of neuron populations                                    |
    # +-------------------------------------------------------------------+

    # Neuron populations
    pre_pop = p.Population(pop_size, model, cell_params)
    post_pop = p.Population(pop_size, model, cell_params)

    # Test of the effect of activity of the pre_pop population on the post_pop
    # population prior to the "pairing" protocol : only pre_pop is stimulated
    for i in range(n_stim_test):
        IAddPre.append(p.Population(pop_size, p.SpikeSourcePoisson,
                                    {'rate': in_rate,
                                     'start': start_test_pre_pairing + ISI*(i),
                                     'duration': dur_stim}))

    # Pairing protocol : pre_pop and post_pop are stimulated with a 10 ms
    # difference
    for i in range(n_stim_pairing):
        IAddPre.append(p.Population(pop_size, p.SpikeSourcePoisson,
                                    {'rate': in_rate,
                                     'start': start_pairing + ISI*(i),
                                     'duration': dur_stim}))
        IAddPost.append(p.Population(pop_size, p.SpikeSourcePoisson,
                                     {'rate': in_rate,
                                      'start': start_pairing + ISI*(i) + 10.,
                                      'duration': dur_stim}))

    # Test post pairing : only pre_pop is stimulated
    # (and should trigger activity in Post)
    for i in range(n_stim_test):
        start = start_pairing + ISI * (n_stim_pairing) + \
                start_test_post_pairing + ISI * (i),
        IAddPre.append(p.Population(pop_size, p.SpikeSourcePoisson,
                                    {'rate': in_rate, 'start': start,
                                     'duration': dur_stim}))

    # Noise inputs
    INoisePre = p.Population(pop_size, p.SpikeSourcePoisson,
                             {'rate': e_rate, 'start': 0, 'duration': simtime},
                             label="expoisson")
    params = {'rate': e_rate, 'start': 0, 'duration': simtime}
    INoisePost = p.Population(pop_size, p.SpikeSourcePoisson, params,
                              label="expoisson")

    # +-------------------------------------------------------------------+
    # | Creation of connections                                           |
    # +-------------------------------------------------------------------+

    # Connection parameters
    JEE = 3.

    # Connection type between noise poisson generator and
    # excitatory populations
    ee_connector = p.OneToOneConnector(weights=JEE*0.05)

    # Noise projections
    p.Projection(INoisePre, pre_pop, ee_connector, target='excitatory')
    p.Projection(INoisePost, post_pop, ee_connector, target='excitatory')

    # Additional Inputs projections
    for i in range(len(IAddPre)):
        p.Projection(IAddPre[i], pre_pop, ee_connector, target='excitatory')
    for i in range(len(IAddPost)):
        p.Projection(IAddPost[i], post_pop, ee_connector, target='excitatory')

    # Plastic Connections between pre_pop and post_pop
    timing_dependence = p.SpikePairRule(tau_plus=20., tau_minus=50.0,
                                        nearest=True)
    weight_dependence = p.AdditiveWeightDependence(w_min=0, w_max=0.9,
                                                   A_plus=0.02, A_minus=0.02)
    stdp_model = p.STDPMechanism(timing_dependence=timing_dependence,
                                 weight_dependence=weight_dependence)

    plastic_projection = \
        p.Projection(pre_pop, post_pop,
                     p.FixedProbabilityConnector(p_connect=0.5),
                     synapse_dynamics=p.SynapseDynamics(slow=stdp_model)
                     )

    # +-------------------------------------------------------------------+
    # | Simulation and results                                            |
    # +-------------------------------------------------------------------+

    # Record neurons' potentials
    pre_pop.record_v()
    post_pop.record_v()

    # Record spikes
    pre_pop.record()
    post_pop.record()

    # Run simulation
    p.run(simtime)

    weights = plastic_projection.getWeights()

    pre_spikes = pre_pop.getSpikes(compatible_output=True)
    post_spikes = post_pop.getSpikes(compatible_output=True)

    p.end()

    return (weights, pre_spikes, post_spikes)


class stdp_example(BaseTestCase):

    @unittest.skip("Skipping tests_for_projection_param_retrieval_from_board/"
                   "test_stdp_example.py")
    def test_run(self):
        (weights, pre_spikes, post_spikes) = do_run()
        self.assertLess(140, len(pre_spikes))
        self.assertGreater(170, len(post_spikes))
        self.assertLess(80, len(post_spikes))
        self.assertGreater(100, len(post_spikes))
        self.assertLess(750, len(weights))
        self.assertGreater(850, len(weights))


if __name__ == '__main__':
    (weights, pre_spikes, post_spikes) = do_run()
    print len(pre_spikes)
    print len(post_spikes)
    plot_utils.plot_spikes(pre_spikes, title="pre-synaptic")
    plot_utils.plot_spikes(post_spikes, title="post-synaptic")
    print len(weights)
    print("Weights:", weights)
