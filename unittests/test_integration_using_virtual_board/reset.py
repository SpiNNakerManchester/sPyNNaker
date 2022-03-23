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

import spynnaker8 as p
from spinnaker_testbase import BaseTestCase


class SynfireIfCurrExp(BaseTestCase):

    def test_run(self):
        p.setup()
        cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                           'tau_refrac': 2.0, 'tau_syn_E': 5.0,
                           'tau_syn_I': 5.0, 'v_reset': -70.0, 'v_rest': -65.0,
                           'v_thresh': -50.0}

        pop = p.Population(10, p.IF_curr_exp(**cell_params_lif), label='test')
        p.run(100)
        pop.set(cm=0.30)


if __name__ == '__main__':
    x = SynfireIfCurrExp()
    x.test_run()
