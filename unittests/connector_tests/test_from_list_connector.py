from spynnaker.pyNN.models.neural_projections.connectors import (
    FromListConnector)
import numpy
import pytest
from pacman.model.graphs.common.slice import Slice
from unittests.mocks import MockSimulator


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
    assert(numpy.array_equal(
        connector.get_extra_parameters(), expected_extra_parameters))
    assert(numpy.array_equal(
        connector.get_extra_parameter_names(), expected_extra_parameter_names))

    # Check weights and delays are used or ignored as expected
    block = connector.create_synaptic_block(
        weights, delays, [], 0, [], 0, Slice(0, 10), Slice(0, 10), 1)
    assert(numpy.array_equal(block["weight"], numpy.array(expected_weights)))
    assert(numpy.array_equal(block["delay"], numpy.array(expected_delays)))
