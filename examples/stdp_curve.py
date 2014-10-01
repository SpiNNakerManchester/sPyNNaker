import math, numpy, pylab, random, sys
import spynnaker.pyNN as sim

#-------------------------------------------------------------------
# Common parameters
#-------------------------------------------------------------------
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

time_between_pairs = 1000
num_pairs = 10
pop_size = 1

delta_t = [-100, -60, -40, -30, -20, -10, -1, 1, 10, 20, 30, 40, 60, 100]

#-------------------------------------------------------------------
# Experiment loop
#-------------------------------------------------------------------
resultant_weights = []
for t in delta_t:
    # SpiNNaker setup
    sim.setup(timestep=1.0, min_delay=1.0, max_delay=10.0)

    # If post-spikes are after pre-spikes - non-causal
    if t > 0:
        post_phase = 0
        pre_phase = 1 + t
    else:
        post_phase = -t
        pre_phase = 1

    sim_time = (num_pairs * time_between_pairs) + abs(t)

    # Neuron populations
    pre_pop = sim.Population(pop_size, model, cell_params)
    post_pop = sim.Population(pop_size, model, cell_params)

    # Stimulating populations
    pre_times = [i for i in range(pre_phase, sim_time, time_between_pairs)]
    post_times = [i for i in range(post_phase, sim_time, time_between_pairs)]
    pre_stim = sim.Population(pop_size, sim.SpikeSourceArray, {'spike_times': [pre_times,]})
    post_stim = sim.Population(pop_size, sim.SpikeSourceArray, {'spike_times': [post_times,]})

    # Connections between noise poisson generator and neuron populations
    ee_connector = sim.OneToOneConnector(weights=2)
    sim.Projection(pre_stim, pre_pop, ee_connector, target='excitatory')
    sim.Projection(post_stim, post_pop, ee_connector, target='excitatory')


    # Plastic Connection between pre_pop and post_pop
    stdp_model = sim.STDPMechanism(
        timing_dependence = sim.SpikePairRule(tau_plus = 16.7, tau_minus = 33.7, nearest = False),
        weight_dependence = sim.AdditiveWeightDependence(w_min = 0, w_max = 1, A_plus = 0.005, A_minus = 0.005)
    )
  
    plastic_projection = sim.Projection(pre_pop, post_pop, sim.OneToOneConnector(weights = 0.5), 
        synapse_dynamics = sim.SynapseDynamics(slow = stdp_model)
    )


    # Run simulation
    sim.run(sim_time)

    resultant_weights.append(plastic_projection.getWeights())
    
    # End simulation on SpiNNaker
    sim.end()

#-------------------------------------------------------------------
# Experiment loop
#-------------------------------------------------------------------
print resultant_weights