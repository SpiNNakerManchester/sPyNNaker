# coding: utf-8
"""
An implementation of benchmarks 1 and 2 from

    Brette et al. (2007) Journal of Computational Neuroscience 23: 349-398

The IF network is based on the CUBA and COBA models of Vogels & Abbott
(J. Neurosci, 2005).  The model consists of a network of excitatory and
inhibitory neurons, connected via current-based "exponential"
synapses (instantaneous rise, exponential decay).

Andrew Davison, UNIC, CNRS
August 2006
"""
import socket

simulator_name = 'spiNNaker'
benchmark = 'CUBA'

# exec("from pyNN.%s import *" % simulator_name)
from spynnaker.pyNN import *
from pyNN.random import NumpyRNG, RandomDistribution
from pyNN.utility import Timer

timer = Timer()

# === Define parameters ===
threads = 1
rngseed = 98766987
parallel_safe = True

n = 1500  # number of cells
r_ei = 4.0  # number of excitatory cells:number of inhibitory cells
pconn = 0.02  # connection probability
stim_dur = 50.  # (ms) duration of random stimulation
rate = 100.  # (Hz) frequency of the random stimulation

dt = 1.0  # (ms) simulation timestep
tstop = 1000  # (ms) simulaton duration
delay = 2

# Cell parameters
area = 20000.  # (µm²)
tau_m = 20.  # (ms)
cm = 1.  # (µF/cm²)
g_leak = 5e-5  # (S/cm²)
if benchmark == "COBA":
    E_leak = -60.  # (mV)
elif benchmark == "CUBA":
    E_leak = -49.  # (mV)
v_thresh = -50.  # (mV)
v_reset = -60.  # (mV)
t_refrac = 5.  # (ms) (clamped at v_reset)
v_mean = -60.  # (mV) mean membrane potential, for calculating CUBA weights
tau_exc = 5.  # (ms)
tau_inh = 10.  # (ms)

# Synapse parameters
if benchmark == "COBA":
    Gexc = 4.  # (nS)
    Ginh = 51.  # (nS)
elif benchmark == "CUBA":
    Gexc = 0.27  # (nS) # Those weights should be similar to the COBA weights
    Ginh = 4.5  # (nS) # but with depolarising drift
Erev_exc = 0.  # (mV)
Erev_inh = -80.  # (mV)

# === Calculate derived parameters ===
area = area * 1e-8  # convert to cm²
cm = cm * area * 1000  # convert to nF
Rm = 1e-6 / (g_leak * area)  # membrane resistance in MΩ
assert tau_m == cm * Rm  # just to check

n_exc = int(round((n * r_ei / (1 + r_ei))))  # number of excitatory cells
n_inh = n - n_exc  # number of inhibitory cells

print n_exc, n_inh

if benchmark == "COBA":
    celltype = IF_cond_exp
    w_exc = Gexc * 1e-3  # We convert conductances to uS
    w_inh = Ginh * 1e-3
    print w_exc, w_inh
elif benchmark == "CUBA":
    celltype = IF_curr_exp
    w_exc = 1e-3 * Gexc * (Erev_exc - v_mean)  # (nA) weight of exc synapses
    w_inh = 1e-3 * Ginh * (Erev_inh - v_mean)  # (nA)
    assert w_exc > 0
    assert w_inh < 0

# === Build the network ===

extra = {'threads': threads,
         'filename': "va_%s.xml" % benchmark,
         'label': 'VA'}
if simulator_name == "neuroml":
    extra["file"] = "VAbenchmarks.xml"

node_id = setup(timestep=dt, min_delay=delay, max_delay=delay,
                db_name='va_benchmark.sqlite', **extra)

if simulator_name == 'spiNNaker':
    set_number_of_neurons_per_core('IF_curr_exp',
                                   100)  # this will set 100 neurons per core
    set_number_of_neurons_per_core('IF_cond_exp',
                                   50)  # this will set 50 neurons per core

node_id = 1
np = 1

host_name = socket.gethostname()
print "Host #%d is on %s" % (np, host_name)

print "%s Initialising the simulator with %d thread(s)..." % (
    node_id, extra['threads'])

cell_params = {'tau_m': tau_m,
               'tau_syn_E': tau_exc,
               'tau_syn_I': tau_inh,
               'v_rest': E_leak,
               'v_reset': v_reset,
               'v_thresh': v_thresh,
               'cm': cm,
               'tau_refrac': t_refrac,
               'i_offset': 0
               }

print cell_params

if (benchmark == "COBA"):
    cell_params['e_rev_E'] = Erev_exc
    cell_params['e_rev_I'] = Erev_inh

timer.start()

print "%s Creating cell populations..." % node_id
exc_cells = Population(n_exc, celltype, cell_params, label="Excitatory_Cells")
inh_cells = Population(n_inh, celltype, cell_params, label="Inhibitory_Cells")
if benchmark == "COBA":
    ext_stim = Population(
        20, SpikeSourcePoisson,
        {'rate': rate, 'duration': stim_dur},
        label="expoisson")
    rconn = 0.01
    ext_conn = FixedProbabilityConnector(rconn, weights=0.1)
    ext_stim.record()

print "%s Initialising membrane potential to random values..." % node_id
rng = NumpyRNG(seed=rngseed, parallel_safe=parallel_safe)
uniformDistr = RandomDistribution('uniform', [v_reset, v_thresh], rng=rng)
exc_cells.initialize('v', uniformDistr)
inh_cells.initialize('v', uniformDistr)

print "%s Connecting populations..." % node_id
exc_conn = FixedProbabilityConnector(pconn, weights=w_exc, delays=delay)
inh_conn = FixedProbabilityConnector(pconn, weights=w_inh, delays=delay)

connections = {}
connections['e2e'] = Projection(exc_cells, exc_cells, exc_conn,
                                target='excitatory', rng=rng)
connections['e2i'] = Projection(exc_cells, inh_cells, exc_conn,
                                target='excitatory', rng=rng)
connections['i2e'] = Projection(inh_cells, exc_cells, inh_conn,
                                target='inhibitory', rng=rng)
connections['i2i'] = Projection(inh_cells, inh_cells, inh_conn,
                                target='inhibitory', rng=rng)

if (benchmark == "COBA"):
    connections['ext2e'] = Projection(ext_stim, exc_cells, ext_conn,
                                      target='excitatory')
    connections['ext2i'] = Projection(ext_stim, inh_cells, ext_conn,
                                      target='excitatory')

# === Setup recording ===
print "%s Setting up recording..." % node_id
exc_cells.record()

buildCPUTime = timer.diff()

# === Run simulation ===
print "%d Running simulation..." % node_id

print "timings: number of neurons:", n
print "timings: number of synapses:", n * n * pconn

run(tstop)

simCPUTime = timer.diff()

# === Print results to file ===

import pylab

exc_spikes = exc_cells.getSpikes(compatible_output=True)
pylab.figure()
pylab.plot([i[1] for i in exc_spikes],
           [i[0] for i in exc_spikes], ".", markersize=2)
pylab.xlabel('Time/ms')
pylab.ylabel('spikes')
pylab.title('spikes')
pylab.show()

writeCPUTime = timer.diff()

if node_id == 0:
    print "\n--- Vogels-Abbott Network Simulation ---"
    print "Nodes                  : %d" % np
    print "Simulation type        : %s" % benchmark
    print "Number of Neurons      : %d" % n
    print "Number of Synapses     : %s" % connections
    print "Excitatory conductance : %g nS" % Gexc
    print "Inhibitory conductance : %g nS" % Ginh
    print "Build time             : %g s" % buildCPUTime
    print "Simulation time        : %g s" % simCPUTime
    print "Writing time           : %g s" % writeCPUTime


# === Finished with simulator ===

end()
