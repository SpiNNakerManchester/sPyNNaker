from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.machine.impl.machine_vertex \
    import MachineVertex
from spinn_front_end_common.interface.buffer_management\
    .buffer_models.receives_buffers_to_host_basic_impl \
    import ReceiveBuffersToHostBasicImpl
from spinn_front_end_common.abstract_models.abstract_recordable \
    import AbstractRecordable
from spinn_front_end_common.interface.provenance\
    .provides_provenance_data_from_machine_impl \
    import ProvidesProvenanceDataFromMachineImpl

from enum import Enum


class SpikeSourcePoissonMachineVertex(
        MachineVertex, ReceiveBuffersToHostBasicImpl,
        ProvidesProvenanceDataFromMachineImpl, AbstractRecordable):

    _POISSON_SPIKE_SOURCE_REGIONS = Enum(
        value="_POISSON_SPIKE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('POISSON_PARAMS_REGION', 1),
               ('SPIKE_HISTORY_REGION', 2),
               ('BUFFERING_OUT_STATE', 3),
               ('PROVENANCE_REGION', 4)])

    def __init__(
            self, resources_required, is_recording, constraints=None,
            label=None):
        MachineVertex.__init__(self, label, constraints=constraints)
        ReceiveBuffersToHostBasicImpl.__init__(self)
        ProvidesProvenanceDataFromMachineImpl.__init__(
            self, self._POISSON_SPIKE_SOURCE_REGIONS.PROVENANCE_REGION.value,
            0)
        AbstractRecordable.__init__(self)
        self._is_recording = is_recording
        self._resources = resources_required

    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return self._resources

    @overrides(AbstractRecordable.is_recording)
    def is_recording(self):
        return self._is_recording
