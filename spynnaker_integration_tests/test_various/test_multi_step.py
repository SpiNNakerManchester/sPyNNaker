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
import numpy
import sys
from spinnaker_testbase import BaseTestCase


def run_network(timestep, steps_per_timestep):
    p.setup(timestep, max_delay=1.0)
    pre = p.Population(1, p.SpikeSourceArray(range(0, 100, 10)))
    post = p.Population(1, p.IF_cond_exp(), additional_parameters={
        "n_steps_per_timestep": steps_per_timestep})
    post.record(["v", "spikes"])
    p.Projection(pre, post, p.AllToAllConnector(),
                 p.StaticSynapse(weight=0.13))
    p.run(100)
    v = post.get_data("v").segments[0].filter(name='v')[0]
    spikes = post.get_data("spikes").segments[0].spiketrains
    p.end()
    return v, spikes


def do_test_multistep():
    v_005, spikes_005 = run_network(0.05, 1)
    v_005 = numpy.ravel(v_005.magnitude)[1::2][:-1]
    spikes_005 = numpy.round(spikes_005[0].times.magnitude + 0.025, 1)
    v_01, spikes_01 = run_network(0.1, 2)
    v_01 = numpy.ravel(v_01.magnitude)[1:]
    spikes_01 = spikes_01[0].times.magnitude
    return v_01, spikes_01, v_005, spikes_005


class TestMultiStep(BaseTestCase):

    def do_test_multistep(self):
        v_01, spikes_01, v_005, spikes_005 = do_test_multistep()
        assert numpy.array_equal(v_01, v_005)
        assert numpy.allclose(spikes_01, spikes_005)

    def test_do_test_multistep(self):
        self.runsafe(self.do_test_multistep)


if __name__ == "__main__":
    v_01, spikes_01, v_005, spikes_005 = do_test_multistep()

    numpy.set_printoptions(threshold=sys.maxsize)
    print(v_01, spikes_01)
    print(v_005, spikes_005)
