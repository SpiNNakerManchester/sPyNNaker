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
from enum import Enum

from pacman.executor.injection_decorator import inject_items
from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification)
from .population_machine_common import CommonRegions, PopulationMachineCommon
from .population_machine_synapses import (
    SynapseRegions, PopulationMachineSynapses, SynapseProvenance)


class PopulationSynapsesMachineVertex(
        PopulationMachineCommon,
        PopulationMachineSynapses,
        AbstractGeneratesDataSpecification):
    """ A machine vertex for PyNN Populations
    """

    __slots__ = [
        "__change_requires_neuron_parameters_reload",
        "__synaptic_matrices",
        "__key"]

    class REGIONS(Enum):
        """Regions for populations."""
        SYSTEM = 0
        PROVENANCE_DATA = 1
        PROFILING = 2
        RECORDING = 3
        SYNAPSE_PARAMS = 4
        DIRECT_MATRIX = 5
        SYNAPTIC_MATRIX = 6
        POPULATION_TABLE = 7
        SYNAPSE_DYNAMICS = 8
        STRUCTURAL_DYNAMICS = 9
        BIT_FIELD_FILTER = 10
        CONNECTOR_BUILDER = 11
        BIT_FIELD_BUILDER = 12
        BIT_FIELD_KEY_MAP = 13

    # Regions for this vertex used by common parts
    COMMON_REGIONS = CommonRegions(
        system=REGIONS.SYSTEM.value,
        provenance=REGIONS.PROVENANCE_DATA.value,
        profile=REGIONS.PROFILING.value,
        recording=REGIONS.RECORDING.value)

    # Regions for this vertex used by synapse parts
    SYNAPSE_REGIONS = SynapseRegions(
        synapse_params=REGIONS.SYNAPSE_PARAMS.value,
        direct_matrix=REGIONS.DIRECT_MATRIX.value,
        pop_table=REGIONS.POPULATION_TABLE.value,
        synaptic_matrix=REGIONS.SYNAPTIC_MATRIX.value,
        synapse_dynamics=REGIONS.SYNAPSE_DYNAMICS.value,
        structural_dynamics=REGIONS.STRUCTURAL_DYNAMICS.value,
        bitfield_builder=REGIONS.BIT_FIELD_BUILDER.value,
        bitfield_key_map=REGIONS.BIT_FIELD_KEY_MAP.value,
        bitfield_filter=REGIONS.BIT_FIELD_FILTER.value,
        connection_builder=REGIONS.CONNECTOR_BUILDER.value
    )

    _PROFILE_TAG_LABELS = {
        0: "TIMER_SYNAPSES",
        1: "DMA_READ",
        2: "INCOMING_SPIKE",
        3: "PROCESS_FIXED_SYNAPSES",
        4: "PROCESS_PLASTIC_SYNAPSES"}

    def __init__(
            self, resources_required, label, constraints, app_vertex,
            vertex_slice):
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
        super(PopulationSynapsesMachineVertex, self).__init__(
            label, constraints, app_vertex, vertex_slice, resources_required,
            self.COMMON_REGIONS,
            SynapseProvenance.N_ITEMS,
            self._PROFILE_TAG_LABELS, self.__get_binary_file_name(app_vertex))
        self.__key = None
        self.__synaptic_matrices = self._create_synaptic_matrices()
        self.__change_requires_neuron_parameters_reload = False

    @property
    @overrides(PopulationMachineSynapses._synapse_regions)
    def _synapse_regions(self):
        return self.SYNAPSE_REGIONS

    @property
    @overrides(PopulationMachineSynapses._synaptic_matrices)
    def _synaptic_matrices(self):
        return self.__synaptic_matrices

    @staticmethod
    def __get_binary_file_name(app_vertex):
        """ Get the local binary filename for this vertex.  Static because at
            the time this is needed, the local app_vertex is not set.

        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :rtype: str
        """

        # Reunite title and extension and return
        return "synapses" + app_vertex.synapse_executable_suffix + ".aplx"

    @overrides(PopulationMachineCommon._append_additional_provenance)
    def _append_additional_provenance(
            self, provenance_items, prov_list_from_machine, placement):
        # translate into provenance data items
        self._append_synapse_provenance(
            provenance_items, prov_list_from_machine, 0, placement)

    @overrides(PopulationMachineCommon.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        ids = self._app_vertex.synapse_recorder.recorded_ids_by_slice(
            self.vertex_slice)
        return ids

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "machine_graph": "MemoryMachineGraph",
        "routing_info": "MemoryRoutingInfos",
        "data_n_time_steps": "DataNTimeSteps",
        "n_key_map": "MemoryMachinePartitionNKeysMap"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "machine_graph",
            "routing_info", "data_n_time_steps", "n_key_map"
        })
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            machine_graph, routing_info, data_n_time_steps, n_key_map):
        """
        :param machine_time_step: (injected)
        :param time_scale_factor: (injected)
        :param machine_graph: (injected)
        :param routing_info: (injected)
        :param data_n_time_steps: (injected)
        :param n_key_map: (injected)
        """
        # pylint: disable=arguments-differ
        rec_regions = self._app_vertex.synapse_recorder.get_region_sizes(
            self.vertex_slice, data_n_time_steps)
        self._write_common_data_spec(
            spec, machine_time_step, time_scale_factor, rec_regions)

        self._write_synapse_data_spec(
            spec, machine_time_step, routing_info, machine_graph, n_key_map)

        # End the writing of this specification:
        spec.end_specification()
