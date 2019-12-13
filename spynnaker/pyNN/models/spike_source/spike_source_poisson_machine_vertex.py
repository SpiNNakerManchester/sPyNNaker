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
from pacman.executor.injection_decorator import inject_items
from pacman.model.graphs.machine import MachineVertex
from spinn_front_end_common.abstract_models import (
    AbstractSupportsDatabaseInjection, AbstractRecordable)
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl)
from spinn_front_end_common.interface.buffer_management.buffer_models import (
    AbstractReceiveBuffersToHost)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.interface.profiling import AbstractHasProfileData
from spinn_front_end_common.interface.profiling.profile_utils import (
    get_profiling_data)
from spynnaker.pyNN.utilities.constants import (
    LIVE_POISSON_CONTROL_PARTITION_ID)


class SpikeSourcePoissonMachineVertex(
        MachineVertex, AbstractReceiveBuffersToHost,
        ProvidesProvenanceDataFromMachineImpl, AbstractRecordable,
        AbstractSupportsDatabaseInjection, AbstractHasProfileData):
    __slots__ = [
        "__buffered_sdram_per_timestep",
        "__is_recording",
        "__minimum_buffer_sdram",
        "__resources"]

    class POISSON_SPIKE_SOURCE_REGIONS(Enum):
        SYSTEM_REGION = 0
        POISSON_PARAMS_REGION = 1
        RATES_REGION = 2
        SPIKE_HISTORY_REGION = 3
        PROVENANCE_REGION = 4
        PROFILER_REGION = 5

    PROFILE_TAG_LABELS = {
        0: "TIMER",
        1: "PROB_FUNC"}

    def __init__(
            self, resources_required, is_recording, constraints=None,
            label=None):
        # pylint: disable=too-many-arguments
        super(SpikeSourcePoissonMachineVertex, self).__init__(
            label, constraints=constraints)
        self.__is_recording = is_recording
        self.__resources = resources_required

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return self.__resources

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._provenance_region_id)
    def _provenance_region_id(self):
        return self.POISSON_SPIKE_SOURCE_REGIONS.PROVENANCE_REGION.value

    @property
    @overrides(
        ProvidesProvenanceDataFromMachineImpl._n_additional_data_items)
    def _n_additional_data_items(self):
        return 0

    @overrides(AbstractRecordable.is_recording)
    def is_recording(self):
        return self.__is_recording

    @overrides(AbstractReceiveBuffersToHost.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        if self.__is_recording:
            return [0]
        return []

    @overrides(AbstractReceiveBuffersToHost.get_recording_region_base_address)
    def get_recording_region_base_address(self, txrx, placement):
        return locate_memory_region_for_placement(
            placement,
            self.POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value,
            txrx)

    @property
    @overrides(AbstractSupportsDatabaseInjection.is_in_injection_mode)
    def is_in_injection_mode(self):
        # pylint: disable=no-value-for-parameter
        return self._is_in_injection_mode()

    @inject_items({"graph": "MemoryMachineGraph"})
    def _is_in_injection_mode(self, graph):
        # pylint: disable=arguments-differ
        in_edges = graph.get_edges_ending_at_vertex_with_partition_name(
            self, LIVE_POISSON_CONTROL_PARTITION_ID)
        if len(in_edges) > 1:
            raise ConfigurationException(
                "Poisson source can only have one incoming control")
        return len(in_edges) == 1

    @overrides(AbstractHasProfileData.get_profile_data)
    def get_profile_data(self, transceiver, placement):
        return get_profiling_data(
            self.POISSON_SPIKE_SOURCE_REGIONS.PROFILER_REGION.value,
            self.PROFILE_TAG_LABELS, transceiver, placement)
