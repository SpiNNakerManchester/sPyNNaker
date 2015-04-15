"""
Synfirechain-like example
"""
#!/usr/bin/python
import pylab

import spynnaker.pyNN as p


p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
nNeurons = 200 # number of neurons in each population

cell_params_lif = {'cm'        : 0.25, # nF
                     'i_offset'  : 0.0,
                     'tau_m'     : 20.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 5.0,
                     'tau_syn_I' : 5.0,
                     'v_reset'   : -70.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -50.0
                     }

populations = list()
projections = list()

weight_to_spike = 2.0
delay = 1

connections = list()
for i in range(0, nNeurons):
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
    connections.append(singleConnection)

# Plastic Connection between pre_pop and post_pop
stdp_model1 = p.STDPMechanism(
    timing_dependence=p.SpikePairRule(
        tau_plus=16.7, tau_minus=33.7, nearest=True),
    weight_dependence=p.AdditiveWeightDependence(
        w_min=0.0, w_max=1.0, A_plus=0.005, A_minus=0.005),
    mad=True
)

# Plastic Connection between pre_pop and post_pop
stdp_model2 = p.STDPMechanism(
    timing_dependence=p.PfisterSpikeTripletRule(
        tau_plus=16.7, tau_minus=33.7, tau_x=44, tau_y=44),
    weight_dependence=p.AdditiveWeightDependence(
        w_min=0.0, w_max=1.0, A_plus=0.005, A_minus=0.005),
    mad=True
)

# Plastic Connection between pre_pop and post_pop
stdp_model3 = p.STDPMechanism(
    timing_dependence=p.SpikePairRule(
        tau_plus=16.7, tau_minus=33.7, nearest=True),
    weight_dependence=p.MultiplicativeWeightDependence(
        w_min=0.0, w_max=1.0, A_plus=0.005, A_minus=0.005),
    mad=True
)


injectionConnection = [(0, 0, weight_to_spike, 1)]
spikeArray1 = {'spike_times': [[0]]}
spikeArray2 = {'spike_times': [[25]]}
spikeArray3 = {'spike_times': [[50]]}
spikeArray4 = {'spike_times': [[75]]}
spikeArray5 = {'spike_times': [[100]]}
spikeArray6 = {'spike_times': [[125]]}
spikeArray7 = {'spike_times': [[150]]}
spikeArray8 = {'spike_times': [[175]]}

populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                label='pop_1'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray1,
                                label='inputSpikes_1'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray2,
                                label='inputSpikes_2'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray3,
                                label='inputSpikes_3'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray4,
                                label='inputSpikes_4'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray5,
                                label='inputSpikes_5'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray6,
                                label='inputSpikes_6'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray7,
                                label='inputSpikes_7'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray8,
                                label='inputSpikes_8'))

projections.append(p.Projection(populations[0], populations[0],
                                p.FromListConnector(connections)))
projections.append(p.Projection(populations[1], populations[0],
                                p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[2], populations[0],
                                p.FromListConnector(injectionConnection),
                                synapse_dynamics=
                                p.SynapseDynamics(slow=stdp_model1)))
projections.append(p.Projection(populations[3], populations[0],
                                p.FromListConnector(injectionConnection),
                                synapse_dynamics=
                                p.SynapseDynamics(slow=stdp_model2)))
projections.append(p.Projection(populations[4], populations[0],
                                p.FromListConnector(injectionConnection),
                                synapse_dynamics=
                                p.SynapseDynamics(slow=stdp_model3)))
# currently only slow SynapseDynamics are supported, therefore fast ones need to
# be removed
#projections.append(p.Projection(populations[5], populations[0],
#                                p.FromListConnector(injectionConnection),
#                                synapse_dynamics=
#                                p.SynapseDynamics(fast=stdp_model1)))
#projections.append(p.Projection(populations[6], populations[0],
#                                p.FromListConnector(injectionConnection),
#                                synapse_dynamics=
#                                p.SynapseDynamics(fast=stdp_model2)))
#projections.append(p.Projection(populations[7], populations[0],
#                                p.FromListConnector(injectionConnection),
#                                synapse_dynamics=
 #                               p.SynapseDynamics(fast=stdp_model3)))

populations[0].record()

p.run(500)

v = None
gsyn = None
spikes = None

spikes = populations[0].getSpikes(compatible_output=True)

if spikes is not None:
    print spikes
    pylab.figure()
    pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
    pylab.xlabel('Time/ms')
    pylab.ylabel('spikes')
    pylab.xticks([0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000])
    pylab.yticks([0, 50, 100, 150, 200])
    pylab.title('spikes')
    pylab.show()
else:
    print "No spikes received"

# Make some graphs

if v is not None:
    ticks = len(v) / nNeurons
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('v')
    pylab.title('v')
    for pos in range(0, nNeurons, 20):
        v_for_neuron = v[pos * ticks : (pos + 1) * ticks]
        pylab.plot([i[1] for i in v_for_neuron],
                [i[2] for i in v_for_neuron])
    pylab.show()

if gsyn is not None:
    ticks = len(gsyn) / nNeurons
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('gsyn')
    pylab.title('gsyn')
    for pos in range(0, nNeurons, 20):
        gsyn_for_neuron = gsyn[pos * ticks : (pos + 1) * ticks]
        pylab.plot([i[1] for i in gsyn_for_neuron],
                [i[2] for i in gsyn_for_neuron])
    pylab.show()

p.end(stop_on_board=True)
