
"""
Synfirechain-like example
"""
import spynnaker.pyNN as p

p.setup(timestep=0.1, min_delay=1.0, max_delay=1.0)
n_generators = 475  # number of neurons in each population
p.set_number_of_neurons_per_core("IF_curr_exp", 1)

cell_params_lif = {'cm': 0.25,
                   'i_offset': 0.0,
                   'tau_m': 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E': 5.0,
                   'tau_syn_I': 5.0,
                   'v_reset': -70.0,
                   'v_rest': -65.0,
                   'v_thresh': -50.0,
                   'spikes_per_second': 10000
                   }

populations = list()
projections = list()

weight_to_spike = 0.000002

target_connection = list()
for i in range(0, n_generators):
    singleConnection = None
    if i <= n_generators / 2:
        singleConnection = (i, 0, weight_to_spike, 1)
    else:
        singleConnection = (i, 1, weight_to_spike, 1)
    target_connection.append(singleConnection)

populations.append(p.Population(2, p.IF_curr_exp, cell_params_lif,
                   label='pop_1'))
populations.append(p.Population(n_generators, p.SpikeSourcePoisson,
                                {'rate': 10000, 'seed': 12345},
                   label='inputSpikes_1'))

projections.append(p.Projection(populations[1], populations[0],
                   p.FromListConnector(target_connection)))

p.run(500)
p.end()
