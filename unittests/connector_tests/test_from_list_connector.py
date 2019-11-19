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

from spynnaker.pyNN.models.neural_projections.connectors import (
    FromListConnector)
import numpy
import pytest
from pacman.model.graphs.common.slice import Slice
from unittests.mocks import MockSimulator, MockSynapseInfo, MockPopulation
from six import reraise
import sys


@pytest.mark.parametrize(
    "clist, column_names, weights, delays, expected_clist, expected_weights, "
    "expected_delays, expected_extra_parameters, "
    "expected_extra_parameter_names", [
        (None, None, 0, 0, numpy.zeros((0, 2)), [], [], None, None),
        ([], None, 0, 0, numpy.zeros((0, 2)), [], [], None, None),
        (numpy.array([(0, 0, 0, 0), (1, 1, 1, 1), (2, 2, 2, 2)]), None, 5, 1,
         None, [0, 1, 2], [0, 1, 2], None, None),
        (numpy.array([(0, 0), (1, 1), (2, 2)]), None, 5, 1,
         None, [5, 5, 5], [1, 1, 1], None, None),
        (numpy.array([(0, 0, 0), (1, 1, 1), (2, 2, 2)]), ["weight"], 5, 1,
         None, [0, 1, 2], [1, 1, 1], None, None),
        (numpy.array([(0, 0, 0), (1, 1, 1), (2, 2, 2)]), ["delay"], 5, 1,
         None, [5, 5, 5], [0, 1, 2], None, None),
        (numpy.array([(0, 0, 0), (1, 1, 0), (2, 2, 0)]), ["extra"], 5, 1,
         None, [5, 5, 5], [1, 1, 1], numpy.array([[0], [0], [0]]), ["extra"]),
    ], ids=[
        "None Connections",
        "Empty Connections",
        "4-elements",
        "2-elements",
        "3-elements-weight",
        "3-elements-delay",
        "3-elements-extra"
    ])
def test_connector(
        clist, column_names, weights, delays, expected_clist, expected_weights,
        expected_delays, expected_extra_parameters,
        expected_extra_parameter_names):
    MockSimulator.setup()
    connector = FromListConnector(clist, column_names=column_names)
    if expected_clist is not None:
        assert(numpy.array_equal(connector.conn_list, expected_clist))
    else:
        assert(numpy.array_equal(connector.conn_list, clist))

    # Check extra parameters are as expected
    extra_params = connector.get_extra_parameters()
    extra_param_names = connector.get_extra_parameter_names()
    assert(numpy.array_equal(extra_params, expected_extra_parameters))
    assert(numpy.array_equal(
        extra_param_names, expected_extra_parameter_names))
    if extra_params is not None:
        assert(len(extra_params.shape) == 2)
        assert(extra_params.shape[1] == len(extra_param_names))
        for i in range(len(extra_param_names)):
            assert(extra_params[:, i].shape == (len(clist), ))

    # Check weights and delays are used or ignored as expected
    pre_slice = Slice(0, 10)
    post_slice = Slice(0, 10)
    mock_synapse_info = MockSynapseInfo(MockPopulation(10, "Pre"),
                                        MockPopulation(10, "Post"),
                                        weights, delays)
    block = connector.create_synaptic_block(
        [pre_slice], 0, [post_slice], 0,
        pre_slice, post_slice, 1, mock_synapse_info)
    assert(numpy.array_equal(block["weight"], numpy.array(expected_weights)))
    assert(numpy.array_equal(block["delay"], numpy.array(expected_delays)))


class MockFromListConnector(FromListConnector):
    # Use to check that the split is done only once

    def __init__(self, conn_list, safe=True, verbose=False, column_names=None):
        FromListConnector.__init__(
            self, conn_list, safe=safe, verbose=verbose,
            column_names=column_names)
        self._split_count = 0

    def _split_connections(self, pre_slices, post_slices):
        split = FromListConnector._split_connections(
            self, pre_slices, post_slices)
        if split:
            self._split_count += 1


def test_connector_split():
    MockSimulator.setup()
    n_sources = 1000
    n_targets = 1000
    n_connections = 10000
    pre_neurons_per_core = 57
    post_neurons_per_core = 59
    sources = numpy.random.randint(0, n_sources, n_connections)
    targets = numpy.random.randint(0, n_targets, n_connections)
    pre_slices = [Slice(i, i + pre_neurons_per_core - 1)
                  for i in range(0, n_sources, pre_neurons_per_core)]
    post_slices = [Slice(i, i + post_neurons_per_core - 1)
                   for i in range(0, n_targets, post_neurons_per_core)]

    connection_list = numpy.dstack((sources, targets))[0]
    connector = MockFromListConnector(connection_list)
    weight = 1.0
    delay = 1.0
    mock_synapse_info = MockSynapseInfo(MockPopulation(n_sources, "Pre"),
                                        MockPopulation(n_targets, "Post"),
                                        weight, delay)
    has_block = set()
    try:
        # Check each connection is in the right place
        for i, pre_slice in enumerate(pre_slices):
            for j, post_slice in enumerate(post_slices):
                block = connector.create_synaptic_block(
                    pre_slices, i, post_slices, j,
                    pre_slice, post_slice, 1, mock_synapse_info)
                for source in block["source"]:
                    assert(pre_slice.lo_atom <= source <= pre_slice.hi_atom)
                for target in block["target"]:
                    assert(post_slice.lo_atom <= target <= post_slice.hi_atom)
                for item in block:
                    has_block.add((item["source"], item["target"]))

        # Check each connection has a place
        for source, target in zip(sources, targets):
            assert (source, target) in has_block

        # Check the split only happens once
        assert connector._split_count == 1
    except AssertionError:
        print(connection_list)
        reraise(*sys.exc_info())
