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
import ctypes

from pacman.executor.injection_decorator import inject_items
from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification, AbstractRewritesDataSpecification)
from spinn_front_end_common.utilities.utility_objs import ProvenanceDataItem
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl)
from .population_machine_common import CommonRegions, PopulationMachineCommon
from .population_machine_neurons import (
    NeuronRegions, PopulationMachineNeurons, NeuronProvenance)
from .population_machine_synapses import (
    SynapseRegions, PopulationMachineSynapses)
from .population_machine_synapses_provenance import SynapseProvenance


get_placement_details = \
    ProvidesProvenanceDataFromMachineImpl._get_placement_details
add_name = ProvidesProvenanceDataFromMachineImpl._add_name


class MainProvenance(ctypes.LittleEndianStructure):
    """ Provenance items from synapse processing
    """
    _fields_ = [
        # the maximum number of background tasks queued
        ("max_background_queued", ctypes.c_uint32),
        # the number of times the background queue overloaded
        ("n_background_overloads", ctypes.c_uint32)
    ]

    N_ITEMS = len(_fields_)


class PopulationMachineVertex(
        PopulationMachineCommon,
        PopulationMachineNeurons,
        PopulationMachineSynapses,
        AbstractGeneratesDataSpecification,
        AbstractRewritesDataSpecification):
    """ A machine vertex for PyNN Populations
    """

    __slots__ = [
        "__change_requires_neuron_parameters_reload",
        "__synaptic_matrices",
        "__key",
        "__ring_buffer_shifts",
        "__weight_scales",
        "__all_syn_block_sz",
        "__structural_sz",
        "__slice_index"]

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

    # Regions for this vertex used by common parts
    COMMON_REGIONS = CommonRegions(
        system=REGIONS.SYSTEM.value,
        provenance=REGIONS.PROVENANCE_DATA.value,
        profile=REGIONS.PROFILING.value,
        recording=REGIONS.RECORDING.value)

    # Regions for this vertex used by neuron parts
    NEURON_REGIONS = NeuronRegions(
        neuron_params=REGIONS.NEURON_PARAMS.value,
        neuron_recording=REGIONS.NEURON_RECORDING.value
    )

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

    _BACKGROUND_OVERLOADS_NAME = "Times_the_background_queue_overloaded"
    _BACKGROUND_MAX_QUEUED_NAME = "Max_backgrounds_queued"

    _PROFILE_TAG_LABELS = {
        0: "TIMER",
        1: "DMA_READ",
        2: "INCOMING_SPIKE",
        3: "PROCESS_FIXED_SYNAPSES",
        4: "PROCESS_PLASTIC_SYNAPSES"}

    def __init__(
            self, resources_required, label, constraints, app_vertex,
            vertex_slice, slice_index, ring_buffer_shifts, weight_scales,
            all_syn_block_sz, structural_sz):
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
        super(PopulationMachineVertex, self).__init__(
            label, constraints, app_vertex, vertex_slice, resources_required,
            self.COMMON_REGIONS,
            NeuronProvenance.N_ITEMS + SynapseProvenance.N_ITEMS +
            MainProvenance.N_ITEMS,
            self._PROFILE_TAG_LABELS, self.__get_binary_file_name(app_vertex))
        self.__key = None
        self.__synaptic_matrices = self._create_synaptic_matrices()
        self.__change_requires_neuron_parameters_reload = False
        self.__slice_index = slice_index
        self.__ring_buffer_shifts = ring_buffer_shifts
        self.__weight_scales = weight_scales
        self.__all_syn_block_sz = all_syn_block_sz
        self.__structural_sz = structural_sz

    @property
    @overrides(PopulationMachineNeurons._slice_index)
    def _slice_index(self):
        return self.__slice_index

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

    @staticmethod
    def __get_binary_file_name(app_vertex):
        """ Get the local binary filename for this vertex.  Static because at
            the time this is needed, the local app_vertex is not set.

        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :rtype: str
        """
        # Split binary name into title and extension
        name, ext = os.path.splitext(app_vertex.neuron_impl.binary_name)

        # Reunite title and extension and return
        return name + app_vertex.synapse_executable_suffix + ext

    @overrides(PopulationMachineCommon._append_additional_provenance)
    def _append_additional_provenance(
            self, provenance_items, prov_list_from_machine, placement):
        # translate into provenance data items
        offset = self._append_neuron_provenance(
            provenance_items, prov_list_from_machine, 0, placement)
        offset += self._append_synapse_provenance(
            provenance_items, prov_list_from_machine, offset, placement)
        main_prov = MainProvenance(
            *prov_list_from_machine[offset:MainProvenance.N_ITEMS + offset])
        label, x, y, p, names = get_placement_details(placement)
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self._BACKGROUND_MAX_QUEUED_NAME),
            main_prov.max_background_queued,
            report=main_prov.max_background_queued > 1,
            message=(
                "A maximum of {} background tasks were queued on {} on"
                " {}, {}, {}.  Try increasing the time_scale_factor located"
                " within the .spynnaker.cfg file or in the pynn.setup()"
                " method.".format(
                    main_prov.max_background_queued, label, x, y, p))))
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self._BACKGROUND_OVERLOADS_NAME),
            main_prov.n_background_overloads,
            report=main_prov.n_background_overloads > 0,
            message=(
                "On {} on {}, {}, {}, the background queue overloaded {}"
                " times.  Try increasing the time_scale_factor located within"
                " the .spynnaker.cfg file or in the pynn.setup() method."
                .format(label, x, y, p, main_prov.n_background_overloads))))

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
        rec_regions = self._app_vertex.neuron_recorder.get_region_sizes(
            self.vertex_slice, data_n_time_steps)
        rec_regions.extend(self._app_vertex.synapse_recorder.get_region_sizes(
            self.vertex_slice, data_n_time_steps))
        self._write_common_data_spec(
            spec, machine_time_step, time_scale_factor, rec_regions)

        self._write_neuron_data_spec(
            spec, routing_info, self.__ring_buffer_shifts)

        self._write_synapse_data_spec(
            spec, machine_time_step, routing_info, machine_graph, n_key_map,
            self.__ring_buffer_shifts, self.__weight_scales,
            self.__all_syn_block_sz, self.__structural_sz)

        # End the writing of this specification:
        spec.end_specification()

    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification)
    def regenerate_data_specification(self, spec, placement):
        # pylint: disable=too-many-arguments, arguments-differ

        # write the neuron params into the new DSG region
        self._write_neuron_parameters(spec, self.__ring_buffer_shifts)

        # close spec
        spec.end_specification()

    @overrides(AbstractRewritesDataSpecification.reload_required)
    def reload_required(self):
        return self.__change_requires_neuron_parameters_reload

    @overrides(AbstractRewritesDataSpecification.set_reload_required)
    def set_reload_required(self, new_value):
        self.__change_requires_neuron_parameters_reload = new_value
