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
import shutil
import struct
import unittest
from tempfile import mkdtemp
import numpy
import pytest

from spinn_utilities.overrides import overrides
from spinn_utilities.config_holder import set_config
from spinnman.transceiver.mockable_transceiver import MockableTransceiver
from spinnman.transceiver import Transceiver
from pacman.model.placements import Placement
from pacman.operations.routing_info_allocator_algorithms import (
    ZonedRoutingInfoAllocator)
from pacman.operations.partition_algorithms import splitter_partitioner
from spinn_front_end_common.interface.ds import (
    DataSpecificationGenerator, DsSqlliteDatabase)
from spinn_front_end_common.interface.interface_functions import (
    load_application_data_specs)
from spynnaker.pyNN.data.spynnaker_data_writer import SpynnakerDataWriter
from spynnaker.pyNN.models.neuron.synaptic_matrices import (
    SynapticMatrices, SynapseRegions)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic, SynapseDynamicsStructuralSTDP,
    SynapseDynamicsSTDP, SynapseDynamicsStructuralStatic,
    SynapseDynamicsNeuromodulation)
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependenceSpikePair)
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependenceAdditive, WeightDependenceMultiplicative)
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .partner_selection import (LastNeuronSelection, RandomSelection)
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .formation import DistanceDependentFormation
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .elimination import RandomByWeightElimination
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neuron.builds.if_curr_exp_base import IFCurrExpBase
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexFixed)
from spynnaker.pyNN.extra_algorithms import delay_support_adder
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.utilities import constants
import pyNN.spiNNaker as p


class _MockTransceiverinOut(MockableTransceiver):

    @overrides(MockableTransceiver.malloc_sdram)
    def malloc_sdram(self, x, y, size, app_id, tag=None):
        self._data_to_read = bytearray(size)
        return 0

    @overrides(MockableTransceiver.write_memory)
    def write_memory(self, x, y, base_address, data, n_bytes=None, offset=0,
                     cpu=0, is_filename=False, get_sum=False):
        if data is None:
            return
        if isinstance(data, int):
            data = struct.Struct("<I").pack(data)
        self._data_to_read[base_address:base_address + len(data)] = data

    @overrides(Transceiver.get_region_base_address)
    def get_region_base_address(self, x, y, p):
        return 0

    @overrides(MockableTransceiver.read_memory)
    def read_memory(self, x, y, base_address, length, cpu=0):
        return self._data_to_read[base_address:base_address + length]

    @overrides(MockableTransceiver.read_word)
    def read_word(self, x, y, base_address, cpu=0):
        datum, = struct.unpack("<I", self.read_memory(x, y, base_address, 4))
        return datum


def say_false(self, weights, delays):
    return False


def test_write_data_spec():
    unittest_setup()
    set_config("Machine", "version", 5)
    writer = SpynnakerDataWriter.mock()
    # UGLY but the mock transceiver NEED generate_on_machine to be False
    AbstractGenerateConnectorOnMachine.generate_on_machine = say_false

    set_config("Machine", "enable_advanced_monitor_support", "False")
    set_config("Java", "use_java", "False")

    p.set_number_of_neurons_per_core(p.IF_curr_exp, 100)
    pre_pop = p.Population(
        10, p.IF_curr_exp(), label="Pre",
        additional_parameters={
            "splitter": SplitterAbstractPopulationVertexFixed()})
    post_pop = p.Population(
        10, p.IF_curr_exp(), label="Post",
        additional_parameters={
            "splitter": SplitterAbstractPopulationVertexFixed()})
    proj_one_to_one_1 = p.Projection(
        pre_pop, post_pop, p.OneToOneConnector(),
        p.StaticSynapse(weight=1.5, delay=1.0))
    proj_one_to_one_2 = p.Projection(
        pre_pop, post_pop, p.OneToOneConnector(),
        p.StaticSynapse(weight=2.5, delay=2.0))
    proj_all_to_all = p.Projection(
        pre_pop, post_pop, p.AllToAllConnector(allow_self_connections=False),
        p.StaticSynapse(weight=4.5, delay=4.0))

    from_list_list = [(i, i, i, (i * 5) + 1) for i in range(10)]
    proj_from_list = p.Projection(
        pre_pop, post_pop, p.FromListConnector(from_list_list),
        p.StaticSynapse())

    writer.set_plan_n_timesteps(100)
    d_vertices, d_edges = delay_support_adder()
    for vertex in d_vertices:
        writer.add_vertex(vertex)
    for edge in d_edges:
        writer.add_edge(
            edge, constants.SPIKE_PARTITION_ID)
    splitter_partitioner()
    allocator = ZonedRoutingInfoAllocator()
    writer.set_routing_infos(allocator.__call__([], flexible=False))

    post_vertex = next(iter(post_pop._vertex.machine_vertices))
    post_vertex_slice = post_vertex.vertex_slice
    post_vertex_placement = Placement(post_vertex, 0, 0, 3)

    regions = SynapseRegions(
        synapse_params=5, synapse_dynamics=6, structural_dynamics=7,
        bitfield_filter=8,
        synaptic_matrix=1, pop_table=3, connection_builder=4)
    references = SynapseRegions(
        synapse_params=None, synapse_dynamics=None, structural_dynamics=None,
        bitfield_filter=None, synaptic_matrix=None, pop_table=None,
        connection_builder=None)
    synaptic_matrices = SynapticMatrices(
        post_pop._vertex, regions, max_atoms_per_core=10,
        weight_scales=[32, 32], all_syn_block_sz=10000)
    synaptic_matrices.generate_data()

    with DsSqlliteDatabase() as ds_db:
        spec = DataSpecificationGenerator(0, 0, 3, post_vertex, ds_db)
        synaptic_matrices.write_synaptic_data(
            spec, post_vertex_slice, references)

    writer.set_transceiver(_MockTransceiverinOut())
    load_application_data_specs()

    report_folder = mkdtemp()
    try:
        connections_1 = numpy.concatenate(
            synaptic_matrices.get_connections_from_machine(
                post_vertex_placement,
                proj_one_to_one_1._projection_edge,
                proj_one_to_one_1._synapse_information))

        # Check that all the connections have the right weight and delay
        assert len(connections_1) == post_vertex_slice.n_atoms
        assert all([conn["weight"] == 1.5 for conn in connections_1])
        assert all([conn["delay"] == 1.0 for conn in connections_1])

        connections_2 = numpy.concatenate(
            synaptic_matrices.get_connections_from_machine(
                post_vertex_placement,
                proj_one_to_one_2._projection_edge,
                proj_one_to_one_2._synapse_information))

        # Check that all the connections have the right weight and delay
        assert len(connections_2) == post_vertex_slice.n_atoms
        assert all([conn["weight"] == 2.5 for conn in connections_2])
        assert all([conn["delay"] == 2.0 for conn in connections_2])

        connections_3 = numpy.concatenate(
            synaptic_matrices.get_connections_from_machine(
                post_vertex_placement,
                proj_all_to_all._projection_edge,
                proj_all_to_all._synapse_information))

        # Check that all the connections have the right weight and delay
        assert len(connections_3) == 90
        assert all([conn["weight"] == 4.5 for conn in connections_3])
        assert all([conn["delay"] == 4.0 for conn in connections_3])

        connections_4 = numpy.concatenate(
            synaptic_matrices.get_connections_from_machine(
                post_vertex_placement,
                proj_from_list._projection_edge,
                proj_from_list._synapse_information))

        # Check that all the connections have the right weight and delay
        assert len(connections_4) == len(from_list_list)
        list_weights = [values[2] for values in from_list_list]
        list_delays = [values[3] for values in from_list_list]
        assert all(list_weights == connections_4["weight"])
        assert all(list_delays == connections_4["delay"])
    finally:
        shutil.rmtree(report_folder, ignore_errors=True)


def test_set_synapse_dynamics():
    raise unittest.SkipTest("needs fixing")
    unittest_setup()
    post_app_model = IFCurrExpBase()
    post_app_vertex = post_app_model.create_vertex(
        n_neurons=10, label="post", spikes_per_second=None,
        ring_buffer_sigma=None, incoming_spike_buffer_size=None,
        n_steps_per_timestep=1, drop_late_spikes=True, splitter=None,
        seed=None, n_colour_bits=None)

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
    neuromodulation = SynapseDynamicsNeuromodulation()
    alt_neuromodulation = SynapseDynamicsNeuromodulation(tau_c=1)

    # This should be fine as it is the first call
    post_app_vertex.synapse_dynamics = static

    # This should fail as can't add neuromodulation first
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = neuromodulation

    # This should be fine as STDP overrides static
    post_app_vertex.synapse_dynamics = stdp

    # This should fail because STDP dependences are difference
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_stdp

    # This should pass because neuromodulation is OK after STDP
    post_app_vertex.synapse_dynamics = neuromodulation
    assert isinstance(post_app_vertex.synapse_dynamics, SynapseDynamicsSTDP)

    # This should work because STDP dependences are the same
    post_app_vertex.synapse_dynamics = stdp

    # This should fail as neuromodulation type is different
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_neuromodulation

    # This should be fine as same neuromodulation
    post_app_vertex.synapse_dynamics = neuromodulation
    assert isinstance(post_app_vertex.synapse_dynamics, SynapseDynamicsSTDP)

    # This should work because static always works, but the type should
    # still be STDP
    post_app_vertex.synapse_dynamics = static
    assert isinstance(post_app_vertex.synapse_dynamics, SynapseDynamicsSTDP)

    # This should work but should merge with the STDP rule
    post_app_vertex.synapse_dynamics = static_struct
    assert isinstance(
        post_app_vertex.synapse_dynamics, SynapseDynamicsStructuralSTDP)

    # These should work as static / the STDP is the same but neither should
    # change anything
    post_app_vertex.synapse_dynamics = static
    assert isinstance(
        post_app_vertex.synapse_dynamics, SynapseDynamicsStructuralSTDP)
    post_app_vertex.synapse_dynamics = stdp
    assert isinstance(
        post_app_vertex.synapse_dynamics, SynapseDynamicsStructuralSTDP)
    post_app_vertex.synapse_dynamics = static_struct
    assert isinstance(
        post_app_vertex.synapse_dynamics, SynapseDynamicsStructuralSTDP)

    # These should fail as things are different
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_static_struct
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_stdp

    # This should pass as same structural STDP
    post_app_vertex.synapse_dynamics = stdp_struct
    assert isinstance(
        post_app_vertex.synapse_dynamics, SynapseDynamicsStructuralSTDP)

    # These should fail as both different
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_stdp_struct
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_stdp_struct_2

    # Try starting again to get a couple more combinations
    post_app_vertex = post_app_model.create_vertex(
        n_neurons=10, label="post", spikes_per_second=None,
        ring_buffer_sigma=None, incoming_spike_buffer_size=None,
        n_steps_per_timestep=1, drop_late_spikes=True, splitter=None,
        seed=None, n_colour_bits=None)

    # STDP followed by structural STDP should result in Structural STDP
    post_app_vertex.synapse_dynamics = stdp
    post_app_vertex.synapse_dynamics = stdp_struct
    assert isinstance(
        post_app_vertex.synapse_dynamics, SynapseDynamicsStructuralSTDP)

    # ... and should fail here because of differences
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_stdp
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_static_struct
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_stdp_struct
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_stdp_struct_2

    # One more time!
    post_app_vertex = post_app_model.create_vertex(
        n_neurons=10, label="post", spikes_per_second=None,
        ring_buffer_sigma=None, incoming_spike_buffer_size=None,
        n_steps_per_timestep=1, drop_late_spikes=True, splitter=None,
        seed=None, n_colour_bits=None)

    # Static followed by static structural should result in static
    # structural
    post_app_vertex.synapse_dynamics = static
    post_app_vertex.synapse_dynamics = static_struct
    assert isinstance(
        post_app_vertex.synapse_dynamics, SynapseDynamicsStructuralStatic)

    # ... and should fail here because of differences
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_static_struct
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_stdp_struct

    # This should be fine
    post_app_vertex.synapse_dynamics = static

    # This should be OK, but should merge with STDP (opposite of above)
    post_app_vertex.synapse_dynamics = stdp
    assert isinstance(
        post_app_vertex.synapse_dynamics, SynapseDynamicsStructuralSTDP)

    # ... and now these should fail
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_stdp
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_static_struct
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_stdp_struct
    with pytest.raises(SynapticConfigurationException):
        post_app_vertex.synapse_dynamics = alt_stdp_struct_2

    # OK, just one more, honest
    post_app_vertex = post_app_model.create_vertex(
        n_neurons=10, label="post", spikes_per_second=None,
        ring_buffer_sigma=None, incoming_spike_buffer_size=None,
        n_steps_per_timestep=1, drop_late_spikes=True, splitter=None,
        seed=None, n_colour_bits=None)
    post_app_vertex.synapse_dynamics = static_struct
    post_app_vertex.synapse_dynamics = stdp_struct


@pytest.mark.parametrize(
    "undelayed_indices_connected,delayed_indices_connected,n_pre_neurons,"
    "neurons_per_core,max_delay", [
        # Only undelayed, all edges exist
        (range(10), [], 1000, 100, None),
        # Only delayed, all edges exist
        ([], range(10), 1000, 100, 200),
        # All undelayed and delayed edges exist
        (range(10), range(10), 1000, 100, 200),
        # Only undelayed, some connections missing but app keys can still work
        ([0, 1, 2, 3, 4], [], 1000, 100, None),
        # Only delayed, some connections missing but app keys can still work
        ([], [5, 6, 7, 8, 9], 1000, 100, 200),
        # Both delayed and undelayed, some undelayed edges don't exist
        # (app keys work because undelayed aren't filtered)
        ([3, 4, 5, 6, 7], range(10), 1000, 100, 200),
        # Both delayed and undelayed, some delayed edges don't exist
        # (app keys work because all undelayed exist)
        (range(10), [4, 5, 6, 7], 1000, 100, 200),
        # Should work but number of cores doesn't work out
        (range(2000), [], 10000, 5, None)
    ])
def test_pop_based_master_pop_table_standard(
        undelayed_indices_connected, delayed_indices_connected,
        n_pre_neurons, neurons_per_core, max_delay):
    unittest_setup()
    set_config("Machine", "version", 5)
    writer = SpynnakerDataWriter.mock()

    # Build a from list connector with the delays we want
    connections = []
    connections.extend([(i * neurons_per_core + j, j, 0, 10)
                        for i in undelayed_indices_connected
                        for j in range(100)])
    connections.extend([(i * neurons_per_core + j, j, 0, max_delay)
                        for i in delayed_indices_connected
                        for j in range(100)])

    # Make simple source and target, where the source has 1000 atoms
    # split into 10 vertices (100 each) and the target has 100 atoms in
    # a single vertex
    post_pop = p.Population(
        256, p.IF_curr_exp(), label="Post",
        additional_parameters={
            "splitter": SplitterAbstractPopulationVertexFixed()})
    p.IF_curr_exp.set_model_max_atoms_per_dimension_per_core(neurons_per_core)
    pre_pop = p.Population(
        n_pre_neurons, p.IF_curr_exp(), label="Pre",
        additional_parameters={
            "splitter": SplitterAbstractPopulationVertexFixed()})
    p.Projection(
        pre_pop, post_pop, p.FromListConnector(connections), p.StaticSynapse())

    writer.set_plan_n_timesteps(100)
    d_vertices, d_edges = delay_support_adder()
    for vertex in d_vertices:
        writer.add_vertex(vertex)
    for edge in d_edges:
        writer.add_edge(
            edge, constants.SPIKE_PARTITION_ID)
    splitter_partitioner()
    allocator = ZonedRoutingInfoAllocator()
    writer.set_routing_infos(allocator.__call__([], flexible=False))

    post_mac_vertex = next(iter(post_pop._vertex.machine_vertices))
    post_vertex_slice = post_mac_vertex.vertex_slice

    # Generate the data
    with DsSqlliteDatabase() as db:
        spec = DataSpecificationGenerator(1, 2, 3, post_mac_vertex, db)

        regions = SynapseRegions(
            synapse_params=5, synapse_dynamics=6, structural_dynamics=7,
            bitfield_filter=8,
            synaptic_matrix=1, pop_table=3, connection_builder=4)
        references = SynapseRegions(
            synapse_params=None, synapse_dynamics=None,
            structural_dynamics=None, bitfield_filter=None,
            synaptic_matrix=None, pop_table=None, connection_builder=None)
        synaptic_matrices = SynapticMatrices(
            post_pop._vertex, regions, max_atoms_per_core=neurons_per_core,
            weight_scales=[32, 32], all_syn_block_sz=10000000)
        synaptic_matrices.generate_data()
        synaptic_matrices.write_synaptic_data(
            spec, post_vertex_slice, references)

        # Read the population table and check entries
        info = list(db.get_region_pointers_and_content(1, 2, 3))
    region, _, region_data = info[1]
    assert region == 3
    mpop_data = numpy.frombuffer(region_data, dtype="uint8").view("uint32")
    n_entries = mpop_data[0]
    n_addresses = mpop_data[1]

    # Always one for undelayed, maybe one for delayed if present
    n_app_entries = 1 + int(bool(delayed_indices_connected))
    expected_n_entries = n_app_entries
    expected_n_addresses = n_app_entries

    assert n_entries == expected_n_entries
    assert n_addresses == expected_n_addresses
