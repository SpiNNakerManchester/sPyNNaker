# Copyright (c) 2017 The University of Manchester
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
    AbstractGeneratesDataSpecification, AbstractRewritesDataSpecification)
from .population_machine_common import PopulationMachineCommon
from .population_machine_synapses import PopulationMachineSynapses
from .population_synapses_machine_vertex_common import (
    PopulationSynapsesMachineVertexCommon)


class PopulationSynapsesMachineVertexLead(
        PopulationSynapsesMachineVertexCommon,
        PopulationMachineSynapses,
        AbstractGeneratesDataSpecification,
        AbstractRewritesDataSpecification):
    """ A synaptic machine vertex that leads other Synaptic machine vertices,
        writing shared areas.
    """

    __slots__ = [
        "__synaptic_matrices",
        "__min_weights",
        "__weight_scales",
        "__structural_sz",
        "__synapse_references",
        "__max_atoms_per_core",
        "__regenerate_data"]

    def __init__(
            self, sdram, label, app_vertex,
            vertex_slice, min_weights, weight_scales, structural_sz,
            synapse_references, max_atoms_per_core, synaptic_matrices):
        """
        :param ~pacman.model.resources.AbstractSDRAM sdram:
            The sdram used by the vertex
        :param str label: The label of the vertex
        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the population that this implements
        :param list(float) min_weights:
            The computed minimum weights to be used in the simulation
        """
        super(PopulationSynapsesMachineVertexLead, self).__init__(
            sdram, label, app_vertex, vertex_slice)
        self.__min_weights = min_weights
        self.__weight_scales = weight_scales
        self.__structural_sz = structural_sz
        self.__synapse_references = synapse_references
        self.__max_atoms_per_core = max_atoms_per_core
        self.__regenerate_data = False

        # Need to do this last so that the values above can be used
        self.__synaptic_matrices = synaptic_matrices

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

    @property
    @overrides(PopulationMachineSynapses._max_atoms_per_core)
    def _max_atoms_per_core(self):
        return self.__max_atoms_per_core

    @overrides(PopulationMachineCommon.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        ids = self._app_vertex.synapse_recorder.recorded_ids_by_slice(
            self.vertex_slice)
        return ids

    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(self, spec, placement):
        """
        :param routing_info: (injected)
        """
        # pylint: disable=arguments-differ
        rec_regions = self._app_vertex.synapse_recorder.get_region_sizes(
            self.vertex_slice)
        self._write_common_data_spec(spec, rec_regions)

        self._write_synapse_data_spec(
            spec, self.__min_weights,
            self.__weight_scales, self.__structural_sz)

        # Write information about SDRAM
        self._write_sdram_edge_spec(spec)

        # Write information about keys
        self._write_key_spec(spec)

        # End the writing of this specification:
        spec.end_specification()

    @overrides(PopulationSynapsesMachineVertexCommon._parse_synapse_provenance)
    def _parse_synapse_provenance(self, label, x, y, p, provenance_data):
        return PopulationMachineSynapses._parse_synapse_provenance(
            self, label, x, y, p, provenance_data)

    @overrides(AbstractRewritesDataSpecification.regenerate_data_specification)
    def regenerate_data_specification(self, spec, placement):
        # We don't need to do anything here because the originally written
        # data can be used again
        pass

    @overrides(AbstractRewritesDataSpecification.reload_required)
    def reload_required(self):
        return self.__regenerate_data

    @overrides(AbstractRewritesDataSpecification.set_reload_required)
    def set_reload_required(self, new_value):
        self.__regenerate_data = new_value

    @overrides(PopulationMachineSynapses.set_do_synapse_regeneration)
    def set_do_synapse_regeneration(self):
        self.__regenerate_data = True
