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
from spinn_utilities.overrides import overrides
from pacman.model.graphs.machine import MachineVertex
from spinn_front_end_common.abstract_models import AbstractRecordable
from spinn_front_end_common.utilities.utility_objs import ProvenanceDataItem
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl)
from spinn_front_end_common.interface.buffer_management.buffer_models import (
    AbstractReceiveBuffersToHost)
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.interface.profiling import AbstractHasProfileData
from spinn_front_end_common.interface.profiling.profile_utils import (
    get_profiling_data)

class RateSourceLiveMachineVertex(
        MachineVertex, AbstractReceiveBuffersToHost,
        ProvidesProvenanceDataFromMachineImpl, AbstractRecordable,
        AbstractHasProfileData):

    __slots__ = [
        "__buffered_sdram_per_timestep",
        "__is_recording",
        "__minimum_buffer_sdram",
        "__resources",
        "__vertex_index",
        "__vertex_offset",
        "__starting_slice"]

    EXTRA_PROVENANCE_DATA_ENTRIES = Enum(
        value="EXTRA_PROVENANCE_DATA_ENTRIES",
        names=[("CURRENT_TIMER_TICK", 0),
               ("REFRESH_CALLS", 1)])

    RATE_SOURCE_REGIONS = Enum(
        value="RATE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('RATE_PARAMS_REGION', 1),
               ('RATE_VALUES_REGION', 2),
               ('PROVENANCE_REGION', 3),
               ('PROFILER_REGION', 4)])

    PROFILE_TAG_LABELS = {
        0: "TIMER",
        1: "PROB_FUNC"}

    N_ADDITIONAL_PROVENANCE_DATA_ITEMS = len(EXTRA_PROVENANCE_DATA_ENTRIES)

    def __init__(
            self, resources_required, is_recording, constraints=None,
            label=None, vertex_offset=0, starting_slice=None):
        # pylint: disable=too-many-arguments
        super(RateSourceLiveMachineVertex, self).__init__(
            label, constraints=constraints)
        self.__is_recording = is_recording
        self.__resources = resources_required
        self.__vertex_index = None
        self.__vertex_offset = vertex_offset
        self.__starting_slice = starting_slice

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return self.__resources

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._provenance_region_id)
    def _provenance_region_id(self):
        return self.RATE_SOURCE_REGIONS.PROVENANCE_REGION.value

    @property
    @overrides(
        ProvidesProvenanceDataFromMachineImpl._n_additional_data_items)
    def _n_additional_data_items(self):
        return self.N_ADDITIONAL_PROVENANCE_DATA_ITEMS

    @overrides(AbstractRecordable.is_recording)
    def is_recording(self):
        return self.__is_recording

    @property
    def vertex_index(self):
        return self.__vertex_index

    @vertex_index.setter
    def vertex_index(self, vertex_index):
        self.__vertex_index = vertex_index

    @property
    def vertex_offset(self):
        return self.__vertex_offset

    @property
    def starting_slice(self):
        return self.__starting_slice

    @overrides(ProvidesProvenanceDataFromMachineImpl.
               get_provenance_data_from_machine)
    def get_provenance_data_from_machine(self, transceiver, placement):
        provenance_data = self._read_provenance_data(transceiver, placement)
        provenance_items = self._read_basic_provenance_items(
            provenance_data, placement)
        provenance_data = self._get_remaining_provenance_data_items(
            provenance_data)

        last_timer_tick = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.CURRENT_TIMER_TICK.value]

        refresh_counts = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.REFRESH_CALLS.value]

        label, x, y, p, names = self._get_placement_details(placement)

        # translate into provenance data items
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Last_timer_tick_the_core_ran_to"),
            last_timer_tick))

        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Number of times the input has been refreshed"),
            refresh_counts))

        return provenance_items

    @overrides(AbstractReceiveBuffersToHost.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        if self.__is_recording:
            return [0]
        return []

    @overrides(AbstractReceiveBuffersToHost.get_recording_region_base_address)
    def get_recording_region_base_address(self, txrx, placement):
        return locate_memory_region_for_placement(
            placement,
            self.RATE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value,
            txrx)

    @overrides(AbstractHasProfileData.get_profile_data)
    def get_profile_data(self, transceiver, placement):
        return get_profiling_data(
            self.RATE_SOURCE_REGIONS.PROFILER_REGION.value,
            self.PROFILE_TAG_LABELS, transceiver, placement)