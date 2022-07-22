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

import csa
import sys
from spynnaker.pyNN.models.neural_projections.connectors import CSAConnector
from unittests.mocks import MockPopulation
from pacman.model.graphs.common.slice import Slice
from unittest import SkipTest
from spynnaker.pyNN.models.neural_projections import SynapseInformation
from spynnaker.pyNN.config_setup import unittest_setup


def test_csa_one_to_one_connector():
    unittest_setup()
    connector = CSAConnector(csa.oneToOne)
    weight = 1.0
    delay = 2.0
    synapse_info = SynapseInformation(
            connector=None, pre_population=MockPopulation(10, "Pre"),
            post_population=MockPopulation(10, "Post"), prepop_is_view=False,
            postpop_is_view=False, rng=None, synapse_dynamics=None,
            synapse_type=None, receptor_type=None,
            synapse_type_from_dynamics=False, weights=weight, delays=delay)
    connector.set_projection_information(synapse_info)
    post_vertex_slice = Slice(0, 10)
    block = connector.create_synaptic_block(
        [post_vertex_slice], post_vertex_slice, 0, synapse_info)
    assert(len(block) > 0)
    assert(all(item["source"] == item["target"] for item in block))
    assert(all(item["weight"] == 1.0 for item in block))
    assert(all(item["delay"] == 2.0 for item in block))


def test_csa_from_list_connector():
    unittest_setup()
    conn_list = [(i, i + 1 % 10) for i in range(10)]
    connector = CSAConnector(conn_list)
    weight = 1.0
    delay = 2.0
    mock_synapse_info = SynapseInformation(
            connector=None, pre_population=MockPopulation(10, "Pre"),
            post_population=MockPopulation(10, "Post"), prepop_is_view=False,
            postpop_is_view=False, rng=None, synapse_dynamics=None,
            synapse_type=None, receptor_type=None,
            synapse_type_from_dynamics=False, weights=weight, delays=delay)
    connector.set_projection_information(mock_synapse_info)
    post_vertex_slice = Slice(0, 10)
    block = connector.create_synaptic_block(
        [post_vertex_slice], post_vertex_slice, 0, mock_synapse_info)
    assert(len(block) > 0)
    assert(all(item["source"] == conn[0]
               for item, conn in zip(block, conn_list)))
    assert(all(item["target"] == conn[1]
               for item, conn in zip(block, conn_list)))
    assert(all(item["weight"] == 1.0 for item in block))
    assert(all(item["delay"] == 2.0 for item in block))


def test_csa_random_connector():
    unittest_setup()
    connector = CSAConnector(csa.random(0.05))
    weight = 1.0
    delay = 2.0
    mock_synapse_info = SynapseInformation(
            connector=None, pre_population=MockPopulation(10, "Pre"),
            post_population=MockPopulation(10, "Post"), prepop_is_view=False,
            postpop_is_view=False, rng=None, synapse_dynamics=None,
            synapse_type=None, receptor_type=None,
            synapse_type_from_dynamics=False, weights=weight, delays=delay)
    connector.set_projection_information(mock_synapse_info)
    post_vertex_slice = Slice(0, 10)
    block = connector.create_synaptic_block(
        [post_vertex_slice], post_vertex_slice, 0, mock_synapse_info)
    assert(len(block) >= 0)
    assert(all(item["weight"] == 1.0 for item in block))
    assert(all(item["delay"] == 2.0 for item in block))


def test_csa_block_connector():
    unittest_setup()
    try:
        # This creates a block of size (2, 5) with a probability of 0.5; then
        # within the block an individual connection has a probability of 0.3
        connector = CSAConnector(
            csa.block(2, 5) * csa.random(0.5) * csa.random(0.3))
        weight = 1.0
        delay = 2.0
        mock_synapse_info = SynapseInformation(
            connector=None, pre_population=MockPopulation(10, "Pre"),
            post_population=MockPopulation(10, "Post"), prepop_is_view=False,
            postpop_is_view=False, rng=None, synapse_dynamics=None,
            synapse_type=None, receptor_type=None,
            synapse_type_from_dynamics=False,
            weights=weight, delays=delay)

        connector.set_projection_information(mock_synapse_info)
        pre_vertex_slice = Slice(0, 10)
        post_vertex_slice = Slice(0, 10)
        block = connector.create_synaptic_block(
            [pre_vertex_slice], 0, [post_vertex_slice], 0,
            pre_vertex_slice, post_vertex_slice, 0, mock_synapse_info)
        assert(len(block) >= 0)
        assert(all(item["weight"] == 1.0 for item in block))
        assert(all(item["delay"] == 2.0 for item in block))
    except TypeError as e:
        raise SkipTest("https://github.com/INCF/csa/issues/17") from e
    except RuntimeError as e:
        if sys.version_info >= (3, 7):
            raise SkipTest("https://github.com/INCF/csa/issues/16") from e
        raise e
