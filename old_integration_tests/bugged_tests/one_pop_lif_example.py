#!/usr/bin/python
import spynnaker.pyNN as p
import numpy, pylab


p.setup(timestep=1.0, min_delay = 1.0, max_delay = 8.0)

nNeurons = 255  # number of neurons in each population

cell_params_lif_in = { 'tau_m' : 333.33,
                'cm'        : 208.33,
                'v_init'    : 0.0,
                'v_rest'     : 0.1,   
                'v_reset'    : 0.0,  
                'v_thresh'   : 1.0,
                'tau_syn_E'   : 1,   # was 5
                'tau_syn_I'   : 2,   # 10
                'tau_refrac'   : 2.5,                 
                'i_offset'   : 3.0
                }

pop1 = p.Population(nNeurons, p.IF_curr_exp, cell_params_lif_in, label='pop_0')


p.run(3000)

p.end()

