# Copyright (c) 2021-2022 The University of Manchester
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
from .population_machine_local_only_synapses_vertex_common import (
    PopulationMachineLocalOnlySynapsesVertexCommon)


class PopulationMachineLocalOnlySynapsesVertexShared(
        PopulationMachineLocalOnlySynapsesVertexCommon,
        AbstractGeneratesDataSpecification):
    """ A machine vertex for PyNN Populations
    """

    __slots__ = ["__synapse_references"]

    def __init__(self, sdram, label, app_vertex, vertex_slice,
                 synapse_references):
        """
        :param ~pacman.model.resources.AbstractSDRAM sdram:
            The sdram used by the vertex
        :param str label: The label of the vertex
        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the population that this implements
        """
        super(PopulationMachineLocalOnlySynapsesVertexShared, self).__init__(
            sdram, label, app_vertex, vertex_slice)
        self.__synapse_references = synapse_references

    @overrides(AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(self, spec, placement):
        # pylint: disable=arguments-differ
        rec_regions = self._app_vertex.synapse_recorder.get_region_sizes(
            self.vertex_slice)
        self._write_common_data_spec(spec, rec_regions)
        self._write_sdram_edge_spec(spec)

        spec.reference_memory_region(
            self.REGIONS.LOCAL_ONLY.value,
            self.__synapse_references.local_only)
        spec.reference_memory_region(
            self.REGIONS.LOCAL_ONLY_PARAMS.value,
            self.__synapse_references.local_only_params)

        # End the writing of this specification:
        spec.end_specification()
