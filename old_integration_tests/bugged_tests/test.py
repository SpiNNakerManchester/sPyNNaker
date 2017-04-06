"""
Synfirechain-like example
"""
#!/usr/bin/python
import spynnaker.pyNN as p
#import pyNN.nest as p
import numpy, pylab

p.setup(timestep=1, min_delay=1, max_delay=15)

nNeurons = 1 # number of neurons in each population
nSources = 1 # Number of Poisson sources

neuron_parameters = {'cm'        : 0.25, # nF
                     'i_offset'  : 2,
                     'tau_m'     : 10.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 0.5,
                     'tau_syn_I' : 0.5,
                     'v_reset'   : -65.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -50.0}

populations = list()
projections = list()

poisson_params = {'rate': 100, 'start':0, 'duration' : 100000000}
poisson_params2 = {'rate': 10, 'start':0, 'duration' : 100000000}
populations.append(p.Population(nNeurons, p.IF_curr_exp, neuron_parameters, label='pop_1'))
populations.append(p.Population(nNeurons, p.IF_curr_exp, neuron_parameters, label='pop_2'))
populations[1].add_placement_constraint(x=1,y=0)#{"x": 1, "y": 0})
#populations.append(p.Population(nSources, p.SpikeSourcePoisson, poisson_params, label='pois_1'))
#populations.append(p.Population(nSources, p.SpikeSourcePoisson, poisson_params2, label='pois_2'))

#projections.append(p.Projection(populations[0], populations[1], p.OneToOneConnector(weights=2, delays=0.1)))
#projections.append(p.Projection(populations[1], populations[0], p.OneToOneConnector(weights=2, delays=0.1)))
#projections.append(p.Projection(populations[0], populations[0], p.OneToOneConnector(weights=2, delays=0.1)))
#projections.append(p.Projection(populations[1], populations[1], p.OneToOneConnector(weights=2, delays=0.1)))

#projections.append(p.Projection(populations[1], populations[0], p.OneToOneConnector(weights=2, delays=1)))
#projections.append(p.Projection(populations[2], populations[0], p.OneToOneConnector(weights=-4, delays=1)))

#populations[0].record_v()
#populations[0].record_gsyn()
populations[0].record()
populations[1].record()

p.run(100)

v = None
spikes = None
gsyn = None

v = populations[0].get_v()
#spikes = populations[0].getSpikes()
#gsyn = populations[0].get_gsyn()

if spikes != None:
    print "Spikes:", spikes
    pylab.figure()
    pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
    pylab.xlabel('Time/ms')
    pylab.ylabel('spikes')
    pylab.title('spikes')
    pylab.show()
else:
    print "No Spikes"

# Make some graphs
if v != None:
    v_per_neuron = [numpy.zeros((0, 2)) for neuronID in range(nNeurons)]
    for (nid, time, value) in v:
        v_per_neuron[int(nid)] = numpy.append(v_per_neuron[int(nid)],
                [[time, value]], 0)

    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('v')
    pylab.title('v')
    for v_n in v_per_neuron:
        pylab.plot([i[0] for i in v_n], [i[1] for i in v_n])
    pylab.show()
else:
    print "No V"

if gsyn != None:
    gsyn_per_neuron = [numpy.zeros((0, 2)) for neuronID in range(nNeurons)]
    for (nid, time, value) in gsyn:
        gsyn_per_neuron[int(nid)] = numpy.append(gsyn_per_neuron[int(nid)],
                 [[time, value]], 0)

    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('gsyn')
    pylab.title('gsyn')
    for g_n in gsyn_per_neuron:
        pylab.plot([i[0] for i in g_n], [i[1] for i in g_n])
    pylab.show()


p.end()