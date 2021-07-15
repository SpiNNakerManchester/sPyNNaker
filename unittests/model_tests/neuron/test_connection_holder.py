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

import math
import pytest
import numpy
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neuron import ConnectionHolder
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamics)


@pytest.fixture(
    scope="module",
    params=[None, [], ["weight"], ["source", "target", "weight", "delay"]],
    ids=["None", "Empty", "SingleItem", "MultiItem"])
def data_items(request):
    return request.param


@pytest.fixture(
    scope="module",
    params=[None, [], [("test", 100)],
            [("test", 100), ("test_2", 200), ("test_3", 300)]],
    ids=["None", "Empty", "SingleValue", "MultiValue"])
def fixed_values(request):
    return request.param


@pytest.fixture(
    scope="module",
    params=[True, False],
    ids=["AsList", "AsMatrix"])
def as_list(request):
    return request.param


def test_connection_holder(data_items, fixed_values, as_list):
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
        AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE)
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
                for j, item in enumerate(test_data_items):

                    item_index = connections.dtype.names.index(item)

                    # Check that the value matches with the correct field value
                    if n_items == 1:
                        assert connection_holder[i] == \
                            connections[i][item_index]
                    else:
                        assert connection_holder[i][j] == \
                            connections[i][item_index]

            if fixed_values is not None:
                for j, item in enumerate(fixed_values):
                    if n_items == 1:
                        assert connection_holder[i] == item[1]
                    else:
                        assert connection_holder[i][p + j] == item[1]

    else:

        if n_items == 0:
            assert len(connection_holder) == 0
        else:

            # Should have n_items matrices returned, each of which is a 2x2
            # matrix
            if n_items == 1:
                assert len(connection_holder) == 2
                assert len(connection_holder[0]) == 2
                assert len(connection_holder[1]) == 2
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
                for j, item in enumerate(test_data_items):

                    # Check that the value matches with the correct field value
                    item_index = connections.dtype.names.index(item)
                    if n_items == 1:
                        matrix = connection_holder
                    else:
                        matrix = connection_holder[j]

                    assert matrix[0, 0] == connections[1][item_index]
                    assert matrix[0, 1] == connections[2][item_index]
                    assert math.isnan(matrix[1, 0])
                    assert math.isnan(matrix[1, 1])

            if fixed_values is not None:
                for j, item in enumerate(fixed_values):
                    if n_items == 1:
                        matrix = connection_holder
                    else:
                        matrix = connection_holder[j + p]
                    assert matrix[0, 0] == item[1]
                    assert matrix[0, 1] == item[1]
                    assert math.isnan(matrix[1, 0])
                    assert math.isnan(matrix[1, 1])


def test_connection_holder_matrix_multiple_items():
    unittest_setup()
    data_items = ["source", "target", "delay", "weight"]
    connection_holder = ConnectionHolder(
        data_items_to_return=data_items,
        as_list=False, n_pre_atoms=2, n_post_atoms=2)
    connections = numpy.array(
        [(0, 0, 1, 10), (0, 0, 2, 20), (0, 1, 3, 30)],
        AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE)
    connection_holder.add_connections(connections)
