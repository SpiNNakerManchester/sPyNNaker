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
from pacman.executor.injection_decorator import inject_items
from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification)
from .population_machine_common import PopulationMachineCommon
from .population_machine_synapses import PopulationMachineSynapses
from .population_synapses_machine_vertex_common import (
    PopulationSynapsesMachineVertexCommon)


class PopulationSynapsesMachineVertexLead(
        PopulationSynapsesMachineVertexCommon,
        PopulationMachineSynapses,
        AbstractGeneratesDataSpecification):
    """ A synaptic machine vertex that leads other Synaptic machine vertices,
        writing shared areas.
    """

    __slots__ = [
        "__synaptic_matrices",
        "__min_weights",
        "__weight_scales",
        "__all_syn_block_sz",
        "__structural_sz",
        "__synapse_references"]

    def __init__(
            self, resources_required, label, constraints, app_vertex,
            vertex_slice, min_weights, weight_scales, all_syn_block_sz,
            structural_sz, synapse_references):
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
        :param list(float) min_weights:
            The computed minimum weights to be used in the simulation
        """
        super(PopulationSynapsesMachineVertexLead, self).__init__(
            resources_required, label, constraints, app_vertex, vertex_slice)
        self.__min_weights = min_weights
        self.__weight_scales = weight_scales
        self.__all_syn_block_sz = all_syn_block_sz
        self.__structural_sz = structural_sz
        self.__synapse_references = synapse_references

        # Need to do this last so that the values above can be used
        self.__synaptic_matrices = self._create_synaptic_matrices(False)

    @property
    @overrides(PopulationMachineSynapses._synapse_regions)
    def _synapse_regions(self):
        return self.SYNAPSE_REGIONS

    @property
    @overrides(PopulationMachineSynapses._synaptic_matrices)
    def _synaptic_matrices(self):
        return self.__synaptic_matrices

    @property
    @overrides(PopulationMachineSynapses._synapse_references)
    def _synapse_references(self):
        return self.__synapse_references

    @overrides(PopulationMachineCommon.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        ids = self._app_vertex.synapse_recorder.recorded_ids_by_slice(
            self.vertex_slice)
        return ids

    @inject_items({
        "routing_info": "RoutingInfos",
        "data_n_time_steps": "DataNTimeSteps"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={"routing_info", "data_n_time_steps"})
    def generate_data_specification(
            self, spec, placement, routing_info, data_n_time_steps):
        """
        :param routing_info: (injected)
        :param data_n_time_steps: (injected)
        """
        # pylint: disable=arguments-differ
        rec_regions = self._app_vertex.synapse_recorder.get_region_sizes(
            self.vertex_slice, data_n_time_steps)
        self._write_common_data_spec(spec, rec_regions)

        self._write_synapse_data_spec(
            spec, routing_info, self.__min_weights,
            self.__weight_scales, self.__all_syn_block_sz,
            self.__structural_sz)

        # Write information about SDRAM
        self._write_sdram_edge_spec(spec)

        # Write information about keys
        self._write_key_spec(spec, routing_info)

        # End the writing of this specification:
        spec.end_specification()

    @overrides(PopulationSynapsesMachineVertexCommon._parse_synapse_provenance)
    def _parse_synapse_provenance(self, label, x, y, p, provenance_data):
        return PopulationMachineSynapses._parse_synapse_provenance(
            self, label, x, y, p, provenance_data)
