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


def a_run():
    n_neurons = 100  # number of neurons in each population

    p.setup(timestep=1.0, min_delay=1.0)

    x = p.Population(
        n_neurons, p.IF_curr_exp(), label='pop_1',
        additional_parameters={"spikes_per_second": "bacon"})
    assert x._vertex.spikes_per_second == "bacon"
    p.end()


class PopAdditionParamsTest(BaseTestCase):

    def test_a_run(self):
        self.runsafe(a_run)


if __name__ == '__main__':
    a_run()
