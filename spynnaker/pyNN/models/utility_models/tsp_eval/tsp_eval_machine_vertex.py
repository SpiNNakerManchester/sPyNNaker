# Copyright (c) 2016 The University of Manchester
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
from enum import IntEnum
import ctypes
from typing import TYPE_CHECKING, List, Sequence

from spinn_utilities.overrides import overrides
from spinnman.model.enums import ExecutableType
from pacman.model.graphs.common.slice import Slice
from pacman.model.graphs.machine import MachineVertex
from pacman.model.resources import AbstractSDRAM, ConstantSDRAM
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities.constants import (
    SIMULATION_N_BYTES, BYTES_PER_WORD)
from spinn_front_end_common.abstract_models import (
    AbstractHasAssociatedBinary, AbstractGeneratesDataSpecification)
from spinn_front_end_common.interface.buffer_management.buffer_models import (
    AbstractReceiveBuffersToHost)
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.interface.buffer_management\
    .recording_utilities import (
        get_recording_header_size, get_recording_header_array)
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl, ProvenanceWriter)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.constants import (
    SPIKE_PARTITION_ID, LIVE_POISSON_CONTROL_PARTITION_ID)
from spynnaker.pyNN.models.populations import Population
if TYPE_CHECKING:
    from .tsp_eval_vertex import TSPEvalVertex
    from pacman.model.placements import Placement
    from spinn_front_end_common.interface.ds import DataSpecificationGenerator

# send_report, report_key, send_poisson_control, poisson_control_key,
# min_run_length, max_spike_diff, n_sources, n_values, n_key_entries,
# poisson_low_rate, poisson_high_rate, time_between_solution_and_high_rate,
# time_without_solution_before_low_rate
PARAMS_SZ = 13 * BYTES_PER_WORD

# key, mask, n_colour_bits, min_neuron_id, node_index, neurons_per_value
KEY_STRUCT_SZ = 6 * BYTES_PER_WORD


class TSPProvenance(ctypes.LittleEndianStructure):
    """
    Provenance items from TSP evaluation.
    """
    _fields_ = [
        # Number of buffer overflows
        ("n_buffer_overflows", ctypes.c_uint32)
    ]

    N_ITEMS = len(_fields_)


class TSPEvalMachineVertex(
        MachineVertex, AbstractHasAssociatedBinary,
        AbstractGeneratesDataSpecification, AbstractReceiveBuffersToHost,
        ProvidesProvenanceDataFromMachineImpl):
    """
    Vertex that implements TSP evaluation on SpiNNaker.
    """

    __slots__ = (
        "__neurons_per_value",
        "__populations",
        "__min_run_length",
        "__max_spike_diff",
        "__recording_size",
        "__keys_size",
        "__is_recording",
        "__poisson_low_rate",
        "__poisson_high_rate",
        "__time_between_solution_and_high_rate",
        "__time_without_solution_before_low_rate"
    )

    class _REGIONS(IntEnum):
        """
        Region indices.
        """
        SYSTEM = 0
        PARAMS = 1
        KEYS = 2
        RECORDING = 3
        PROVENANCE = 4

    def __init__(self, neurons_per_value: int, populations: List[Population],
                 min_run_length: int, max_spike_diff: int, n_recordings: int,
                 poisson_low_rate: float, poisson_high_rate: float,
                 time_between_solution_and_high_rate: int,
                 time_without_solution_before_low_rate: int,
                 label: str, app_vertex: TSPEvalVertex):
        """
        :param int neurons_per_value:
            The number of neurons per value in the populations
        :param List[Population] populations:
            The populations that make up the TSP solver
        :param int min_run_length:
            The minimum run of spikes considered to be a run
        :param int max_spike_diff:
            The maximum time between spikes in a run
        :param int n_recordings:
            The number of recordings of state to allow at most
        :param str label: The label of the vertex
        :param float poisson_low_rate:
            The rate of the Poisson source when looking for solutions
        :param float poisson_high_rate:
            The rate of the Poisson source when stuck in a local minimum
        :param int time_between_solution_and_high_rate:
            The time between finding a solution and a change in the Poisson
            source rate to high
        :param int time_without_solution_before_low_rate:
            The time without a solution before the Poisson source rate changes
            to low
        :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
            The application vertex that caused this machine vertex to be
            created. If `None`, there is no such application vertex.
        """
        super().__init__(
            label, app_vertex=app_vertex,
            vertex_slice=Slice(0, len(populations)))

        self.__neurons_per_value = neurons_per_value
        self.__populations = populations
        self.__is_recording = False
        self.__min_run_length = min_run_length
        self.__max_spike_diff = max_spike_diff
        self.__poisson_low_rate = poisson_low_rate
        self.__poisson_high_rate = poisson_high_rate
        self.__time_between_solution_and_high_rate = (
            time_between_solution_and_high_rate)
        self.__time_without_solution_before_low_rate = (
            time_without_solution_before_low_rate)

        # Recording is time, followed by int for each population
        self.__recording_size = (
            (1 + len(populations)) * BYTES_PER_WORD * n_recordings)

        self.__keys_size = None

    def set_recording(self, is_recording: bool):
        self.__is_recording = is_recording

    def is_recording(self) -> bool:
        return self.__is_recording

    def __get_keys_size(self):
        if self.__keys_size is None:
            # Keys are one key structure per machine vertex of each population
            # pylint: disable=protected-access
            n_m_verts = sum(len(pop._vertex.splitter.get_out_going_slices())
                            for pop in self.__populations)
            self.__keys_size = n_m_verts * KEY_STRUCT_SZ
        return self.__keys_size

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self) -> AbstractSDRAM:
        return ConstantSDRAM(
            SIMULATION_N_BYTES + PARAMS_SZ + self.__get_keys_size() +
            self.__recording_size + get_recording_header_size(1))

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self) -> str:
        return "tsp_eval.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self) -> ExecutableType:
        return ExecutableType.USES_SIMULATION_INTERFACE

    @overrides(AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(
            self, spec: DataSpecificationGenerator, placement: Placement):
        spec.reserve_memory_region(
            region=self._REGIONS.SYSTEM, size=SIMULATION_N_BYTES,
            label='system')
        spec.switch_write_focus(self._REGIONS.SYSTEM)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name()))

        spec.reserve_memory_region(
            region=self._REGIONS.PARAMS, size=PARAMS_SZ,
            label='params')
        self.write_parameters(spec)

        spec.reserve_memory_region(
            region=self._REGIONS.KEYS, size=self.__get_keys_size(),
            label='keys')
        self.write_keys(spec)

        spec.reserve_memory_region(
            region=self._REGIONS.RECORDING,
            size=self.__recording_size + get_recording_header_size(1),
            label="recording")
        spec.switch_write_focus(self._REGIONS.RECORDING)
        spec.write_array(get_recording_header_array([self.__recording_size]))

        spec.reserve_memory_region(
            region=self._REGIONS.PROVENANCE,
            size=self.get_provenance_data_size(TSPProvenance.N_ITEMS),
            label="provenance")

        # End-of-Spec:
        spec.end_specification()

    def write_parameters(self, spec):
        """
        Generate Parameter data.

        :param ~data_specification.DataSpecificationGenerator spec:
        """

        # Set the focus to the parameters region
        spec.switch_write_focus(self._REGIONS.PARAMS)

        routing_infos = SpynnakerDataView.get_routing_infos()
        report_key = routing_infos.get_first_key_from_pre_vertex(
            self, SPIKE_PARTITION_ID)

        # Write Key info for this core
        if report_key is None:
            spec.write_value(0)
            spec.write_value(0)
        else:
            spec.write_value(1)
            spec.write_value(data=report_key)

        poisson_control_key = routing_infos.get_first_key_from_pre_vertex(
            self, LIVE_POISSON_CONTROL_PARTITION_ID)
        if poisson_control_key is None:
            spec.write_value(0)
            spec.write_value(0)
        else:
            spec.write_value(1)
            spec.write_value(data=poisson_control_key)

        spec.write_value(data=self.__min_run_length)
        spec.write_value(data=self.__max_spike_diff)
        spec.write_value(data=len(self.__populations))
        spec.write_value(data=len(self.__populations))

        # pylint: disable=protected-access
        n_m_verts = sum(len(pop._vertex.splitter.get_out_going_slices())
                        for pop in self.__populations)
        spec.write_value(data=n_m_verts)

        spec.write_value(data=self.__poisson_low_rate)
        spec.write_value(data=self.__poisson_high_rate)
        spec.write_value(data=self.__time_between_solution_and_high_rate)
        spec.write_value(data=self.__time_without_solution_before_low_rate)

    def write_keys(self, spec):
        spec.switch_write_focus(self._REGIONS.KEYS)
        for i, pop in enumerate(self.__populations):
            # pylint: disable=protected-access
            app_vert = pop._vertex
            for m_vert in app_vert.splitter.get_out_going_vertices(
                    SPIKE_PARTITION_ID):
                routing_infos = SpynnakerDataView.get_routing_infos()
                rinfo = routing_infos.get_routing_info_from_pre_vertex(
                    m_vert, SPIKE_PARTITION_ID)
                spec.write_value(data=rinfo.key)
                spec.write_value(data=rinfo.mask)
                spec.write_value(data=app_vert.n_colour_bits)
                spec.write_value(data=m_vert.vertex_slice.lo_atom)
                spec.write_value(data=i)
                spec.write_value(data=self.__neurons_per_value)

    @overrides(AbstractReceiveBuffersToHost.get_recorded_region_ids)
    def get_recorded_region_ids(self) -> List[int]:
        if self.__is_recording:
            return [0]
        return []

    @overrides(AbstractReceiveBuffersToHost.get_recording_region_base_address)
    def get_recording_region_base_address(self, placement: Placement) -> int:
        return locate_memory_region_for_placement(
            placement, self._REGIONS.RECORDING)

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._provenance_region_id)
    def _provenance_region_id(self) -> int:
        return self._REGIONS.PROVENANCE.value

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._n_additional_data_items)
    def _n_additional_data_items(self) -> int:
        return TSPProvenance.N_ITEMS

    def parse_extra_provenance_items(
            self, label: str, x: int, y: int, p: int,
            provenance_data: Sequence[int]):
        prov = TSPProvenance(*provenance_data)
        with ProvenanceWriter() as db:
            db.insert_core(
                x, y, p, "Number of buffer overflows",
                prov.n_buffer_overflows)
            if prov.n_buffer_overflows > 0:
                db.insert_report(
                    f"The buffer for {label} overflowed"
                    f" {prov.n_buffer_overflows} times.")
