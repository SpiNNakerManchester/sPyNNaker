import csa
from spynnaker.pyNN.models.neural_projections.connectors import CSAConnector
from unittests.mocks import MockSimulator, MockPopulation, MockRNG
from pacman.model.graphs.common.slice import Slice
import pytest


def test_csa_one_to_one_connector():
    MockSimulator.setup()
    connector = CSAConnector(csa.oneToOne)
    connector.set_projection_information(
        MockPopulation(10, "pre"), MockPopulation(10, "post"),
        MockRNG(), 1000.0)
    pre_vertex_slice = Slice(0, 10)
    post_vertex_slice = Slice(0, 10)
    block = connector.create_synaptic_block(
        1.0, 2.0, [pre_vertex_slice], 0, [post_vertex_slice], 0,
        pre_vertex_slice, post_vertex_slice, 0)
    assert(len(block) > 0)
    assert(all(item["source"] == item["target"] for item in block))
    assert(all(item["weight"] == 1.0 for item in block))
    assert(all(item["delay"] == 2.0 for item in block))


def test_csa_from_list_connector():
    MockSimulator.setup()
    conn_list = [(i, i + 1 % 10) for i in range(10)]
    connector = CSAConnector(conn_list)
    connector.set_projection_information(
        MockPopulation(10, "pre"), MockPopulation(10, "post"),
        MockRNG(), 1000.0)
    pre_vertex_slice = Slice(0, 10)
    post_vertex_slice = Slice(0, 10)
    block = connector.create_synaptic_block(
        1.0, 2.0, [pre_vertex_slice], 0, [post_vertex_slice], 0,
        pre_vertex_slice, post_vertex_slice, 0)
    assert(len(block) > 0)
    assert(all(item["source"] == conn[0]
               for item, conn in zip(block, conn_list)))
    assert(all(item["target"] == conn[1]
               for item, conn in zip(block, conn_list)))
    assert(all(item["weight"] == 1.0 for item in block))
    assert(all(item["delay"] == 2.0 for item in block))


def test_csa_random_connector():
    MockSimulator.setup()
    connector = CSAConnector(csa.random(0.05))
    connector.set_projection_information(
        MockPopulation(10, "pre"), MockPopulation(10, "post"),
        MockRNG(), 1000.0)
    pre_vertex_slice = Slice(0, 10)
    post_vertex_slice = Slice(0, 10)
    block = connector.create_synaptic_block(
        1.0, 2.0, [pre_vertex_slice], 0, [post_vertex_slice], 0,
        pre_vertex_slice, post_vertex_slice, 0)
    assert(len(block) >= 0)
    assert(all(item["weight"] == 1.0 for item in block))
    assert(all(item["delay"] == 2.0 for item in block))


@pytest.mark.skip(reason="https://github.com/INCF/csa/issues/17")
def test_csa_block_connector():
    MockSimulator.setup()
    # This creates a block of size (2, 5) with a probability of 0.5; then
    # within the block an individual connection has a probability of 0.3
    connector = CSAConnector(
        csa.block(2, 5) * csa.random(0.5) * csa.random(0.3))
    connector.set_projection_information(
        MockPopulation(10, "pre"), MockPopulation(10, "post"),
        MockRNG(), 1000.0)
    pre_vertex_slice = Slice(0, 10)
    post_vertex_slice = Slice(0, 10)
    block = connector.create_synaptic_block(
        1.0, 2.0, [pre_vertex_slice], 0, [post_vertex_slice], 0,
        pre_vertex_slice, post_vertex_slice, 0)
    assert(len(block) >= 0)
    assert(all(item["weight"] == 1.0 for item in block))
    assert(all(item["delay"] == 2.0 for item in block))
