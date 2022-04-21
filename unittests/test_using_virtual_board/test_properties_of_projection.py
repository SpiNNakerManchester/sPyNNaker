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

import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


class TestProps(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_props(self):
        p.setup(timestep=1.0, min_delay=1.0)

        cell_params_lif = {'cm': 0.25,  # nF
                           'i_offset': 0.0, 'tau_m': 20.0, 'tau_refrac': 2.0,
                           'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
                           'v_reset': -70.0,
                           'v_rest': -65.0, 'v_thresh': -50.0}

        source = p.Population(1, p.IF_curr_exp, cell_params_lif, label='pop_1')

        dest = p.Population(1, p.IF_curr_exp, cell_params_lif, label='pop_2')

        connector = p.AllToAllConnector()
        synapse_type = p.StaticSynapse(weight=0, delay=1)

        test_label = "BLAH!"

        proj = p.Projection(
            presynaptic_population=source,
            postsynaptic_population=dest,
            connector=connector, synapse_type=synapse_type, label="BLAH!")

        proj_label = proj.label
        proj_source = proj.pre
        proj_dest = proj.post
        self.assertEqual(source, proj_source)
        self.assertEqual(dest, proj_dest)
        self.assertEqual(test_label, proj_label)
