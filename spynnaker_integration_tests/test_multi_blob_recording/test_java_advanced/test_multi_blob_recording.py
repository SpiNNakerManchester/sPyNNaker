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


class TestMultiBlobRecording(BaseTestCase):
    """ This test checks that the database holding the recording buffers will \
    handle multiple BLOBs for a recording channel correctly.
    """

    def test_multi_blob_recording(self):
        timespan = 100
        size = 255
        n_runs = 5

        sim.setup(1.0)
        pop = sim.Population(size, sim.IF_curr_exp(), label="neuron")
        pop.record("v")
        sim.run(timespan)
        # rabbit
        sim.run(timespan)
        # rabbit
        sim.run(timespan)
        sim.run(timespan)
        sim.run(timespan)
        v = pop.spinnaker_get_data("v")
        self.assertEqual(timespan * size * n_runs, len(v))
        sim.end()


if __name__ == "__main__":
    obj = TestMultiBlobRecording()
    obj.test_multi_blob_recording()
