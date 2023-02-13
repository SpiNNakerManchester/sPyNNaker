# Copyright (c) 2017-2023 The University of Manchester
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

    # NO unittest_setup() as sim.setup is called

    def test_run(self):
        p.setup()
        p.Population(10, p.SpikeSourceArray, {'spike_times': [100, 200]},
                     label='messed up')


if __name__ == '__main__':
    w = SynfireIfCurrExp()
    w.test_run()
