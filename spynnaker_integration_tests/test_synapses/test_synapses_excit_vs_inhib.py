#!/usr/bin/env python

# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pyNN.spiNNaker as p
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


class TestSynapsesExcitVsInhib(BaseTestCase):

    def do_run(self):
        p.setup(timestep=1.0, min_delay=1.0)

        cell_params = {'i_offset': .1, 'tau_refrac': 3.0, 'v_rest': -65.0,
                       'v_thresh': -51.0, 'tau_syn_E': 2.0,
                       'tau_syn_I': 5.0, 'v_reset': -70.0,
                       'e_rev_E': 0., 'e_rev_I': -80.}

        # setup test population
        if_pop = p.Population(1, p.IF_cond_exp, cell_params)
        # setup spike sources
        spike_times = [20., 40., 60.]
        exc_pop = p.Population(1, p.SpikeSourceArray,
                               {'spike_times': spike_times})
        inh_pop = p.Population(1, p.SpikeSourceArray,
                               {'spike_times': [120, 140, 160]})
        # setup excitatory and inhibitory connections
        listcon = p.FromListConnector([(0, 0, 0.05, 1.0)])
        p.Projection(exc_pop, if_pop, listcon, receptor_type='excitatory')
        p.Projection(inh_pop, if_pop, listcon, receptor_type='inhibitory')
        # setup recorder
        if_pop.record(["v"])
        p.run(100)
        p.reset()
        if_pop.initialize(v=-65)
        exc_pop.set(spike_times=[])
        inh_pop.set(spike_times=spike_times)
        p.run(100)
        # read out voltage and plot
        neo = if_pop.get_data("all")
        p.end()
        v = neo_convertor.convert_data(neo, "v", run=0)
        v2 = neo_convertor.convert_data(neo, "v", run=1)

        self.assertGreater(v[22][2], v[21][2])
        self.assertGreater(v[42][2], v[41][2])
        self.assertGreater(v[62][2], v[61][2])
        self.assertLess(v2[22][2], v2[21][2])
        self.assertLess(v2[42][2], v2[41][2])
        self.assertLess(v2[62][2], v2[61][2])

    def test_run(self):
        self.runsafe(self.do_run)
