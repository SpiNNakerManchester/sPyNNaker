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
import shutil
import struct
import tempfile
from tempfile import mkdtemp
import numpy
import pytest

from spinn_machine import SDRAM
from spinn_utilities.overrides import overrides
from spinn_utilities.config_holder import load_config
from spinnman.model import CPUInfo
from spinnman.transceiver import Transceiver
from pacman.model.placements import Placement
from pacman.operations.routing_info_allocator_algorithms import (
    ZonedRoutingInfoAllocator)
from data_specification import (
    DataSpecificationGenerator, DataSpecificationExecutor)
from data_specification.constants import MAX_MEM_REGIONS
from spynnaker.pyNN.data.spynnaker_data_writer import SpynnakerDataWriter
from spynnaker.pyNN.models.neuron.synaptic_matrices import SynapticMatrices
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
    SplitterAbstractPopulationVertexFixed, spynnaker_splitter_partitioner)
from spynnaker.pyNN.extra_algorithms import delay_support_adder
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.config_setup import unittest_setup
import pyNN.spiNNaker as p


class MockTransceiverRawData(Transceiver):
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


def say_false(self, weights, delays):
    return False


def test_write_data_spec():
    unittest_setup()
    writer = SpynnakerDataWriter.mock()
    SDRAM()
    # UGLY but the mock transceiver NEED generate_on_machine to be False
    AbstractGenerateConnectorOnMachine.generate_on_machine = say_false

    p.setup(1.0)
    load_config()
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

    writer.start_run()
    writer.set_plan_n_timesteps(100)
    delay_support_adder()
    spynnaker_splitter_partitioner()
    allocator = ZonedRoutingInfoAllocator()
    writer.set_routing_infos(allocator.__call__([], flexible=False))

    post_vertex = next(iter(post_pop._vertex.machine_vertices))
    post_vertex_slice = post_vertex.vertex_slice
    post_vertex_placement = Placement(post_vertex, 0, 0, 3)

    temp_spec = tempfile.mktemp()
    spec = DataSpecificationGenerator(io.FileIO(temp_spec, "wb"), None)

    synaptic_matrices = SynapticMatrices(
        post_vertex_slice, n_synapse_types=2, all_single_syn_sz=10000,
        synaptic_matrix_region=1, direct_matrix_region=2, poptable_region=3,
        connection_builder_region=4)
    synaptic_matrices.write_synaptic_data(
        spec, post_pop._vertex.incoming_projections, all_syn_block_sz=10000,
        weight_scales=[32, 32])
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

    writer.set_transceiver(MockTransceiverRawData(all_data))
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
        assert len(connections_3) == 100
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
    unittest_setup()
    p.setup(1.0)
    post_app_model = IFCurrExpBase()
    post_app_vertex = post_app_model.create_vertex(
        n_neurons=10, label="post", spikes_per_second=None,
        ring_buffer_sigma=None, incoming_spike_buffer_size=None,
        n_steps_per_timestep=1, drop_late_spikes=True, splitter=None)

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
        n_steps_per_timestep=1, drop_late_spikes=True, splitter=None)

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
        n_steps_per_timestep=1, drop_late_spikes=True, splitter=None)

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
        n_steps_per_timestep=1, drop_late_spikes=True, splitter=None)
    post_app_vertex.synapse_dynamics = static_struct
    post_app_vertex.synapse_dynamics = stdp_struct


@pytest.mark.parametrize(
    "undelayed_indices_connected,delayed_indices_connected,n_pre_neurons,"
    "neurons_per_core,expect_app_keys,max_delay", [
        # Only undelayed, all edges exist
        (range(10), [], 1000, 100, True, None),
        # Only delayed, all edges exist
        ([], range(10), 1000, 100, True, 20),
        # All undelayed and delayed edges exist
        (range(10), range(10), 1000, 100, True, 20),
        # Only undelayed, some connections missing but app keys can still work
        ([0, 1, 2, 3, 4], [], 1000, 100, True, None),
        # Only delayed, some connections missing but app keys can still work
        ([], [5, 6, 7, 8, 9], 1000, 100, True, 20),
        # Both delayed and undelayed, some undelayed edges don't exist
        # (app keys work because undelayed aren't filtered)
        ([3, 4, 5, 6, 7], range(10), 1000, 100, True, 20),
        # Both delayed and undelayed, some delayed edges don't exist
        # (app keys work because all undelayed exist)
        (range(10), [4, 5, 6, 7], 1000, 100, True, 20),
        # Should work but number of cores doesn't work out
        (range(2000), [], 10000, 5, False, None),
        # Should work but number of neurons with delays don't work out
        ([], range(4), 1024, 256, False, 144)
    ])
def test_pop_based_master_pop_table_standard(
        undelayed_indices_connected, delayed_indices_connected,
        n_pre_neurons, neurons_per_core, expect_app_keys, max_delay):
    unittest_setup()
    writer = SpynnakerDataWriter.mock()
    SDRAM()

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
    p.setup(1.0)
    post_pop = p.Population(
        100, p.IF_curr_exp(), label="Post",
        additional_parameters={
            "splitter": SplitterAbstractPopulationVertexFixed()})
    p.IF_curr_exp.set_model_max_atoms_per_dimension_per_core(neurons_per_core)
    pre_pop = p.Population(
        n_pre_neurons, p.IF_curr_exp(), label="Pre",
        additional_parameters={
            "splitter": SplitterAbstractPopulationVertexFixed()})
    p.Projection(
        pre_pop, post_pop, p.FromListConnector(connections), p.StaticSynapse())

    writer.start_run()
    writer.set_plan_n_timesteps(100)
    delay_support_adder()
    spynnaker_splitter_partitioner()
    allocator = ZonedRoutingInfoAllocator()
    writer.set_routing_infos(allocator.__call__([], flexible=False))

    post_mac_vertex = next(iter(post_pop._vertex.machine_vertices))
    post_vertex_slice = post_mac_vertex.vertex_slice

    # Generate the data
    temp_spec = tempfile.mktemp()
    spec = DataSpecificationGenerator(io.FileIO(temp_spec, "wb"), None)

    synaptic_matrices = SynapticMatrices(
        post_vertex_slice, n_synapse_types=2, all_single_syn_sz=10000,
        synaptic_matrix_region=1, direct_matrix_region=2, poptable_region=3,
        connection_builder_region=4)
    synaptic_matrices.write_synaptic_data(
        spec, post_pop._vertex.incoming_projections, all_syn_block_sz=1000000,
        weight_scales=[32, 32])

    with io.FileIO(temp_spec, "rb") as spec_reader:
        executor = DataSpecificationExecutor(
            spec_reader, SDRAM.max_sdram_found)
        executor.execute()

    # Read the population table and check entries
    region = executor.get_region(3)
    mpop_data = numpy.frombuffer(
        region.region_data, dtype="uint8").view("uint32")
    n_entries = mpop_data[0]
    n_addresses = mpop_data[1]

    # Compute how many entries and addresses there should be
    expected_n_entries = 0
    expected_n_addresses = 0
    if expect_app_keys:
        # Always one for undelayed, maybe one for delayed if present
        n_app_entries = 1 + int(bool(delayed_indices_connected))
        expected_n_entries += n_app_entries
        # 2 address list entries for each entry, as there is also extra_info
        expected_n_addresses += 2 * n_app_entries

    # If both delayed and undelayed, there is an entry for each incoming
    # machine edge
    elif delayed_indices_connected and undelayed_indices_connected:
        all_connected = set(undelayed_indices_connected)
        all_connected.update(delayed_indices_connected)
        expected_n_entries += len(all_connected)
        expected_n_addresses += len(all_connected)

    # If there are only undelayed indices, there is an entry for each
    elif undelayed_indices_connected:
        expected_n_entries += len(undelayed_indices_connected)
        expected_n_addresses += len(undelayed_indices_connected)

    # If there are only delayed indices, there are two entries for each because
    # the undelayed ones are still connected
    else:
        expected_n_entries += 2 * len(delayed_indices_connected)
        expected_n_addresses += 2 * len(delayed_indices_connected)

    assert n_entries == expected_n_entries
    assert n_addresses == expected_n_addresses
