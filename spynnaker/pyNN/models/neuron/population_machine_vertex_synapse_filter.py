# Copyright (c) 2026 The University of Manchester
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

import ctypes
from enum import IntEnum
from typing import Sequence, List

from spinn_utilities.config_holder import get_config_int
from spinn_utilities.overrides import overrides
from spinnman.model.enums import ExecutableType
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import MachineVertex
from pacman.model.placements import Placement
from pacman.model.resources import AbstractSDRAM, MultiRegionSDRAM
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification, AbstractHasAssociatedBinary)
from spinn_front_end_common.interface.ds import DataSpecificationGenerator
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl, ProvenanceWriter)
from spinn_front_end_common.interface.simulation.simulation_utilities import (
    get_simulation_header_array)
from spinn_front_end_common.utilities.constants import (
    SIMULATION_N_BYTES, BYTES_PER_WORD)

from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView
from spynnaker.pyNN.utilities.bit_field_utilities import (
    is_sdram_poisson_source)
from .population_vertex import PopulationVertex
from .synaptic_matrices import SynapseRegionReferences
from .population_synapses_machine_vertex_common import (
    PopulationSynapsesMachineVertexCommon)

FILTER_PARTITION_PREFIX = "SynapseFilter_"
N_BYTES_CONFIG = 6 * BYTES_PER_WORD


class REGIONS(IntEnum):
    """
    Regions for populations.
    """
    SYSTEM = 0
    CONFIG = 1
    BIT_FIELD = 2
    MASTER_POPULATION_TABLE = 3
    PROVENANCE = 4


class FilterProvenance(ctypes.LittleEndianStructure):
    """
    Provenance items from synapse filtering.
    """
    _fields_ = [
        # A count of spikes received.
        ("n_spikes_received", ctypes.c_uint32),
        # A count of spikes forwarded to synapse processing.
        ("n_spikes_forwarded", ctypes.c_uint32),
        # The number spikes dropped because of invalid application vertex IDs.
        ("n_spikes_invalid_app_id", ctypes.c_uint32),
        # The number of times the spike queue overloaded.
        ("n_times_queue_overflowed", ctypes.c_uint32),
        # The number of times the bit field filter blocked a spike.
        ("n_times_bitfield_blocked", ctypes.c_uint32),
        # The number of packets discarded at the end of time steps.
        ("n_packets_discarded", ctypes.c_uint32),
        # The maximum number of packets discarded at the end of time steps.
        ("max_packets_discarded", ctypes.c_uint32),
    ]

    N_ITEMS = len(_fields_)


class PopulationMachineVertexSynapseFilter(
        MachineVertex,
        AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary,
        ProvidesProvenanceDataFromMachineImpl):

    __slots__ = ("__synapse_references", "__synapse_cores")

    def __init__(
            self, label: str, app_vertex: PopulationVertex,
            vertex_slice: Slice, synapse_references: SynapseRegionReferences,
            synapse_cores: List[PopulationSynapsesMachineVertexCommon]):
        """
        :param label: The label of the vertex
        :param app_vertex: The population vertex this is part of
        :param vertex_slice: The slice of the population vertex
        :param synapse_references: The synapse region references
        :param synapse_cores: The synapse cores that will process spikes
        """
        super().__init__(label, app_vertex, vertex_slice)
        self.__synapse_references = synapse_references
        self.__synapse_cores = synapse_cores

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self) -> AbstractSDRAM:
        sdram = MultiRegionSDRAM()
        sdram.add_cost(REGIONS.SYSTEM, SIMULATION_N_BYTES)
        sdram.add_cost(
            REGIONS.CONFIG,
            N_BYTES_CONFIG + (len(self.__synapse_cores) * BYTES_PER_WORD))
        sdram.add_cost(
            REGIONS.PROVENANCE,
            self.get_provenance_data_size(FilterProvenance.N_ITEMS))
        # Other regions are shared so cost nothing
        return sdram

    @overrides(MachineVertex.get_n_keys_for_partition)
    def get_n_keys_for_partition(self, partition_id: str) -> int:
        if partition_id.startswith(FILTER_PARTITION_PREFIX):
            return 1
        return 0

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self) -> str:
        return "synapse_filter.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self)->ExecutableType:
        return ExecutableType.USES_SIMULATION_INTERFACE

    @overrides(AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(
            self, spec: DataSpecificationGenerator,
            placement: Placement) -> None:
        # Write the system region
        spec.reserve_memory_region(
            region=REGIONS.SYSTEM, size=SIMULATION_N_BYTES,
            label='System')
        spec.switch_write_focus(REGIONS.SYSTEM)
        spec.write_array(get_simulation_header_array(
            self.get_binary_file_name()))

        # Write this vertex's configuration region
        self._write_config_region(spec)

        # Write references to the bit field and master population table regions
        spec.reference_memory_region(
            REGIONS.BIT_FIELD, self.__synapse_references.bitfield_filter,
            "Bit Field Region")
        spec.reference_memory_region(
            REGIONS.MASTER_POPULATION_TABLE,
            self.__synapse_references.pop_table,
            "Master Population Table Region")

        # Reserve provenance region
        self.reserve_provenance_data_region(spec)

        spec.end_specification()

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._provenance_region_id)
    def _provenance_region_id(self) -> int:
        return REGIONS.PROVENANCE

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._n_additional_data_items)
    def _n_additional_data_items(self) -> int:
        return FilterProvenance.N_ITEMS

    @overrides(ProvidesProvenanceDataFromMachineImpl
               .parse_extra_provenance_items)
    def parse_extra_provenance_items(
            self, label: str, x: int, y: int, p: int,
            provenance_data: Sequence[int]) -> None:
        filter_prov = FilterProvenance(*provenance_data)

        with ProvenanceWriter() as db:
            db.insert_core(
                x, y, p, "Number_of_spikes_received",
                filter_prov.n_spikes_received)

            db.insert_core(
                x, y, p, "Number_of_spikes_forwarded",
                filter_prov.n_spikes_forwarded)

            db.insert_core(
                x, y, p, "Number_of_invalid_application_vertex_ID_spikes",
                filter_prov.n_spikes_invalid_app_id)

            db.insert_core(
                x, y, p, "Number_of_times_spike_queue_overflowed",
                filter_prov.n_times_queue_overflowed)

            db.insert_core(
                x, y, p, "Number_of_times_bitfield_blocked_spikes",
                filter_prov.n_times_bitfield_blocked)

            db.insert_core(
                x, y, p, "Number_of_packets_discarded_end_of_timestep",
                filter_prov.n_packets_discarded)

            db.insert_core(
                x, y, p, "Max_number_of_packets_discarded_end_of_timestep",
                filter_prov.max_packets_discarded)

            if filter_prov.n_spikes_invalid_app_id > 0:
                db.insert_report(
                    f"{filter_prov.n_spikes_invalid_app_id} spikes were "
                    f"dropped on {label}.  This should not happen!")

            if filter_prov.n_times_queue_overflowed > 0:
                db.insert_report(
                    "The spike queue overflowed "
                    f"{filter_prov.n_times_queue_overflowed} times on {label}."
                    "  Consider increasing the spike queue size.")

            if filter_prov.n_packets_discarded > 0:
                db.insert_report(
                    "At the end of time steps, "
                    f"{filter_prov.n_packets_discarded} packets were discarded "
                    f"on {label} (a maximum of "
                    f"{filter_prov.max_packets_discarded} in one time step). ")

    def __lowest_set(self, value: int) -> int:
        """ Return the lowest set bit in value. """
        return (value & -value).bit_length() - 1

    def _write_config_region(self, spec):
        spec.reserve_memory_region(
            region=REGIONS.CONFIG,
            size=N_BYTES_CONFIG + (len(self.__synapse_cores) * BYTES_PER_WORD),
            label='Synapse Filter Config')
        spec.switch_write_focus(REGIONS.CONFIG)

        # Find a common application mask, and minimum and maximum values
        app_mask = None
        app_shift = None
        app_min = None
        app_max = None
        routing_info = SpynnakerDataView.get_routing_infos()
        for proj in self._app_vertex.incoming_projections:
            app_edge = proj._projection_edge
            s_info = proj._synapse_information
            if is_sdram_poisson_source(app_edge):
                continue
            r_info = routing_info.get_info_from(
                app_edge.pre_vertex, s_info.partition_id)
            if app_mask is None:
                app_mask = r_info.mask
                app_shift = self.__lowest_set(app_mask)
            elif app_mask != r_info.mask:
                raise Exception(
                    "Cannot configure synapse filter when application "
                    "masks differ")

            app_value = (r_info.key & app_mask) >> app_shift
            if app_min is None:
                app_min = app_value
                app_max = app_value
            else:
                if app_value < app_min:
                    app_min = app_value
                if app_value > app_max:
                    app_max = app_value
        spec.write_value(app_mask)
        spec.write_value(app_shift)
        spec.write_value(app_min)
        spec.write_value(app_max)
        spec.write_value(get_config_int(
            "Simulation", "incoming_spike_buffer_size"))
        spec.write_value(len(self.__synapse_cores))
        for i, synapse_core in enumerate(self.__synapse_cores):
            spec.write_value(routing_info.get_first_key_from_pre_vertex(
                self, FILTER_PARTITION_PREFIX + self.label + "_" + str(i)))
