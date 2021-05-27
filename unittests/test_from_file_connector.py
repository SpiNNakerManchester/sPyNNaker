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

import tempfile
import numpy
import pytest
from pacman.model.graphs.common.slice import Slice
from spynnaker.pyNN.models.neural_projections.connectors import (
    FromFileConnector)
from unittests.mocks import MockSynapseInfo, MockPopulation
import spynnaker8


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
    spynnaker8.setup()
    temp = tempfile.NamedTemporaryFile(delete=False)
    with temp as f:
        header = ''
        if column_names is not None:
            columns = ["i", "j"]
            columns.extend(column_names)
            header = 'columns = {}'.format(columns)
        if clist is not None and len(clist):
            numpy.savetxt(f, clist, header=header)
        elif len(header):
            f.write("# {}\n".format(header))

    connector = FromFileConnector(temp.name)
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
        [pre_slice], [post_slice], pre_slice, post_slice, 1, mock_synapse_info)
    assert(numpy.array_equal(block["weight"], numpy.array(expected_weights)))
    assert(numpy.array_equal(block["delay"], numpy.array(expected_delays)))
