"""
Noise from spike sources to layer of excitatory neurons

Layer of Poisson sources feeding a layer of excitatory neurons 
and a separate layer of inhibitory neurons.
The target neurons never fire, so we can measure the average 
potential across all 1000.
Note that the neurons do not project anywhere, so they are just
targets. (In particular, the inhib neurons don't inhibit anything!)

Run string:
python noise_testcase.py <numPoissonSources> <numTargetNeuronsPerPop> <weight>
e.g. python noise_testcase.py 14000 1000 0.01

"""
#!/usr/bin/python
import sys
import spynnaker.pyNN as p

#import pacman103.front.pynn as p
#import visualiser.visualiser_modes as modes
import numpy, pylab
import math
from pyNN.random import NumpyRNG, RandomDistribution
#import pacman103.patternGenerator as pg

if __name__ == '__main__':
    # XXXXXX Parameter for the number of poisson sources per core
    poissonSourcesPerCore = 50

    numBins = 10
    #runTime = 2900
    runTime = 1000
    targetSpikeRate = 9.0 # Hz

    def analyseTimeSeries(pots, numNeurons, interval):
       means = numpy.zeros(numNeurons)
       vars  = numpy.zeros(numNeurons)
       stds  = numpy.zeros(numNeurons)
       for elem in pots:
          (neurID, timeStamp, potential) = elem
          if (timeStamp > 99):
              means[neurID] += potential

       # Calculate means:
       #print "Means:"
       for neuron in range(numNeurons):
           means[neuron] = means[neuron]/(interval-100.0)
       #print "Mean[10]: ", means[10]

       # Calculate variances:
       for elem in pots:
          (neurID, timeStamp, potential) = elem
          if (timeStamp > 99):
              vars[neurID] += (potential - means[neurID])*(potential - means[neurID])

       # Calculate standard deviations:
       #print "Std. devs:"
       for neuron in range(numNeurons):
           vars[neuron] = vars[neuron]/(interval-100.0)
           stds[neuron] = math.sqrt(vars[neuron])
       #print "Std. dev.[10]: ", stds[10]

       # Calculate means of these means/std devs:
       total_mean = 0
       if len(means) > 0:
          for val in means:
             #print "Mean is ", val
             total_mean += val
          mean_of_means = total_mean / len(means)

       total_std = 0
       if len(stds) > 0:
          for val in stds:
             total_std += val
          mean_of_stds = total_std / len(stds)

       return (mean_of_means, mean_of_stds)

    if len(sys.argv) is not 4:
        print "Error: expected 3 parameters after filename, but got ", len(sys.argv)-1
        quit()

    p.setup(timestep=1.0, min_delay = 1.0, max_delay = 15.0)
    p.set_number_of_neurons_per_core("IF_curr_exp", 50)
    p.set_number_of_neurons_per_core("SpikeSourcePoisson", poissonSourcesPerCore)

    # Parameters to set for each run:
    # Level 1:
    nL1ExcitNeurons = int(sys.argv[1]) # was 2400
    nL2ExcitNeurons = int(sys.argv[2]) # was 2400
    L1MeanWeightX2X = float(sys.argv[3])
    L1MeanWeightX2I = float(sys.argv[3])
    # Common:
    StdDev = 1.0
    noiseRate = 9 # Hz
    print "Spike sources: ", nL1ExcitNeurons

    rng = NumpyRNG(seed=1)
    E2EmeanDelay = 7.0
    E2ImeanDelay = 3.0
    I2EmeanDelay = 3.0
    E2E_delay_distr = RandomDistribution('normal', parameters = [E2EmeanDelay, 0.75], rng=rng, boundaries=[1.0, 12.0], constrain='redraw')
    E2I_delay_distr = RandomDistribution('normal', parameters = [E2ImeanDelay, 0.75], rng=rng, boundaries=[1.0, 10.0], constrain='redraw')
    I2E_delay_distr = RandomDistribution('normal', parameters = [I2EmeanDelay, 0.75], rng=rng, boundaries=[1.0, 10.0], constrain='redraw')

    cell_params_lif   = {'cm'        : 0.25, # nF was 0.25
                         'i_offset'  : 0.0,
                         'tau_m'     : 20.0,
                         'tau_refrac': 2.0,
                         'tau_syn_E' : 5.0,
                         'tau_syn_I' : 10.0,
                         'v_reset'   : -70.0,
                         'v_rest'    : -65.0,
                         'v_thresh'  : 500.0
                         }

    # Layer 1 (input spike sources):
    L1E = 0 # Index for level 1 excit neurons
    L1I = 1 # Index for level 1 inhib neurons
    # nL1ExcitNeurons = 2400
    nL1InhibNeurons = 600
    pL1E2E = 0.11
    pL1E2I = 0.20 # was 0.11
    pL1I2E = 0.2
    # Layer 2 ('hidden' or feature layer):
    L2E = 2 # Index for level 2 excit neurons
    #nL2ExcitNeurons = 2400 # now set by cmd line parameter

    # Create random distributions for key parameters:
    # Layer 1:
    #distWeightL1E2I = RandomDistribution('exponential', [L1MeanWeightX2I], rng=rng, boundaries=[0.0, 7.0], constrain='redraw')
    #distWeightL1E2E = RandomDistribution('exponential', [L1MeanWeightX2X], rng=rng, boundaries=[0.0, 7.0], constrain='redraw')
    #distWeightL1I2E = RandomDistribution('exponential', [L1MeanWeightI2X], rng=rng, boundaries=[0.0, 7.0], constrain='redraw')

    populations = list()
    projections = list()

    ## Populations
    # Layer 1 (input layer) populations:
    populations.append(p.Population(nL1ExcitNeurons, p.SpikeSourcePoisson, {'rate' : noiseRate, 'duration' : runTime}, label='L1Excit'))
    populations.append(p.Population(nL1InhibNeurons, p.IF_curr_exp, cell_params_lif, label='L1Inhib'))
    # Layer 2 (hidden layer) populations:
    populations.append(p.Population(nL2ExcitNeurons, p.IF_curr_exp, cell_params_lif, label='L2Excit'))

    ## Projections
    # Starting in layer 1:
    projections.append(p.Projection(populations[L1E], populations[L1I], p.FixedProbabilityConnector(p_connect=pL1E2I, weights=L1MeanWeightX2X, delays=E2ImeanDelay), target='excitatory')) # From excit to its own inhib neurons
    projections.append(p.Projection(populations[L1E], populations[L2E], p.FixedProbabilityConnector(p_connect=pL1E2E, weights=L1MeanWeightX2X, delays=E2ImeanDelay), target='excitatory')) # Feedforward excitation
    #projections.append(p.Projection(populations[L1I], populations[L2E], p.FixedProbabilityConnector(p_connect=pL1I2E, weights=distWeightL1I2E, delays=I2EmeanDelay), target='inhibitory')) # Feedforward inhibition

    #populations[L1E].record()
    #populations[L1I].record()
    #populations[L2E].record()
    populations[L1I].record_v()
    populations[L2E].record_v()

    p.run(runTime)

    v1I = populations[L1I].get_v(compatible_output=True)
    v2E = populations[L2E].get_v(compatible_output=True)
    gsyn = None
    spikes = None

    #spikesL1E = populations[L1E].getSpikes(compatible_output=True)
    #spikesL1I = populations[L1I].getSpikes(compatible_output=True)
    #spikesL2E = populations[L2E].getSpikes(compatible_output=True)

    print "Potential info:"
    print v1I
    print "Length: ", len(v1I)
    print "Single potential info:"
    print v1I[1]
    print "Length: ", len(v1I[1])
    print "Element 700: ", v1I[700]

    (meanPotL2E, stdPotL2E) = analyseTimeSeries(v2E, nL2ExcitNeurons, runTime)
    #print "L2E, mean potential: ", meanPotL2E
    #print "L2E, std potential: ", stdPotL2E

    #print "Inhib neurons:"
    (meanPotL1I, stdPotL1I) = analyseTimeSeries(v1I, nL1InhibNeurons, runTime)
    #print "L1I, mean potential: ", meanPotL1I
    #print "L1I, std potential: ", stdPotL1I

    #spikeRateL1E = 1000.0*len(spikesL1E)/nL1ExcitNeurons/runTime
    #spikeRateL1I = 1000.0*len(spikesL1I)/nL1ExcitNeurons/runTime
    #spikeRateL2E = 1000.0*len(spikesL2E)/nL2ExcitNeurons/runTime

    #print "Spike rate L1E: ", spikeRateL1E
    #print "Spike rate L1I: ", spikeRateL1I
    #print "Spike rate L2E: ", spikeRateL2E

    fsock=open("./L2E_stats.txt", 'a')
    myString = "%d %d %.2f    %.2f %.2f %.2f %.2f" % (nL1ExcitNeurons, nL2ExcitNeurons, \
               L1MeanWeightX2X, meanPotL2E, stdPotL2E, meanPotL1I, stdPotL1I)
    fsock.write("%s\n" % myString)
    fsock.close()

    doPlots = False
    if False:
        if spikesL1E != None:
            pylab.figure()
            pylab.plot([i[1] for i in spikesL1E], [i[0] for i in spikesL1E], ".")
            pylab.xlabel('Time/ms')
            pylab.ylabel('spikes')
            pylab.title('Spikes from Source (L1E) Neurons')
        else:
            print "No spikes received"

        if spikesL1I != None:
            pylab.figure()
            pylab.plot([i[1] for i in spikesL1I], [i[0] for i in spikesL1I], ".")
            pylab.xlabel('Time/ms')
            pylab.ylabel('spikes')
            pylab.title('Spikes of L1I Inhibitory Neurons')
        else:
            print "No spikes received"

        if spikesL2E != None:
            pylab.figure()
            pylab.plot([i[1] for i in spikesL2E], [i[0] for i in spikesL2E], ".")
            pylab.xlabel('Time/ms')
            pylab.ylabel('spikes')
            pylab.title('Spikes from L2E Excitatory Neurons')
        else:
            print "No spikes received"

    if doPlots:
        if v1I != None:
            ticks = len(v1I) / nL1InhibNeurons
            for q in range(4):
                pylab.figure()
                pylab.xlabel('Time/ms')
                pylab.ylabel('v')
                pos = q * 20 + 10
                str = "Inhibitory Neuron L1I[%d]" % pos
                pylab.title(str)
                v_for_neuron = v1I[pos * ticks : (pos + 1) * ticks]
                pylab.plot([i[1] for i in v_for_neuron], [i[2] for i in v_for_neuron])

        if v2E != None:
            ticks = len(v2E) / nL2ExcitNeurons
            for q in range(4):
                pylab.figure()
                pylab.xlabel('Time/ms')
                pylab.ylabel('v')
                pos = q * 20 + 10
                str = "Excitatory Neuron L2X[%d]" % pos
                pylab.title(str)
                v_for_neuron = v2E[pos * ticks : (pos + 1) * ticks]
                pylab.plot([i[1] for i in v_for_neuron], [i[2] for i in v_for_neuron])

        pylab.show()

    p.end()
