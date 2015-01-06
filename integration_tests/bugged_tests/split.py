import spynnaker.pyNN as p
import numpy as np

neuron_model = p.IF_curr_exp
p.setup(timestep=1.0,min_delay=1.0,max_delay=10.0)

breakMe = True
if breakMe:
  p.set_number_of_neurons_per_core("IF_curr_exp", 1)
else:
  p.set_number_of_neurons_per_core("IF_curr_exp", 2)

# Network params
simtime = 500.
n_hyper = 1 #10
n_attr = 6 #10
n_exc_hyper = 12 # 800

# Neural/synapse params
cell_params = {  'tau_m'      : 20,
                 'v_rest'     : -70,
                 'v_reset'    : -70,
                 'v_thresh'   : -50,
                 'tau_syn_E'  : 2,
                 'tau_syn_I'  : 2,
                 'tau_refrac' : 2,
                 'cm'         : .25,
                 'i_offset'   : 0.
                  }

exc_populations = list()

# Create cells of network
for i_mini in range(n_attr):
    exc_populations.append(p.Population(n_exc_hyper/n_attr, neuron_model, cell_params, label="pop %u" % i_mini))
    exc_populations[-1].record()

# Noise
noise_rate = 400. #100 #1000
for exc_pop in enumerate(exc_populations):
    noise_gen = p.Population(n_exc_hyper/n_attr, p.SpikeSourcePoisson, {'rate' : noise_rate, 'duration': simtime, 'start': 0}, label="noise %u" % exc_pop[0])
    p.Projection(noise_gen, exc_pop[1], p.OneToOneConnector(weights = 0.1, delays=1), target='excitatory')

p.run(simtime)

import pylab

pylab.figure()
for cell in enumerate(exc_populations):
  spikes = cell[1].getSpikes(compatible_output=True)

  if spikes != None:
      pylab.plot([i[1] for i in spikes], [i[0] + (n_exc_hyper/n_attr * cell[0]) for i in spikes], ".")
  else:
      print "No spikes received"

pylab.xlabel('Time/ms')
pylab.ylabel('spikes')
pylab.title('spikes')
pylab.xlim([0, simtime])
pylab.ylim([0, n_exc_hyper])
pylab.show()

p.end()