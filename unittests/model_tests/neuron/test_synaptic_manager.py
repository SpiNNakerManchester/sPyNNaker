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
from spynnaker.pyNN.abstract_spinnaker_common import AbstractSpiNNakerCommon
import spynnaker.pyNN.abstract_spinnaker_common as abstract_spinnaker_common
from spynnaker.pyNN.models.neural_projections import (
    ProjectionApplicationEdge, ProjectionMachineEdge, SynapseInformation)
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine, AllToAllConnector, OneToOneConnector)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic, SynapseDynamicsStructuralSTDP,
    SynapseDynamicsSTDP, SynapseDynamicsStructuralStatic)
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependenceSpikePair)
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependenceAdditive, WeightDependenceMultiplicative)
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .partner_selection import LastNeuronSelection, RandomSelection
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .formation import DistanceDependentFormation
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .elimination import RandomByWeightElimination
from spynnaker.pyNN.exceptions import SynapticConfigurationException
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

    def __init__(self, n_atoms):
        super(SimpleApplicationVertex, self).__init__()
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

    def say_false(self, weights, delays):
        return False

    def test_write_synaptic_matrix_and_master_population_table(self):
        MockSimulator.setup()
        # Add an sdram so max SDRAM is high enough
        SDRAM(10000)

        # UGLY but the mock transceiver NEED generate_on_machine to be False
        AbstractGenerateConnectorOnMachine.generate_on_machine = self.say_false
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
        direct_synapse_information_1 = SynapseInformation(
            one_to_one_connector_1, pre_app_vertex, post_app_vertex, False,
            False, None, SynapseDynamicsStatic(), 0, 1.5, 1.0)
        one_to_one_connector_1.set_projection_information(
            machine_time_step, direct_synapse_information_1)
        one_to_one_connector_2 = OneToOneConnector(None)
        direct_synapse_information_2 = SynapseInformation(
            one_to_one_connector_2, pre_app_vertex, post_app_vertex, False,
            False, None, SynapseDynamicsStatic(), 1, 2.5, 2.0)
        one_to_one_connector_2.set_projection_information(
            machine_time_step, direct_synapse_information_2)
        all_to_all_connector = AllToAllConnector(None)
        all_to_all_synapse_information = SynapseInformation(
            all_to_all_connector, pre_app_vertex, post_app_vertex, False,
            False, None, SynapseDynamicsStatic(), 0, 4.5, 4.0)
        all_to_all_connector.set_projection_information(
            machine_time_step, all_to_all_synapse_information)

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
        direct_region = 2
        spec.reserve_memory_region(master_pop_region, master_pop_sz)
        spec.reserve_memory_region(synapse_region, all_syn_block_sz)

        synaptic_manager = SynapticManager(
            n_synapse_types=2, ring_buffer_sigma=5.0,
            spikes_per_second=100.0, config=config)
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
        items = synaptic_manager._extract_synaptic_matrix_data_location(
            key, master_pop_table_address, transceiver, placement)

        # The first entry should be direct, but the rest should be indirect;
        # the second is potentially direct, but has been restricted by the
        # restriction on the size of the direct matrix
        assert len(items) == 3
        assert items[0][2]
        assert not items[1][2]
        assert not items[2][2]

        data_1, row_len_1 = synaptic_manager._retrieve_synaptic_block(
            txrx=transceiver, placement=placement,
            master_pop_table_address=master_pop_table_address,
            indirect_synapses_address=indirect_synapses_address,
            direct_synapses_address=direct_synapses_address, key=key,
            n_rows=pre_vertex_slice.n_atoms, index=0,
            using_monitors=False)
        connections_1 = synaptic_manager._read_synapses(
            direct_synapse_information_1, pre_vertex_slice, post_vertex_slice,
            row_len_1, 0, 2, weight_scales, data_1, None, machine_time_step)

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
            row_len_2, 0, 2, weight_scales, data_2, None, machine_time_step)

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
            machine_time_step)

        # The third matrix is an all-to-all matrix, so length is n_atoms
        assert row_len_3 == post_vertex_slice.n_atoms

        # Check that all the connections have the right weight and delay
        assert len(connections_3) == \
            post_vertex_slice.n_atoms * pre_vertex_slice.n_atoms
        assert all([conn["weight"] == 4.5 for conn in connections_3])
        assert all([conn["delay"] == 4.0 for conn in connections_3])

    def test_set_synapse_dynamics(self):
        MockSimulator.setup()
        default_config_paths = os.path.join(
            os.path.dirname(abstract_spinnaker_common.__file__),
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME)
        config = conf_loader.load_config(
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME, default_config_paths)
        synaptic_manager = SynapticManager(
            n_synapse_types=2, ring_buffer_sigma=5.0,
            spikes_per_second=100.0, config=config)

        static = SynapseDynamicsStatic()
        stdp = SynapseDynamicsSTDP(
            timing_dependence=TimingDependenceSpikePair(),
            weight_dependence=WeightDependenceAdditive())
        alt_stdp = SynapseDynamicsSTDP(
            timing_dependence=TimingDependenceSpikePair(),
            weight_dependence=WeightDependenceMultiplicative())
        static_struct = SynapseDynamicsStructuralStatic(
            partner_selection=LastNeuronSelection(),
            formation=DistanceDependentFormation(),
            elimination=RandomByWeightElimination(0.5))
        alt_static_struct = SynapseDynamicsStructuralStatic(
            partner_selection=RandomSelection(),
            formation=DistanceDependentFormation(),
            elimination=RandomByWeightElimination(0.5))
        stdp_struct = SynapseDynamicsStructuralSTDP(
            partner_selection=LastNeuronSelection(),
            formation=DistanceDependentFormation(),
            elimination=RandomByWeightElimination(0.5),
            timing_dependence=TimingDependenceSpikePair(),
            weight_dependence=WeightDependenceAdditive())
        alt_stdp_struct = SynapseDynamicsStructuralSTDP(
            partner_selection=RandomSelection(),
            formation=DistanceDependentFormation(),
            elimination=RandomByWeightElimination(0.5),
            timing_dependence=TimingDependenceSpikePair(),
            weight_dependence=WeightDependenceAdditive())
        alt_stdp_struct_2 = SynapseDynamicsStructuralSTDP(
            partner_selection=LastNeuronSelection(),
            formation=DistanceDependentFormation(),
            elimination=RandomByWeightElimination(0.5),
            timing_dependence=TimingDependenceSpikePair(),
            weight_dependence=WeightDependenceMultiplicative())

        # This should be fine as it is the first call
        synaptic_manager.synapse_dynamics = static

        # This should be fine as STDP overrides static
        synaptic_manager.synapse_dynamics = stdp

        # This should fail because STDP dependences are difference
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_stdp

        # This should work because STDP dependences are the same
        synaptic_manager.synapse_dynamics = stdp

        # This should work because static always works, but the type should
        # still be STDP
        synaptic_manager.synapse_dynamics = static
        self.assertIsInstance(
            synaptic_manager.synapse_dynamics, SynapseDynamicsSTDP)

        # This should work but should merge with the STDP rule
        synaptic_manager.synapse_dynamics = static_struct
        self.assertIsInstance(
            synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)

        # These should work as static / the STDP is the same but neither should
        # change anything
        synaptic_manager.synapse_dynamics = static
        self.assertIsInstance(
            synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)
        synaptic_manager.synapse_dynamics = stdp
        self.assertIsInstance(
            synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)
        synaptic_manager.synapse_dynamics = static_struct
        self.assertIsInstance(
            synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)

        # These should fail as things are different
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_static_struct
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_stdp

        # This should pass as same structural STDP
        synaptic_manager.synapse_dynamics = stdp_struct
        self.assertIsInstance(
            synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)

        # These should fail as both different
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_stdp_struct
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_stdp_struct_2

        # Try starting again to get a couple more combinations
        synaptic_manager = SynapticManager(
            n_synapse_types=2, ring_buffer_sigma=5.0,
            spikes_per_second=100.0, config=config)

        # STDP followed by structural STDP should result in Structural STDP
        synaptic_manager.synapse_dynamics = stdp
        synaptic_manager.synapse_dynamics = stdp_struct
        self.assertIsInstance(
            synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)

        # ... and should fail here because of differences
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_stdp
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_static_struct
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_stdp_struct
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_stdp_struct_2

        # One more time!
        synaptic_manager = SynapticManager(
            n_synapse_types=2, ring_buffer_sigma=5.0,
            spikes_per_second=100.0, config=config)

        # Static followed by static structural should result in static
        # structural
        synaptic_manager.synapse_dynamics = static
        synaptic_manager.synapse_dynamics = static_struct
        self.assertIsInstance(
            synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralStatic)

        # ... and should fail here because of differences
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_static_struct
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_stdp_struct

        # This should be fine
        synaptic_manager.synapse_dynamics = static

        # This should be OK, but should merge with STDP (opposite of above)
        synaptic_manager.synapse_dynamics = stdp
        self.assertIsInstance(
            synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)

        # ... and now these should fail
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_stdp
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_static_struct
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_stdp_struct
        with self.assertRaises(SynapticConfigurationException):
            synaptic_manager.synapse_dynamics = alt_stdp_struct_2

        # OK, just one more, honest
        synaptic_manager = SynapticManager(
            n_synapse_types=2, ring_buffer_sigma=5.0,
            spikes_per_second=100.0, config=config)
        synaptic_manager.synapse_dynamics = static_struct
        synaptic_manager.synapse_dynamics = stdp_struct


if __name__ == "__main__":
    unittest.main()
