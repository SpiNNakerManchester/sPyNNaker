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

import tempfile
from typing import Optional, List

import numpy
from numpy.typing import NDArray
import pytest
import pyNN.spiNNaker as sim

from pacman.model.graphs.common.slice import Slice

from spynnaker.pyNN.models.neural_projections.connectors import (
    FromFileConnector)
from spynnaker.pyNN.models.neural_projections import SynapseInformation
from unittests.connector_tests.test_from_list_connector import MockAppVertex
from unittests.mocks import MockSynapseDynamics, MockPopulation

# NO unittest_setup() as sim.setup is called


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
        clist:Optional[NDArray], column_names: Optional[List[str]],
        weights: int, delays: int, expected_clist: Optional[NDArray],
        expected_weights: List[int], expected_delays: List[int],
        expected_extra_parameters: Optional[NDArray],
        expected_extra_parameter_names: Optional[List[str]]) -> None:
    sim.setup()
    temp = tempfile.NamedTemporaryFile(delete=False)
    with temp as f:
        header = ''
        if column_names is not None:
            columns = ["i", "j"]
            columns.extend(column_names)
            header = 'columns = {}'.format(columns)
        if clist is not None and len(clist):
            numpy.savetxt(f, clist, header=header)
        else:
            assert len(header) == 0

    connector = FromFileConnector(temp.name)
    if expected_clist is not None:
        assert numpy.array_equal(connector.conn_list, expected_clist)
    else:
        assert numpy.array_equal(
            connector.conn_list, clist)  # type: ignore[arg-type]

    # Check extra parameters are as expected
    extra_params = connector.get_extra_parameters()
    extra_param_names = connector.get_extra_parameter_names()
    if extra_params is not None:
        assert len(extra_params.shape) == 2
        assert extra_param_names is not None
        assert extra_params.shape[1] == len(extra_param_names)
        for i in range(len(extra_param_names)):
            assert clist is not None
            assert extra_params[:, i].shape == (len(clist), )

    # Check weights and delays are used or ignored as expected
    pre_slice = Slice(0, 9)
    pre_pop = MockPopulation(10, "Pre", MockAppVertex(10, [pre_slice]))
    post_slice = Slice(0, 9)
    synapse_info = SynapseInformation(
        connector=connector, pre_population=pre_pop,
        post_population=MockPopulation(10, "Post"), prepop_is_view=False,
        postpop_is_view=False, synapse_dynamics=MockSynapseDynamics(1,1),
        synapse_type=0, receptor_type="",
        synapse_type_from_dynamics=False, weights=weights, delays=delays)
    block = connector.create_synaptic_block(
        [post_slice], post_slice, 1, synapse_info)
    assert numpy.array_equal(block["weight"], numpy.array(expected_weights))
    assert numpy.array_equal(block["delay"], numpy.array(expected_delays))
