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


class TestNoVertices(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    @staticmethod
    def test_run() -> None:
        p.setup(timestep=1.0, min_delay=1.0)
        p.run(100)

        p.end()


if __name__ == '__main__':
    TestNoVertices.test_run()
