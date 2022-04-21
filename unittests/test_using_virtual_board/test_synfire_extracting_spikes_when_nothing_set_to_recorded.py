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

import pyNN.spiNNaker as sim
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinnaker_testbase import BaseTestCase


class SynfireExtractingSpikesWhenNothingSetToRecorded(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_cause_error(self):
        with self.assertRaises(ConfigurationException):
            sim.setup(timestep=1.0)
            sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

            pop_1 = sim.Population(1, sim.IF_curr_exp(), label="pop_1")
            input = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]),
                                   label="input")
            sim.Projection(input, pop_1, sim.OneToOneConnector(),
                           synapse_type=sim.StaticSynapse(weight=5, delay=1))
            simtime = 10
            sim.run(simtime)

            pop_1.get_data(variables=["spikes"])
