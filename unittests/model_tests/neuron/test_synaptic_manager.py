import unittest
import struct
import os
import tempfile

import spinn_utilities.conf_loader as conf_loader

from pacman.model.placements.placement import Placement
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.graphs.common.graph_mapper import GraphMapper
from pacman.model.graphs.common.slice import Slice
from pacman.model.graphs.machine.machine_graph import MachineGraph
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.partition_routing_info \
    import PartitionRoutingInfo
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.model.graphs.machine.simple_machine_vertex \
    import SimpleMachineVertex
from pacman.model.graphs.application.application_vertex \
    import ApplicationVertex

from data_specification.data_specification_generator \
    import DataSpecificationGenerator
from data_specification.data_specification_executor \
    import DataSpecificationExecutor

from spinn_storage_handlers.file_data_writer import FileDataWriter
from spinn_storage_handlers.file_data_reader import FileDataReader

from spinn_front_end_common.utilities import globals_variables

from spynnaker.pyNN.models.neuron.synaptic_manager import SynapticManager
from spynnaker.pyNN.abstract_spinnaker_common import AbstractSpiNNakerCommon
import spynnaker.pyNN.abstract_spinnaker_common as abstract_spinnaker_common
from spynnaker.pyNN.models.neural_projections.projection_application_edge \
    import ProjectionApplicationEdge
from spynnaker.pyNN.models.neural_projections.projection_machine_edge \
    import ProjectionMachineEdge
from spynnaker.pyNN.models.neural_projections.synapse_information \
    import SynapseInformation
from spynnaker.pyNN.models.neural_projections.connectors.one_to_one_connector \
    import OneToOneConnector
from spynnaker.pyNN.models.neuron.synapse_dynamics.synapse_dynamics_static \
    import SynapseDynamicsStatic
from spynnaker.pyNN.models.neural_projections.connectors.all_to_all_connector \
    import AllToAllConnector
from spynnaker.pyNN.models.neuron.synapse_types.abstract_synapse_type \
    import AbstractSynapseType
from spynnaker.pyNN.utilities.spynnaker_failed_state \
    import SpynnakerFailedState


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

    def __init__(self, n_atoms):
        ApplicationVertex.__init__(self)
        self._n_atoms = n_atoms

    def n_atoms(self):
        return self._n_atoms

    @property
    def size(self):
        return self._n_atoms

    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        return SimpleMachineVertex(resources_required, label, constraints)

    def get_resources_used_by_atoms(self, vertex_slice):
        return ResourceContainer()


class MockSynapseType(AbstractSynapseType):

    def get_n_synapse_types(self):
        return 2

    def get_synapse_id_by_target(self, target):
        return 0

    def get_synapse_targets(self):
        return [0, 1]

    def get_n_synapse_type_parameters(self):
        return 0

    def get_synapse_type_parameters(self):
        return []

    def get_synapse_type_parameter_types(self):
        return []

    def get_n_cpu_cycles_per_neuron(self):
        return 0


class MockSimulator(object):

    def is_a_pynn_random(self, values):
        return False

    def get_pynn_NumpyRNG(self):
        return None


class TestSynapticManager(unittest.TestCase):

    def test_retrieve_synaptic_block(self):
        default_config_paths = os.path.join(
            os.path.dirname(abstract_spinnaker_common.__file__),
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME)

        config = conf_loader.load_config(
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME, default_config_paths)

        key = 0

        synaptic_manager = SynapticManager(
            synapse_type=None, ring_buffer_sigma=5.0, spikes_per_second=100.0,
            config=config,
            population_table_type=MockMasterPopulationTable(
                {key: [(1, 0, False)]}),
            synapse_io=MockSynapseIO())

        transceiver = MockTransceiverRawData(bytearray(16))
        placement = Placement(None, 0, 0, 1)

        first_block, row_len_1 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=1, index=0,
            using_extra_monitor_cores=False)
        same_block, row_len_1_2 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=1, index=0,
            using_extra_monitor_cores=False)
        synaptic_manager.clear_connection_cache()
        different_block, row_len_2 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=1, index=0,
            using_extra_monitor_cores=False)

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
            synapse_type=None, ring_buffer_sigma=5.0, spikes_per_second=100.0,
            config=config,
            population_table_type=MockMasterPopulationTable(
                {key: [(1, 0, True), (1, n_rows * 4, True)]}),
            synapse_io=MockSynapseIO())

        transceiver = MockTransceiverRawData(direct_matrix)
        placement = Placement(None, 0, 0, 1)

        data_1, row_len_1 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=n_rows, index=0,
            using_extra_monitor_cores=False)
        data_2, row_len_2 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=n_rows, index=1,
            using_extra_monitor_cores=False)

        # Row lengths should be 1
        assert row_len_1 == 1
        assert row_len_2 == 1

        # Check the data retrieved
        assert data_1 == direct_matrix_1_expanded
        assert data_2 == direct_matrix_2_expanded

    def test_write_synaptic_matrix_and_master_population_table(self):

        simulator = MockSimulator()
        globals_variables.set_failed_state(SpynnakerFailedState())
        globals_variables.set_simulator(simulator)

        default_config_paths = os.path.join(
            os.path.dirname(abstract_spinnaker_common.__file__),
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME)

        config = conf_loader.load_config(
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME, default_config_paths)
        config.set("Simulation", "one_to_one_connection_dtcm_max_bytes", 40)

        machine_time_step = 1000.0

        pre_app_vertex = SimpleApplicationVertex(10)
        pre_vertex = SimpleMachineVertex(resources=None)
        pre_vertex_slice = Slice(0, 9)
        post_app_vertex = SimpleApplicationVertex(10)
        post_vertex = SimpleMachineVertex(resources=None)
        post_vertex_slice = Slice(0, 9)
        post_slice_index = 0
        one_to_one_connector_1 = OneToOneConnector(None)
        one_to_one_connector_1.set_projection_information(
            pre_app_vertex, post_app_vertex, None, machine_time_step)
        one_to_one_connector_1.set_weights_and_delays(1.5, 1.0)
        one_to_one_connector_2 = OneToOneConnector(None)
        one_to_one_connector_2.set_projection_information(
            pre_app_vertex, post_app_vertex, None, machine_time_step)
        one_to_one_connector_2.set_weights_and_delays(2.5, 2.0)
        all_to_all_connector = AllToAllConnector(None)
        all_to_all_connector.set_projection_information(
            pre_app_vertex, post_app_vertex, None, machine_time_step)
        all_to_all_connector.set_weights_and_delays(4.5, 4.0)
        direct_synapse_information_1 = SynapseInformation(
            one_to_one_connector_1, SynapseDynamicsStatic(), 0)
        direct_synapse_information_2 = SynapseInformation(
            one_to_one_connector_2, SynapseDynamicsStatic(), 1)
        all_to_all_synapse_information = SynapseInformation(
            all_to_all_connector, SynapseDynamicsStatic(), 0)
        app_edge = ProjectionApplicationEdge(
            pre_app_vertex, post_app_vertex, direct_synapse_information_1)
        app_edge.add_synapse_information(direct_synapse_information_2)
        app_edge.add_synapse_information(all_to_all_synapse_information)
        machine_edge = ProjectionMachineEdge(
            app_edge.synapse_information, pre_vertex, post_vertex)
        partition_name = "TestPartition"

        graph = MachineGraph("Test")
        graph.add_vertex(pre_vertex)
        graph.add_vertex(post_vertex)
        graph.add_edge(machine_edge, partition_name)

        graph_mapper = GraphMapper()
        graph_mapper.add_vertex_mapping(
            pre_vertex, pre_vertex_slice, pre_app_vertex)
        graph_mapper.add_vertex_mapping(
            post_vertex, post_vertex_slice, post_app_vertex)
        graph_mapper.add_edge_mapping(machine_edge, app_edge)

        weight_scales = [4096.0, 4096.0]

        key = 0
        routing_info = RoutingInfo()
        routing_info.add_partition_info(PartitionRoutingInfo(
            [BaseKeyAndMask(key, 0xFFFFFFF0)],
            graph.get_outgoing_edge_partition_starting_at_vertex(
                pre_vertex, partition_name)))

        temp_spec = tempfile.mktemp()
        spec_writer = FileDataWriter(temp_spec)
        spec = DataSpecificationGenerator(spec_writer, None)
        master_pop_sz = 1000
        master_pop_region = 0
        all_syn_block_sz = 2000
        synapse_region = 1
        spec.reserve_memory_region(master_pop_region, master_pop_sz)
        spec.reserve_memory_region(synapse_region, all_syn_block_sz)

        synapse_type = MockSynapseType()

        synaptic_manager = SynapticManager(
            synapse_type=synapse_type, ring_buffer_sigma=5.0,
            spikes_per_second=100.0, config=config)
        synaptic_manager._write_synaptic_matrix_and_master_population_table(
            spec, [post_vertex_slice], post_slice_index, post_vertex,
            post_vertex_slice, all_syn_block_sz, weight_scales,
            master_pop_region, synapse_region, routing_info, graph_mapper,
            graph, machine_time_step)
        spec.end_specification()
        spec_writer.close()

        spec_reader = FileDataReader(temp_spec)
        executor = DataSpecificationExecutor(
            spec_reader, master_pop_sz + all_syn_block_sz)
        executor.execute()

        master_pop_table = executor.get_region(0)
        synaptic_matrix = executor.get_region(1)

        all_data = bytearray()
        all_data.extend(master_pop_table.region_data[
            :master_pop_table.max_write_pointer])
        all_data.extend(synaptic_matrix.region_data[
            :synaptic_matrix.max_write_pointer])
        master_pop_table_address = 0
        synaptic_matrix_address = master_pop_table.max_write_pointer
        direct_synapses_address = struct.unpack_from(
            "<I", synaptic_matrix.region_data)[0]
        direct_synapses_address += synaptic_matrix_address + 8
        indirect_synapses_address = synaptic_matrix_address + 4
        placement = Placement(None, 0, 0, 1)
        transceiver = MockTransceiverRawData(all_data)

        # Get the master population table details
        items = synaptic_manager._poptable_type\
            .extract_synaptic_matrix_data_location(
                key, master_pop_table_address, transceiver,
                placement.x, placement.y)

        # The first entry should be direct, but the rest should be indirect;
        # the second is potentially direct, but has been restricted by the
        # restriction on the size of the direct matrix
        assert len(items) == 3

        # TODO: This has been changed because direct matrices are disabled!
        assert not items[0][2]
        assert not items[1][2]
        assert not items[2][2]

        data_1, row_len_1 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=master_pop_table_address,
            indirect_synapses_address=indirect_synapses_address,
            direct_synapses_address=direct_synapses_address, key=key,
            n_rows=pre_vertex_slice.n_atoms, index=0,
            using_extra_monitor_cores=False)
        connections_1 = synaptic_manager._synapse_io.read_synapses(
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
            transceiver=transceiver, placement=placement,
            master_pop_table_address=master_pop_table_address,
            indirect_synapses_address=indirect_synapses_address,
            direct_synapses_address=direct_synapses_address, key=key,
            n_rows=pre_vertex_slice.n_atoms, index=1,
            using_extra_monitor_cores=False)
        connections_2 = synaptic_manager._synapse_io.read_synapses(
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
            transceiver=transceiver, placement=placement,
            master_pop_table_address=master_pop_table_address,
            indirect_synapses_address=indirect_synapses_address,
            direct_synapses_address=direct_synapses_address, key=key,
            n_rows=pre_vertex_slice.n_atoms, index=2,
            using_extra_monitor_cores=False)
        connections_3 = synaptic_manager._synapse_io.read_synapses(
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

        globals_variables.unset_simulator()


if __name__ == "__main__":
    unittest.main()
