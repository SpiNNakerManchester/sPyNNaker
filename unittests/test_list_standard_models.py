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
import pyNN.spiNNaker as sim


class TestListStandardModules(unittest.TestCase):

    # NO unittest_setup() to make sure call works before setup

    def test_check_list(self):
        results = sim.list_standard_models()
        self.assertIn('IF_cond_exp', results)
        self.assertIn('Izhikevich', results)
        self.assertIn('SpikeSourceArray', results)
        self.assertIn('SpikeSourcePoisson', results)
