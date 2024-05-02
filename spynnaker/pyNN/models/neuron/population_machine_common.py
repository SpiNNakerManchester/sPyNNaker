# Copyright (c) 2017 The University of Manchester
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
from typing import Mapping, NamedTuple, Sequence, cast, TYPE_CHECKING
from spinn_utilities.overrides import overrides
from spinnman.model.enums import ExecutableType
from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.common import Slice
from pacman.model.resources import AbstractSDRAM
from pacman.model.placements import Placement

from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl)
from spinn_front_end_common.interface.buffer_management.buffer_models import (
    AbstractReceiveBuffersToHost)
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.interface.profiling.profile_utils import (
    get_profiling_data, reserve_profile_region, write_profile_region_data)
from spinn_front_end_common.abstract_models import AbstractHasAssociatedBinary
from spinn_front_end_common.interface.buffer_management\
    .recording_utilities import (
        get_recording_header_size, get_recording_header_array)
from spinn_front_end_common.interface.simulation.simulation_utilities import (
    get_simulation_header_array)
from spinn_front_end_common.interface.ds import DataSpecificationGenerator
from spinn_front_end_common.interface.profiling import (
    AbstractHasProfileData, ProfileData)
from spinn_front_end_common.utilities.constants import SIMULATION_N_BYTES
if TYPE_CHECKING:
    from .abstract_population_vertex import AbstractPopulationVertex


class CommonRegions(NamedTuple):
    """
    Identifiers for common regions.
    """
    #: System control region
    system: int
    #: Provenance collection region
    provenance: int
    #: Profiling data region
    profile: int
    #: Recording channels region
    recording: int


# pylint: disable=abstract-method
class PopulationMachineCommon(
        MachineVertex,
        ProvidesProvenanceDataFromMachineImpl,
        AbstractReceiveBuffersToHost,
        AbstractHasProfileData,
        AbstractHasAssociatedBinary):
    """
    A common machine vertex for all population binaries.
    """

    __slots__ = (
        # Sdram used by the machine vertex
        "__sdram",
        # Regions to be used
        "__regions",
        # The total number of provenance items returned by this core
        "__n_provenance_items",
        # The profile tags to be decoded
        "__profile_tags",
        # The name of the binary to run on the core
        "__binary_file_name")

    def __init__(
            self, label: str, app_vertex: AbstractPopulationVertex,
            vertex_slice: Slice, sdram: AbstractSDRAM, regions: CommonRegions,
            n_provenance_items: int, profile_tags: Mapping[int, str],
            binary_file_name: str):
        """
        :param str label: The label of the vertex
        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the population that this implements
        :param ~pacman.model.resources.AbstractSDRAM sdram:
            The SDRAM used by the vertex
        :param .CommonRegions regions: The regions to be assigned
        :param int n_provenance_items:
            The number of additional provenance items to be read
        :param dict(int,str) profile_tags:
            A mapping of profile identifiers to names
        :param str binary_file_name: The name of the binary file
        """
        super().__init__(label, app_vertex, vertex_slice)
        self.__sdram = sdram
        self.__regions = regions
        self.__n_provenance_items = n_provenance_items
        self.__profile_tags = profile_tags
        self.__binary_file_name = binary_file_name

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self) -> AbstractSDRAM:
        return self.__sdram

    @property
    def _pop_vertex(self) -> AbstractPopulationVertex:
        return cast('AbstractPopulationVertex', self._app_vertex)

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._provenance_region_id)
    def _provenance_region_id(self) -> int:
        return self.__regions.provenance

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._n_additional_data_items)
    def _n_additional_data_items(self) -> int:
        return self.__n_provenance_items

    @overrides(AbstractReceiveBuffersToHost.get_recording_region_base_address)
    def get_recording_region_base_address(self, placement: Placement) -> int:
        return locate_memory_region_for_placement(
            placement, self.__regions.recording)

    @overrides(AbstractHasProfileData.get_profile_data)
    def get_profile_data(self, placement: Placement) -> ProfileData:
        return get_profiling_data(
            self.__regions.profile, self.__profile_tags, placement)

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self) -> ExecutableType:
        return ExecutableType.USES_SIMULATION_INTERFACE

    def _write_common_data_spec(
            self, spec: DataSpecificationGenerator,
            rec_regions: Sequence[int]):
        """
        Write the data specification for the common regions.

        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param list(int) rec_regions:
            A list of sizes of each recording region (including empty ones)
        """
        # Write the setup region
        spec.reserve_memory_region(
            region=self.__regions.system, size=SIMULATION_N_BYTES,
            label='System')
        spec.switch_write_focus(self.__regions.system)
        spec.write_array(get_simulation_header_array(self.__binary_file_name))

        # Reserve memory for provenance
        self.reserve_provenance_data_region(spec)

        # Write profile data
        reserve_profile_region(
            spec, self.__regions.profile, self._pop_vertex.n_profile_samples)
        write_profile_region_data(
            spec, self.__regions.profile, self._pop_vertex.n_profile_samples)

        # Set up for recording
        spec.reserve_memory_region(
            region=self.__regions.recording,
            size=get_recording_header_size(len(rec_regions)),
            label="Recording")
        spec.switch_write_focus(self.__regions.recording)
        spec.write_array(get_recording_header_array(rec_regions))

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self) -> str:
        return self.__binary_file_name

    @overrides(MachineVertex.get_n_keys_for_partition)
    def get_n_keys_for_partition(self, partition_id: str) -> int:
        # Colour each time slot with up to 16 colours to allow for delays
        return self.vertex_slice.n_atoms * 16
