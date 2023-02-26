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

import unittest
import spinn_utilities
import spinn_machine
import data_specification
import pacman
import spinnman
import spinn_front_end_common
import spynnaker


class Test(unittest.TestCase):
    """ Tests for the SCAMP version comparison
    """

    # No unittest_setup to verify calls work before setup

    def test_compare_versions(self):
        spinn_utilities_parts = spinn_utilities.__version__.split('.')
        spinn_machine_parts = spinn_machine.__version__.split('.')
        data_specification_parts = data_specification.__version__.split('.')
        pacman_parts = pacman.__version__.split('.')
        spinnman_parts = spinnman.__version__.split('.')
        spinn_front_end_common_parts = spinn_front_end_common.__version__\
            .split('.')
        spynnaker_parts = spynnaker.__version__.split('.')

        self.assertEqual(spinn_utilities_parts[0],
                         spynnaker_parts[0])
        self.assertLessEqual(spinn_utilities_parts[1],
                             spynnaker_parts[1])

        self.assertEqual(spinn_machine_parts[0],
                         spynnaker_parts[0])
        self.assertLessEqual(spinn_machine_parts[1],
                             spynnaker_parts[1])

        self.assertEqual(data_specification_parts[0],
                         spynnaker_parts[0])
        self.assertLessEqual(data_specification_parts[1],
                             spynnaker_parts[1])

        self.assertEqual(pacman_parts[0],
                         spynnaker_parts[0])
        self.assertLessEqual(pacman_parts[1],
                             spynnaker_parts[1])

        self.assertEqual(spinnman_parts[0],
                         spynnaker_parts[0])
        self.assertLessEqual(spinnman_parts[1],
                             spynnaker_parts[1])

        self.assertEqual(spinn_front_end_common_parts[0],
                         spynnaker_parts[0])
        self.assertLessEqual(spinn_front_end_common_parts[1],
                             spynnaker_parts[1])
