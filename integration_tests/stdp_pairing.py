import numpy, pylab, random, sys
#import NeuroTools.signals as nt

import spynnaker.pyNN as sim

# SpiNNaker setup
sim.setup(timestep=1.0, min_delay=1.0, max_delay=10.0)

# +-------------------------------------------------------------------+
# | General Parameters                                                |
# +-------------------------------------------------------------------+

# Population parameters
model = sim.IF_curr_exp
cell_params = {'cm'        : 0.25, # nF
                     'i_offset'  : 0.0,
                     'tau_m'     : 10.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 2.5,
                     'tau_syn_I' : 2.5,
                     'v_reset'   : -70.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -55.4
                     }
# Other simulation parameters
e_rate = 200
in_rate = 350


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
pre_pop = sim.Population(pop_size, model, cell_params)
post_pop = sim.Population(pop_size, model, cell_params)


# Stimulating populations
pre_stim = sim.Population(pop_size, sim.SpikeSourceArray, {'spike_times': [[i for i in range(0, sim_time, time_between_pairs)],]})
post_stim = sim.Population(pop_size, sim.SpikeSourceArray, {'spike_times': [[i for i in range(pairing_start_time, pairing_end_time, time_between_pairs)],]})

# +-------------------------------------------------------------------+
# | Creation of connections                                           |
# +-------------------------------------------------------------------+
# Connection type between noise poisson generator and excitatory populations
ee_connector = sim.OneToOneConnector(weights=2)

sim.Projection(pre_stim, pre_pop, ee_connector, target='excitatory')
sim.Projection(post_stim, post_pop, ee_connector, target='excitatory')

# Plastic Connections between pre_pop and post_pop
stdp_model = sim.STDPMechanism(
  timing_dependence = sim.SpikePairRule(tau_plus = 20.0, tau_minus = 50.0),
  weight_dependence = sim.AdditiveWeightDependence(w_min = 0, w_max = 1, A_plus=0.02, A_minus = 0.02)
)

sim.Projection(pre_pop, post_pop, sim.OneToOneConnector(), 
  synapse_dynamics = sim.SynapseDynamics(slow= stdp_model)
)

# Record spikes
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
      pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".") 
      pylab.xlabel('Time/ms')
      pylab.ylabel('spikes')
      pylab.title(title)
     
  else:
      print "No spikes received"

pre_spikes = pre_pop.getSpikes(compatible_output=True)
post_spikes = post_pop.getSpikes(compatible_output=True)

plot_spikes(pre_spikes, "pre-synaptic")
plot_spikes(post_spikes, "post-synaptic")
pylab.show()


# End simulation on SpiNNaker
sim.end()
