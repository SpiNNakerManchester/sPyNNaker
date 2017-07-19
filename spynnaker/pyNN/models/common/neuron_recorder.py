import logging
from spynnaker.pyNN.models.common import recording_utils
from .abstract_uint32_recorder import AbstractUInt32Recorder
from spinn_front_end_common.utilities import exceptions as fec_excceptions

logger = logging.getLogger(__name__)


class NeuronRecorder(AbstractUInt32Recorder):

    def __init__(self, allowed_variables):
        AbstractUInt32Recorder.__init__(self)
        self._record = dict()
        for variable in allowed_variables:
            self._record[variable] = False

    def get_recordable_variables(self):
        return self._record.keys()

    def is_recording(self, variable):
        if variable in self._record:
            return self._record[variable]
        msg = "Variable {} is not supported. Supported variables include {}" \
              "".format(variable, self._record.keys())
        raise fec_excceptions.ConfigurationException(msg)

    @property
    def recording_variables(self):
        results = list()
        for key, value in self._record.iteritems():
            if value:
                results.append(key)
        return results

    def set_recording(self, variable, new_state):
        if variable == "all":
            for key in self._record.keys():
                self._record[key] = new_state
        elif variable in self._record:
            self._record[variable] = new_state
        else:
            msg = "Variable {} is not supported ".format(variable)
            raise fec_excceptions.ConfigurationException(msg)

    def get_sdram_usage_in_bytes(self, variable, n_neurons,
                                 n_machine_time_steps):
        if self.is_recording(variable):
            return recording_utils.get_recording_region_size_in_bytes(
                n_machine_time_steps,  self.N_BYTES_PER_NEURON * n_neurons)
        else:
            return 0

    def get_dtcm_usage_in_bytes(self):
        return self.N_BYTES_PER_NEURON * sum(self._record.values())

    def get_n_cpu_cycles(self, n_neurons):
        return n_neurons * self.N_CPU_CYCLES_PER_NEURON * \
                sum(self._record.values())
