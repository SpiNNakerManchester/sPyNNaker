import numpy, pylab, random, sys
import spynnaker.pyNN as sim
from matplotlib.pyplot import bar
from matplotlib import pyplot

# SpiNNaker setup
sim.setup(timestep=1.0, min_delay=1.0, max_delay=10.0)
sim.set_number_of_neurons_per_core("IF_curr_exp", 100)

# +-------------------------------------------------------------------+
# | General Parameters                                                |
# +-------------------------------------------------------------------+

# Population parameters
pop_size = 101
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
sim_time = 10000

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

def plot_spikes(spikes, title):
    if spikes != None:
        pylab.figure()
        pylab.xlim((0, sim_time))
        pylab.ylim((0, pop_size))
        pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
        pylab.xlabel('Time [ms]')
        pylab.ylabel('Neuron ID')
        pylab.title(title)
    else:
        print "No spikes received"

def plot_firing_rate(spikes, title):
    pylab.figure()
    # plot firing rate in bins of 10 ms (factor to scale to Hz)
    a = pyplot.hist(spikes[:,1], bins=sim_time/10, range=[0,sim_time])*100/pop_size
    bar(a)
    pylab.title(title)
    pylab.xlabel('Time [ms]')
    pylab.ylabel('FiringRate [Hz]')
    pyplot.show()

pre_stim_spikes = pre_stim.getSpikes(compatible_output=True)
pre_spikes = pre_pop.getSpikes(compatible_output=True)
post_spikes = post_pop.getSpikes(compatible_output=True)

plot_spikes(pre_stim_spikes, "Poisson-source")
plot_spikes(pre_spikes, "Pre-synaptic")
plot_spikes(post_spikes, "Post-synaptic")

plot_firing_rate(pre_stim_spikes, "Poisson-source")
plot_firing_rate(pre_spikes, "Pre-synaptic")
plot_firing_rate(post_spikes, "Post-synaptic")

# End simulation on SpiNNaker
sim.end()