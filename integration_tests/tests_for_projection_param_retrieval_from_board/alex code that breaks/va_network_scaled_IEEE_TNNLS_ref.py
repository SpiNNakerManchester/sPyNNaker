#!/usr/bin/python
"""
Visual selection model
Francesco Galluppi, Kevin Brohan

--------------------------------------------------------------------------------

Modified 2013 ADR. WTA sharpened (bug-fixed?), added plasticity (optional)
between V2 and V4, added PFC preferred and aversive stimulus capability
with tunable parameters

--------------------------------------------------------------------------------

Scaling module added January 2014 ADR to auto-scale dependent network parameters
with the size of the input field.

--------------------------------------------------------------------------------

Enhanced June 2014 ADR. Modified Gaussian creation to permit specification of
gains and eccentricities in the Gaussian filter (also available for Gabor filtering).
Tuned weights, gain, eccentricity for sample visual input.
Added optional features that:

1) Allow the PFC to provide bipolar (excitatory/inhibitory) reinforcement
2) Implement top-down feedback as per Bernabe Linares-Barranco's suggestions
3) Add additional PFC priming to V1 layer
4) Provide a new output module for better visualisation of LIP output

--------------------------------------------------------------------------------

FEF style PFC added September 2014 ADR. The "active_pfc" option instantiates a
module which makes PFC output dependent upon V2 activity, modelling the FEF
in biology.

--------------------------------------------------------------------------------

This is the scalable PyNN only version of the model and is designed to
work with real input from iCub cameras using Yarp for comms

"""


import sys
import itertools
import visual_network_scaling
import visual_metrics

import numpy
import matplotlib.pyplot as plt
import matplotlib.cm as cmap
from matplotlib.colors import ListedColormap

from gaussiancreatejose import *
from vector_topographic_activity_plot import * #mapped_boxplot
#from spike_file_to_spike_array import * #convert_file_to_spikes

#from pyNN.brian import *               # use if running brian
from pyNN.random import *               # add support for RNG from native PyNN
from spynnaker.pyNN import *      # Imports the pyNN.spiNNaker module
#from pyNN.random import NumpyRNG, RandomDistribution
from pyNN.utility import Timer

from operator import itemgetter

time_step = 1.0

# Simulation Setup
setup(timestep=time_step, min_delay = 1.0, max_delay = 11.0, db_name='vis_attn_iCub.sqlite')

layer_to_observe = 'lip'
lip_map_on = True
plasticity_on = True
feedback_on = True
aversive_inhibitory = True
top_down_priming = False
metrics_on = True
vector_plot = True
active_pfc = True
output_to_file = False

preferred_orientation = 0   # ADR added preferred and aversive orientations. These
aversive_orientation = 2   # will be used to set biassing in LIP
base_num_neurons = 48 #128
weight_prescale_factor = 1  # prescales weights and capacitances to account for system limits

input_file_type = 1 # Input from: 1 - a simple list of ids; 0 - full list of spikes and times
metrics_with_input = 0 # Get metrics from 1 - the input file; 0 - a separate file
input_run_number = 3 # run number for input files arranged by run

if input_file_type:
   InputFilePol1 = 'spikes_in_%dx%d' % (tuple([base_num_neurons]*2))
else:
   InputFilePol1 = 'run%d_%dx%d_pol1.dat' % (tuple([input_run_number]+[base_num_neurons]*2))
   InputFilePol2 = 'run%d_%dx%d_pol2.dat' % (tuple([input_run_number]+[base_num_neurons]*2))
if metrics_with_input:
   MetricFile = InputFilePol1
else:
   MetricFile = 'object_annots_%dx%d' % (tuple([base_num_neurons]*2))
#neuronSim = True
# loopT = True

scale = visual_network_scaling.scale_factor(dimensions=2, dim_sizes=None, base_dim_size=base_num_neurons, subsample_factor_i_1=1.6, subsample_factor_1_2=1.0, subsample_factor_2_4=2.0, subsample_factor_4_L=1.0, subsample_factor_4_P=1.0, base_filter_size=5.0, sweep_filter=False, filter_scale=(1,1,1), xy_kernel_quant_cutoff=(0,0), base_v2_subfield_size=2, sweep_subfield=False, subfield_scale=(1,1,1), active_P=active_pfc)
scale.setindex(f_idx=0, s_idx=0) # base_filter_size=5.0

# Create some arrays for neuron ID to x-y coord mappings
# for doing nice 2D plotting
# Normally I'd do this with PyNN spatial structure functionality
# but not sure if it's available in PyNN.SpiNNaker

input_x_array = numpy.zeros((int(scale.input_size[0]*scale.input_size[1])),int)
input_y_array = numpy.zeros((int(scale.input_size[0]*scale.input_size[1])),int)

startx = 0
starty = 0

for nrn in xrange(scale.input_size[0]*scale.input_size[1]):
   input_x_array[nrn] = startx
   input_y_array[nrn] = starty
   if startx == (scale.input_size[0] - 1):
       startx = 0
       starty = starty + 1
   else:
       startx = startx + 1

lip_x_array = numpy.zeros((int(scale.lip_pop_size[0]*scale.lip_pop_size[1])),int)
lip_y_array = numpy.zeros((int(scale.lip_pop_size[0]*scale.lip_pop_size[1])),int)

startx = 0
starty = 0

for nrn in xrange(scale.lip_pop_size[0]*scale.lip_pop_size[1]):
   lip_x_array[nrn] = startx
   lip_y_array[nrn] = starty
   if startx == (scale.lip_pop_size[0] - 1):
       startx = 0
       starty = starty + 1
   else:
       startx = startx + 1


#PARAMETERS gaussian
scales=2                # scales
orientations=4          # orientations
#sizeg1=5.0             # size of the gaussian filter

#size_k1 = 5            # x-Size kernel (connections)
#size_k2 = 5            # y-Size kernel (connections)
#jump = 1               # overlapping
delays = 1.0            # connection delays
v2_v4_delays = 2*delays if active_pfc else delays

# PARAMETERS NETWORK

feedback_weight_scaling = 0.81 #1.25 #0.9
input_gain = 1.0 #0.8 #0.5 #1.0 #0.4                     # steepness of the Gaussian input filter. This varies parametrically with scales. Generally the more scales, the shallower,
gaussian_eccentricity = 5.5 #4.6 #4.0 #8.0 # 2.25        # ratio of major/minor axis for the input filter. This varies parametrically with orientations. Generally the more orientations, the more eccentric
input_strength = 2.25*weight_prescale_factor #2.25 #1.86 #4 #7 #4.1 #2.25 #24 #15 #9 #24 #20         # spinn is 20   # drive strength of the input->gaussian filters
v1_v2_weights = 8*weight_prescale_factor #8 #15 #10.75 #15 #12 #15         # spinn is 15   # weights between v1 and v2 orientation maps (one2one connectors)
wta_v2 = True      	                   # do the gaussian filter maps in v2 inhibit each other?
wta_between_v2_weight = -1.85*weight_prescale_factor #-1 # spinn is -1   # inhibition weight between several orientations in v2
wta_within_v2_weight = -0.6*weight_prescale_factor #0.2 #-0.155 #-1  # spinn is -1   # inhibition weight within a single orientation in v2
weights_v4_lip = 22*weight_prescale_factor #22 #35 #25 #5         # spinn is 3
wta_lip_weight = -7*weight_prescale_factor #-20 #-10       # spinn is -7   # competition in LIP
pfc_v1_weights = 0.0725*weight_prescale_factor # pfc->v1 competition biasing weights. Used if top-down priming is on.
pfc_v4_weights = 7.25*weight_prescale_factor if active_pfc else 0.0725*weight_prescale_factor #0.0915 #0.6 #.6  # spinn is 0.1  # pfc->v4 competition biasing weights
v2_pfc_weights = 48*weight_prescale_factor # base weight value for v1-pfc connections when using active PFC
wta_bias = 1.3 #1.3 #1.5             # spinn is 1.3  # sets the relative strength of the other- (heterosynaptic) vs self- (homosynaptic) inhibitory connections for WTA
wta_IOR_delay = 1           # scales the delay for IOR (self-inhibition)

# set weight values for the critical V2->V4 connection. History of parameters:
#3 AP 2.25 #4.5 FB #5.5 !FB #3 #6.79 #2.5 #2.9 #2.3 #7 # spinn is 3
if plasticity_on:
   weights_v2_v4 = 5*weight_prescale_factor
elif active_pfc:
   if feedback_on:
      weights_v2_v4 = 3*weight_prescale_factor
   else:
      weights_v2_v4 = 3*weight_prescale_factor
else:
   if feedback_on:
      weights_v2_v4 = 4.5*weight_prescale_factor
   else:
      weights_v2_v4 = 5.5*weight_prescale_factor

# random objects and initialisations
rng = NumpyRNG(seed=28374)
v_init_distr = RandomDistribution('uniform', [-55,-95], rng)
v_rest_distr = RandomDistribution('uniform', [-55,-65], rng)

# Neural Parameters
tau_m    = 24.0    # (ms)
cm       = 1
v_rest   = -65      # (mV)
v_thresh = -45      # (mV)
v_reset  = -65      # (mV)
t_refrac = 3.       # (ms) (clamped at v_reset)
tau_syn_exc = 3
tau_syn_inh = tau_syn_exc*3
i_offset = 0

i_bias_pref = 0.825 if active_pfc else 1.0  #3.0 #4.0          # spinn is 4.0  # strong stimulation; should cause persistent spiking ADR
i_bias_avert = 0.7 if active_pfc else 0.6 # 0.8 #0.0         # spinn is 0.0  # mild stimulation to non-aversive orientations;
                                                                             # biasses away from the  aversive group. ADR
i_bias_neut = 0.5 if active_pfc else 0.5 #0.0               # spinn is 0.0  # very mild stimulation;
                                                                             # should just keep a population in random spiking ADR

if plasticity_on: # set plasticity between v2 and v4, if desired
   # sets symmetric window, biassed slightly towards inhibition,
   # maximum weight is the must-fire weight
   stdp_model = STDPMechanism(
                timing_dependence = SpikePairRule(tau_plus = 30.0, tau_minus = 30.0),
                weight_dependence = AdditiveWeightDependence(w_min = 0, w_max = 20, A_plus=0.005, A_minus = 0.006) # _A_plus=0.5, _A_minus=0.6
                )

runtime = 100
#runtime = 500
#runtime = 120000
#runtime =  1000000
metric_window = 100
metric_start_offset = 0
metric_t_start = 0
metric_t_stop = runtime


timer = Timer()
timer.start()


# cell_params will be passed to the constructor of the Population Object

cell_params = {
    'tau_m'      : tau_m,    'cm'         : cm,
    'v_rest'     : v_rest,   'v_reset'    : v_reset,  'v_thresh'   : v_thresh,
    'tau_syn_E'       : tau_syn_exc,        'tau_syn_I'       : tau_syn_inh, 'tau_refrac'       : t_refrac, 'i_offset' : i_offset
    }




print "%g - Creating input population: %d x %d" % (timer.elapsedTime(), scale.input_size[0], scale.input_size[1])
if input_file_type:
   input_file = open(InputFilePol1, 'r')
   input_spike_list = eval(input_file.readline())
   data_input_1 = convert_spike_list_to_timed_spikes(spike_list=input_spike_list, min_idx=0, max_idx=scale.input_size[0]*scale.input_size[1], tmin=0, tmax=runtime, tstep=int(time_step))
else:
   data_input_1 = convert_file_to_spikes(input_file_name=InputFilePol1, min_idx=0, max_idx=scale.input_size[0]*scale.input_size[1], tmin=0, tmax=runtime)
data_input_1 = subsample_spikes_by_time(data_input_1, 0, 100, 6)
data_input_1 = random_skew_times(data_input_1, 3)
data_input_1 = [data_input_1[neuron] if neuron in data_input_1 else [] for neuron in range(scale.input_size[0]*scale.input_size[1])]
input_pol_1 = Population(scale.input_size[0]*scale.input_size[1],         # size
              SpikeSourceArray,   # Neuron Type
              {'spike_times': data_input_1},   # Neuron Parameters
              label="input_pol_1") # Label
if layer_to_observe == 'input_pol_1' or layer_to_observe == 'all':
   print "%g - observing input (positive polarity)" % timer.elapsedTime()
   #input_pol_1.set_mapping_constraint({'x':0, 'y':0})
   input_pol_1.record() # ('spikes', to_file=False)

if input_file_type:
   data_input_2 = convert_spike_list_to_timed_spikes(spike_list=input_spike_list, min_idx=0, max_idx=scale.input_size[0]*scale.input_size[1], tmin=int(time_step), tmax=runtime, tstep=int(time_step))
else:
   data_input_2 = convert_file_to_spikes(input_file_name=InputFilePol2, min_idx=0, max_idx=scale.input_size[0]*scale.input_size[1], tmin=0, tmax=runtime)
data_input_2 = subsample_spikes_by_time(data_input_2, 0, 100, 6)
data_input_2 = random_skew_times(data_input_2, 3)
data_input_2 = [data_input_2[neuron] if neuron in data_input_2 else [] for neuron in range(scale.input_size[0]*scale.input_size[1])]
input_pol_2 = Population(scale.input_size[0]*scale.input_size[1],         # size
              SpikeSourceArray,   # Neuron Type
              {'spike_times': data_input_2},   # Neuron Parameters
              label="input_pol_2") # Label
if layer_to_observe == 'input_pol_2' or layer_to_observe == 'all':
   print "%g - observing input (negative polarity)" % timer.elapsedTime()
   #input_pol_2.set_mapping_constraint({'x':0, 'y':0})
   input_pol_2.record() # ('spikes', to_file=False)

# population and projection containers
v1_pop = []
v2_pop = []
v4_pop = []
pfc = []
projections = []

print "%g - Creating v1 populations" % timer.elapsedTime()

for i in range(orientations):           # Cycles orientations
    # creates a population for each connection
    v1_pop.append(Population(scale.v1_pop_size[0]*scale.v1_pop_size[1],         # size
                  IF_curr_exp,   # Neuron Type
                  cell_params,   # Neuron Parameters
                  label="v1_%d" % i)) # Label)
    if layer_to_observe == 'v1' or layer_to_observe == 'all':
        print "%g - observing v1" % timer.elapsedTime()
        #if layer_to_observe == 'v1':    v1_pop[i].set_mapping_constraint({'x':0, 'y':0})
        v1_pop[i].record() # ('spikes', to_file=False)

print "%g - Creating v2 populations" % timer.elapsedTime()

for i in range(orientations):           # Cycles orientations
    # creates a population for each connection
    v2_pop.append(Population(scale.v2_pop_size[0]*scale.v2_pop_size[1],         # size
                  IF_curr_exp,   # Neuron Type
                  cell_params,   # Neuron Parameters
                  label="v2_%d" % i)) # Label)
    if layer_to_observe == 'v2' or layer_to_observe == 'all':
        print "%g - observing v2" % timer.elapsedTime()
        #if layer_to_observe == 'v2':    v2_pop[i].set_mapping_constraint({'x':0, 'y':0})
        v2_pop[i].record() # ('spikes', to_file=False)

print "%g - Creating v4 populations" % timer.elapsedTime()

for i in range(orientations):           # Cycles orientations
    # creates a population for each connection
    v4_pop.append(Population(scale.v4_pop_size[0]*scale.v4_pop_size[1],         # size
            IF_curr_exp,   # Neuron Type
        cell_params,   # Neuron Parameters
        label="v4_%d" % i)) # Label)
    if layer_to_observe == 'v4' or layer_to_observe == 'all':
        print "%g - observing v4" % timer.elapsedTime()
        #if layer_to_observe == 'v4':    v4_pop[i].set_mapping_constraint({'x':0, 'y':1})
        v4_pop[i].record() # ('spikes', to_file=False)

print "%g - Creating PFC population" % timer.elapsedTime()

for i in range(orientations):           # Cycles orientations
    pfc.append(Population(scale.pfc_pop_size[0]*scale.pfc_pop_size[1],         # size
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
    if active_pfc == False:
       v_rest_or = []
       for j in range(pfc[i].size):
    v_rest_or.append(v_rest_distr.next())
       pfc[i].set('v_rest', v_rest_or)
       #pfc[i].tset('v_rest', numpy.array(v_rest_or))

    if layer_to_observe == 'pfc' or layer_to_observe == 'all':
        print "%g - observing pfc" % timer.elapsedTime()
        #pfc[i].set_mapping_constraint({'x':0, 'y':1})
        pfc[i].record() # ('spikes', to_file=False)


print "%g - Creating LIP population" % timer.elapsedTime()
lip = Population(scale.lip_pop_size[0]*scale.lip_pop_size[1],         # size
            IF_curr_exp,   # Neuron Type
            cell_params,   # Neuron Parameters
            label="lip")
if layer_to_observe == 'lip' or layer_to_observe == 'all':
    print "%g - observing lip" % timer.elapsedTime()
    lip_placement = PlacerChipAndCoreConstraint(x=0, y=0)
    lip.set_constraint(lip_placement)
    #lip.set_mapping_constraint({'x':0, 'y':0}) # , 'p':15}
    lip.record() # ('spikes', to_file=False)


print "%g - Creating gaussian Filters connections: scale=%d orientation=%d size=%f" % (timer.elapsedTime(), scales, orientations, scale.filter_scale)

projections = []     # Connection Handler
gaussian_filters = TunedGaussianConnectorList(scales, orientations, scale.filter_scale, input_gain, gaussian_eccentricity)

for i in range(orientations):
    # creates connections lists for different orientations, implementing a
    # convolutional network with different gaussian orientation filters (single scale)
    conn_list = Filter2DConnector_jose(scale.input_size[0], scale.input_size[1],
                            scale.v1_pop_size[0], scale.v1_pop_size[1],
                            gaussian_filters[i],
                            scale.x_kernel, scale.y_kernel,
                            scale.jump[0], delays,
                            gain=input_strength)
    #conn_list_pairs = [(conn[0], conn[1]) for conn in conn_list]
    #conn_list_pairs.sort()
    #conn_list_file=open('input_v1_connections.txt', 'w')
    #conn_list_file.write('input->v1 connections: %s\n' % conn_list_pairs)
    #conn_list_file.close
    projections.append(Projection(input_pol_1, v1_pop[i],
    FromListConnector(conn_list), label='input[p0]->v1_pop_%d' % (i)))
    projections.append(Projection(input_pol_2, v1_pop[i],
    FromListConnector(conn_list), label='input[p1]->v1_pop_%d' % (i)))
    """
    SortedConnections = sorted(conn_list, key=lambda x: x[1])
    ConnectionsByDestination = itertools.groupby(SortedConnections, key=lambda x: x[1])
    numDestinations = 0
    numLinks = 0
    ConnectionsFile = open('Conn_Stats_InV1_%d' % i, 'w')
    for key in ConnectionsByDestination:
        sources = [conn[0] for conn in key[1]]
        ConnectionsFile.write('j: %i fanin: %i, sources: %s\n' % (key[0], len(sources), sources))
        numDestinations += 1
        numLinks += len(sources)
    ConnectionsFile.write('Total projection size %i, Mean fan-in per neuron %f\n' % (numLinks, float(numLinks)/float(numDestinations)))
    ConnectionsFile.close()
    """

if active_pfc == True:
   print "%g - Creating v2->pfc connections" % timer.elapsedTime()
   pfc_filters = TunedGaussianConnectorList(1, 1, scale.pfc_filter_scale[0], scale.pfc_filter_gain, scale.pfc_eccentricities[0])
   pfc_filter_conn_list = Filter2DConnector_jose(scale.v2_pop_size[0], scale.v2_pop_size[1],
                            scale.pfc_pop_size[0], scale.pfc_pop_size[1],
                            pfc_filters[0],
                            int(math.floor(scale.pfc_filter_scale[0])), int(math.floor(scale.pfc_filter_scale[1])),
                            scale.pfc_jumps[0], delays,
                            gain=v2_pfc_weights)
   for i in range(orientations):
       projections.append(Projection(v2_pop[i], pfc[i], FromListConnector(pfc_filter_conn_list), label='v2_pop%d->pfc_%d' % (i,i)))

print "%g - Creating v1->v2 connections" % timer.elapsedTime()

for i in range(orientations):
    projections.append(Projection(v1_pop[i], v2_pop[i], OneToOneConnector(weights=v1_v2_weights, delays=delays), label='v1->v2(pop_%d)' % (i)))
    if feedback_on:
       projections.append(Projection(v2_pop[i], v1_pop[i], OneToOneConnector(weights=v1_v2_weights*feedback_weight_scaling, delays=delays), label='v2->v1(pop%d)' % (i)))

if(wta_v2 == True):
    print "%g - Creating Lateral inhibition for the v2 populations" % timer.elapsedTime()
    for i in range(orientations):           # Cycles orientations
    for j in range(orientations):           # Cycles orientations
        if (i!=j):                      # Avoid self connections
        # Creates lateral inhibition between the v2 populations
        print "%g - v2[%d]->v2[%d] lateral inhibition" % (timer.elapsedTime(), i, j)
            wta_between_list =  ProximityConnector(scale.v2_pop_size[0], scale.v2_pop_size[1], scale.v2_subfield,
                                                        wta_between_v2_weight, 1, allow_self_connections=True)
        projections.append(Projection(  v2_pop[i],
                                        v2_pop[j],
                                        FromListConnector(wta_between_list),
                                        target='inhibitory'))

print "%g - Creating within inhibition pools" % timer.elapsedTime()
for i in range(orientations):           # Cycles orientations
    wta_within_list =  ProximityConnector(scale.v2_pop_size[0], scale.v2_pop_size[1], scale.v2_subfield,
                                            wta_within_v2_weight, 1, allow_self_connections=False)
    print "%g - v2[%d] within inhibition" % (timer.elapsedTime(), i)
    projections.append(Projection(  v2_pop[i],
                            v2_pop[i],
                            FromListConnector(wta_within_list),
                            target='inhibitory'))

print "%g - Creating v2->v4 projections" % timer.elapsedTime()

for i in range(orientations):           # Cycles orientations
    v2_v4_conn_list =  subSamplerConnector2D(scale.v2_pop_size[0], scale.v4_pop_size[0], weights_v2_v4, v2_v4_delays)
    print "%g - v2-v4[%d] subsampling projection" % (timer.elapsedTime(), i)
    projections.append(Projection(  v2_pop[i],
                            v4_pop[i],
                            FromListConnector(v2_v4_conn_list),
                            target='excitatory'))
    if plasticity_on: # added ability to set plasticity ADR
       # this turns on plasticity in the last projection to be appended
       # to the list (which was just done above)
       Proj_Plasticity = SynapseDynamics(slow=stdp_model)
       #projections[-1].set('synapse_dynamics', SynapseDynamics(slow=stdp_model))
       projections[-1].synapse_dynamics = Proj_Plasticity
       #projections[-1].plasticity_id = Proj_Plasticity.id
    if feedback_on: # feedback adds top-down biassing of preferred/active stimuli
       v4_v2_conn_list =  overSamplerConnector2D(scale.v4_pop_size[0], scale.v2_pop_size[0], weights_v2_v4*feedback_weight_scaling, v2_v4_delays) # overSamplerConnector remaps the downscaled connections to their original sources
       projections.append(Projection(  v4_pop[i],
                                       v2_pop[i],
                                       FromListConnector(v4_v2_conn_list),
                                       target='excitatory'))
       #v4_v1_conn_list =  overSamplerConnector2D(scale.v4_pop_size[0], scale.v1_pop_size[0], feedback_weight_scaling, 1) # overSamplerConnector remaps the downscaled connections to their original sources
       #projections.append(Projection(  v4_pop[i],
       #                                v1_pop[i],
        #                               FromListConnector(v4_v2_conn_list),
         #                              target='excitatory'))

print "%g - Creating v4->lip projections" % timer.elapsedTime()
for i in range(orientations):           # Cycles orientations
    projections.append(Projection(  v4_pop[i],
                            lip,
                            OneToOneConnector(weights=weights_v4_lip, delays=delays),
                            target='excitatory'))

print "%g - Creating LIP WTA" % timer.elapsedTime()
#projections.append(Projection(  lip,
#		                lip,
#		                OneToOneConnector(weights=wta_lip_weight, delays=delays),
#		                target='inhibitory'))

# ADR added WTA connections to neighbouring neurons. Original version had only the
# self connection, which looks wrong (would be an "inverse WTA")
#projections.append(Projection(  lip,
#		                lip,
#		                AllToAllConnector(weights=wta_lip_weight*wta_bias, delays=delays, allow_self_connections=False),
#		                target='inhibitory'))

# Temporary workaround for PACMAN103 builds a FromListConnector until such time as allow_self_connections
# option is properly supported
lip_WTA_conn_list = [(i, j, wta_lip_weight if i == j else wta_lip_weight*wta_bias, 1) for i in range(scale.lip_pop_size[0]*scale.lip_pop_size[1]) for j in range(scale.lip_pop_size[0]*scale.lip_pop_size[1])]
#conn_list_pairs = [(conn[0], conn[1], conn[2]) for conn in lip_WTA_conn_list]
#conn_list_pairs.sort()
#conn_list_file=open('lip_lip_connections.txt', 'w')
#conn_list_file.write('lip->lip connections: %s\n' % conn_list_pairs)
#conn_list_file.close
projections.append(Projection(  lip,
                        lip,
                        FromListConnector(lip_WTA_conn_list),
                        target='inhibitory'))


print "%g - Creating pfc->v4 projections" % timer.elapsedTime()
for i in range(orientations):           # Cycles orientations
    if i == aversive_orientation:       # aversive orientation connectivity projects to other orientations ADR
       if aversive_inhibitory:
          if active_pfc:
             projections.append(Projection(  pfc[i],
                                             v4_pop[i],
                                             OneToOneConnector(weights=-pfc_v4_weights, delays=delays),
                                             target='inhibitory'))
          else:
             projections.append(Projection(  pfc[i],
                                             v4_pop[i],
                                             AllToAllConnector(weights=-pfc_v4_weights, delays=delays),
                                             target='inhibitory'))
          if top_down_priming:
             projections.append(Projection(  pfc[i],
                                             v1_pop[i],
                                             AllToAllConnector(weights=-pfc_v1_weights, delays=delays),
                                             target='inhibitory'))
       else:
          for j in [orientation for orientation in range(orientations) if orientation != i]:
              if active_pfc:
                 projections.append(Projection(  pfc[i],
                                                 v4_pop[j],
                                                 OneToOneConnector(weights=pfc_v4_weights, delays=delays),
                                                 target='excitatory'))
              else:
                 projections.append(Projection(  pfc[i],
                                                 v4_pop[j],
                                                 AllToAllConnector(weights=pfc_v4_weights, delays=delays),
                                                 target='excitatory'))
              if top_down_priming:
                 projections.append(Projection(  pfc[i],
                                                 v1_pop[j],
                                                 AllToAllConnector(weights=pfc_v1_weights, delays=delays),
                                                 target='excitatory'))
    else:
       if active_pfc:
          projections.append(Projection(  pfc[i],
                                          v4_pop[i],
                                          OneToOneConnector(weights=pfc_v4_weights, delays=delays),
                                          target='excitatory'))
       else:
          projections.append(Projection(  pfc[i],
                                          v4_pop[i],
                                          AllToAllConnector(weights=pfc_v4_weights, delays=delays),
                                          target='excitatory'))
       if top_down_priming:
          projections.append(Projection(  pfc[i],
                                          v1_pop[i],
                                          AllToAllConnector(weights=pfc_v1_weights, delays=delays),
                                          target='excitatory'))


lip.set('tau_syn_E', 20)
#pfc[3].set('i_offset', 1)
#pfc[3].set('tau_refrac', 50)

weights_before = dict([(o, projections[orientations*(2+active_pfc+feedback_on+(wta_v2*orientations)+1)+o].getWeights('array')) for o in range(orientations)])

setup_time = timer.elapsedTime()

# Run the model

run(runtime)    # Simulation time

run_time = timer.elapsedTime()

weights_after = dict([(o, projections[orientations*(2+active_pfc+feedback_on+(wta_v2*orientations)+1)+o].getWeights('array')) for o in range(orientations)])
weights_file = open('IEEETNNLS_wt_record.txt', 'w+')
weights_file.write('weights before learning:\n')
for o in range(orientations):
    weights_file.write('orientation %d:\n' % o)
    weights_file.write('%s\n' % weights_before[o])
weights_file.write('weights after learning:\n')
for o in range(orientations):
    weights_file.write('orientation %d:\n' % o)
    weights_file.write('%s\n' % weights_after[o])

if output_to_file:
   output_file = open("./VA_runs_IEEE.txt", "a+")
   output_file.write("--------------------------------------------------------------------------------\n")
   output_file.write("NETWORK PARAMETERS:\n")
   output_file.write("-------------------------------\n")
   output_file.write("Input file name: %s\n" % InputFilePol1)
   output_file.write("Network base input size: %d\n" % base_num_neurons)
   output_file.write("Feedback on? %s\n" % feedback_on)
   output_file.write("FEF PFC? %s\n" % active_pfc)
   output_file.write("Learning on? %s\n" % plasticity_on)
   output_file.write("Preferred orientation: %d\n" % preferred_orientation)
   output_file.write("Aversive orientation: %d\n" % aversive_orientation)
   output_file.write("WV2->V4_init: %f\n" % weights_v2_v4)
   output_file.write("-------------------------------\n")
   output_file.write("TIMINGS:\n")
   output_file.write("Setup time: %f s\n" % setup_time)
   print type(run_time)
   print type(setup_time)
   print type(runtime)
   output_file.write("Load time: %f s \n" % (run_time-setup_time-(runtime/1000.0)))
   output_file.write("Run time: %f s \n" % (runtime/1000.0))
else:
   print "Setup time", setup_time
   print "Load time", (run_time - setup_time - runtime/1000.0)
   print "Run time", (runtime/1000.0)

# get spikes and plot

# For layers with sub-populations (V1, V2, PFC, V4)

'''
print "V1 size is", scale.v1_pop_size[0], 'x', scale.v1_pop_size[1]

for i in xrange(orientations):
    V1_spikes = v1_pop[i].getSpikes(gather=True, compatible_output=True)
    print "V1, orientation", i, len(V1_spikes)
print
print "V2 size is", scale.v2_pop_size[0], 'x', scale.v2_pop_size[1]
for i in xrange(orientations):
    V2_spikes = v2_pop[i].getSpikes(gather=True, compatible_output=True)
    print "V2, orientation", i, len(V2_spikes), v2_pop[i].meanSpikeCount(gather=True)
print
print "PFC size is", scale.pfc_pop_size[0], 'x', scale.pfc_pop_size[1]
for i in xrange(orientations):
    PFC_spikes = pfc[i].getSpikes(gather=True, compatible_output=True)
    print "PFC, orientation", i, len(PFC_spikes)
print
print "V4 size is", scale.v4_pop_size[0], 'x', scale.v4_pop_size[1]
for i in xrange(orientations):
    V4_spikes = v4_pop[i].getSpikes(gather=True, compatible_output=True)
    print "V4, orientation", i, len(V4_spikes), v4_pop[i].meanSpikeCount(gather=True)
'''
if layer_to_observe == 'input_pol_1':
   data = numpy.asarray(input_pol_1.getSpikes())
  # data[:,0] = data[(all_rows, column_0)]
   plt.scatter(data[:,0], data[:,1], color='green', s=4) # s=1
elif layer_to_observe == 'input_pol_2':
   data = numpy.asarray(input_pol_2.getSpikes())
   plt.scatter(data[:,0], data[:,1], color='green', s=4) # s=1
if layer_to_observe == 'v1':
   id_accumulator=0
   data_vector = []
   for i in range(len(v1_pop)):
       data = numpy.asarray(v1_pop[i].getSpikes())
       if vector_plot:
          data_vector.append(data)
       else:
          if len(data) > 0:
             plt.scatter(data[:,0], data[:,1] + id_accumulator, color='green', s=4) # s=1
          id_accumulator = id_accumulator + v1_pop[i].size
   if vector_plot:
      mapped_arrowplot(data_vector, x_dim=scale.v1_pop_size[0], y_dim=scale.v1_pop_size[1], t_max=runtime)
elif layer_to_observe == 'v2':
   id_accumulator=0
   data_vector = []
   for i in range(len(v2_pop)):
       data = numpy.asarray(v2_pop[i].getSpikes())
       if vector_plot:
          data_vector.append(data)
       else:
          if len(data) > 0:
             plt.scatter(data[:,0], data[:,1] + id_accumulator, color='green', s=4) # s=1
          id_accumulator = id_accumulator + v2_pop[i].size
   if vector_plot:
      mapped_arrowplot(data_vector, x_dim=scale.v2_pop_size[0], y_dim=scale.v2_pop_size[1], t_max=runtime)
elif layer_to_observe == 'v4':
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

if layer_to_observe == 'lip' or layer_to_observe == 'all':
   # make a 2D array for plotting (lip)

    print "LIP size is", scale.lip_pop_size[0], 'x', scale.lip_pop_size[1]

    lip_array = numpy.zeros((int(scale.lip_pop_size[0]),int(scale.lip_pop_size[1])),float)

    # Analysis and plotting of LIP spikes

    lip_spikes = lip.getSpikes()

    lip_counts = numpy.zeros((int(scale.lip_pop_size[0])*int(scale.lip_pop_size[1])),int)

    lip_id = []
    lip_times = []
    xvals_lip = []
    yvals_lip = []

    # Do a plot of all spikes
    for sp in lip_spikes:
        lip_id.append(sp[1])
        lip_counts[sp[1]] +=1
        lip_times.append(sp[0])
        xpos = lip_x_array[sp[1]]
        ypos = lip_y_array[sp[1]]
        xvals_lip.append(xpos)
        yvals_lip.append(ypos)

    print lip_counts

    lip_total = sum(lip_counts)

    print "Total activity", lip_total

    # Get the coordinates of the most active area
    # and do a coarse mapping up to input resolution
    activeLip = numpy.argmax(lip_counts)
    lip_mag = round(float(scale.input_size[0])/float(scale.lip_pop_size[0]))
    print activeLip, lip_counts[activeLip], lip_x_array[activeLip],lip_y_array[activeLip],lip_x_array[activeLip]*lip_mag, lip_y_array[activeLip]*lip_mag

    x_attend = double(lip_x_array[activeLip]*lip_mag)
    y_attend = double(lip_y_array[activeLip]*lip_mag)
    print "Salient position in Input Space", x_attend, y_attend

    max_activation = float(lip_counts[activeLip])/float(lip_total)

    print "Max Activation", max_activation

    if lip_map_on:
       data = numpy.asarray(lip_spikes)
       mapped_boxplot(data=data, x_dim=scale.lip_pop_size[0], y_dim=scale.lip_pop_size[1], t_max=runtime, tau=16)

    else:
       # Plotting of LIP saliency map

       # Calculate LIP map

       for nrn in xrange(scale.lip_pop_size[0]*scale.lip_pop_size[1]):
           xpos = lip_x_array[nrn]
           ypos = lip_y_array[nrn]
           lip_array[xpos,ypos] = float(lip_counts[nrn])/float(lip_total)
           #print nrn, xpos,ypos, float(lip_counts[nrn])/float(lip_total)

       print lip_array

       # make a custom colormap for plotting

       colormap = numpy.array([(0.0,0.0,0.0),
                        (0.1,0.1,0.1),
                (0.2,0.2,0.2),
                (0.3,0.3,0.3),
                (0.4,0.4,0.4),
                (0.5,0.5,0.5),
                (0.6,0.6,0.6),
                (0.7,0.7,0.7),
                (0.8,0.8,0.8),
                (0.9,0.9,0.9),
                (1.0,1.0,1.0)])

       ColMap = ListedColormap(colormap, name='attncolmap')

       register_cmap(cmap=ColMap)

       x = numpy.arange(0,scale.lip_pop_size[0]+1)
       y = numpy.arange(0,scale.lip_pop_size[1]+1)
       X,Y = numpy.meshgrid(x,y)

       plt.figure()
       plt.pcolor(X, Y, lip_array, shading='faceted', cmap=ColMap, vmin=0.0, vmax=max_activation)
       plt.colorbar()
       plt.title("LIP map")

       plt.figure()
       plt.plot(lip_times,lip_id,'.b')
       plt.xlim(0,runtime)
       plt.ylim(0,scale.lip_pop_size[0]*scale.lip_pop_size[1])
       plt.title("LIP spikes")

    if metrics_on:
       met_data = numpy.asarray(lip_spikes)
       actual_objs = visual_metrics.get_annotations(input_file_name=MetricFile)
       rescaled_objs = visual_metrics.scale_annotations(annotations=actual_objs, scale_x=1/(1.6*2.0), scale_y=1/(1.6*2.0))
       biassed_objs = visual_metrics.bias_annotations(annotations=rescaled_objs, preferred=preferred_orientation, aversive=aversive_orientation)
       performance = visual_metrics.attn_performance_monitor(data=met_data, objects=biassed_objs, y_dim=scale.pfc_pop_size[1], t_window=metric_window, t_w_offset=metric_start_offset, t_start=metric_t_start, t_stop=metric_t_stop)
       if output_to_file:
          output_file.write("Metric time window: %d ms\n" % metric_window)
          output_file.write("Metric window offset %d ms\n" % metric_start_offset)
          output_file.write("Start recording metrics at: %d ms\n" % metric_t_start)
          output_file.write("Stop recording metrics at: %d ms\n" % metric_t_stop)
          output_file.write("--------------------------------------\n")
          output_file.write("PERFORMANCE: \n")
          output_file.write("Time reference    Metric\n")
          output_file.write("__________________________\n")
          t_ref = metric_t_start+metric_start_offset
          for t_m in performance:
              output_file.write("%d ms             %f\n" % (t_ref, t_m))
              t_ref += metric_window
          output_file.write("--------------------------------------------------------------------------------\n\n")
          output_file.close()
       else:
          print "Computed network performance(s) for this trial: %s\n" % performance
    else:
       output_file.write("--------------------------------------------------------------------------------\n\n")
       output_file.close()
if layer_to_observe == 'input_pol_1' or layer_to_observe == 'all':
   # make a 2D array for plotting (input)

   plotting_array = numpy.zeros((int(scale.input_size[0]),int(scale.input_size[1])),int)

   pop_1_spikes = input_pol_1.getSpikes()

   pop_1_id = []
   pop_1_times = []
   xvals_1 = []
   yvals_1 = []

   # indicate areas of input activation
   for sp in pop_1_spikes:
       pop_1_id.append(sp[1])
       pop_1_times.append(sp[0])
       xpos = input_x_array[sp[1]]
       ypos = input_y_array[sp[1]]
       xvals_1.append(xpos)
       yvals_1.append(ypos)
       plotting_array[xpos,ypos] = 3

   # indicate salient position in input space
   # calculated from LIP activity

   # plotting_array[int(x_attend),int(y_attend)] = 2

   x = numpy.arange(0,scale.input_size[0]+1)
   y = numpy.arange(0,scale.input_size[1]+1)
   X,Y = numpy.meshgrid(x,y)

   plt.figure()
   plt.pcolor(X, Y, plotting_array, shading='faceted', cmap=cmap.spectral)
   plt.xlim(0,scale.input_size[0])
   plt.ylim(0,scale.input_size[1])
   plt.title("Input pop 1")

plt.show()

#end()

