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
            self, resources_required, label, constraints, app_vertex,
            vertex_slice, synapse_references):
        """
        :param ~pacman.model.resources.ResourceContainer resources_required:
            The resources used by the vertex
        :param str label: The label of the vertex
        :param list(~pacman.model.constraints.AbstractConstraint) constraints:
            Constraints for the vertex
        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the population that this implements
        """
        super(PopulationSynapsesMachineVertexShared, self).__init__(
            resources_required, label, constraints, app_vertex, vertex_slice)
        self.__synapse_references = synapse_references

    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(self, spec, placement):
        """
        :param n_key_map: (injected)
        """
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
