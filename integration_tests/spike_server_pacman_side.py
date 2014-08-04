__author__ = 'stokesa6'
"""
retina example that just feeds data from retina to vis
"""

#!/usr/bin/python
import spynnaker.pyNN as p
import numpy, pylab

#set up pacman103
p.setup(timestep=1.0, min_delay = 1.0, max_delay = 32.0)
cell_params_lif = {'cm'        : 0.25, # nF
                     'i_offset'  : 0.0,
                     'tau_m'     : 10,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 0.5,
                     'tau_syn_I' : 0.5,
                     'v_reset'   : -65.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -64.4
                     }


populations = list()
projections = list()

populations.append(p.Population(1,p.ExternalSpikeSource, {}))
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_1'))

projections.append(p.Projection(populations[0], populations[1], p.AllToAllConnector()))

populations[0].record()
#populations[1].record()
p.run(100000)