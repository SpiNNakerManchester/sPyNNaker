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
