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

import unittest
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neuron.builds.if_cond_exp_base import IFCondExpBase
import spynnaker8 as p


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
