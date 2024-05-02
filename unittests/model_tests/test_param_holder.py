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

import unittest
from spynnaker.pyNN.models.common import ParameterHolder


def get_mock(parameter, selector):
    if parameter == "foo":
        return [1, 2, 3]
    if parameter == "bar":
        return [4, 5, 6]
    else:
        raise NotImplementedError


class TestParamHolder(unittest.TestCase):

    # NO unittest_setup() to make sure call works before setup

    def test_mulitple_items(self):
        ph = ParameterHolder(["foo", "bar"], get_mock)
        self.assertEqual(2, len(ph))
        self.assertEqual("{'foo': [1, 2, 3], 'bar': [4, 5, 6]}", str(ph))
        self.assertTrue("foo" in ph)
        self.assertFalse(1 in ph)

    def test_sinle_item(self):
        ph = ParameterHolder("foo", get_mock)
        self.assertEqual(3, len(ph))
        self.assertEqual("[1, 2, 3]", str(ph))
        self.assertFalse("foo" in ph)
        self.assertTrue(2 in ph)
