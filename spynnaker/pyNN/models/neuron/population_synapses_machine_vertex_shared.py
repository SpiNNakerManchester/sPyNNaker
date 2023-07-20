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
from __future__ import annotations
from typing import Sequence, cast, TYPE_CHECKING
from spinn_utilities.overrides import overrides
from pacman.model.graphs.common import Slice
from pacman.model.resources import AbstractSDRAM
from pacman.model.placements import Placement
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification)
from spinn_front_end_common.interface.ds import DataSpecificationGenerator
from .population_synapses_machine_vertex_common import (
    PopulationSynapsesMachineVertexCommon)
from .population_machine_synapses_provenance import (
    PopulationMachineSynapsesProvenance)
if TYPE_CHECKING:
    from .abstract_population_vertex import AbstractPopulationVertex
    from spynnaker.pyNN.models.neuron.synaptic_matrices import SynapseRegions


class PopulationSynapsesMachineVertexShared(
        PopulationSynapsesMachineVertexCommon,
        PopulationMachineSynapsesProvenance,
        AbstractGeneratesDataSpecification):
    """
    A machine vertex for PyNN Populations.
    """

    __slots__ = ("__synapse_references", )

    def __init__(
            self, sdram: AbstractSDRAM, label: str,
            app_vertex: AbstractPopulationVertex, vertex_slice: Slice,
            synapse_references: SynapseRegions):
        """
        :param ~pacman.model.resources.AbstractSDRAM sdram:
            The SDRAM used by the vertex
        :param str label: The label of the vertex
        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the population that this implements
        """
        super().__init__(sdram, label, app_vertex, vertex_slice)
        self.__synapse_references = synapse_references

    @overrides(AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(
            self, spec: DataSpecificationGenerator, placement: Placement):
        rec_regions = self._pop_vertex.synapse_recorder.get_region_sizes(
            self.vertex_slice)
        self._write_common_data_spec(spec, rec_regions)

        # Write references to shared regions
        for reg, ref in zip(self.SYNAPSE_REGIONS, self.__synapse_references):
            if ref is not None:
                # Ignore a region if there's no target reference
                spec.reference_memory_region(cast(int, reg), ref)

        # Write information about SDRAM
        self._write_sdram_edge_spec(spec)

        # Write information about keys
        self._write_key_spec(spec)

        # End the writing of this specification:
        spec.end_specification()

    @overrides(PopulationSynapsesMachineVertexCommon._parse_synapse_provenance)
    def _parse_synapse_provenance(
            self, label: str, x: int, y: int, p: int,
            provenance_data: Sequence[int]):
        return PopulationMachineSynapsesProvenance._parse_synapse_provenance(
            self, label, x, y, p, provenance_data)
