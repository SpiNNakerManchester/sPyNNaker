from spynnaker.pyNN.models.common import recording_utils

import logging

from spynnaker.pyNN.models.common.abstract_uint32_recorder import \
    AbstractUInt32Recorder

logger = logging.getLogger(__name__)


class GsynExcitatoryRecorder(AbstractUInt32Recorder):

    def __init__(self):
        AbstractUInt32Recorder.__init__(self)
        self._record_gsyn_excitatory = False

    @property
    def record_gsyn_excitatory(self):
        return self._record_gsyn_excitatory

    @record_gsyn_excitatory.setter
    def record_gsyn_excitatory(self, record_gsyn_excitatory):
        self._record_gsyn_excitatory = record_gsyn_excitatory

    def get_sdram_usage_in_bytes(self, n_neurons, n_machine_time_steps):
        if not self._record_gsyn_excitatory:
            return 0

        return recording_utils.get_recording_region_size_in_bytes(
            n_machine_time_steps, self.N_BYTES_PER_NEURON * n_neurons)

    def get_dtcm_usage_in_bytes(self):
        if not self._record_gsyn_excitatory:
            return 0
        return self.N_BYTES_PER_NEURON

    def get_n_cpu_cycles(self, n_neurons):
        if not self._record_gsyn_excitatory:
            return 0
        return n_neurons * self.N_CPU_CYCLES_PER_NEURON

    def get_gsyn_excitatory(
            self, label, buffer_manager, region, placements, graph_mapper,
            application_vertex, machine_time_step):
        return self.get_data(
            label, buffer_manager, region, placements, graph_mapper,
            application_vertex, machine_time_step, "gsyn_excitatory")
