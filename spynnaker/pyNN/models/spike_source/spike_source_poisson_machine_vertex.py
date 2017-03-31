from pacman.model.decorators.overrides import overrides
from spinn_front_end_common.utilities import helpful_functions
from pacman.model.graphs.machine import MachineVertex
from spinn_front_end_common.abstract_models.abstract_recordable \
    import AbstractRecordable
from spinn_front_end_common.interface.provenance\
    .provides_provenance_data_from_machine_impl \
    import ProvidesProvenanceDataFromMachineImpl
from spinn_front_end_common.interface.buffer_management.buffer_models\
    .abstract_receive_buffers_to_host import AbstractReceiveBuffersToHost
from spinn_front_end_common.interface.buffer_management \
    import recording_utilities

from enum import Enum


class SpikeSourcePoissonMachineVertex(
        MachineVertex, AbstractReceiveBuffersToHost,
        ProvidesProvenanceDataFromMachineImpl, AbstractRecordable):
    POISSON_SPIKE_SOURCE_REGIONS = Enum(
        value="POISSON_SPIKE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('POISSON_PARAMS_REGION', 1),
               ('SPIKE_HISTORY_REGION', 2),
               ('PROVENANCE_REGION', 3)])

    def __init__(
            self, resources_required, is_recording, minimum_buffer_sdram,
            buffered_sdram_per_timestep, constraints=None, label=None):
        MachineVertex.__init__(self, label, constraints=constraints)
        AbstractRecordable.__init__(self)
        self._is_recording = is_recording
        self._resources = resources_required
        self._minimum_buffer_sdram = minimum_buffer_sdram
        self._buffered_sdram_per_timestep = buffered_sdram_per_timestep

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return self._resources

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
        return self._is_recording

    @overrides(AbstractReceiveBuffersToHost.get_minimum_buffer_sdram_usage)
    def get_minimum_buffer_sdram_usage(self):
        return self._minimum_buffer_sdram

    @overrides(AbstractReceiveBuffersToHost.get_n_timesteps_in_buffer_space)
    def get_n_timesteps_in_buffer_space(self, buffer_space, machine_time_step):
        return recording_utilities.get_n_timesteps_in_buffer_space(
            buffer_space, [self._buffered_sdram_per_timestep])

    @overrides(AbstractReceiveBuffersToHost.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        if self._is_recording:
            return [0]
        return []

    @overrides(AbstractReceiveBuffersToHost.get_recording_region_base_address)
    def get_recording_region_base_address(self, txrx, placement):
        return helpful_functions.locate_memory_region_for_placement(
            placement,
            self.POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value,
            txrx)
