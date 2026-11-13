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

"""Check selection and data-spec allocation of the optional firmware."""

import struct

import pyNN.spiNNaker as sim
import pytest

from spinn_utilities.config_holder import set_config

from pacman.model.graphs.machine import MachineVertex

from spinn_front_end_common.abstract_models import AbstractHasAssociatedBinary
from spinn_front_end_common.interface.ds.ds_sqllite_database import (
    DsSqlliteDatabase,
)

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterPopulationVertexFixed,
    SplitterPopulationVertexNeuronsSynapses,
)


@pytest.mark.parametrize("split", [False, True])
def test_no_spike_update_mapping(split: bool) -> None:
    sim.setup(timestep=1.0)
    try:
        set_config("Machine", "virtual_board", "True")
        set_config("Machine", "version", "5")
        dynamics = sim.STDPMechanism(
            timing_dependence=sim.SpikePairRule(),
            weight_dependence=sim.AdditiveWeightDependence(),
            no_spike_updates_per_timestep=2, no_spike_update_capacity=8)
        source = sim.Population(1, sim.SpikeSourceArray(spike_times=[1]))
        extra = {
            "splitter": SplitterPopulationVertexNeuronsSynapses() if split
            else SplitterPopulationVertexFixed(),
            "n_synapse_cores": 2 if split else 0,
        }
        target = sim.Population(
            5, sim.IF_curr_exp(), additional_parameters=extra)
        sim.Projection(
            source, target, sim.AllToAllConnector(), synapse_type=dynamics)
        sim.run(2)

        synapse_vertices = [
            vertex
            for vertex in target._vertex.machine_vertices
            if isinstance(vertex, MachineVertex) and
            isinstance(vertex, AbstractHasAssociatedBinary) and
            vertex.get_binary_file_name().endswith("_no_spike_updates.aplx")
        ]
        assert len(synapse_vertices) == (2 if split else 1)
        region = 13 if split else 17
        with DsSqlliteDatabase() as ds:
            for vertex in synapse_vertices:
                placement = SpynnakerDataView.get_placement_of_vertex(vertex)
                xyz = placement.x, placement.y, placement.p
                # The shared synapse core needs its own region with content,
                # rather than a reference to the lead core's registry.
                assert ds.get_region_size(*xyz, region) == 488
                contents = {
                    number: data for number, _, data
                    in ds.get_regions_content(*xyz)
                }
                assert contents[region] == struct.pack("<II", 2, 8)
    finally:
        sim.end()


def test_no_spike_updates_cannot_merge_with_structural() -> None:
    sim.setup(timestep=1.0)
    try:
        stdp = sim.STDPMechanism(
            timing_dependence=sim.SpikePairRule(),
            weight_dependence=sim.AdditiveWeightDependence(),
            no_spike_updates_per_timestep=1)
        structural = sim.StructuralMechanismStatic(
            sim.RandomSelection(), sim.DistanceDependentFormation([3, 3]),
            sim.RandomByWeightElimination(4.0), delay=1.0)
        with pytest.raises(SynapticConfigurationException,
                           match="structural plasticity"):
            structural.merge(stdp)
        with pytest.raises(SynapticConfigurationException,
                           match="structural plasticity"):
            stdp.merge(structural)
    finally:
        sim.end()
