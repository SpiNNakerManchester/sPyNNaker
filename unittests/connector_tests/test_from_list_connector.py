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

import numpy
import pytest
from pacman.model.graphs.common.slice import Slice
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neural_projections.connectors import (
    FromListConnector)
from spynnaker.pyNN.models.neural_projections import SynapseInformation
from unittests.mocks import MockPopulation


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
    unittest_setup()
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
    synapse_info = SynapseInformation(
            connector=None, pre_population=MockPopulation(10, "Pre"),
            post_population=MockPopulation(10, "Post"), prepop_is_view=False,
            postpop_is_view=False, rng=None, synapse_dynamics=None,
            synapse_type=None, receptor_type=None,
            synapse_type_from_dynamics=False, weights=weights, delays=delays)
    block = connector.create_synaptic_block(
        [pre_slice], [post_slice], pre_slice, post_slice, 1, synapse_info)
    assert(numpy.array_equal(block["weight"], numpy.array(expected_weights)))
    assert(numpy.array_equal(block["delay"], numpy.array(expected_delays)))


class MockFromListConnector(FromListConnector):
    # Use to check that the split is done only once

    def __init__(self, conn_list, safe=True, verbose=False, column_names=None):
        super().__init__(
            conn_list, safe=safe, verbose=verbose, column_names=column_names)
        self._split_count = 0

    def _split_connections(self, pre_slices, post_slices):
        split = super()._split_connections(pre_slices, post_slices)
        if split:
            self._split_count += 1
        return split


def test_connector_split():
    unittest_setup()
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
    synapse_info = SynapseInformation(
        connector=None, pre_population=MockPopulation(n_sources, "Pre"),
        post_population=MockPopulation(n_targets, "Post"),
        prepop_is_view=False, postpop_is_view=False, rng=None,
        synapse_dynamics=None, synapse_type=None, receptor_type=None,
        synapse_type_from_dynamics=False, weights=weight, delays=delay)
    has_block = set()
    try:
        # Check each connection is in the right place
        for pre_slice in pre_slices:
            for post_slice in post_slices:
                block = connector.create_synaptic_block(
                    pre_slices, post_slices, pre_slice, post_slice, 1,
                    synapse_info)
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
    except AssertionError as e:
        print(connection_list)
        raise e


class MockSplitter(object):

    def __init__(self, slices):
        self.slices = slices

    def get_out_going_slices(self):
        return (self.slices, True)

    def get_in_coming_slices(self):
        return (self.slices, True)


class MockAppVertex(object):

    def __init__(self, slices):
        self.splitter = MockSplitter(slices)


class MockMachineVertex(object):

    def __init__(self, slice, slices):
        self.vertex_slice = slice
        self.app_vertex = MockAppVertex(slices)


def test_could_connect():
    unittest_setup()
    connector = FromListConnector(
        [[0, 0], [1, 2], [2, 0], [3, 3], [2, 6], [1, 8], [4, 1], [5, 0],
         [6, 2], [4, 8]])
    pre_slices = [Slice(0, 3), Slice(4, 6), Slice(7, 9)]
    post_slices = [Slice(0, 2), Slice(3, 5), Slice(6, 9)]
    for pre_slice in pre_slices:
        pre_vertex = MockMachineVertex(pre_slice, pre_slices)
        for post_slice in post_slices:
            post_vertex = MockMachineVertex(post_slice, post_slices)
            count = connector.get_n_connections(
                pre_slices, post_slices, pre_slice.hi_atom,
                post_slice.hi_atom)
            if count:
                assert(connector.could_connect(None, pre_vertex, post_vertex))
            else:
                assert(not connector.could_connect(
                    None, pre_vertex, post_vertex))
