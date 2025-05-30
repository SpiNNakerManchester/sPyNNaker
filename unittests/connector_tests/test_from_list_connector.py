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

from typing import Iterable, List, Optional, Sequence

import numpy
from numpy.typing import NDArray
import pytest

from spinn_utilities.overrides import overrides

from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.common.slice import Slice
from pacman.model.graphs.machine import SimpleMachineVertex, MachineVertex
from pacman.model.partitioner_splitters import AbstractSplitterCommon
from pacman.utilities.utility_objs import ChipCounter

from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neural_projections.connectors import (
    FromListConnector)
from spynnaker.pyNN.models.neural_projections import SynapseInformation
from unittests.mocks import (
    MockConnector, MockPopulation, MockSynapseDynamics, MockVertex)


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
        clist: Optional[NDArray], column_names: Optional[List[str]],
        weights: int, delays: int, expected_clist: Optional[NDArray],
        expected_weights: List[int], expected_delays: List[int],
        expected_extra_parameters: Optional[NDArray],
        expected_extra_parameter_names: Optional[List[str]]) -> None:
    unittest_setup()
    connector = FromListConnector(clist, column_names=column_names)
    if expected_clist is not None:
        assert numpy.array_equal(connector.conn_list, expected_clist)
    else:
        assert numpy.array_equal(
            connector.conn_list, clist)  # type: ignore[arg-type]

    # Check extra parameters are as expected
    extra_params = connector.get_extra_parameters()
    extra_param_names = connector.get_extra_parameter_names()
    assert numpy.array_equal(
        extra_params, expected_extra_parameters)  # type: ignore[arg-type]
    assert numpy.array_equal(
        extra_param_names,  # type: ignore[arg-type]
        expected_extra_parameter_names)   # type: ignore[arg-type]
    if extra_params is not None:
        assert len(extra_params.shape) == 2
        assert extra_param_names is not None
        assert extra_params.shape[1] == len(extra_param_names)
        assert clist is not None
        for i in range(len(extra_param_names)):
            assert extra_params[:, i].shape == (len(clist), )

    # Check weights and delays are used or ignored as expected
    pre_pop = MockPopulation(10, "Pre", MockAppVertex(10, [Slice(0, 9)]))
    post_slice = Slice(0, 9)
    synapse_info = SynapseInformation(
            connector=MockConnector(), pre_population=pre_pop,
            post_population=MockPopulation(10, "Post"), prepop_is_view=False,
            postpop_is_view=False, synapse_dynamics=MockSynapseDynamics(1, 1),
            synapse_type=1, receptor_type="bacon",
            synapse_type_from_dynamics=False, weights=weights, delays=delays)
    block = connector.create_synaptic_block(
        [post_slice], post_slice, 1, synapse_info)
    assert numpy.array_equal(block["weight"], numpy.array(expected_weights))
    assert numpy.array_equal(block["delay"], numpy.array(expected_delays))


def test_connector_split() -> None:
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
    connector = FromListConnector(connection_list)
    weight = 1.0
    delay = 1.0
    pre_pop = MockPopulation(
        n_sources, "Pre", MockAppVertex(n_sources, [Slice(0, n_sources - 1)]))
    synapse_info = SynapseInformation(
        connector=MockConnector(), pre_population=pre_pop,
        post_population=MockPopulation(n_targets, "Post"),
        prepop_is_view=False, postpop_is_view=False,
        synapse_dynamics=MockSynapseDynamics(1, 1), synapse_type=1,
        receptor_type="bacon", synapse_type_from_dynamics=False,
        weights=weight, delays=delay)
    has_block = set()
    try:
        # Check each connection is in the right place
        for post_slice in post_slices:
            block = connector.create_synaptic_block(
                post_slices, post_slice, 1, synapse_info)
            for target in block["target"]:
                # The target should be one of the post-vertex-indexed atoms
                assert 0 <= target <= post_slice.n_atoms
            for item in block:
                has_block.add((
                    item["source"],
                    post_slice.get_raster_indices(
                        numpy.array([item["target"]]))[0]))

        # Check each connection has a place
        for source, target in zip(sources, targets):
            assert (source, target) in has_block
    except AssertionError as e:
        print(connection_list)
        raise e


class MockSplitter(AbstractSplitterCommon):

    def __init__(self, slices: List[Slice], app_vertex: ApplicationVertex):
        super().__init__()
        self.slices = slices
        self.m_vertices = [SimpleMachineVertex(
            None, app_vertex=app_vertex, vertex_slice=vertex_slice)
            for vertex_slice in slices]

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> Sequence[Slice]:
        return self.slices

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> Sequence[Slice]:
        return self.slices

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        return self.m_vertices

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        return self.m_vertices

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter) -> None:
        raise NotImplementedError

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> Iterable[MachineVertex]:
        raise NotImplementedError

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        raise NotImplementedError


class MockAppVertex(MockVertex):

    def __init__(self, n_atoms: int, slices: List[Slice]):
        super().__init__(splitter=MockSplitter(slices, self))
        self._n_atoms = n_atoms

    @overrides(ApplicationVertex.get_key_ordered_indices)
    def get_key_ordered_indices(
            self, indices: Optional[numpy.ndarray] = None) -> numpy.ndarray:
        if indices is None:
            indices = numpy.arange(self.n_atoms)
        # All of them are 1D so this is good enough
        return indices

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self) -> int:
        return self._n_atoms


def test_get_connected() -> None:
    unittest_setup()
    pairs = numpy.array([[0, 0], [1, 2], [2, 0], [3, 3], [2, 6], [1, 8],
                         [4, 1], [5, 0], [6, 2], [4, 8]])
    connector = FromListConnector(pairs)
    pre_slices = [Slice(0, 3), Slice(4, 6), Slice(7, 9)]
    post_slices = [Slice(0, 2), Slice(3, 5), Slice(6, 9)]
    pre_app_vertex = MockAppVertex(10, pre_slices)
    post_app_vertex = MockAppVertex(10, post_slices)
    pre_pop = MockPopulation(10, "Pre", pre_app_vertex)
    post_pop = MockPopulation(10, "Post", post_app_vertex)
    s_info = SynapseInformation(
        MockConnector(), pre_pop, post_pop, False, False,
        MockSynapseDynamics(1, 1), 1, "bacon", False, 1.0, 1.0)
    connected = connector.get_connected_vertices(
        s_info, pre_app_vertex, post_app_vertex)

    for post_vertex, pre_vertices in connected:
        post_slice = post_vertex.vertex_slice
        for pre_mac_vertex in pre_vertices:
            assert isinstance(pre_mac_vertex, MachineVertex)
            pre_slice = pre_mac_vertex.vertex_slice
            count = __get_n_connections(pairs, pre_slice, post_slice)
            assert count > 0


def __get_n_connections(pairs: NDArray, pre_slice: Slice,
                        post_slice: Slice) -> int:
    conns = pairs[(pairs[:, 0] >= pre_slice.lo_atom) &
                  (pairs[:, 0] <= pre_slice.hi_atom)]
    conns = conns[(conns[:, 1] >= post_slice.lo_atom) &
                  (conns[:, 1] <= post_slice.hi_atom)]
    return len(conns)
