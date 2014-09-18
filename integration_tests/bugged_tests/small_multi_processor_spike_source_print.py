"""
Synfirechain-like example
"""
#!/usr/bin/python
import spynnaker.pyNN as p
import numpy, pylab
cell_params_lif = {'cm'        : 0.25, # nF
                     'i_offset'  : 0.0,
                     'tau_m'     : 10.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 2.5,
                     'tau_syn_I' : 2.5,
                     'v_reset'   : -70.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -55.4
                     }

spike_list = {'spike_times': [float(x) for x in range(599)]}
#p.setup(timestep=1.0, min_delay = 1.0, max_delay = 32.0)
p.setup(timestep=1.0, min_delay = 1.0, max_delay = 32.0)

nNeurons = 256 # number of neurons in each population
populations = list()
projections = list()

populations.append(p.Population(nNeurons, p.SpikeSourceArray, spike_list, label='input'))
populations.append(p.Population(1, p.IF_curr_exp, cell_params_lif, label='pop_1'))
projections.append(p.Projection(populations[0], populations[1], p.AllToAllConnector()))

populations[0].record()


p.run(1000)
spikes = populations[0].getSpikes(compatible_output=True)
print spikes
p.end()