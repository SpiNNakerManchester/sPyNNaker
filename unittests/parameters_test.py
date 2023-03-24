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
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neuron.builds.if_cond_exp_base import IFCondExpBase
import pyNN.spiNNaker as p


class TestParameters(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_class_default_parameters(self):
        self.assertEqual(IFCondExpBase.default_parameters,
                         p.IF_cond_exp.default_parameters)

    def test_module_default_parameters(self):
        module = p.IF_cond_exp()
        self.assertEqual(IFCondExpBase.default_parameters,
                         module.default_parameters)

    def test_class_get_parameter_names(self):
        self.assertEqual(IFCondExpBase.default_parameters.keys(),
                         p.IF_cond_exp.get_parameter_names())

    def test_module_get_parameter_names(self):
        module = p.IF_cond_exp()
        self.assertEqual(IFCondExpBase.default_parameters.keys(),
                         module.get_parameter_names())
