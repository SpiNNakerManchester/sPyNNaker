from pacman.model.decorators import overrides
from pacman.executor.injection_decorator import inject_items
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.abstract_models \
    import AbstractSupportsDatabaseInjection
from spinn_front_end_common.utilities.helpful_functions \
    import locate_memory_region_for_placement
from pacman.model.graphs.machine import MachineVertex
from spinn_front_end_common.abstract_models import AbstractRecordable
from spinn_front_end_common.interface.provenance \
    import ProvidesProvenanceDataFromMachineImpl
from spinn_front_end_common.interface.buffer_management.buffer_models \
    import AbstractReceiveBuffersToHost
from spinn_front_end_common.interface.buffer_management \
    import recording_utilities

from spynnaker.pyNN.utilities.constants import LIVE_POISSON_CONTROL_PARTITION_ID

from enum import Enum


class SpikeSourcePoissonMachineVertex(
        MachineVertex, AbstractReceiveBuffersToHost,
        ProvidesProvenanceDataFromMachineImpl, AbstractRecordable,
        AbstractSupportsDatabaseInjection):
    POISSON_SPIKE_SOURCE_REGIONS = Enum(
        value="POISSON_SPIKE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('POISSON_PARAMS_REGION', 1),
               ('SPIKE_HISTORY_REGION', 2),
               ('PROVENANCE_REGION', 3)])

    def __init__(
            self, resources_required, is_recording, minimum_buffer_sdram,
            buffered_sdram_per_timestep, constraints=None, label=None):
        # pylint: disable=too-many-arguments
        super(SpikeSourcePoissonMachineVertex, self).__init__(
            label, constraints=constraints)
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
        return locate_memory_region_for_placement(
            placement,
            self.POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value,
            txrx)

    @inject_items({"graph": "MemoryMachineGraph"})
    @overrides(
        AbstractSupportsDatabaseInjection.is_in_injection_mode,
        additional_arguments=["graph"])
    def is_in_injection_mode(self, graph):
        # pylint: disable=arguments-differ
        in_edges = graph.get_edges_ending_at_vertex_with_partition_name(
            self, LIVE_POISSON_CONTROL_PARTITION_ID)
        if len(in_edges) > 1:
            raise ConfigurationException(
                "Poisson source can only have one incoming control")
        return len(in_edges) == 1
