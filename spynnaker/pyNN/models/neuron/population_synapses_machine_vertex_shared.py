# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification)
from .population_synapses_machine_vertex_common import (
    PopulationSynapsesMachineVertexCommon)
from .population_machine_synapses_provenance import (
    PopulationMachineSynapsesProvenance)


class PopulationSynapsesMachineVertexShared(
        PopulationSynapsesMachineVertexCommon,
        PopulationMachineSynapsesProvenance,
        AbstractGeneratesDataSpecification):
    """ A machine vertex for PyNN Populations
    """

    __slots__ = [
        "__synapse_references"
    ]

    def __init__(
            self, sdram, label, app_vertex, vertex_slice, synapse_references):
        """
        :param ~pacman.model.resources.AbstractSDRAM sdram:
            The sdram used by the vertex
        :param str label: The label of the vertex
        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the population that this implements
        """
        super(PopulationSynapsesMachineVertexShared, self).__init__(
            sdram, label, app_vertex, vertex_slice)
        self.__synapse_references = synapse_references

    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(self, spec, placement):
        # pylint: disable=arguments-differ
        rec_regions = self._app_vertex.synapse_recorder.get_region_sizes(
            self.vertex_slice)
        self._write_common_data_spec(spec, rec_regions)

        # Write references to shared regions
        for reg, ref in zip(self.SYNAPSE_REGIONS, self.__synapse_references):
            spec.reference_memory_region(reg, ref)

        # Write information about SDRAM
        self._write_sdram_edge_spec(spec)

        # Write information about keys
        self._write_key_spec(spec)

        # End the writing of this specification:
        spec.end_specification()

    @overrides(PopulationSynapsesMachineVertexCommon._parse_synapse_provenance)
    def _parse_synapse_provenance(self, label, x, y, p, provenance_data):
        return PopulationMachineSynapsesProvenance._parse_synapse_provenance(
            self, label, x, y, p, provenance_data)
