import numpy
import pylab
import spynnaker.pyNN as sim

sim.setup(timestep=1.0, min_delay=1.0, max_delay=10.0)

input_rate = 15.0
sim_time = 1000.0

cell_params = {'cm'        : 0.25, # nF
               'i_offset'  : 0.0,
               'tau_m'     : 10.0,
               'tau_refrac': 2.0,
               'tau_syn_E' : 20.0,
               'v_reset'   : -70.0,
               'v_rest'    : -65.0,
               'v_thresh'  : -55.4}

# Create spike source
input_isi = 1000 / 15.0
spike_source = sim.Population(1, sim.SpikeSourceArray,
                              {"spike_times": numpy.arange(10.0, sim_time, input_isi)})

# Create single neuron
neuron_pop = sim.Population(1, sim.IF_curr_exp, cell_params)
neuron_pop.record_gsyn()

# Create Tskodyks Markram synapse
synapse_dynamics = sim.SynapseDynamics(
    fast=sim.TsodyksMarkramMechanism(U=0.45, tau_rec=750.0, tau_facil=50.0))

# Use this to connect spike source to neuron
sim.Projection(spike_source, neuron_pop, sim.OneToOneConnector(weights=2.0),
               synapse_dynamics=synapse_dynamics)

sim.run(sim_time)

gsyn = neuron_pop.get_gsyn(compatible_output=True)

figure, axis = pylab.subplots()
axis.plot(gsyn[:,1], gsyn[:,2])
pylab.show()

