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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class SSPNeuronClassNoEdgeTest(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_run(self) -> None:
        sim.setup()

        sim.Population(3, sim.SpikeSourcePoisson, {"rate": 100})
        p2 = sim.Population(3, sim.SpikeSourceArray,
                            {"spike_times": [[10.0], [20.0], [30.0]]})
        p3 = sim.Population(4, sim.IF_cond_exp, {})

        sim.Projection(p2, p3, sim.FromListConnector([
            (0, 0, 0.1, 1.0), (1, 1, 0.1, 1.0), (2, 2, 0.1, 1.0)]))

        sim.run(100.0)

        sim.end()


if __name__ == "__main__":
    """
    main entrance method
    """
    blah = SSPNeuronClassNoEdgeTest()
    blah.test_run()
