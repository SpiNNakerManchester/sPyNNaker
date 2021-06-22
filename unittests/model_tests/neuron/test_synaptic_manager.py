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
import io
import math
import shutil
import struct
import tempfile
from tempfile import mkdtemp
import numpy
import pytest

from spinn_utilities.overrides import overrides
from spinn_machine import SDRAM
from spinnman.model import CPUInfo
from spinnman.transceiver import Transceiver
from pacman.model.placements import Placement, Placements
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import (MachineGraph, MachineEdge)
from pacman.model.routing_info import (
    RoutingInfo, PartitionRoutingInfo, BaseKeyAndMask)
from pacman.model.graphs.application import ApplicationGraph
from pacman.model.partitioner_splitters import SplitterSliceLegacy
from spinn_utilities.config_holder import set_config
from data_specification import (
    DataSpecificationGenerator, DataSpecificationExecutor)
from data_specification.constants import MAX_MEM_REGIONS
from spynnaker.pyNN.models.neuron import SynapticManager
from spynnaker.pyNN.models.neural_projections import (
    ProjectionApplicationEdge, SynapseInformation, DelayedApplicationEdge)
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector, AllToAllConnector,
    FromListConnector)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic, SynapseDynamicsStructuralSTDP,
    SynapseDynamicsSTDP, SynapseDynamicsStructuralStatic)
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependenceSpikePair)
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependenceAdditive, WeightDependenceMultiplicative)
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .partner_selection import (
        LastNeuronSelection, RandomSelection)
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .formation import (
        DistanceDependentFormation)
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .elimination import (
        RandomByWeightElimination)
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.utility_models.delays import (
    DelayExtensionVertex, DelayExtensionMachineVertex)
from spynnaker.pyNN.utilities.constants import POPULATION_BASED_REGIONS
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterDelayVertexSlice, AbstractSpynnakerSplitterDelay)
from pacman_test_objects import SimpleTestVertex
from unittests.mocks import MockPopulation
import spynnaker8


class MockTransceiverRawData(object):
    def __init__(self, data_to_read):
        self._data_to_read = data_to_read

    @overrides(Transceiver.get_cpu_information_from_core)
    def get_cpu_information_from_core(self, x, y, p):
        bs = bytearray(128)
        return CPUInfo(x=1, y=2, p=3, cpu_data=bytes(bs), offset=0)

    @overrides(Transceiver.read_memory)
    def read_memory(self, x, y, base_address, length, cpu=0):
        return self._data_to_read[base_address:base_address + length]

    @overrides(Transceiver.read_word)
    def read_word(self, x, y, base_address, cpu=0):
        datum, = struct.unpack("<I", self.read_memory(x, y, base_address, 4))
        return datum


class MockSplitter(SplitterSliceLegacy, AbstractSpynnakerSplitterDelay):
    def __init__(self):
        super().__init__("mock splitter")


def test_write_data_spec():
    spynnaker8.setup(timestep=1)
    # Add an sdram so max SDRAM is high enough
    SDRAM(10000)

    set_config("Simulation", "one_to_one_connection_dtcm_max_bytes", 40)

    placements = Placements()
    pre_app_population = MockPopulation(10, "mock pop pre")
    pre_app_vertex = SimpleTestVertex(10, label="pre")
    pre_app_vertex.splitter = MockSplitter()
    pre_app_vertex.splitter._called = True
    pre_vertex_slice = Slice(0, 9)

    post_app_population = MockPopulation(10, "mock pop post")
    pre_vertex = pre_app_vertex.create_machine_vertex(
        pre_vertex_slice, None)
    placements.add_placement(Placement(pre_vertex, 0, 0, 1))
    post_app_vertex = SimpleTestVertex(10, label="post")
    post_app_vertex.splitter = MockSplitter()
    post_app_vertex.splitter._called = True
    post_vertex_slice = Slice(0, 9)
    post_vertex = post_app_vertex.create_machine_vertex(
        post_vertex_slice, None)
    post_vertex_placement = Placement(post_vertex, 0, 0, 2)
    placements.add_placement(post_vertex_placement)
    delay_app_vertex = DelayExtensionVertex(
        10, 16, 51, pre_app_vertex, label="delay")
    delay_app_vertex.set_new_n_delay_stages_and_delay_per_stage(
        16, 51)
    delay_app_vertex.splitter = SplitterDelayVertexSlice(
        pre_app_vertex.splitter)
    delay_vertex = DelayExtensionMachineVertex(
        resources_required=None, label="", constraints=[],
        app_vertex=delay_app_vertex, vertex_slice=post_vertex_slice)
    placements.add_placement(Placement(delay_vertex, 0, 0, 3))
    one_to_one_connector_1 = OneToOneConnector(None)
    direct_synapse_information_1 = SynapseInformation(
        one_to_one_connector_1, pre_app_population, post_app_population,
        False, False, None, SynapseDynamicsStatic(), 0, True, 1.5, 1.0)
    one_to_one_connector_1.set_projection_information(
        direct_synapse_information_1)
    one_to_one_connector_2 = OneToOneConnector(None)
    direct_synapse_information_2 = SynapseInformation(
        one_to_one_connector_2, pre_app_population, post_app_population,
        False, False, None, SynapseDynamicsStatic(), 1, True, 2.5, 2.0)
    one_to_one_connector_2.set_projection_information(
        direct_synapse_information_2)
    all_to_all_connector = AllToAllConnector(False)
    all_to_all_synapse_information = SynapseInformation(
        all_to_all_connector, pre_app_population, post_app_population,
        False, False, None, SynapseDynamicsStatic(), 0, True, 4.5, 4.0)
    all_to_all_connector.set_projection_information(
        all_to_all_synapse_information)
    from_list_list = [(i, i, i, (i * 5) + 1) for i in range(10)]
    from_list_connector = FromListConnector(conn_list=from_list_list)
    from_list_synapse_information = SynapseInformation(
        from_list_connector, pre_app_population, post_app_population,
        False, False, None, SynapseDynamicsStatic(), 0, True)
    from_list_connector.set_projection_information(
        from_list_synapse_information)
    app_edge = ProjectionApplicationEdge(
        pre_app_vertex, post_app_vertex, direct_synapse_information_1)
    app_edge.add_synapse_information(direct_synapse_information_2)
    app_edge.add_synapse_information(all_to_all_synapse_information)
    app_edge.add_synapse_information(from_list_synapse_information)
    delay_edge = DelayedApplicationEdge(
        delay_app_vertex, post_app_vertex, direct_synapse_information_1,
        app_edge)
    delay_edge.add_synapse_information(direct_synapse_information_2)
    delay_edge.add_synapse_information(all_to_all_synapse_information)
    delay_edge.add_synapse_information(from_list_synapse_information)
    app_edge.delay_edge = delay_edge
    machine_edge = MachineEdge(
        pre_vertex, post_vertex, app_edge=app_edge)
    delay_machine_edge = MachineEdge(
        delay_vertex, post_vertex, app_edge=delay_edge)
    partition_name = "TestPartition"

    app_graph = ApplicationGraph("Test")
    graph = MachineGraph("Test", app_graph)
    graph.add_vertex(pre_vertex)
    graph.add_vertex(post_vertex)
    graph.add_vertex(delay_vertex)
    graph.add_edge(machine_edge, partition_name)
    graph.add_edge(delay_machine_edge, partition_name)

    app_graph.add_vertex(pre_app_vertex)
    app_graph.add_vertex(post_app_vertex)
    app_graph.add_vertex(delay_app_vertex)
    app_graph.add_edge(app_edge, partition_name)
    app_graph.add_edge(delay_edge, partition_name)

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
    spec = DataSpecificationGenerator(io.FileIO(temp_spec, "wb"), None)

    synaptic_manager = SynapticManager(
        n_synapse_types=2, ring_buffer_sigma=5.0,
        spikes_per_second=100.0, drop_late_spikes=True)
    synaptic_manager.write_data_spec(
        spec, post_app_vertex, post_vertex_slice, post_vertex,
        graph, app_graph, routing_info, 1.0)
    spec.end_specification()

    with io.FileIO(temp_spec, "rb") as spec_reader:
        executor = DataSpecificationExecutor(spec_reader, 20000)
        executor.execute()

    all_data = bytearray()
    all_data.extend(bytearray(executor.get_header()))
    all_data.extend(bytearray(executor.get_pointer_table(0)))
    for r in range(MAX_MEM_REGIONS):
        region = executor.get_region(r)
        if region is not None:
            all_data.extend(region.region_data)
    transceiver = MockTransceiverRawData(all_data)
    report_folder = mkdtemp()
    try:
        connections_1 = synaptic_manager.get_connections_from_machine(
            transceiver, placements, app_edge,
            direct_synapse_information_1)

        # Check that all the connections have the right weight and delay
        assert len(connections_1) == post_vertex_slice.n_atoms
        assert all([conn["weight"] == 1.5 for conn in connections_1])
        assert all([conn["delay"] == 1.0 for conn in connections_1])

        connections_2 = synaptic_manager.get_connections_from_machine(
            transceiver, placements, app_edge,
            direct_synapse_information_2)

        # Check that all the connections have the right weight and delay
        assert len(connections_2) == post_vertex_slice.n_atoms
        assert all([conn["weight"] == 2.5 for conn in connections_2])
        assert all([conn["delay"] == 2.0 for conn in connections_2])

        connections_3 = synaptic_manager.get_connections_from_machine(
            transceiver, placements, app_edge,
            all_to_all_synapse_information)

        # Check that all the connections have the right weight and delay
        assert len(connections_3) == \
            post_vertex_slice.n_atoms * pre_vertex_slice.n_atoms
        assert all([conn["weight"] == 4.5 for conn in connections_3])
        assert all([conn["delay"] == 4.0 for conn in connections_3])

        connections_4 = synaptic_manager.get_connections_from_machine(
            transceiver, placements, app_edge,
            from_list_synapse_information)

        # Check that all the connections have the right weight and delay
        assert len(connections_4) == len(from_list_list)
        list_weights = [values[2] for values in from_list_list]
        list_delays = [values[3] for values in from_list_list]
        assert all(list_weights == connections_4["weight"])
        assert all(list_delays == connections_4["delay"])
    finally:
        shutil.rmtree(report_folder, ignore_errors=True)


def test_set_synapse_dynamics():
    spynnaker8.setup()
    synaptic_manager = SynapticManager(
        n_synapse_types=2, ring_buffer_sigma=5.0,
        spikes_per_second=100.0, drop_late_spikes=True)

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
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_stdp

    # This should work because STDP dependences are the same
    synaptic_manager.synapse_dynamics = stdp

    # This should work because static always works, but the type should
    # still be STDP
    synaptic_manager.synapse_dynamics = static
    assert isinstance(
        synaptic_manager.synapse_dynamics, SynapseDynamicsSTDP)

    # This should work but should merge with the STDP rule
    synaptic_manager.synapse_dynamics = static_struct
    assert isinstance(
        synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)

    # These should work as static / the STDP is the same but neither should
    # change anything
    synaptic_manager.synapse_dynamics = static
    assert isinstance(
        synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)
    synaptic_manager.synapse_dynamics = stdp
    assert isinstance(
        synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)
    synaptic_manager.synapse_dynamics = static_struct
    assert isinstance(
        synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)

    # These should fail as things are different
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_static_struct
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_stdp

    # This should pass as same structural STDP
    synaptic_manager.synapse_dynamics = stdp_struct
    assert isinstance(
        synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)

    # These should fail as both different
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_stdp_struct
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_stdp_struct_2

    # Try starting again to get a couple more combinations
    synaptic_manager = SynapticManager(
        n_synapse_types=2, ring_buffer_sigma=5.0,
        spikes_per_second=100.0, drop_late_spikes=True)

    # STDP followed by structural STDP should result in Structural STDP
    synaptic_manager.synapse_dynamics = stdp
    synaptic_manager.synapse_dynamics = stdp_struct
    assert isinstance(
        synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)

    # ... and should fail here because of differences
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_stdp
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_static_struct
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_stdp_struct
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_stdp_struct_2

    # One more time!
    synaptic_manager = SynapticManager(
        n_synapse_types=2, ring_buffer_sigma=5.0,
        spikes_per_second=100.0, drop_late_spikes=True)

    # Static followed by static structural should result in static
    # structural
    synaptic_manager.synapse_dynamics = static
    synaptic_manager.synapse_dynamics = static_struct
    assert isinstance(
        synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralStatic)

    # ... and should fail here because of differences
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_static_struct
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_stdp_struct

    # This should be fine
    synaptic_manager.synapse_dynamics = static

    # This should be OK, but should merge with STDP (opposite of above)
    synaptic_manager.synapse_dynamics = stdp
    assert isinstance(
        synaptic_manager.synapse_dynamics, SynapseDynamicsStructuralSTDP)

    # ... and now these should fail
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_stdp
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_static_struct
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_stdp_struct
    with pytest.raises(SynapticConfigurationException):
        synaptic_manager.synapse_dynamics = alt_stdp_struct_2

    # OK, just one more, honest
    synaptic_manager = SynapticManager(
        n_synapse_types=2, ring_buffer_sigma=5.0,
        spikes_per_second=100.0, drop_late_spikes=True)
    synaptic_manager.synapse_dynamics = static_struct
    synaptic_manager.synapse_dynamics = stdp_struct


@pytest.mark.parametrize(
    "undelayed_indices_connected,delayed_indices_connected,n_pre_neurons,"
    "neurons_per_core,expect_app_keys,max_delay", [
        # Only undelayed, all edges exist
        (set(range(10)), None, 1000, 100, True, None),
        # Only delayed, all edges exist
        (None, set(range(10)), 1000, 100, True, 20),
        # All undelayed and delayed edges exist
        (set(range(10)), set(range(10)), 1000, 100, True, 20),
        # Only undelayed, some edges are filtered (app keys shouldn't work)
        ({0, 1, 2, 3, 4}, None, 1000, 100, False, None),
        # Only delayed, some edges are filtered (app keys shouldn't work)
        (None, {5, 6, 7, 8, 9}, 1000, 100, False, 20),
        # Both delayed and undelayed, some undelayed edges don't exist
        ({3, 4, 5, 6, 7}, set(range(10)), 1000, 100, False, 20),
        # Both delayed and undelayed, some delayed edges don't exist
        (set(range(10)), {4, 5, 6, 7}, 1000, 100, False, 20),
        # Should work but number of neurons don't work out
        (set(range(5)), None, 10000, 2048, False, None),
        # Should work but number of cores doesn't work out
        (set(range(2000)), None, 10000, 5, False, None),
        # Should work but number of neurons with delays don't work out
        (None, set(range(4)), 1024, 256, False, 144)
    ])
def test_pop_based_master_pop_table_standard(
        undelayed_indices_connected, delayed_indices_connected,
        n_pre_neurons, neurons_per_core, expect_app_keys, max_delay):
    spynnaker8.setup(1.0)

    # Add an sdram so max SDRAM is high enough
    SDRAM(128000000)

    # Make simple source and target, where the source has 1000 atoms
    # split into 10 vertices (100 each) and the target has 100 atoms in
    # a single vertex
    app_graph = ApplicationGraph("Test")
    mac_graph = MachineGraph("Test", app_graph)
    pre_app_vertex = SimpleTestVertex(
        n_pre_neurons, max_atoms_per_core=neurons_per_core)
    pre_app_vertex.splitter = MockSplitter()
    app_graph.add_vertex(pre_app_vertex)
    post_vertex_slice = Slice(0, 99)
    post_app_vertex = SimpleTestVertex(100)
    post_app_vertex.splitter = MockSplitter()
    app_graph.add_vertex(post_app_vertex)
    post_mac_vertex = post_app_vertex.create_machine_vertex(
        post_vertex_slice, None)
    mac_graph.add_vertex(post_mac_vertex)

    # Create the pre-machine-vertices
    for lo in range(0, n_pre_neurons, neurons_per_core):
        pre_mac_slice = Slice(
            lo, min(lo + neurons_per_core - 1, n_pre_neurons - 1))
        pre_mac_vertex = pre_app_vertex.create_machine_vertex(
            pre_mac_slice, None)
        mac_graph.add_vertex(pre_mac_vertex)

    # Add delays if needed
    if delayed_indices_connected:
        pre_app_delay_vertex = DelayExtensionVertex(
            n_pre_neurons, 16.0, max_delay, pre_app_vertex)
        app_graph.add_vertex(pre_app_delay_vertex)

        for lo in range(0, n_pre_neurons, neurons_per_core):
            pre_mac_slice = Slice(
                lo, min(lo + neurons_per_core - 1, n_pre_neurons - 1))
            pre_mac_vertex = DelayExtensionMachineVertex(
                None, "", [], pre_app_delay_vertex, pre_mac_slice)
            mac_graph.add_vertex(pre_mac_vertex)

    # Make the routing info line up to force an app key in the pop table if
    # the constraints match up
    routing_info = RoutingInfo()
    n_key_bits = int(math.ceil(math.log(100, 2)))
    n_keys = 2**n_key_bits
    mask = 0xFFFFFFFF - (n_keys - 1)

    # Build a from list connector that is really an all-to-all connector,
    # but with delays that depend on what types of connection we want
    delays = []
    if undelayed_indices_connected:
        delays.append(10)
    if delayed_indices_connected:
        delays.append(20)
    connections = [(i, j, 0, delays[i % len(delays)])
                   for i in range(n_pre_neurons) for j in range(100)]
    connector = FromListConnector(connections)
    synapse_dynamics = SynapseDynamicsStatic()
    synapse_info = SynapseInformation(
        connector, pre_app_vertex, post_app_vertex, False, False, None,
        synapse_dynamics, 0, True)

    # Create the application edge
    app_edge = ProjectionApplicationEdge(
        pre_app_vertex, post_app_vertex, synapse_info)
    app_graph.add_edge(app_edge, "Test")

    # Create the machine edges
    for pre_mac_vertex in pre_app_vertex.machine_vertices:
        i = pre_mac_vertex.index
        mac_edge = MachineEdge(
            pre_mac_vertex, post_mac_vertex, app_edge=app_edge)
        if undelayed_indices_connected and i in undelayed_indices_connected:
            mac_graph.add_edge(mac_edge, "Test")
            partition = mac_graph.get_outgoing_partition_for_edge(mac_edge)
            partition_info = PartitionRoutingInfo(
                [BaseKeyAndMask(i * n_keys, mask)], partition)
            routing_info.add_partition_info(partition_info)

    # Create the delay application edge and delay machine edges
    if delayed_indices_connected:
        delay_app_edge = DelayedApplicationEdge(
            pre_app_delay_vertex, post_app_vertex, synapse_info, app_edge)
        app_edge.delay_edge = delay_app_edge
        app_graph.add_edge(delay_app_edge, "Test")

        base_d_key = 16 * n_keys
        for pre_mac_vertex in pre_app_delay_vertex.machine_vertices:
            i = pre_mac_vertex.index
            mac_edge = MachineEdge(
                pre_mac_vertex, post_mac_vertex, app_edge=delay_app_edge)
            if i in delayed_indices_connected:
                mac_graph.add_edge(mac_edge, "Test")
                partition = mac_graph.get_outgoing_partition_for_edge(mac_edge)
                partition_info = PartitionRoutingInfo(
                    [BaseKeyAndMask(base_d_key + (i * n_keys), mask)],
                    partition)
                routing_info.add_partition_info(partition_info)

    # Generate the data
    temp_spec = tempfile.mktemp()
    spec = DataSpecificationGenerator(io.FileIO(temp_spec, "wb"), None)
    synaptic_manager = SynapticManager(
        n_synapse_types=2, ring_buffer_sigma=5.0,
        spikes_per_second=100.0, drop_late_spikes=True)
    synaptic_manager.write_data_spec(
        spec, post_app_vertex, post_vertex_slice, post_mac_vertex,
        mac_graph, app_graph, routing_info, 1.0)
    spec.end_specification()
    with io.FileIO(temp_spec, "rb") as spec_reader:
        executor = DataSpecificationExecutor(
            spec_reader, SDRAM.max_sdram_found)
        executor.execute()

    # Read the population table and check entries
    region = executor.get_region(
        POPULATION_BASED_REGIONS.POPULATION_TABLE.value)
    mpop_data = numpy.frombuffer(
        region.region_data, dtype="uint8").view("uint32")
    n_entries = mpop_data[0]
    n_addresses = mpop_data[1]

    # Compute how many entries and addresses there should be
    expected_n_entries = 0
    expected_n_addresses = 0
    if expect_app_keys:
        n_app_entries = (int(bool(undelayed_indices_connected)) +
                         int(bool(delayed_indices_connected)))
        expected_n_entries += n_app_entries
        # 2 addresses for an app key because of the extra info
        expected_n_addresses += n_app_entries * 2
    else:
        # An entry and address for each incoming machine edge
        if undelayed_indices_connected:
            expected_n_entries += len(undelayed_indices_connected)
            expected_n_addresses += len(undelayed_indices_connected)
        if delayed_indices_connected:
            expected_n_entries += len(delayed_indices_connected)
            expected_n_addresses += len(delayed_indices_connected)

    assert(n_entries == expected_n_entries)
    assert(n_addresses == expected_n_addresses)
