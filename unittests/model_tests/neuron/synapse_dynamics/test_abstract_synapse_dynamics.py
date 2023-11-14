# Copyright (c) 2023 The University of Manchester
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

from numpy import float64, ndarray
from numpy.typing import NDArray
from pyNN.random import RandomDistribution
import unittest
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic)


class TestAbstractSynapseDynamics(unittest.TestCase):

    # Note these tests use SynapseDynamicsStatic because it is the simplist
    # Just because it is used here does not indicate that all types are
    # by it let alone in all use case

    def setUp(self):
        unittest_setup()

    def test_int(self):
        synapse = SynapseDynamicsStatic(delay=1, weight=2)
        self.assertEqual(float64, type(synapse.delay))
        self.assertEqual(int, type(synapse.weight))

    def test_float(self):
        synapse = SynapseDynamicsStatic(delay=1.1, weight=2.2)
        self.assertEqual(float64, type(synapse.delay))
        self.assertEqual(float, type(synapse.weight))

    def test_str(self):
        # Only some (distance) Connectors support str
        # And of course not foo and bar
        synapse = SynapseDynamicsStatic(delay="foo", weight="bar")
        self.assertEqual(str, type(synapse.delay))
        self.assertEqual(str, type(synapse.weight))

    def test_random(self):
        # Only some connectors support Random
        rng = RandomDistribution('uniform', (-70, -50))
        synapse = SynapseDynamicsStatic(delay=rng, weight=rng)
        self.assertEqual(RandomDistribution, type(synapse.delay))
        self.assertEqual(RandomDistribution, type(synapse.weight))

    def test_int_list(self):
        # Only some connectors support list
        synapse = SynapseDynamicsStatic(delay=[1, 2, 3], weight=[4, 5, 6])
        delay = synapse.delay
        self.assertEqual(ndarray, type(delay))
        for d in delay:
            self.assertEqual(float64, type(d))
        weight = synapse.weight
        self.assertEqual(list, type(weight))
        for w in weight:
            self.assertEqual(int, type(w))

    def test_float_list(self):
        # Only some connectors support list
        synapse = SynapseDynamicsStatic(
            delay=[1.1, 2.2, 3.3], weight=[4.4, 5.5, 6.6])
        delay = synapse.delay
        self.assertEqual(ndarray, type(delay))
        for d in delay:
            self.assertEqual(float64, type(d))
        weight = synapse.weight
        self.assertEqual(list, type(weight))
        for w in weight:
            self.assertEqual(float, type(w))

    def test_delay_none(self):
        synapse = SynapseDynamicsStatic(delay=None, weight=2)
        self.assertEqual(float64, type(synapse.delay))
        self.assertEqual(int, type(synapse.weight))

    def test_weight_none(self):
        with self.assertRaises(TypeError):
            SynapseDynamicsStatic(delay=1, weight=None)

    def test_bad_type(self):
        with self.assertRaises(TypeError):
            SynapseDynamicsStatic(delay=1, weight=None)
