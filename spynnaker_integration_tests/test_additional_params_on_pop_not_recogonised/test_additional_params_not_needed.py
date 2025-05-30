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
from testfixtures import LogCapture  # type: ignore[import]


def a_run() -> None:
    n_neurons = 100  # number of neurons in each population

    p.setup(timestep=1.0, min_delay=1.0)
    p.Population(
        n_neurons, p.IF_curr_exp(), label='pop_1',
        additional_parameters={"bacon": "bacon"})
    p.end()


class PopAdditionParamsTest(BaseTestCase):

    def a_run(self) -> None:
        n_neurons = 100  # number of neurons in each population

        p.setup(timestep=1.0, min_delay=1.0)
        with LogCapture() as lc:
            p.Population(
                n_neurons, p.IF_curr_exp(), label='pop_1',
                additional_parameters={"bacon": "bacon"})

            self.assert_logs_messages(
                lc.records,
                "additional_parameter bacon will be ignored", 'WARNING', 1)

    def test_a_run(self) -> None:
        self.runsafe(a_run)


if __name__ == '__main__':
    a_run()
