#!/usr/bin/python

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

from spinnaker_testbase import BaseTestCase
import spynnaker8 as sim


class AllToAllWithDelayExtensionCase(BaseTestCase):

    # Added to check that the delay expander runs; a previous fix
    # for a related issue inadvertently turned it off for this type of case

    def do_run(self):
        sim.setup(timestep=1.0)

        model = sim.IF_curr_exp

        cell_params_input = {'cm': 0.25,
                             'i_offset': 1.0,
                             'tau_m': 20.0,
                             'tau_refrac': 2.0,
                             'tau_syn_E': 5.0,
                             'tau_syn_I': 5.0,
                             'v_reset': -70.0,
                             'v_rest': -65.0,
                             'v_thresh': -50.0
                             }

        cell_params_output = {'cm': 0.25,
                              'i_offset': 0.0,
                              'tau_m': 20.0,
                              'tau_refrac': 2.0,
                              'tau_syn_E': 5.0,
                              'tau_syn_I': 5.0,
                              'v_reset': -70.0,
                              'v_rest': -65.0,
                              'v_thresh': -50.0
                              }

        pre_size = 2
        post_size = 3
        simtime = 200

        pre_pop = sim.Population(pre_size, model(**cell_params_input))
        post_pop = sim.Population(post_size, model(**cell_params_output))

        wiring = sim.AllToAllConnector()
        static_synapse = sim.StaticSynapse(weight=2.5, delay=100.0)
        sim.Projection(pre_pop, post_pop, wiring, receptor_type='excitatory',
                       synapse_type=static_synapse)

        # record post-pop spikes to check activation
        post_pop.record(['spikes'])

        # run simulation
        sim.run(simtime)

        # get data
        neo_post_spikes = post_pop.get_data(['spikes'])

        # end simulation
        sim.end()

        # Check there are spikes
        length = len(neo_post_spikes.segments[0].spiketrains[0])
        self.assertGreater(length, 0)

    def test_run(self):
        self.runsafe(self.do_run)
