from spynnaker.pyNN.models.common import recording_utils

import logging

from spynnaker.pyNN.models.common.abstract_uint32_recorder import \
    AbstractUInt32Recorder

logger = logging.getLogger(__name__)


class VRecorder(AbstractUInt32Recorder):

    def __init__(self):
        AbstractUInt32Recorder.__init__(self)
        self._record_v = False

    @property
    def record_v(self):
        return self._record_v

    @record_v.setter
    def record_v(self, record_v):
        self._record_v = record_v

    def get_sdram_usage_in_bytes(self, n_neurons, n_machine_time_steps):
        if not self._record_v:
            return 0

        return recording_utils.get_recording_region_size_in_bytes(
            n_machine_time_steps, 4 * n_neurons)

    def get_dtcm_usage_in_bytes(self):
        if not self._record_v:
            return 0
        return 4

    def get_n_cpu_cycles(self, n_neurons):
        if not self._record_v:
            return 0
        return n_neurons * 4

    def get_v(self, label, buffer_manager, region, placements,
              graph_mapper, application_vertex, machine_time_step):
        return self.get_data(
            label, buffer_manager, region, placements, graph_mapper,
            application_vertex, machine_time_step, "membrane voltage")
