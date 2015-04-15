# coding: utf-8
"""
An implementation of benchmarks 1 and 2 from

    Brette et al. (2007) Journal of Computational Neuroscience 23: 349-398

The IF network is based on the CUBA and COBA abstract_models of Vogels & Abbott
(J. Neurosci, 2005).  The model consists of a network of excitatory and
inhibitory neurons, connected via current-based "exponential"
synapses (instantaneous rise, exponential decay).

Andrew Davison, UNIC, CNRS
August 2006

$Id:VAbenchmarks.py 5 2007-04-16 15:01:24Z davison $
"""

import os
import socket
import unittest
from spynnaker.pyNN import *
from pyNN.random import NumpyRNG, RandomDistribution
from pyNN.utility import Timer

class TestVABenchmarkSpikes(unittest.TestCase):
    """
    tests the va benchmark spikes
    """

    def test_va_benchmark(self):

        simulator_name = 'spiNNaker'
        benchmark = 'CUBA'

        timer = Timer()

        # === Define parameters ========================================================

        threads  = 1
        rngseed  = 98766987
        parallel_safe = True

        n        = 1500  # number of cells
        r_ei     = 4.0   # number of excitatory cells:number of inhibitory cells
        pconn    = 0.02  # connection probability
        stim_dur = 50.   # (ms) duration of random stimulation
        rate     = 100.  # (Hz) frequency of the random stimulation

        dt       = 1        # (ms) simulation timestep
        tstop    = 2000    # (ms) simulaton duration
        delay    = 1

        # Cell parameters
        area     = 20000. # (µm²)
        tau_m    = 20.    # (ms)
        cm       = 1.     # (µF/cm²)
        g_leak   = 5e-5   # (S/cm²)
        E_leak   = -49.  # (mV)
        v_thresh = -50.   # (mV)
        v_reset  = -60.   # (mV)
        t_refrac = 5.     # (ms) (clamped at v_reset)
        v_mean   = -60.   # (mV) 'mean' membrane potential, for calculating CUBA weights
        tau_exc  = 5.     # (ms)
        tau_inh  = 10.    # (ms)

        Gexc = 0.27   # (nS) #Those weights should be similar to the COBA weights
        Ginh = 4.5    # (nS) # but the delpolarising drift should be taken into account
        Erev_exc = 0.     # (mV)
        Erev_inh = -80.   # (mV)

        ### what is the synaptic delay???

        # === Calculate derived parameters =============================================

        area  = area*1e-8                     # convert to cm²
        cm    = cm*area*1000                  # convert to nF
        Rm    = 1e-6/(g_leak*area)            # membrane resistance in MΩ
        assert tau_m == cm*Rm                 # just to check



        n_exc = int(round((n*r_ei/(1+r_ei)))) # number of excitatory cells
        n_inh = n - n_exc                     # number of inhibitory cells

        print n_exc, n_inh

        celltype = IF_curr_exp
        w_exc = 1e-3*Gexc*(Erev_exc - v_mean) # (nA) weight of excitatory synapses
        w_inh = 1e-3*Ginh*(Erev_inh - v_mean) # (nA)
        assert w_exc > 0; assert w_inh < 0

        # === Build the network ========================================================

        extra = {'threads' : threads,
                 'filename': "va_%s.xml" % benchmark,
                 'label': 'VA'}
        if simulator_name == "neuroml":
            extra["file"] = "VAbenchmarks.xml"

        node_id = setup(timestep=dt, min_delay=delay, max_delay=delay, db_name='va_benchmark.sqlite', **extra)

        if simulator_name == 'spiNNaker':
            set_number_of_neurons_per_core('IF_curr_exp', 100)      # this will set 100 neurons per core
            set_number_of_neurons_per_core('IF_cond_exp', 50)      # this will set 50 neurons per core

        node_id = 1
        np = 1

        host_name = socket.gethostname()
        print "Host #%d is on %s" % (np, host_name)

        print "%s Initialising the simulator with %d thread(s)..." % (node_id, extra['threads'])

        cell_params = {
            'tau_m'      : tau_m,    'tau_syn_E'  : tau_exc,  'tau_syn_I'  : tau_inh,
            'v_rest'     : E_leak,   'v_reset'    : v_reset,  'v_thresh'   : v_thresh,
            'cm'         : cm,       'tau_refrac' : t_refrac, 'i_offset' : 0}

        print cell_params

        timer.start()

        print "%s Creating cell populations..." % node_id
        exc_cells = Population(n_exc, celltype, cell_params, label="Excitatory_Cells")
        inh_cells = Population(n_inh, celltype, cell_params, label="Inhibitory_Cells")
        NativeRNG(12345)

        print "%s Initialising membrane potential to random values..." % node_id
        rng = NumpyRNG(seed=rngseed, parallel_safe=parallel_safe)
        uniformDistr = RandomDistribution('uniform', [v_reset,v_thresh], rng=rng)
        exc_cells.initialize('v', uniformDistr)
        inh_cells.initialize('v', uniformDistr)

        print "%s Connecting populations..." % node_id
        exc_conn = FixedProbabilityConnector(pconn, weights=w_exc, delays=delay)
        inh_conn = FixedProbabilityConnector(pconn, weights=w_inh, delays=delay)


        connections={}
        connections['e2e'] = Projection(exc_cells, exc_cells, exc_conn, target='excitatory', rng=rng)
        connections['e2i'] = Projection(exc_cells, inh_cells, exc_conn, target='excitatory', rng=rng)
        connections['i2e'] = Projection(inh_cells, exc_cells, inh_conn, target='inhibitory', rng=rng)
        connections['i2i'] = Projection(inh_cells, inh_cells, inh_conn, target='inhibitory', rng=rng)

        # === Setup recording ==============================
        print "%s Setting up recording..." % node_id
        exc_cells.record()

        # === Run simulation ================================
        print "%d Running simulation..." % node_id

        print "timings: number of neurons:", n
        print "timings: number of synapses:", n*n*pconn

        run(tstop)

        # === Print results to file ===============================

        print "%d Writing data to file..." % node_id

        if not(os.path.isdir('Results')):
            os.mkdir('Results')

        exc_spikes = exc_cells.getSpikes()

        current_file_path = os.path.dirname(os.path.abspath(__file__))
        current_file_path = os.path.join(current_file_path, "spikes.data")
        #  exc_cells.printSpikes(current_file_path)
        pre_recorded_spikes = utility_calls.read_spikes_from_file(
            current_file_path, 0, n_exc, 0, tstop)

        end()

        for spike_element, read_element in zip(exc_spikes, pre_recorded_spikes):
                self.assertEqual(round(spike_element[0], 1),
                                 round(read_element[0], 1))
                self.assertEqual(round(spike_element[1], 1),
                                 round(read_element[1], 1))