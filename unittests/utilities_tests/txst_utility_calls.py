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

import os
import shutil
import unittest
from pyNN.random import RandomDistribution
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.utilities import utility_calls


class TestUtilityCalls(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_check_directory_exists(self):
        utility_calls.check_directory_exists_and_create_if_not(os.path.dirname(
            os.path.realpath(__file__)))
        self.assertTrue(os.path.exists(os.path.dirname(
            os.path.realpath(__file__))))

    def test_check_directory_not_exists(self):
        test_dir = os.path.join(os.path.dirname(__file__),
                                "test_utility_call")
        test_file = os.path.join(test_dir, "test")
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print("Directory existed. Deleting...")

        utility_calls.check_directory_exists_and_create_if_not(test_file)

        if not os.path.exists(test_dir):
            raise AssertionError("Directory was not created")
        print("Directory created successfully. Deleting...")
        os.rmdir(test_dir)

    def test_convert_param_to_numpy_random_distribution(self):
        random = RandomDistribution("uniform", [0, 1])
        single_value = utility_calls.convert_param_to_numpy(random, 1)
        multi_value = utility_calls.convert_param_to_numpy(random, 10)

        self.assertTrue(hasattr(single_value, "__iter__"))
        self.assertEqual(len(single_value), 1)
        self.assertTrue(hasattr(multi_value, "__iter__"))
        self.assertEqual(len(multi_value), 10)


if __name__ == '__main__':
    unittest.main()
