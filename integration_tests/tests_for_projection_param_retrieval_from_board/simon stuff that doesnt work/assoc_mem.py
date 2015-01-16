"""
Simple Associative Memory
"""
#!/usr/bin/python
import pacman103.front.pynn as p
import visualiser.visualiser_modes as modes
import numpy, pylab
from pyNN.random import NumpyRNG, RandomDistribution
import pacman103.patternGenerator as pg

p.setup(timestep=1.0, min_delay = 1.0, max_delay = 15.0)
p.set_number_of_neurons_per_core("IF_curr_exp", 100)

nSourceNeurons = 2000 # number of input (excitatory) neurons
nExcitNeurons  = 2000 # number of excitatory neurons in the recurrent memory
nInhibNeurons  = 10  # number of inhibitory neurons in the recurrent memory
nTeachNeurons  = 2000
nNoiseNeurons  = 10
runTime = 2900

input_cell_params = {'cm'        : 0.25, # nF
                     'i_offset'  : 5.0,
                     'tau_m'     : 10.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 0.5,
                     'tau_syn_I' : 0.5,
                     'v_reset'   : -65.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -64.4
                     }

cell_params_lif   = {'cm'        : 0.25, # nF was 0.25
                     'i_offset'  : 0.0,
                     'tau_m'     : 10.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 0.5,
                     'tau_syn_I' : 0.5,
                     'v_reset'   : -70.0,
                     'v_rest'    : -70.0,
                     'v_thresh'  : -50.0
                     }

numNeurons = nSourceNeurons
numFiring = 100
patternCycleTime = 100
numPatterns = 4
numRepeats  = 9
numRecallRepeats  = 4

inPatterns = list()
outPatterns = list()
for i in range(numPatterns):
   patt = pg.pattern(numNeurons, numFiring, patternCycleTime)
   patt.generateRandomPattern()
   inPatterns.append(patt)
   patt = pg.pattern(numNeurons, numFiring, patternCycleTime)
   patt.generateRandomPattern()
   outPatterns.append(patt)

timeCount = 0
patternPresentationOrder = list()
teachingOrder = list()
# Teaching phase:
for patt in range(numPatterns):
    for rpt in range(numRepeats):
        patternPresentationOrder.append(patt)
        teachingOrder.append(patt)
        timeCount +=1
# Gap:
patternPresentationOrder.append(-1)
patternPresentationOrder.append(-1)
timeCount +=2
# Recall phase:
for patt in range(numPatterns):
    for rpt in range(numRecallRepeats):
        patternPresentationOrder.append(patt)
        timeCount +=1

runTime = timeCount * patternCycleTime

print "Pattern present order: ", patternPresentationOrder
print "Teaching present order: ", teachingOrder
#patternPresentationOrder = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, 0, 0, 0, 0, 1, 1, 1, 1]
#teachingOrder = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1]
#teachingOrder = [-1, -1]
myStimulus=pg.spikeStream()
myStimulus.buildStream(numSources=numNeurons, patterns=inPatterns, interPatternGap=10, order=patternPresentationOrder)
teachingInput=pg.spikeStream()
teachingInput.buildStream(numSources=numNeurons, patterns=inPatterns, interPatternGap=10, order=teachingOrder)

populations = list()
projections = list()

stimulus = 0
inhib = 1
excit  = 2
teacher = 3
noise = 3
decoy = 3

rate = 100
stim_dur = 150
noise_weight = 0.04 * 4.0/3.0
weight_to_force_firing = 15.0
baseline_excit_weight = 0.5
baseline_inhib_weight = 1.0
#weight_to_spike = 4.7
#weight_recurrent = 1.0
#weight_to_inhib = 0.5
#inhib_weight    = 0.0
#excit_in_delay  = 3.0
#inhib_in_delay  = 1.0
#inhib_out_delay = 1.0
#p_connect = 1.0
#conn_prob = 0.75
p_exc2exc = 0.10
p_exc2inh = 0.10
p_inh2exc = 0.17
p_to_inhib_connect = 1.0
p_from_inhib_connect = 1.0

spikeArray = {'spike_times': myStimulus.streams}
teachingSpikeArray = {'spike_times': teachingInput.streams}

populations.append(p.Population(nSourceNeurons, p.SpikeSourceArray, spikeArray, label='excit_pop_ss_array'))       # 0
populations.append(p.Population(nInhibNeurons, p.IF_curr_exp, cell_params_lif, label='inhib_pop'))                 # 1
populations.append(p.Population(nExcitNeurons, p.IF_curr_exp, cell_params_lif, label='excit_pop'))                 # 2
populations.append(p.Population(nTeachNeurons, p.SpikeSourceArray, teachingSpikeArray, label='teaching_ss_array')) # 3

#stdp_model = p.STDPMechanism( timing_dependence = p.RecurrentRule(accumulator_depression = -6, accumulator_potentiation = 6, mean_pre_window = 10.0, mean_post_window = 10.0), weight_dependence = p.SimpleMultiplicativeWeightDependence(potentiation_multiplier = 1.3, depression_multiplier = 1.3))
stdp_model = p.STDPMechanism( timing_dependence = p.RecurrentRule(accumulator_depression = -6, accumulator_potentiation = 6, mean_pre_window = 10.0, mean_post_window = 10.0), weight_dependence = p.MultiplicativeWeightDependence(w_min=0.0, w_max=16.0, A_plus=0.4, A_minus=0.4))

rng = NumpyRNG(seed=1)
ext_delay_distr = RandomDistribution('normal', parameters = [1.5, 0.75], rng=rng, boundaries=[0.1, 9.9], constrain='redraw')
inh_delay_distr = RandomDistribution('normal', parameters = [0.75, 0.375], rng=rng, boundaries=[0.1, 9.9], constrain='redraw')
delay_distr_recurrent = RandomDistribution('uniform', [2.0, 8.0], rng=rng)
weight_distr_ffwd = RandomDistribution('uniform', [0.5, 1.25], rng=rng)
weight_distr_recurrent = RandomDistribution('uniform', [0.1, 0.2], rng=rng)

projections.append(p.Projection(populations[stimulus], populations[excit], p.AllToAllConnector(weights=baseline_excit_weight, delays=1.0), target='excitatory', synapse_dynamics=p.SynapseDynamics(slow=stdp_model)))

projections.append(p.Projection(populations[teacher], populations[excit], p.OneToOneConnector(weights=weight_to_force_firing, delays=1.0), target='excitatory'))
#projections.append(p.Projection(populations[stimulus], populations[inhib], p.FixedProbabilityConnector(p_connect=p_exc2inh, weights=baseline_excit_weight, delays=inh_delay_distr), target='excitatory'))

populations[stimulus].record(visualiser_mode=modes.RASTER)

#populations[inhib].record_v()
#populations[inhib].record(visualiser_mode=modes.RASTER)

populations[excit].record_v()
populations[excit].record(visualiser_mode=modes.RASTER)

populations[teacher].record(visualiser_mode=modes.RASTER)

#populations[noise].record_v()
#populations[noise].record(visualiser_mode=modes.RASTER)

p.run(runTime)

#final_weights = projections[0].getWeights()
final_weights = projections[0].getWeights(format="array")
print "Length of weights is ", len(final_weights)
print "Length of one row of weights is ", len(final_weights[1])
count_plus = 0
count_minus = 0
weightUse = {}
for row in final_weights:
    for i in row:
       myString="%f"%i
       if myString in weightUse:
           weightUse[myString] += 1
       else:
           weightUse[myString] = 1
       if i > 0.5:
           count_plus += 1
       if i < 0.5:
           count_minus += 1

print "Higher weights: ", count_plus
print "Lower weights: ", count_minus
print "Weight usage: ", weightUse

#myDelays = projections[0].getDelays()
#total=0.0
#count = len(myDelays)
#for i in range(count):
#    total = total + myDelays[i]
#print "Average: ", total*1.0/count
#print "Delays:\n", myDelays

#myDelays = projections[1].getDelays()
#print "Delays:\n", myDelays
#myDelaysRecurrent = projections[2].getDelays(format='list')
#print "Recurrent delays:\n", myDelaysRecurrent
#myWeights= projections[0].getWeights()
#print "Weights:\n", myWeights
#myWeightsRecurr= projections[2].getWeights()
#print "Recurrent weights:\n", myWeightsRecurr

v = None
gsyn = None
spikes = None

v = populations[excit].get_v(compatible_output=True)
spikesStim = populations[stimulus].getSpikes(compatible_output=True)
spikes = populations[excit].getSpikes(compatible_output=True)
#vInhib = populations[inhib].get_v(compatible_output=True)
#spikesInhib = populations[inhib].getSpikes(compatible_output=True)
spikesTeach = populations[teacher].getSpikes(compatible_output=True)
# spikesNoise = populations[noise].getSpikes(compatible_output=True)

if spikesStim != None:
    pylab.figure()
    pylab.plot([i[1] for i in spikesStim], [i[0] for i in spikesStim], ".") 
    pylab.xlabel('Time/ms')
    pylab.ylabel('spikes')
    pylab.title('Spikes from Source Neurons')
    #pylab.show()
else:
    print "No spikes received"

if spikes != None:
    pylab.figure()
    pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".") 
    pylab.xlabel('Time/ms')
    pylab.ylabel('spikes')
    pylab.title('Spikes of Excitatory Neurons')
    #pylab.show()
else:
    print "No spikes received"

if spikesTeach != None:
    pylab.figure()
    pylab.plot([i[1] for i in spikesTeach], [i[0] for i in spikesTeach], ".") 
    pylab.xlabel('Time/ms')
    pylab.ylabel('spikes')
    pylab.title('Spikes of Teaching Input')
    #pylab.show()
else:
    print "No spikes received"

#if spikesInhib != None:
#    pylab.figure()
#    pylab.plot([i[1] for i in spikesInhib], [i[0] for i in spikesInhib], ".") 
#    pylab.xlabel('Time/ms')
#    pylab.ylabel('spikes')
#    pylab.title('Spikes Inhibitory Neurons')
#    #pylab.show()
#else:
#    print "No spikes received"

#if spikesNoise != None:
#    pylab.figure()
#    pylab.plot([i[1] for i in spikesNoise], [i[0] for i in spikesNoise], ".") 
#    pylab.xlabel('Time/ms')
#    pylab.ylabel('spikes')
#    pylab.title('Spikes of Noise Sources')
#    pylab.show()
#else:
#    print "No spikes received"

# Make some graphs
ticks = len(v) / nExcitNeurons

# Excitatory neuron current:
if v != None:
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('mV')
    pylab.title('Potential of neuron 1')
    for pos in range(0, nExcitNeurons, 40):
        v_for_neuron = v[pos * ticks : (pos + 1) * ticks]
        pylab.plot([i[1] for i in v_for_neuron], 
                [i[2] for i in v_for_neuron])
    #pylab.show()

# Inhibitory neuron current:
#if v != None:
#    pylab.figure()
#    pylab.xlabel('Time/ms')
#    pylab.ylabel('mV')
#    pylab.title('Potential of inhib neuron 1, 41, 81')
#    for pos in range(1, nInhibNeurons, 40):
#        v_for_neuron = vInhib[pos * ticks : (pos + 1) * ticks]
#        pylab.plot([i[1] for i in v_for_neuron], 
#                [i[2] for i in v_for_neuron])

pylab.show()

p.end()

