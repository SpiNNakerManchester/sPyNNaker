#!/usr/bin/python

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

"""
Synfirechain-like example
"""
import math
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


def do_run():
    p.setup(timestep=1.0)
    weight = math.sqrt(2.0)
    random_delay = p.RandomDistribution("uniform", low=1, high=16)

    pop_input_1 = p.Population(10000, p.IF_curr_exp())
    pop_auto_1 = p.Population(256, p.IF_curr_exp())
    pop_fixed_1 = p.Population(
        256, p.IF_curr_exp(), max_expected_summed_weight=[2.0, 0.0])
    proj_auto_1 = p.Projection(
        pop_input_1, pop_auto_1, p.FixedProbabilityConnector(0.5),
        p.StaticSynapse(weight=weight, delay=random_delay))
    proj_fixed_1 = p.Projection(
        pop_input_1, pop_fixed_1, p.FixedProbabilityConnector(0.5),
        p.StaticSynapse(weight=weight, delay=random_delay))

    pop_input_2 = p.Population(1000, p.IF_curr_exp())
    pop_auto_2 = p.Population(256, p.IF_curr_exp())
    pop_fixed_2 = p.Population(
        256, p.IF_curr_exp(), max_expected_summed_weight=[2.0, 0.0])
    proj_auto_2 = p.Projection(
        pop_input_2, pop_auto_2, p.FixedProbabilityConnector(0.5),
        p.StaticSynapse(weight=weight, delay=random_delay))
    proj_fixed_2 = p.Projection(
        pop_input_2, pop_fixed_2, p.FixedProbabilityConnector(0.5),
        p.StaticSynapse(weight=weight, delay=random_delay))

    p.run(0)

    weights_auto_1 = proj_auto_1.get("weight", "list", with_address=False)
    weights_fixed_1 = proj_fixed_1.get("weight", "list", with_address=False)
    weights_auto_2 = proj_auto_2.get("weight", "list", with_address=False)
    weights_fixed_2 = proj_fixed_2.get("weight", "list", with_address=False)

    p.end()

    print("Auto 1 weights: {}".format(weights_auto_1[0]))
    print("Fixed 1 weights: {}".format(weights_fixed_1[0]))
    print("Auto 2 weights: {}".format(weights_auto_2[0]))
    print("Fixed 2 weights: {}".format(weights_fixed_2[0]))

    assert weights_auto_1[0] != weights_auto_2[0]
    assert weights_fixed_1[0] == weights_fixed_2[0]
    assert weights_auto_1[0] != weights_fixed_1[0]
    assert weights_auto_2[0] != weights_fixed_2[0]


class TestMaxWeight(BaseTestCase):

    def test_run(self):
        self.runsafe(do_run)


if __name__ == '__main__':
    do_run()
