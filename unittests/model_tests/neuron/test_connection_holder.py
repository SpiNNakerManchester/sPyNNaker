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

import math
import pytest
import numpy
from typing import Any, List, Optional, Tuple

from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neuron import ConnectionHolder
from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
    NUMPY_CONNECTORS_DTYPE)


@pytest.fixture(
    scope="module",
    params=[None, [], ["weight"], ["source", "target", "weight", "delay"]],
    ids=["None", "Empty", "SingleItem", "MultiItem"])
def data_items(request: Any) -> Optional[List[str]]:
    return request.param


@pytest.fixture(
    scope="module",
    params=[None, [], [("test", 100)],
            [("test", 100), ("test_2", 200), ("test_3", 300)]],
    ids=["None", "Empty", "SingleValue", "MultiValue"])
def fixed_values(request: Any) -> Optional[List[Tuple[str, int]]]:
    return request.param


@pytest.fixture(
    scope="module",
    params=[True, False],
    ids=["AsList", "AsMatrix"])
def as_list(request: Any) -> bool:
    return request.param


def test_connection_holder(
        data_items: Optional[List[str]],
        fixed_values: Optional[List[Tuple[str, int]]], as_list: bool) -> None:
    unittest_setup()
    all_values = None
    n_items = 0
    if data_items is not None or fixed_values is not None:
        all_values = list()
    elif as_list:
        n_items = 4
    if data_items is not None:
        all_values.extend(data_items)
        n_items += len(data_items)
    if fixed_values is not None:
        all_values.extend([item[0] for item in fixed_values])
        n_items += len(fixed_values)
    test_data_items = data_items
    if test_data_items is None and fixed_values is None:
        test_data_items = ["source", "target", "weight", "delay"]

    connection_holder = ConnectionHolder(
        data_items_to_return=all_values, as_list=as_list, n_pre_atoms=2,
        n_post_atoms=2, fixed_values=fixed_values)
    connections = numpy.array(
        [(0, 0, 1, 10), (0, 0, 2, 20), (0, 1, 3, 30)],
        NUMPY_CONNECTORS_DTYPE)
    connection_holder.add_connections(connections)

    if as_list:

        # Just a list so should be the same length as connections
        assert len(connection_holder) == len(connections)

        # Check that the selected item values are correct
        for i in range(len(connections)):

            # Go through each of the selected fields
            p = 0
            if test_data_items is not None:
                p = len(test_data_items)
                for j, item_d in enumerate(test_data_items):

                    names = connections.dtype.names
                    assert names is not None
                    item_index = names.index(item_d)

                    chi = connection_holder[i]
                    # Check that the value matches with the correct field value
                    if n_items == 1:
                        assert chi == connections[i][item_index]
                    else:
                        assert isinstance(chi, list)
                        assert chi[j] == connections[i][item_index]

            if fixed_values is not None:
                for j, item_f in enumerate(fixed_values):
                    if n_items == 1:
                        assert connection_holder[i] == item_f[1]
                    else:
                        chi = connection_holder[i]
                        assert isinstance(chi, list)
                        assert chi[p + j] == item_f[1]

    else:

        if n_items == 0:
            assert len(connection_holder) == 0
        else:

            # Should have n_items matrices returned, each of which is a 2x2
            # matrix
            if n_items == 1:
                assert len(connection_holder) == 2
                ch0 = connection_holder[0]
                assert isinstance(ch0, numpy.ndarray)
                assert len(ch0) == 2
                ch1 = connection_holder[1]
                assert isinstance(ch1, numpy.ndarray)
                assert len(ch1) == 2
            else:
                assert len(connection_holder) == n_items
                for matrix in connection_holder:
                    assert len(matrix) == 2
                    assert len(matrix[0]) == 2
                    assert len(matrix[1]) == 2

            # Should have the values in the appropriate places
            # Go through each of the selected fields
            p = 0
            if test_data_items is not None:
                p = len(test_data_items)
                for j, item_d in enumerate(test_data_items):

                    # Check that the value matches with the correct field value
                    names = connections.dtype.names
                    assert names is not None
                    item_index = names.index(item_d)
                    if n_items == 1:
                        matrix = connection_holder
                    else:
                        matrix = connection_holder[j]

                    assert matrix[0, 0] == connections[1][item_index]
                    assert matrix[0, 1] == connections[2][item_index]
                    assert math.isnan(matrix[1, 0])
                    assert math.isnan(matrix[1, 1])

            if fixed_values is not None:
                for j, item_f in enumerate(fixed_values):
                    if n_items == 1:
                        matrix = connection_holder
                    else:
                        matrix = connection_holder[j + p]
                    assert matrix[0, 0] == item_f[1]
                    assert matrix[0, 1] == item_f[1]
                    assert math.isnan(matrix[1, 0])
                    assert math.isnan(matrix[1, 1])


def test_connection_holder_matrix_multiple_items() -> None:
    unittest_setup()
    data_items_to_return = ["source", "target", "delay", "weight"]
    connection_holder = ConnectionHolder(
        data_items_to_return=data_items_to_return,
        as_list=False, n_pre_atoms=2, n_post_atoms=2)
    connections = numpy.array(
        [(0, 0, 1, 10), (0, 0, 2, 20), (0, 1, 3, 30)],
        NUMPY_CONNECTORS_DTYPE)
    connection_holder.add_connections(connections)
