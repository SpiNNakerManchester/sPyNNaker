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

import os
import struct
import tempfile
import unittest
import math
import spinn_utilities.conf_loader as conf_loader
from spinn_utilities.overrides import overrides
from spinn_machine import SDRAM
from pacman.model.placements import Placement
from pacman.model.resources import ResourceContainer
from pacman.model.graphs.common import GraphMapper, Slice
from pacman.model.graphs.machine import MachineGraph, SimpleMachineVertex
from pacman.model.routing_info import (
    RoutingInfo, PartitionRoutingInfo, BaseKeyAndMask)
from pacman.model.graphs.application import ApplicationVertex
from spinn_storage_handlers import FileDataWriter, FileDataReader
from data_specification import (
    DataSpecificationGenerator, DataSpecificationExecutor)
from spynnaker.pyNN.models.neuron import SynapticManager
import spynnaker.pyNN.models.neural_projections.connectors.\
    abstract_generate_connector_on_machine as \
    abstract_generate_connector_on_machine
from spynnaker.pyNN.abstract_spinnaker_common import AbstractSpiNNakerCommon
import spynnaker.pyNN.abstract_spinnaker_common as abstract_spinnaker_common
from spynnaker.pyNN.models.neural_projections import (
    ProjectionApplicationEdge, ProjectionMachineEdge, SynapseInformation,
    DelayedApplicationEdge, DelayedMachineEdge)
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector, AllToAllConnector, FromListConnector)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic)
from unittests.mocks import MockSimulator


class MockSynapseIO(object):

    def get_block_n_bytes(self, max_row_length, n_rows):
        return 4


class MockMasterPopulationTable(object):

    def __init__(self, key_to_entry_map):
        self._key_to_entry_map = key_to_entry_map

    def extract_synaptic_matrix_data_location(
            self, key, master_pop_table_address, transceiver, x, y):
        return self._key_to_entry_map[key]


class MockTransceiverRawData(object):

    def __init__(self, data_to_read):
        self._data_to_read = data_to_read

    def read_memory(self, x, y, base_address, length):
        return self._data_to_read[base_address:base_address + length]


class SimpleApplicationVertex(ApplicationVertex):

    def __init__(self, n_atoms, label=None):
        super(SimpleApplicationVertex, self).__init__(label=label)
        self._n_atoms = n_atoms

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        return self._n_atoms

    @property
    def size(self):
        return self._n_atoms

    @overrides(ApplicationVertex.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        return SimpleMachineVertex(resources_required, label, constraints)

    @overrides(ApplicationVertex.get_resources_used_by_atoms)
    def get_resources_used_by_atoms(self, vertex_slice):
        return ResourceContainer()

    def add_delays(self, *args, **kwargs):
        pass


class TestSynapticManager(unittest.TestCase):

    def test_retrieve_synaptic_block(self):
        default_config_paths = os.path.join(
            os.path.dirname(abstract_spinnaker_common.__file__),
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME)

        config = conf_loader.load_config(
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME, default_config_paths)

        key = 0

        synaptic_manager = SynapticManager(
            n_synapse_types=2, ring_buffer_sigma=5.0, spikes_per_second=100.0,
            config=config,
            population_table_type=MockMasterPopulationTable(
                {key: [(1, 0, False)]}),
            synapse_io=MockSynapseIO())

        transceiver = MockTransceiverRawData(bytearray(16))
        placement = Placement(None, 0, 0, 1)

        first_block, row_len_1 = synaptic_manager._retrieve_synaptic_block(
            txrx=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=1, index=0,
            using_monitors=False)
        same_block, row_len_1_2 = synaptic_manager._retrieve_synaptic_block(
            txrx=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=1, index=0,
            using_monitors=False)
        synaptic_manager.clear_connection_cache()
        different_block, row_len_2 = synaptic_manager._retrieve_synaptic_block(
            txrx=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=1, index=0,
            using_monitors=False)

        # Check that the row lengths are all the same
        assert row_len_1 == row_len_1_2
        assert row_len_1 == row_len_2

        # Check that the block retrieved twice without reset is cached
        assert id(first_block) == id(same_block)

        # Check that the block after reset is not a copy
        assert id(first_block) != id(different_block)

    def test_retrieve_direct_block(self):
        default_config_paths = os.path.join(
            os.path.dirname(abstract_spinnaker_common.__file__),
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME)

        config = conf_loader.load_config(
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME, default_config_paths)

        key = 0
        n_rows = 2

        direct_matrix = bytearray(struct.pack("<IIII", 1, 2, 3, 4))
        direct_matrix_1_expanded = bytearray(
            struct.pack("<IIIIIIII", 0, 1, 0, 1, 0, 1, 0, 2))
        direct_matrix_2_expanded = bytearray(
            struct.pack("<IIIIIIII", 0, 1, 0, 3, 0, 1, 0, 4))

        synaptic_manager = SynapticManager(
            n_synapse_types=2, ring_buffer_sigma=5.0, spikes_per_second=100.0,
            config=config,
            population_table_type=MockMasterPopulationTable(
                {key: [(1, 0, True), (1, n_rows * 4, True)]}),
            synapse_io=MockSynapseIO())

        transceiver = MockTransceiverRawData(direct_matrix)
        placement = Placement(None, 0, 0, 1)

        data_1, row_len_1 = synaptic_manager._retrieve_synaptic_block(
            txrx=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=n_rows, index=0,
            using_monitors=False)
        data_2, row_len_2 = synaptic_manager._retrieve_synaptic_block(
            txrx=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=n_rows, index=1,
            using_monitors=False)

        # Row lengths should be 1
        assert row_len_1 == 1
        assert row_len_2 == 1

        # Check the data retrieved
        assert data_1 == direct_matrix_1_expanded
        assert data_2 == direct_matrix_2_expanded

    def test_write_synaptic_matrix_and_master_population_table(self):
        MockSimulator.setup()
        # Add an sdram so maxsdram is high enough
        SDRAM(10000)

        default_config_paths = os.path.join(
            os.path.dirname(abstract_spinnaker_common.__file__),
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME)

        config = conf_loader.load_config(
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME, default_config_paths)
        config.set("Simulation", "one_to_one_connection_dtcm_max_bytes", 40)

        machine_time_step = 1000.0

        pre_app_vertex = SimpleApplicationVertex(10, label="pre")
        pre_vertex = SimpleMachineVertex(resources=None, label="pre_m")
        pre_vertex_slice = Slice(0, 9)
        post_app_vertex = SimpleApplicationVertex(10, label="post")
        post_vertex = SimpleMachineVertex(resources=None, label="post_m")
        post_vertex_slice = Slice(0, 9)
        post_slice_index = 0
        delay_app_vertex = SimpleApplicationVertex(10, label="delay")
        delay_vertex = SimpleMachineVertex(resources=None)
        one_to_one_connector_1 = OneToOneConnector(None)
        one_to_one_connector_1.set_projection_information(
            pre_app_vertex, post_app_vertex, None, machine_time_step)
        one_to_one_connector_2 = OneToOneConnector(None)
        one_to_one_connector_2.set_projection_information(
            pre_app_vertex, post_app_vertex, None, machine_time_step)
        all_to_all_connector = AllToAllConnector()
        all_to_all_connector.set_projection_information(
            pre_app_vertex, post_app_vertex, None, machine_time_step)
        from_list_list = [(i, i, i, (i * 5) + 1) for i in range(10)]
        from_list_connector = FromListConnector(conn_list=from_list_list)
        n_delay_stages = int(math.ceil(
            max([values[3] for values in from_list_list]) / 16.0))
        direct_synapse_information_1 = SynapseInformation(
            one_to_one_connector_1, SynapseDynamicsStatic(), 0, 1.5, 1.0)
        direct_synapse_information_2 = SynapseInformation(
            one_to_one_connector_2, SynapseDynamicsStatic(), 1, 2.5, 2.0)
        all_to_all_synapse_information = SynapseInformation(
            all_to_all_connector, SynapseDynamicsStatic(), 0, 4.5, 4.0)
        from_list_synapse_information = SynapseInformation(
            from_list_connector, SynapseDynamicsStatic(), 0)
        app_edge = ProjectionApplicationEdge(
            pre_app_vertex, post_app_vertex, direct_synapse_information_1)
        app_edge.add_synapse_information(direct_synapse_information_2)
        app_edge.add_synapse_information(all_to_all_synapse_information)
        app_edge.add_synapse_information(from_list_synapse_information)
        delay_app_vertex.n_delay_stages = n_delay_stages
        delay_edge = DelayedApplicationEdge(
            delay_app_vertex, post_app_vertex, direct_synapse_information_1)
        delay_edge.add_synapse_information(direct_synapse_information_2)
        delay_edge.add_synapse_information(all_to_all_synapse_information)
        delay_edge.add_synapse_information(from_list_synapse_information)
        app_edge.delay_edge = delay_edge
        machine_edge = ProjectionMachineEdge(
            app_edge.synapse_information, pre_vertex, post_vertex)
        delay_machine_edge = DelayedMachineEdge(
            delay_edge.synapse_information, delay_vertex, post_vertex)
        partition_name = "TestPartition"

        graph = MachineGraph("Test")
        graph.add_vertex(pre_vertex)
        graph.add_vertex(post_vertex)
        graph.add_vertex(delay_vertex)
        graph.add_edge(machine_edge, partition_name)
        graph.add_edge(delay_machine_edge, partition_name)

        graph_mapper = GraphMapper()
        graph_mapper.add_vertex_mapping(
            pre_vertex, pre_vertex_slice, pre_app_vertex)
        graph_mapper.add_vertex_mapping(
            post_vertex, post_vertex_slice, post_app_vertex)
        graph_mapper.add_vertex_mapping(
            delay_vertex, pre_vertex_slice, delay_app_vertex)
        graph_mapper.add_edge_mapping(machine_edge, app_edge)
        graph_mapper.add_edge_mapping(delay_machine_edge, delay_edge)

        weight_scales = [4096.0, 4096.0]

        routing_info = RoutingInfo()
        key = 0
        routing_info.add_partition_info(PartitionRoutingInfo(
            [BaseKeyAndMask(key, 0xFFFFFFF0)],
            graph.get_outgoing_edge_partition_starting_at_vertex(
                pre_vertex, partition_name)))
        delay_key = 0xF0
        delay_key_and_mask = BaseKeyAndMask(delay_key, 0xFFFFFFF0)
        delay_routing_info = PartitionRoutingInfo(
            [delay_key_and_mask],
            graph.get_outgoing_edge_partition_starting_at_vertex(
                delay_vertex, partition_name))
        routing_info.add_partition_info(delay_routing_info)

        temp_spec = tempfile.mktemp()
        spec_writer = FileDataWriter(temp_spec)
        spec = DataSpecificationGenerator(spec_writer, None)
        master_pop_sz = 1000
        master_pop_region = 0
        all_syn_block_sz = 2000
        synapse_region = 1
        direct_region = 2
        spec.reserve_memory_region(master_pop_region, master_pop_sz)
        spec.reserve_memory_region(synapse_region, all_syn_block_sz)

        synaptic_manager = SynapticManager(
            n_synapse_types=2, ring_buffer_sigma=5.0,
            spikes_per_second=100.0, config=config)
        # UGLY but the mock transceiver NEED generate_on_machine be False
        abstract_generate_connector_on_machine.IS_PYNN_8 = False
        synaptic_manager._delay_key_index[
            pre_app_vertex, pre_vertex_slice.lo_atom,
            pre_vertex_slice.hi_atom] = delay_routing_info
        synaptic_manager._write_synaptic_matrix_and_master_population_table(
            spec, [post_vertex_slice], post_slice_index, post_vertex,
            post_vertex_slice, all_syn_block_sz, weight_scales,
            master_pop_region, synapse_region, direct_region, routing_info,
            graph_mapper, graph, machine_time_step)
        spec.end_specification()
        spec_writer.close()

        spec_reader = FileDataReader(temp_spec)
        executor = DataSpecificationExecutor(
            spec_reader, master_pop_sz + all_syn_block_sz)
        executor.execute()

        master_pop_table = executor.get_region(0)
        synaptic_matrix = executor.get_region(1)
        direct_matrix = executor.get_region(2)

        all_data = bytearray()
        all_data.extend(master_pop_table.region_data[
            :master_pop_table.max_write_pointer])
        all_data.extend(synaptic_matrix.region_data[
            :synaptic_matrix.max_write_pointer])
        all_data.extend(direct_matrix.region_data[
            :direct_matrix.max_write_pointer])
        master_pop_table_address = 0
        synaptic_matrix_address = master_pop_table.max_write_pointer
        direct_synapses_address = (
            synaptic_matrix_address + synaptic_matrix.max_write_pointer)
        direct_synapses_address += 4
        indirect_synapses_address = synaptic_matrix_address
        placement = Placement(None, 0, 0, 1)
        transceiver = MockTransceiverRawData(all_data)

        # Get the master population table details
        items = synaptic_manager._poptable_type\
            .extract_synaptic_matrix_data_location(
                key, master_pop_table_address, transceiver,
                placement.x, placement.y)
        delay_items = synaptic_manager._poptable_type\
            .extract_synaptic_matrix_data_location(
                delay_key, master_pop_table_address, transceiver,
                placement.x, placement.y)

        # The first entry should be direct, but the rest should be indirect;
        # the second is potentially direct, but has been restricted by the
        # restriction on the size of the direct matrix.  All items
        # should be "valid" in that they have row length
        assert len(items) == 4
        assert items[0][2]
        assert not items[1][2]
        assert not items[2][2]
        assert not items[3][2]
        assert items[0][0] > 0
        assert items[1][0] > 0
        assert items[2][0] > 0
        assert items[3][0] > 0
        assert items[0][1] == 0
        assert items[1][1] == 0
        assert items[2][1] > 0
        assert items[3][1] > 0

        # There are 4 delay items even though there is only one delayed entry
        # because invalid entries are added to keep the indices the same
        # between delayed and not delayed items.  The first 3 items should all
        # be invalid in that they have a row length of 0.  The last item should
        # not be single
        assert len(delay_items) == 4
        assert delay_items[0][0] == 0
        assert delay_items[1][0] == 0
        assert delay_items[2][0] == 0
        assert delay_items[3][0] > 0
        assert not delay_items[3][2]

        data_1, row_len_1 = synaptic_manager._retrieve_synaptic_block(
            txrx=transceiver, placement=placement,
            master_pop_table_address=master_pop_table_address,
            indirect_synapses_address=indirect_synapses_address,
            direct_synapses_address=direct_synapses_address, key=key,
            n_rows=pre_vertex_slice.n_atoms, index=0,
            using_monitors=False)
        connections_1 = synaptic_manager._read_synapses(
            direct_synapse_information_1, pre_vertex_slice, post_vertex_slice,
            row_len_1, 0, 2, weight_scales, data_1, None,
            app_edge.n_delay_stages, machine_time_step)

        # The first matrix is a 1-1 matrix, so row length is 1
        assert row_len_1 == 1

        # Check that all the connections have the right weight and delay
        assert len(connections_1) == post_vertex_slice.n_atoms
        assert all([conn["weight"] == 1.5 for conn in connections_1])
        assert all([conn["delay"] == 1.0 for conn in connections_1])

        data_2, row_len_2 = synaptic_manager._retrieve_synaptic_block(
            txrx=transceiver, placement=placement,
            master_pop_table_address=master_pop_table_address,
            indirect_synapses_address=indirect_synapses_address,
            direct_synapses_address=direct_synapses_address, key=key,
            n_rows=pre_vertex_slice.n_atoms, index=1,
            using_monitors=False)
        connections_2 = synaptic_manager._read_synapses(
            direct_synapse_information_2, pre_vertex_slice, post_vertex_slice,
            row_len_2, 0, 2, weight_scales, data_2, None,
            app_edge.n_delay_stages, machine_time_step)

        # The second matrix is a 1-1 matrix, so row length is 1
        assert row_len_2 == 1

        # Check that all the connections have the right weight and delay
        assert len(connections_2) == post_vertex_slice.n_atoms
        assert all([conn["weight"] == 2.5 for conn in connections_2])
        assert all([conn["delay"] == 2.0 for conn in connections_2])

        data_3, row_len_3 = synaptic_manager._retrieve_synaptic_block(
            txrx=transceiver, placement=placement,
            master_pop_table_address=master_pop_table_address,
            indirect_synapses_address=indirect_synapses_address,
            direct_synapses_address=direct_synapses_address, key=key,
            n_rows=pre_vertex_slice.n_atoms, index=2,
            using_monitors=False)
        connections_3 = synaptic_manager._read_synapses(
            all_to_all_synapse_information, pre_vertex_slice,
            post_vertex_slice, row_len_3, 0, 2, weight_scales, data_3, None,
            app_edge.n_delay_stages, machine_time_step)

        # The third matrix is an all-to-all matrix, so length is n_atoms
        assert row_len_3 == post_vertex_slice.n_atoms

        # Check that all the connections have the right weight and delay
        assert len(connections_3) == \
            post_vertex_slice.n_atoms * pre_vertex_slice.n_atoms
        assert all([conn["weight"] == 4.5 for conn in connections_3])
        assert all([conn["delay"] == 4.0 for conn in connections_3])

        data_4, row_len_4 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=master_pop_table_address,
            indirect_synapses_address=indirect_synapses_address,
            direct_synapses_address=direct_synapses_address, key=key,
            n_rows=pre_vertex_slice.n_atoms, index=3,
            using_extra_monitor_cores=False)
        d_data_4, d_row_len_4 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=master_pop_table_address,
            indirect_synapses_address=indirect_synapses_address,
            direct_synapses_address=direct_synapses_address, key=delay_key,
            n_rows=pre_vertex_slice.n_atoms * n_delay_stages, index=3,
            using_extra_monitor_cores=False)
        connections_4 = synaptic_manager._synapse_io.read_synapses(
            from_list_synapse_information, pre_vertex_slice,
            post_vertex_slice, row_len_4, d_row_len_4, 2, weight_scales,
            data_4, d_data_4, app_edge.n_delay_stages, machine_time_step)

        # Check that all the connections have the right weight and delay
        assert len(connections_4) == len(from_list_list)
        list_weights = [values[2] for values in from_list_list]
        list_delays = [values[3] for values in from_list_list]
        assert all(list_weights == connections_4["weight"])
        assert all(list_delays == connections_4["delay"])


if __name__ == "__main__":
    unittest.main()
