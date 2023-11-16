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

import numpy
import pytest
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector)
from unittests.mocks import MockPopulation
from spynnaker.pyNN.models.neural_projections import SynapseInformation
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.exceptions import SpynnakerException

@pytest.mark.parametrize(
    "weight, delay", [
        (1, 2.0),
        (3.3, 4.4)
        ], ids=[
        "ints",
        "floats"
    ])
def test_good_values(weight, delay):
    unittest_setup()
    connector = OneToOneConnector()
    synapse_info = SynapseInformation(
            connector=None, pre_population=MockPopulation(10, "Pre"),
            post_population=MockPopulation(10, "Post"), prepop_is_view=False,
            postpop_is_view=False, synapse_dynamics=None,
            synapse_type=None, receptor_type=None,
            synapse_type_from_dynamics=False, weights=weight, delays=delay)
    assert delay == connector.get_delay_maximum(synapse_info)
    assert weight == connector.get_weight_maximum(synapse_info)


@pytest.mark.parametrize(
    "weight, delay", [
        ([0, 1, 2, 3], [4, 5, 6, 7]),
        (numpy.array([0, 1, 2, 3]), numpy.array([4, 5, 6, 7])),
        ("foo", "bar"),
        (OneToOneConnector(), MockPopulation(10, "Pre"))
        ], ids=[
        "ints",
        "array",
        "str",
        "weird types"
    ])
def test_bad_values(weight, delay):
    unittest_setup()
    connector = OneToOneConnector()
    synapse_info = SynapseInformation(
            connector=None, pre_population=MockPopulation(10, "Pre"),
            post_population=MockPopulation(10, "Post"), prepop_is_view=False,
            postpop_is_view=False, synapse_dynamics=None,
            synapse_type=None, receptor_type=None,
            synapse_type_from_dynamics=False, weights=weight, delays=delay)
    try:
        connector.get_delay_maximum(synapse_info)
        raise NotImplementedError
    except SpynnakerException:
        pass
    try:
        connector.get_weight_maximum(synapse_info)
        raise NotImplementedError
    except SpynnakerException:
        pass
