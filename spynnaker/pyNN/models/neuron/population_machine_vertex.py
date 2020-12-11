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
import os

from pacman.executor.injection_decorator import inject_items
from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification, AbstractRewritesDataSpecification)
from .population_machine_common import CommonRegions, PopulationMachineCommon
from .population_machine_neurons import (
    NeuronRegions, PopulationMachineNeurons, NeuronProvenance)
from .population_machine_synapses import (
    SynapseRegions, PopulationMachineSynapses, SynapseProvenance)


class PopulationMachineVertex(
        PopulationMachineCommon,
        PopulationMachineNeurons,
        PopulationMachineSynapses,
        AbstractGeneratesDataSpecification,
        AbstractRewritesDataSpecification):

    __slots__ = [
        "__change_requires_neuron_parameters_reload",
        "__synaptic_matrices",
        "__key"]

    class REGIONS(Enum):
        """Regions for populations."""
        SYSTEM = 0
        NEURON_PARAMS = 1
        SYNAPSE_PARAMS = 2
        POPULATION_TABLE = 3
        SYNAPTIC_MATRIX = 4
        SYNAPSE_DYNAMICS = 5
        STRUCTURAL_DYNAMICS = 6
        NEURON_RECORDING = 7
        PROVENANCE_DATA = 8
        PROFILING = 9
        CONNECTOR_BUILDER = 10
        DIRECT_MATRIX = 11
        BIT_FIELD_FILTER = 12
        BIT_FIELD_BUILDER = 13
        BIT_FIELD_KEY_MAP = 14
        RECORDING = 15

    COMMON_REGIONS = CommonRegions(
        system=REGIONS.SYSTEM.value,
        provenance=REGIONS.PROVENANCE_DATA.value,
        profile=REGIONS.PROFILING.value,
        recording=REGIONS.RECORDING.value)

    NEURON_REGIONS = NeuronRegions(
        neuron_params=REGIONS.NEURON_PARAMS.value,
        neuron_recording=REGIONS.NEURON_RECORDING.value
    )

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
        0: "TIMER",
        1: "DMA_READ",
        2: "INCOMING_SPIKE",
        3: "PROCESS_FIXED_SYNAPSES",
        4: "PROCESS_PLASTIC_SYNAPSES"}

    def __init__(
            self, resources_required, label, constraints, app_vertex,
            vertex_slice):
        """
        :param ~pacman.model.resources.ResourceContainer resources_required:
        :param iterable(int) recorded_region_ids:
        :param str label:
        :param list(~pacman.model.constraints.AbstractConstraint) constraints:
        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the population that this implements
        """
        super(PopulationMachineVertex, self).__init__(
            label, constraints, app_vertex, vertex_slice, resources_required,
            self.COMMON_REGIONS,
            NeuronProvenance.N_ITEMS + SynapseProvenance.N_ITEMS,
            self._PROFILE_TAG_LABELS, self.__get_binary_file_name(app_vertex))
        self.__key = None
        self.__synaptic_matrices = self._create_synaptic_matrices()

    @property
    @overrides(PopulationMachineNeurons._key)
    def _key(self):
        return self.__key

    @overrides(PopulationMachineNeurons._set_key)
    def _set_key(self, key):
        self.__key = key

    @property
    @overrides(PopulationMachineNeurons._neuron_regions)
    def _neuron_regions(self):
        return self.NEURON_REGIONS

    @property
    @overrides(PopulationMachineSynapses._synapse_regions)
    def _synapse_regions(self):
        return self.SYNAPSE_REGIONS

    @property
    @overrides(PopulationMachineSynapses._synaptic_matrices)
    def _synaptic_matrices(self):
        return self.__synaptic_matrices

    def __get_binary_file_name(self, app_vertex):
        # Split binary name into title and extension
        name, ext = os.path.splitext(app_vertex.neuron_impl.binary_name)

        # Reunite title and extension and return
        return name + app_vertex.synapse_executable_suffix + ext

    @overrides(PopulationMachineCommon.append_additional_provenance)
    def append_additional_provenance(
            self, provenance_items, prov_list_from_machine, placement):
        # translate into provenance data items
        offset = self._append_neuron_provenance(
            provenance_items, prov_list_from_machine, 0, placement)
        self._append_synapse_provenance(
            provenance_items, prov_list_from_machine, offset, placement)

    @overrides(PopulationMachineCommon.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        ids = self._app_vertex.neuron_recorder.recorded_ids_by_slice(
            self.vertex_slice)
        ids.extend(self._app_vertex.synapse_recorder.recorded_ids_by_slice(
            self.vertex_slice))
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
            "machine_time_step", "time_scale_factor",
            "machine_graph", "routing_info",
            "data_n_time_steps", "n_key_map"
        })
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            machine_graph, routing_info, data_n_time_steps,
            n_key_map):
        """
        :param machine_time_step: (injected)
        :param time_scale_factor: (injected)
        :param application_graph: (injected)
        :param machine_graph: (injected)
        :param routing_info: (injected)
        :param data_n_time_steps: (injected)
        :param n_key_map: (injected)
        """

        rec_regions = self._app_vertex.neuron_recorder.get_region_sizes(
            self.vertex_slice, data_n_time_steps)
        rec_regions.extend(self._app_vertex.synapse_recorder.get_region_sizes(
            self.vertex_slice, data_n_time_steps))
        self.write_common_data_spec(
            spec, machine_time_step, time_scale_factor, rec_regions)

        self.write_neuron_data_spec(spec, routing_info)

        self.write_synapse_data_spec(
            spec, machine_time_step, routing_info, machine_graph, n_key_map)

        # End the writing of this specification:
        spec.end_specification()

    @inject_items({"routing_info": "MemoryRoutingInfos"})
    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification,
        additional_arguments={"routing_info"})
    def regenerate_data_specification(self, spec, placement, routing_info):
        # pylint: disable=too-many-arguments, arguments-differ

        # write the neuron params into the new DSG region
        self._write_neuron_parameters(
            spec, self.NEURON_REGIONS.neuron_params, routing_info)

        # close spec
        spec.end_specification()

    @overrides(AbstractRewritesDataSpecification.reload_required)
    def reload_required(self):
        return self.__change_requires_neuron_parameters_reload

    @overrides(AbstractRewritesDataSpecification.set_reload_required)
    def set_reload_required(self, new_value):
        self.__change_requires_neuron_parameters_reload = new_value
