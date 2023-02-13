# Copyright (c) 2015-2023 The University of Manchester
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
