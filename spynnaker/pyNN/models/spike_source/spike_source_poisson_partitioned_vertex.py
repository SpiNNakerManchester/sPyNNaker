from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from spinn_front_end_common.interface.buffer_management\
    .buffer_models.receives_buffers_to_host_basic_impl \
    import ReceiveBuffersToHostBasicImpl
from spinn_front_end_common.interface.provenance\
    .provides_provenance_data_from_machine_impl \
    import ProvidesProvenanceDataFromMachineImpl
from spinn_front_end_common.abstract_models.abstract_live import AbstractLive

from enum import Enum


class SpikeSourcePoissonPartitionedVertex(
        PartitionedVertex, ReceiveBuffersToHostBasicImpl,
        ProvidesProvenanceDataFromMachineImpl, AbstractLive):

    _POISSON_SPIKE_SOURCE_REGIONS = Enum(
        value="_POISSON_SPIKE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('POISSON_PARAMS_REGION', 1),
               ('SPIKE_HISTORY_REGION', 2),
               ('BUFFERING_OUT_STATE', 3),
               ('PROVENANCE_REGION', 4)])

    def __init__(
            self, resources_required, label, is_updatable, constraints=None):
        PartitionedVertex.__init__(
            self, resources_required, label, constraints=constraints)
        ReceiveBuffersToHostBasicImpl.__init__(self)
        ProvidesProvenanceDataFromMachineImpl.__init__(
            self, self._POISSON_SPIKE_SOURCE_REGIONS.PROVENANCE_REGION.value,
            0)
        self._is_updatable = is_updatable

    def is_active(self):
        return self._is_updatable
