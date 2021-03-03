# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import spynnaker8 as sim
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
