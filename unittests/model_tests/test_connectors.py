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

import functools
import numpy
import pytest
import random
from pacman.model.graphs.common import Slice
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neural_projections.connectors import (
    FixedNumberPreConnector, FixedNumberPostConnector,
    FixedProbabilityConnector, IndexBasedProbabilityConnector)
from spynnaker.pyNN.models.neural_projections import SynapseInformation
from unittests.mocks import MockPopulation


@pytest.fixture(scope="module", params=[10, 100])
def n_pre(request):
    return request.param


@pytest.fixture(scope="module", params=[10, 100])
def n_post(request):
    return request.param


@pytest.fixture(scope="module", params=[10])
def n_in_slice(request):
    return request.param


@pytest.fixture(
    scope="module",
    params=[
        functools.partial(FixedNumberPreConnector, 1),
        functools.partial(FixedNumberPostConnector, 1),
        functools.partial(FixedNumberPreConnector, 2),
        functools.partial(FixedNumberPostConnector, 2),
        functools.partial(FixedNumberPreConnector, 5, with_replacement=True),
        functools.partial(FixedNumberPostConnector, 5, with_replacement=True),
        functools.partial(FixedNumberPreConnector, 20, with_replacement=True),
        functools.partial(FixedNumberPostConnector, 20, with_replacement=True),
        functools.partial(FixedProbabilityConnector, 0.1),
        functools.partial(FixedProbabilityConnector, 0.5),
        functools.partial(IndexBasedProbabilityConnector,
                          "1 / sqrt(((i + 1) ** 2) + ((j + 1) ** 2))")],
    ids=[
        "FixedNumberPreConnector1-",
        "FixedNumberPostConnector1-",
        "FixedNumberPreConnector2-",
        "FixedNumberPostConnector2-",
        "FixedNumberPreConnector5Replace-",
        "FixedNumberPostConnector5Replace-",
        "FixedNumberPreConnector20Replace-",
        "FixedNumberPostConnector20Replace-",
        "FixedProbabilityConnector0.1-",
        "FixedProbabilityConnector0.5-",
        "IndexBasedProbabilityConnector"]
    )
def create_connector(request):
    return request.param


@pytest.fixture(scope="module", params=[5])
def weight(request):
    return request.param


@pytest.fixture(scope="module", params=[5])
def delay(request):
    return request.param


def test_connectors(
        n_pre, n_post, n_in_slice, create_connector, weight, delay):
    unittest_setup()
    max_target = 0
    max_source = 0
    max_row_length = None
    max_col_length = None
    for _ in range(10):
        numpy.random.seed(random.randint(0, 1000))
        connector = create_connector()
        synapse_info = SynapseInformation(
            connector=None, pre_population=MockPopulation(n_pre, "Pre"),
            post_population=MockPopulation(n_post, "Post"),
            prepop_is_view=False, postpop_is_view=False, rng=None,
            synapse_dynamics=None, synapse_type=None, receptor_type=None,
            synapse_type_from_dynamics=False,
            weights=weight, delays=delay)
        connector.set_projection_information(synapse_info=synapse_info)

        post_slices = [
            Slice(i, i + n_in_slice - 1) for i in range(0, n_post, n_in_slice)]
        post_slice_index = 0
        post_vertex_slice = post_slices[post_slice_index]
        synapse_type = 0
        post_slice = post_slices[post_slice_index]
        pre_range = numpy.arange(0, n_pre + 1)
        post_range = numpy.arange(post_slice.lo_atom, post_slice.hi_atom + 2)

        max_delay = connector.get_delay_maximum(synapse_info)
        max_weight = connector.get_weight_maximum(synapse_info)
        if max_row_length is None:
            max_row_length = connector.\
                get_n_connections_from_pre_vertex_maximum(
                    n_in_slice, synapse_info)
        else:
            assert(max_row_length == connector.
                   get_n_connections_from_pre_vertex_maximum(
                        n_in_slice, synapse_info))
        if max_col_length is None:
            max_col_length = connector.\
                get_n_connections_to_post_vertex_maximum(synapse_info)
        else:
            assert(max_col_length == connector.
                   get_n_connections_to_post_vertex_maximum(synapse_info))
        synaptic_block = connector.create_synaptic_block(
            post_slices, post_vertex_slice, synapse_type, synapse_info)
        source_histogram = numpy.histogram(
            synaptic_block["source"], pre_range)[0]
        target_histogram = numpy.histogram(
            synaptic_block["target"], post_range)[0]
        matrix_max_weight = (
            max(synaptic_block["weight"]) if len(synaptic_block) > 0 else 0)
        matrix_max_delay = (
            max(synaptic_block["delay"]) if len(synaptic_block) > 0 else 0)

        max_source = max((max(source_histogram), max_source))
        max_target = max((max(target_histogram), max_target))

        if len(post_slices) > post_slice_index + 1:
            test_post_slice = post_slices[post_slice_index + 1]
            test_synaptic_block = connector.create_synaptic_block(
                post_slices, test_post_slice, synapse_type, synapse_info)
            if len(test_synaptic_block) > 0:
                assert not numpy.array_equal(
                    test_synaptic_block, synaptic_block)

        try:
            assert max(source_histogram) <= max_row_length
            assert max(target_histogram) <= max_col_length
            assert matrix_max_weight <= max_weight
            assert matrix_max_delay <= max_delay
        except Exception:
            print(connector, n_pre, n_post, n_in_slice)
            print(max_row_length, max(source_histogram), source_histogram)
            print(max_col_length, max(target_histogram), target_histogram)
            print(max_weight, matrix_max_weight, synaptic_block["weight"])
            print(max_delay, matrix_max_delay, synaptic_block["delay"])
    print(connector, n_pre, n_post, n_in_slice, max_row_length,
          max_source, max_col_length, max_target)
