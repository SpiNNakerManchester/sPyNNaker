from __future__ import division
from collections import OrderedDict
from fractions import gcd
import logging
import numpy
from data_specification.enums import DataType
from spynnaker.pyNN.models.common import recording_utils
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from .abstract_uint32_recorder import AbstractUInt32Recorder
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities import exceptions as fec_excceptions

logger = logging.getLogger(__name__)

MAX_RATE = 2 ** 32 - 1  # To allow a unit32_t to be used to store the rate


class NeuronRecorder(AbstractUInt32Recorder):

    def __init__(self, allowed_variables, n_neurons):
        AbstractUInt32Recorder.__init__(self)
        self._sampling_rates = OrderedDict()
        self._n_neurons = n_neurons
        for variable in allowed_variables:
            self._sampling_rates[variable] = numpy.zeros(self._n_neurons)

    def get_recordable_variables(self):
        return self._sampling_rates.keys()

    def is_recording(self, variable):
        if variable in self._sampling_rates:
            return sum(self._sampling_rates[variable]) > 0
        msg = "Variable {} is not supported. Supported variables include {}" \
              "".format(variable, self._sampling_rates.keys())
        raise fec_excceptions.ConfigurationException(msg)

    @property
    def recording_variables(self):
        results = list()
        for key in self._sampling_rates:
            if self.is_recording(key):
                results.append(key)
        return results

    def set_recording(
            self, variable, new_state, sampling_interval=None, neurons=None):
        if variable == "all":
            for key in self._sampling_rates.keys():
                self.set_recording(key, new_state, sampling_interval)
        elif variable in self._sampling_rates:
            if new_state:
                if sampling_interval is None:
                    if neurons is None:
                        self._sampling_rates[variable] = \
                            numpy.ones(self._n_neurons)
                    else:
                        for neuron in neurons:
                            self._sampling_rates[variable][neuron] = 1
                else:
                    step = globals_variables.get_simulator().\
                               machine_time_step / 1000
                    rate = sampling_interval // step
                    if sampling_interval != rate * step:
                        msg = "sampling_interval {} is not an an integer " \
                              "multiple of the simulation timestep {}" \
                              "".format(sampling_interval, step)
                        raise fec_excceptions.ConfigurationException(msg)
                    if rate > MAX_RATE:
                        msg = "sampling_interval {} higher than max allowed " \
                              "which is {}" \
                              "".format(sampling_interval, step * MAX_RATE)
                        raise fec_excceptions.ConfigurationException(msg)
                    if neurons is None:
                        self._sampling_rates[variable] = \
                            numpy.full(self._n_neurons, rate)
                    else:
                        logger.warning(
                            "Setting Sampling rate for a view is only "
                            "partially supported. You may get more data than "
                            "specified.")
                        for neuron in neurons:
                            self._sampling_rates[variable][neuron] = rate
            else:
                if neurons is None:
                    self._sampling_rates[variable] = \
                        numpy.zeros(self._n_neurons)
                else:
                    for neuron in neurons:
                        self._sampling_rates[variable][neuron] = 0
        else:
            msg = "Variable {} is not supported ".format(variable)
            raise fec_excceptions.ConfigurationException(msg)

    def _count_recording_per_slice(self, variable, slice):
        neuron_count = 0
        for neuron in xrange(slice.lo_atom, slice.hi_atom+1):
            if self._sampling_rates[variable][neuron] > 0:
                neuron_count += 1
        return neuron_count

    def get_sdram_usage_in_bytes_for_slice(self, variable, slice,
                                           n_machine_time_steps):
        neuron_count = self._count_recording_per_slice(variable, slice)
        return recording_utils.get_recording_region_size_in_bytes(
            n_machine_time_steps, self.N_BYTES_PER_NEURON * neuron_count)

    def get_sdram_usage_in_bytes(self, variable, n_neurons,
                                 n_machine_time_steps):
        if self.is_recording(variable):
            return recording_utils.get_recording_region_size_in_bytes(
                n_machine_time_steps,  self.N_BYTES_PER_NEURON * n_neurons)
        else:
            return 0

    def get_dtcm_usage_in_bytes(self):
        return self.N_BYTES_PER_NEURON * len(self.recording_variables)

    def get_n_cpu_cycles(self, n_neurons):
        return n_neurons * self.N_CPU_CYCLES_PER_NEURON * \
                len(self.recording_variables)

    def sampling_rate(self, variable, slice):
        rate = 0
        for neuron in xrange(slice.lo_atom, slice.hi_atom+1):
            if self._sampling_rates[variable][neuron] != rate:
                rate = gcd(rate, self._sampling_rates[variable][neuron])
        return rate

    def get_sdram_usage_for_global_parameters_in_bytes(self):
        return len(self._sampling_rates) * 4

    def get_global_parameters(self, slice):
        params = []
        for key in self._sampling_rates:
            params.append(NeuronParameter(
                self.sampling_rate(key, slice), DataType.UINT32))
            # params.append(NeuronParameter(
            #    self._count_recording_per_slice(key, slice), DataType.UINT32))
        return params

    def get_indexes_for_slice(self, variable, slice):
        neuron_count = self._count_recording_per_slice(variable, slice)
        indexes = numpy.empty(slice.n_atoms)
        index = 0
        for neuron in xrange(slice.lo_atom, slice.hi_atom+1):
            if self._sampling_rates[variable][neuron] > 0:
                indexes[neuron-slice.lo_atom] = index
                index += 1
            else:
                indexes[neuron-slice.lo_atom] = neuron_count
        return indexes
