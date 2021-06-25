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

import spynnaker8 as p
from spinnaker_testbase import BaseTestCase


class TestNoVertices(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    @staticmethod
    def test_run():
        p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
        p.run(100)

        p.end()


if __name__ == '__main__':
    TestNoVertices.test_run()
