import pylab
from matplotlib.pyplot import bar
from matplotlib import pyplot
import unittest

import spynnaker.pyNN as sim
import spynnaker.plot_utils as plot_utils

def do_run(sim_time, pop_size):
    # SpiNNaker setup
    sim.setup(timestep=1.0, min_delay=1.0, max_delay=10.0)
    sim.set_number_of_neurons_per_core("IF_curr_exp", 100)

    # +-------------------------------------------------------------------+
    # | General Parameters                                                |
    # +-------------------------------------------------------------------+

    # Population parameters
    model = sim.IF_curr_exp
    cell_params = {'cm'        : 0.25, # nF
                         'i_offset'  : 0.0,
                         'tau_m'     : 10.0,
                         'tau_refrac': 1,
                         'tau_syn_E' : 2,
                         'tau_syn_I' : 2,
                         'v_reset'   : -70.0,
                         'v_rest'    : -65.0,
                         'v_thresh'  : -55
                         }

    # Other simulation parameters
    # +-------------------------------------------------------------------+
    # | Creation of neuron populations                                    |
    # +-------------------------------------------------------------------+
    # Neuron populations
    pre_pop = sim.Population(pop_size, model, cell_params, label="pre")
    #pre_pop.set_mapping_constraint({"x": 0, "y": 1})
    post_pop = sim.Population(pop_size, model, cell_params, label="post")
    #post_pop.set_mapping_constraint({"x": 1, "y": 0})
    # Stimulating populations
    pre_stim = sim.Population(pop_size, sim.SpikeSourcePoisson, {'rate': 5})
    #pre_stim.set_mapping_constraint({"x": 1, "y": 1})

    # +-------------------------------------------------------------------+
    # | Creation of connections                                           |
    # +-------------------------------------------------------------------+
    # Connection type between noise poisson generator and presynaptic populations
    #sim.Projection(pre_stim, pre_pop, sim.FixedProbabilityConnector(0.1, weights=.5))
    # Pre to Post (inlcuding defninition of STDP model)
    stdp_model = sim.STDPMechanism(
      timing_dependence = sim.SpikePairRule(tau_plus = 20.0, tau_minus = 20.0),
      weight_dependence = sim.AdditiveWeightDependence(w_min = 0, w_max = 1, A_plus=0.2, A_minus = 0.2)
    )
    variableWeights = sim.Projection(pre_pop, post_pop, sim.FixedProbabilityConnector(0.1, weights=.5), synapse_dynamics = sim.SynapseDynamics(slow= stdp_model))

    # Record spikes
    pre_stim.record()
    pre_pop.record()
    post_pop.record()

    # Run simulation
    sim.run(sim_time)

    # Dump data
    #pre_pop.printSpikes("results/stdp_pre.spikes")
    #post_pop.printSpikes("results/stdp_post.spikes")
    #pre_pop.print_v("results/stdp_pre.v")
    #post_pop.print_v("results/stdp_post.v")


    pre_stim_spikes = pre_stim.getSpikes(compatible_output=True)
    pre_spikes = pre_pop.getSpikes(compatible_output=True)
    post_spikes = post_pop.getSpikes(compatible_output=True)

    # End simulation on SpiNNaker
    sim.end()

    return (pre_stim_spikes, pre_spikes, post_spikes)

# Code failes but left in
def plot_firing_rate(spikes, title, sim_time, pop_size):
    pylab.figure()
    # plot firing rate in bins of 10 ms (factor to scale to Hz)
    a = pyplot.hist(spikes[:,1], bins=sim_time/10, range=[0,sim_time])*100/pop_size
    bar(a)
    pylab.title(title)
    pylab.xlabel('Time [ms]')
    pylab.ylabel('FiringRate [Hz]')
    pyplot.show()


class TestPoisson(unittest.TestCase):

    def test_run(self):
        sim_time = 10000
        pop_size = 101

        (pre_stim_spikes, pre_spikes, post_spikes) = do_run(sim_time, pop_size)
        # print len(pre_stim_spikes)
        # print len(pre_spikes)
        # print len(post_spikes)
        # plot_utils.plot_spikes(pre_stim_spikes, pre_spikes, post_spikes)
        self.assertLess(4500, len(pre_stim_spikes))
        self.assertGreater(5500, len(pre_stim_spikes))

if __name__ == '__main__':
    (spikes1, spikes2) = do_run()
    plot_utils.plot_spikes(spikes1, spikes2)
