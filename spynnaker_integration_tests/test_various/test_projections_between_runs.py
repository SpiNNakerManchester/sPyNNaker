# Copyright (c) 2017 The University of Manchester
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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase
# import neo_convertor


def do_run():
    sim.setup(timestep=1)
    pop_1 = sim.Population(1, sim.IF_curr_exp, {}, label="pop_1")
    inp = sim.Population(
        1, sim.SpikeSourceArray, {'spike_times': [[0]]}, label="input")
    sim.Projection(
        pop_1, pop_1, sim.OneToOneConnector(),
        synapse_type=sim.StaticSynapse(weight=5.0, delay=1),
        receptor_type="excitatory", source=None, space=None)

    pop_1.record("spikes")
    sim.run(20)
    first_spikes = pop_1.spinnaker_get_data("spikes")

    sim.Projection(
        inp, pop_1, sim.FromListConnector([[0, 0, 5, 5]]),
        synapse_type=sim.StaticSynapse(weight=5.0, delay=1),
        receptor_type="excitatory", source=None,
        space=None)

    sim.reset()
    sim.run(20)
    second_spikes = pop_1.spinnaker_get_data("spikes")
    sim.end()

    return first_spikes, second_spikes


class TestProjectionBetweenRun(BaseTestCase):
    def do_run(self):
        first_spikes, second_spikes = do_run()
        assert len(first_spikes) == 0
        assert len(second_spikes[0]) == 2

    def test_run(self):
        self.runsafe(self.do_run)
