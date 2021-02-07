# coding: utf-8

# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
An implementation of benchmarks 1 and 2 from

    Brette et al. (2007) Journal of Computational Neuroscience 23: 349-398

The IF network is based on the CUBA and COBA abstract_models of Vogels & Abbott
(J. Neurosci, 2005).  The model consists of a network of excitatory and
inhibitory neurons, connected via current-based "exponential"
synapses (instantaneous rise, exponential decay).

Andrew Davison, UNIC, CNRS
August 2006

Adapted to PyNN8 by Christian Brenninkmeijer

$Id:VAbenchmarks.py 5 2007-04-16 15:01:24Z davison $
"""
import os
from neo.io import PickleIO
# import socket
import unittest
from unittest import SkipTest
from p8_integration_tests.base_test_case import BaseTestCase
import spynnaker8 as p
from spynnaker8.utilities import neo_compare
from spynnaker8.utilities import neo_convertor
from pyNN.random import NumpyRNG, RandomDistribution
from pyNN.utility import Timer
from spinnman.exceptions import SpinnmanTimeoutException

current_file_path = os.path.dirname(os.path.abspath(__file__))
neo_path = os.path.join(current_file_path, "spikes.pickle")


def do_run():
    simulator_name = 'spiNNaker'

    timer = Timer()

    # === Define parameters =========================================

    rngseed = 98766987
    parallel_safe = True

    n = 1500  # number of cells
    # number of excitatory cells:number of inhibitory cells
    r_ei = 4.0
    pconn = 0.02  # connection probability

    dt = 0.1  # (ms) simulation timestep
    tstop = 200  # (ms) simulaton duration
    delay = 1

    # Cell parameters
    area = 20000.  # (µm²)
    tau_m = 20.  # (ms)
    cm = 1.  # (µF/cm²)
    g_leak = 5e-5  # (S/cm²)
    e_leak = -49.  # (mV)
    v_thresh = -50.  # (mV)
    v_reset = -60.  # (mV)
    t_refrac = 5.  # (ms) (clamped at v_reset)
    # (mV) 'mean' membrane potential,  for calculating CUBA weights
    v_mean = -60.
    tau_exc = 5.  # (ms)
    tau_inh = 10.  # (ms)
    # (nS) #Those weights should be similar to the COBA weights
    g_exc = 0.27
    # (nS) # but the delpolarising drift should be taken into account
    g_inh = 4.5
    e_rev_exc = 0.  # (mV)
    e_rev_inh = -80.  # (mV)

    # === Calculate derived parameters ===============================

    area *= 1e-8  # convert to cm²
    cm *= area * 1000  # convert to nF
    r_m = 1e-6 / (g_leak * area)  # membrane resistance in MΩ
    assert tau_m == cm * r_m  # just to check

    # number of excitatory cells
    n_exc = int(round((n * r_ei / (1 + r_ei))))
    n_inh = n - n_exc  # number of inhibitory cells

    celltype = p.IF_curr_exp
    # (nA) weight of excitatory synapses
    w_exc = 1e-3 * g_exc * (e_rev_exc - v_mean)
    w_inh = 1e-3 * g_inh * (e_rev_inh - v_mean)  # (nA)
    assert w_exc > 0
    assert w_inh < 0

    # === Build the network ==========================================

    p.setup(timestep=dt, min_delay=delay, max_delay=delay)

    if simulator_name == 'spiNNaker':
        # this will set 100 neurons per core
        p.set_number_of_neurons_per_core(p.IF_curr_exp, 10)
        # this will set 50 neurons per core
        p.set_number_of_neurons_per_core(p.IF_cond_exp, 10)

    # node_id = 1
    # np = 1

    # host_name = socket.gethostname()

    cell_params = {'tau_m': tau_m, 'tau_syn_E': tau_exc, 'tau_syn_I': tau_inh,
                   'v_rest': e_leak, 'v_reset': v_reset, 'v_thresh': v_thresh,
                   'cm': cm, 'tau_refrac': t_refrac, 'i_offset': 0}

    timer.start()

    exc_cells = p.Population(n_exc, celltype, cell_params,
                             label="Excitatory_Cells")
    inh_cells = p.Population(n_inh, celltype, cell_params,
                             label="Inhibitory_Cells")
    p.NativeRNG(12345)

    rng = NumpyRNG(seed=rngseed, parallel_safe=parallel_safe)
    uniform_distr = RandomDistribution('uniform', [v_reset, v_thresh], rng=rng)
    exc_cells.initialize(v=uniform_distr)
    inh_cells.initialize(v=uniform_distr)

    exc_conn = p.FixedProbabilityConnector(pconn, rng=rng)
    synapse_exc = p.StaticSynapse(weight=w_exc, delay=delay)
    inh_conn = p.FixedProbabilityConnector(pconn, rng=rng)
    synapse_inh = p.StaticSynapse(weight=w_inh, delay=delay)

    connections = dict()
    connections['e2e'] = p.Projection(exc_cells, exc_cells, exc_conn,
                                      synapse_type=synapse_exc,
                                      receptor_type='excitatory')
    connections['e2i'] = p.Projection(exc_cells, inh_cells, exc_conn,
                                      synapse_type=synapse_exc,
                                      receptor_type='excitatory')
    connections['i2e'] = p.Projection(inh_cells, exc_cells, inh_conn,
                                      synapse_type=synapse_inh,
                                      receptor_type='inhibitory')
    connections['i2i'] = p.Projection(inh_cells, inh_cells, inh_conn,
                                      synapse_type=synapse_inh,
                                      receptor_type='inhibitory')

    # === Setup recording ==============================
    exc_cells.record("spikes")

    # === Run simulation ================================
    p.run(tstop)

    exc_spikes = exc_cells.get_data("spikes")

    exc_cells.write_data(neo_path, "spikes")

    p.end()

    return exc_spikes


class TestVABenchmarkSpikes(BaseTestCase):
    """
    tests the va benchmark spikes
    """

    def test_va_benchmark(self):

        try:
            exc_spikes = do_run()
        # System intentional overload so may error
        except SpinnmanTimeoutException as ex:
            raise SkipTest() from ex
        spike_count = neo_convertor.count_spikes(exc_spikes)
        print(spike_count)
        # CB Jan 14 2019 Result varie between runs
        self.assertLessEqual(2558, spike_count)
        self.assertGreaterEqual(2559, spike_count)
        io = PickleIO(filename=neo_path)
        recorded_spikes = io.read()[0]
        neo_compare.compare_blocks(exc_spikes, recorded_spikes)


if __name__ == '__main__':
    unittest.main()
