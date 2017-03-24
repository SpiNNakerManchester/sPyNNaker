#!/usr/bin/python
"""
RandomInit test network

19 October 2014 ADR

This network is intended to be a simple test network for randomisation
functions (especially randomInit) in sPyNNaker. Based on a radically 
cut-down version of the visual attention network used for Babel.

"""


import sys
import itertools

import numpy
import matplotlib.pyplot as plt
import matplotlib.cm as cmap
from matplotlib.colors import ListedColormap

if __name__ == '__main__':
    from vector_topographic_activity_plot import * #mapped_boxplot

    #from pyNN.brian import *               # use if running brian
    from pyNN.random import *               # add support for RNG from native PyNN
    from spynnaker.pyNN import *      # Imports the pyNN.spiNNaker module
    #from pyNN.random import NumpyRNG, RandomDistribution
    from pyNN.utility import Timer

    from operator import itemgetter

    time_step = 1.0

    # Simulation Setup
    setup(timestep=time_step, min_delay = 1.0, max_delay = 11.0, db_name='test_RandomInit.sqlite')

    #PARAMETERS SIMULATION

    layer_to_observe = 'v4'
    aversive_inhibitory = True
    vector_plot = True
    output_to_file = True

    preferred_orientation = 0   # ADR added preferred and aversive orientations. These
    aversive_orientation = 2   # will be used to set biassing

    # PARAMETERS NETWORK

    base_v4_num_neurons = 32 #128
    base_pfc_num_neurons = 16
    weight_prescale_factor = 1  # prescales weights and capacitances to account for system limits

    orientations=4          # orientations
    delays = 1.0            # connection delays
    pfc_v4_weights = 0.0725*weight_prescale_factor #0.0915 #0.6 #.6  # spinn is 0.1  # pfc->v4 competition biasing weights

    # random objects and initialisations
    rng = NumpyRNG(seed=28374)
    v_init_distr = RandomDistribution('uniform', [-55,-95], rng)
    v_rest_distr = RandomDistribution('uniform', [-55,-65], rng)

    # Neural Parameters
    tau_m    = 24.0    # (ms)
    cm       = 1
    v_rest   = -65.     # (mV)
    v_thresh = -45.     # (mV)
    v_reset  = -90.     # (mV)
    t_refrac = 3.       # (ms) (clamped at v_reset)
    tau_syn_exc = 3
    tau_syn_inh = tau_syn_exc*3

    i_bias_pref = 1.0  #3.0 #4.0
    i_bias_avert = 0.6 # 0.8 #0.0
    i_bias_neut = 0.5 #0.0

    runtime = 100
    #runtime = 500
    #runtime = 120000
    #runtime =  1000000

    timer = Timer()
    timer.start()


    # cell_params will be passed to the constructor of the Population Object

    cell_params = {
        'tau_m'      : tau_m,    'cm'         : cm,
        'v_rest'     : -65,   'v_reset'    : -65,  'v_thresh'   : -45,
        'tau_syn_E'       : tau_syn_exc,        'tau_syn_I'       : tau_syn_inh, 'tau_refrac'       : t_refrac, 'i_offset' : 0
        }


    # population and projection containers
    v4_pop = []
    pfc = []
    projections = []

    print "%g - Creating v4 populations" % timer.elapsedTime()

    for i in range(orientations):           # Cycles orientations
        # creates a population for each connection
        v4_pop.append(Population(base_v4_num_neurons*base_v4_num_neurons,         # size
                  IF_curr_exp,   # Neuron Type
              cell_params,   # Neuron Parameters
              label="v4_%d" % i)) # Label)
        if layer_to_observe == 'v4' or layer_to_observe == 'all':
            print "%g - observing v4" % timer.elapsedTime()
            # if layer_to_observe == 'v4':    v4_pop[i].set_mapping_constraint({'x':0, 'y':1})
            v4_pop[i].record() # ('spikes', to_file=False)

    print "%g - Creating PFC population" % timer.elapsedTime()

    for i in range(orientations):           # Cycles orientations
        pfc.append(Population(base_pfc_num_neurons*base_pfc_num_neurons,         # size
               IF_curr_exp,   # Neuron Type
               cell_params,   # Neuron Parameters
               label="pfc_%d" % i))
        #pfc[i].initialize('v',v_init_distr)
        pfc[i].randomInit(v_init_distr) # this was commented in SA's version
        # set biasses to hardwire preference ADR
        if i == preferred_orientation:
           pfc[i].set('i_offset', i_bias_pref)
        elif i == aversive_orientation:
           pfc[i].set('i_offset', i_bias_avert)
        else:
           pfc[i].set('i_offset', i_bias_neut)
        v_rest_or = []
        for j in range(pfc[i].size):
            v_rest_or.append(v_rest_distr.next())
        pfc[i].set('v_rest', v_rest_or)
        #pfc[i].tset('v_rest', numpy.array(v_rest_or))

        if layer_to_observe == 'pfc' or layer_to_observe == 'all':
            print "%g - observing pfc" % timer.elapsedTime()
            #pfc[i].set_mapping_constraint({'x':0, 'y':1})
            pfc[i].record() # ('spikes', to_file=False)

    projections = []     # Connection Handler

    print "%g - Creating pfc->v4 projections" % timer.elapsedTime()
    for i in range(orientations):           # Cycles orientations
        if i == aversive_orientation:       # aversive orientation connectivity projects to other orientations ADR
           if aversive_inhibitory:
              projections.append(Projection(  pfc[i],
                                              v4_pop[i],
                                              AllToAllConnector(weights=-pfc_v4_weights, delays=delays),
                                              target='inhibitory'))
           else:
              for j in [orientation for orientation in range(orientations) if orientation != i]:
                  projections.append(Projection(  pfc[i],
                                                  v4_pop[j],
                                                  AllToAllConnector(weights=pfc_v4_weights, delays=delays),
                                                  target='excitatory'))
        else:
           projections.append(Projection(  pfc[i],
                                           v4_pop[i],
                                           AllToAllConnector(weights=pfc_v4_weights, delays=delays),
                                           target='excitatory'))
    #pfc[3].set('i_offset', 1)
    #pfc[3].set('tau_refrac', 50)

    setup_time = timer.elapsedTime()

    # Run the model

    run(runtime)    # Simulation time

    run_time = timer.elapsedTime()

    if output_to_file:
       output_file = open("./VA_runs_IEEE.txt", "a+")
       output_file.write("--------------------------------------------------------------------------------\n")
       output_file.write("NETWORK PARAMETERS:\n")
       output_file.write("-------------------------------\n")
       output_file.write("Network base input size: %d\n" % base_num_neurons)
       output_file.write("Preferred orientation: %d\n" % preferred_orientation)
       output_file.write("Aversive orientation: %d\n" % aversive_orientation)
       output_file.write("-------------------------------\n")
       output_file.write("TIMINGS:\n")
       output_file.write("Setup time: %f s\n" % setup_time)
       print type(run_time)
       print type(setup_time)
       print type(runtime)
       output_file.write("Load time: %f s \n" % (run_time-setup_time-(runtime/1000.0)))
       output_file.write("Run time: %f s \n" % (runtime/1000.0))
       output_file.write("--------------------------------------------------------------------------------\n\n")
       output_file.close()
    else:
       print "Setup time", setup_time
       print "Load time", (run_time - setup_time - runtime/1000.0)
       print "Run time", (runtime/1000.0)

    # get spikes and plot

    # For layers with sub-populations (V1, V2, PFC, V4)

    if layer_to_observe == 'v4':
       id_accumulator=0
       data_vector = []
       for i in range(len(v4_pop)):
           data = numpy.asarray(v4_pop[i].getSpikes())
           if vector_plot:
              data_vector.append(data)
           else:
              if len(data) > 0:
                 plt.scatter(data[:,0], data[:,1] + id_accumulator, color='green', s=4) # s=1
              id_accumulator = id_accumulator + v4_pop[i].size
       if vector_plot:
          mapped_arrowplot(data_vector, x_dim=scale.v4_pop_size[0], y_dim=scale.v4_pop_size[1], t_max=runtime)
    elif layer_to_observe == 'pfc':
       id_accumulator=0
       data_vector = []
       for i in range(len(pfc)):
           data = numpy.asarray(pfc[i].getSpikes())
           if vector_plot:
              data_vector.append(data)
           else:
              if len(data) > 0:
                 plt.scatter(data[:,0], data[:,1] + id_accumulator, color='green', s=4) # s=1
              id_accumulator = id_accumulator + pfc[i].size
       if vector_plot:
          mapped_arrowplot(data_vector, x_dim=scale.pfc_pop_size[0], y_dim=scale.pfc_pop_size[1], t_max=runtime)

    plt.show()

    #end()

