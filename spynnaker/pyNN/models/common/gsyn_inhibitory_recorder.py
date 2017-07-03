import logging

from spynnaker.pyNN.models.common import recording_utils

from spynnaker.pyNN.models.common.abstract_uint32_recorder import \
    AbstractUInt32Recorder

logger = logging.getLogger(__name__)


class GsynInhibitoryRecorder(AbstractUInt32Recorder):
    def __init__(self):
        AbstractUInt32Recorder.__init__(self)
        self._record_gsyn_inhibitory = False

    @property
    def record_gsyn_inhibitory(self):
        return self._record_gsyn_inhibitory

    @record_gsyn_inhibitory.setter
    def record_gsyn_inhibitory(self, record_gsyn_inhibitory):
        self._record_gsyn_inhibitory = record_gsyn_inhibitory

    def get_sdram_usage_in_bytes(self, n_neurons, n_machine_time_steps):
        if not self._record_gsyn_inhibitory:
            return 0

        return recording_utils.get_recording_region_size_in_bytes(
            n_machine_time_steps, 8 * n_neurons)

    def get_dtcm_usage_in_bytes(self):
        if not self._record_gsyn_inhibitory:
            return 0
        return 4

    def get_n_cpu_cycles(self, n_neurons):
        if not self._record_gsyn_inhibitory:
            return 0
        return n_neurons * 8

    def get_gsyn_inhibitory(
            self, label, buffer_manager, region, placements, graph_mapper,
            application_vertex, machine_time_step):

        return self.get_data(
            label, buffer_manager, region, placements, graph_mapper,
            application_vertex, machine_time_step, "gsyn_inhibitory")
