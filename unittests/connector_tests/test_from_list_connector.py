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
        assert numpy.array_equal(connector.conn_list, expected_clist)
    else:
        assert numpy.array_equal(connector.conn_list, clist)

    # Check extra parameters are as expected
    extra_params = connector.get_extra_parameters()
    extra_param_names = connector.get_extra_parameter_names()
    assert numpy.array_equal(extra_params, expected_extra_parameters)
    assert numpy.array_equal(
        extra_param_names, expected_extra_parameter_names)
    if extra_params is not None:
        assert len(extra_params.shape) == 2
        assert extra_params.shape[1] == len(extra_param_names)
        for i in range(len(extra_param_names)):
            assert extra_params[:, i].shape == (len(clist), )

    # Check weights and delays are used or ignored as expected
    pre_pop = MockPopulation(10, "Pre")
    pre_pop._vertex = MockAppVertex([Slice(0, 9)])
    post_slice = Slice(0, 9)
    synapse_info = SynapseInformation(
            connector=None, pre_population=pre_pop,
            post_population=MockPopulation(10, "Post"), prepop_is_view=False,
            postpop_is_view=False, rng=None, synapse_dynamics=None,
            synapse_type=None, receptor_type=None,
            synapse_type_from_dynamics=False, weights=weights, delays=delays)
    block = connector.create_synaptic_block(
        [post_slice], post_slice, 1, synapse_info)
    assert numpy.array_equal(block["weight"], numpy.array(expected_weights))
    assert numpy.array_equal(block["delay"], numpy.array(expected_delays))


class MockFromListConnector(FromListConnector):
    # Use to check that the split is done only once

    def __init__(self, conn_list, safe=True, verbose=False, column_names=None):
        super().__init__(
            conn_list, safe=safe, verbose=verbose, column_names=column_names)
        self._split_count = 0

    def _split_connections(self, n_atoms, post_slices):
        split = super()._split_connections(n_atoms, post_slices)
        if split:
            self._split_count += 1
        return split


def test_connector_split():
    unittest_setup()
    n_sources = 1000
    n_targets = 1000
    n_connections = 10000
    post_neurons_per_core = 59
    sources = numpy.random.randint(0, n_sources, n_connections)
    targets = numpy.random.randint(0, n_targets, n_connections)
    post_slices = [
        Slice(i, min((i + post_neurons_per_core) - 1, n_targets - 1))
        for i in range(0, n_targets, post_neurons_per_core)]

    connection_list = numpy.dstack((sources, targets))[0]
    connector = MockFromListConnector(connection_list)
    weight = 1.0
    delay = 1.0
    pre_pop = MockPopulation(n_sources, "Pre")
    pre_pop._vertex = MockAppVertex([Slice(0, n_sources - 1)])
    synapse_info = SynapseInformation(
        connector=None, pre_population=pre_pop,
        post_population=MockPopulation(n_targets, "Post"),
        prepop_is_view=False, postpop_is_view=False, rng=None,
        synapse_dynamics=None, synapse_type=None, receptor_type=None,
        synapse_type_from_dynamics=False, weights=weight, delays=delay)
    has_block = set()
    try:
        # Check each connection is in the right place
        for post_slice in post_slices:
            block = connector.create_synaptic_block(
                post_slices, post_slice, 1, synapse_info)
            for target in block["target"]:
                assert post_slice.lo_atom <= target <= post_slice.hi_atom
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

    def __init__(self, slices, app_vertex):
        self.slices = slices
        self.m_vertices = [MockMachineVertex(vertex_slice, app_vertex)
                           for vertex_slice in slices]

    def get_out_going_slices(self):
        return self.slices

    def get_in_coming_slices(self):
        return self.slices

    def get_in_coming_vertices(self, partition_id):
        return self.m_vertices

    def get_out_going_vertices(self, partition_id):
        return self.m_vertices


class MockAppVertex(object):

    def __init__(self, slices):
        self.splitter = MockSplitter(slices, self)


class MockMachineVertex(object):

    def __init__(self, vertex_slice, app_vertex):
        self.vertex_slice = vertex_slice
        self.app_vertex = app_vertex


def test_get_connected():
    unittest_setup()
    pairs = numpy.array([[0, 0], [1, 2], [2, 0], [3, 3], [2, 6], [1, 8],
                         [4, 1], [5, 0], [6, 2], [4, 8]])
    connector = FromListConnector(pairs)
    pre_slices = [Slice(0, 3), Slice(4, 6), Slice(7, 9)]
    post_slices = [Slice(0, 2), Slice(3, 5), Slice(6, 9)]
    pre_vertex = MockAppVertex(pre_slices)
    post_vertex = MockAppVertex(post_slices)
    pre_pop = MockPopulation(10, "Pre")
    post_pop = MockPopulation(10, "Post")
    # pylint: disable=protected-access
    pre_pop._vertex = pre_vertex
    post_pop._vertex = post_vertex
    s_info = SynapseInformation(None, pre_pop, post_pop, False, False, None,
                                None, 1, None, None, 1.0, 1.0)
    connected = connector.get_connected_vertices(
        s_info, pre_vertex, post_vertex)

    for post_vertex, pre_vertices in connected:
        post_slice = post_vertex.vertex_slice
        for pre_vertex in pre_vertices:
            pre_slice = pre_vertex.vertex_slice
            count = __get_n_connections(pairs, pre_slice, post_slice)
            assert count > 0


def __get_n_connections(pairs, pre_slice, post_slice):
    conns = pairs[(pairs[:, 0] >= pre_slice.lo_atom) &
                  (pairs[:, 0] <= pre_slice.hi_atom)]
    conns = conns[(conns[:, 1] >= post_slice.lo_atom) &
                  (conns[:, 1] <= post_slice.hi_atom)]
    return len(conns)
