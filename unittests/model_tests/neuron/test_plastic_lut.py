# Copyright (c) 2017-2019 The University of Manchester
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

import numpy
import unittest
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
    write_mfvn_lut, write_pfpc_lut)


class TestPlasticLUT(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_plastic_mfvn_lut(self):
        t_mfvn, out_float_mfvn, _plot_times = write_mfvn_lut(
            spec=None, sigma=200, beta=10, lut_size=256, shift=0,
            time_probe=22)

        t_compare = [15, 20, 30, 35, 45, 47, 99, 115, 135, 140, 150]
        mfvn_float = [0.4697, 0.3642, 0.2181, 0.1685, 0.1002, 0.0902, 0.0055,
                      0.0022, 0.0007, 0.0005, 0.0003]
        print(t_mfvn, out_float_mfvn[t_mfvn], mfvn_float)
        assert list(t_mfvn) == t_compare
        self.assertTrue(numpy.allclose(out_float_mfvn[t_mfvn], mfvn_float,
                                       atol=0.0001))

    def test_plastic_pfpc_lut(self):
        t_pfpc, out_float_pfpc, out_fixed_pfpc, _plot_times = write_pfpc_lut(
            spec=None, peak_time=100, lut_size=256, shift=0, time_probe=100)

        t_compare = [15, 20, 30, 35, 45, 47, 99, 115, 135, 140, 150]
        pfpc_fixed = [0, 0, 0, 0, 1, 1, 2043, 1215, 109, 42, 4]
        pfpc_float = [0.0, 0.0, 0.0, 0.0, 0.0002, 0.0005,
                      0.9977, 0.5932, 0.0534, 0.0207, 0.0019]
        print(t_pfpc, out_float_pfpc[t_pfpc], out_fixed_pfpc[t_pfpc])
        assert list(t_pfpc) == t_compare
        assert list(out_fixed_pfpc[t_pfpc]) == pfpc_fixed
        self.assertTrue(numpy.allclose(out_float_pfpc[t_pfpc], pfpc_float,
                                       atol=0.0001))
