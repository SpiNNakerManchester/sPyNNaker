# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


class TestSimpleScript(BaseTestCase):

    def simple_script(self):
        # A simple script that should work whatever we do, but only if the
        # SDRAM is worked out correctly!
        p.setup(1.0)
        src = p.Population(1, p.SpikeSourceArray([50, 150]), label="input_pop")
        pop = p.Population(1, p.IF_curr_exp(), label="neuron")
        p.Projection(
            src, pop, p.OneToOneConnector(),
            synapse_type=p.StaticSynapse(weight=1.0))
        src.record('spikes')
        pop.record("all")
        p.run(200)
        p.end()

    def test_simple_script(self):
        self.runsafe(self.simple_script)
