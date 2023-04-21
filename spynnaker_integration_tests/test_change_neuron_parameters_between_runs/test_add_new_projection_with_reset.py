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


class TestAddNewProjectionWithReset(BaseTestCase):

    def projection_with_reset(self):
        p.setup(1.0)

        inp = p.Population(1, p.IF_curr_exp(), label="input")
        layer = p.Population(1, p.IF_curr_exp(), label="layer")
        output = p.Population(1, p.IF_curr_exp(), label="output")

        p.Projection(inp, layer, p.AllToAllConnector(),
                     p.StaticSynapse(weight=5, delay=2))

        p.run(100)

        layer_to_output = p.Projection(layer, output, p.AllToAllConnector(),
                                       p.StaticSynapse(weight=4, delay=10))

        p.reset()

        p.run(100)

        weights_delays_out = layer_to_output.get(["weight", "delay"], "list")

        p.end()

        assert weights_delays_out[0][2] == 4.0

    def test_projection_with_reset(self):
        self.runsafe(self.projection_with_reset)
