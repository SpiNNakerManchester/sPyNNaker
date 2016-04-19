
"""
Synfirechain-like example
"""
import spynnaker.pyNN as p

p.setup(timestep=0.1, min_delay=1.0, max_delay=1.0)
nNeurons = 400  # number of neurons in each population


cell_params_lif = {'cm': 0.25,
                   'i_offset': 0.0,
                   'tau_m': 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E': 5.0,
                   'tau_syn_I': 5.0,
                   'v_reset': -70.0,
                   'v_rest': -65.0,
                   'v_thresh': -50.0
                   }

populations = list()
projections = list()

weight_to_spike = 2.0

populations.append(p.Population(1, p.IF_curr_exp, cell_params_lif,
                   label='pop_1'))
populations.append(p.Population(nNeurons, p.SpikeSourcePoisson, {'rate': 10000, 'seed': 123456},
                   label='inputSpikes_1'))

projections.append(p.Projection(populations[1], populations[0],
                   p.AllToAllConnector()))

p.run(500)
p.end()
