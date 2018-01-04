from __future__ import division
from collections import OrderedDict
import logging
import math
import numpy

from data_specification.enums import DataType
from spinn_front_end_common.utilities import exceptions as fec_excceptions
from spinn_utilities.index_is_value import IndexIsValue
from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.models.common import recording_utils
from spynnaker.pyNN.models.neural_properties import NeuronParameter

logger = logging.getLogger(__name__)

SPIKES = "spikes"


class NeuronRecorder(object):
    N_BYTES_FOR_TIMESTAMP = 4
    N_BYTES_PER_VALUE = 4
    N_BYTES_PER_RATE = 4  # uint32
    N_BYTES_PER_INDEX = 1  # currently uint8
    N_BYTES_PER_SIZE = 4
    N_CPU_CYCLES_PER_NEURON = 8
    N_BYTES_PER_WORD = 4

    def __init__(self, allowed_variables, n_neurons):
        self._sampling_rates = OrderedDict()
        self._indexes = dict()
        self._n_neurons = n_neurons
        for variable in allowed_variables:
            self._sampling_rates[variable] = 0
            self._indexes[variable] = None

    def _count_recording_per_slice(self, variable, slice):
        if self._sampling_rates[variable] == 0:
            return 0
        if self._indexes[variable] is None:
            return slice.n_atoms
        return sum((index >= slice.lo_atom and index <= slice.hi_atom)
                   for index in self._indexes[variable])

    def _neurons_recording(self, variable, slice):
        if self._sampling_rates[variable] == 0:
            return []
        if self._indexes[variable] is None:
            return range(slice.lo_atom, slice.hi_atom+1)
        recording = []
        indexes = self._indexes[variable]
        for index in xrange(slice.lo_atom, slice.hi_atom+1):
            if index in indexes:
                recording.append(index)
        return recording

    def get_neuron_sampling_interval(self, variable):
        """
        Returns the current sampling interval for this variable
        :param variable: PyNN name of the variable
        :return: Sampling interval in micro seconds
        """
        return recording_utils.compute_interval(self._sampling_rates[variable])

    def get_matrix_data(
            self, label, buffer_manager, region, placements, graph_mapper,
            application_vertex, variable, n_machine_time_steps):
        """ method for reading a uint32 mapped to time and neuron ids from\
        the SpiNNaker machine

        :param label: vertex label
        :param buffer_manager: the manager for buffered data
        :param region: the dsg region id used for this data
        :param placements: the placements object
        :param graph_mapper: the mapping between application and machine\
            vertices
        :param application_vertex:
        :param variable: PyNN name for the variable (V, gsy_ihn ect
        :type variable: str
        :param n_machine_time_steps:
        :return:
        """
        if variable == SPIKES:
            msg = "Variable {} is not supported use get_spikes".format(SPIKES)
            raise fec_excceptions.ConfigurationException(msg)
        vertices = graph_mapper.get_machine_vertices(application_vertex)
        progress = ProgressBar(
                vertices, "Getting {} for {}".format(variable, label))
        sampling_interval = self._sampling_rates[variable]
        expected_rows = int(math.ceil(
            n_machine_time_steps / sampling_interval))
        missing_str = ""
        data = None
        indexes = []
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)
            neurons = self._neurons_recording(variable, vertex_slice)
            n_neurons = len(neurons)
            indexes.extend(neurons)
            # for buffering output info is taken form the buffer manager
            neuron_param_region_data_pointer, missing_data = \
                buffer_manager.get_data_for_vertex(
                    placement, region)
            record_raw = neuron_param_region_data_pointer.read_all()
            record_length = len(record_raw)
            row_length = self.N_BYTES_FOR_TIMESTAMP + \
                         n_neurons * self.N_BYTES_PER_VALUE
            # There is one column for time and one for each neuron recording
            n_rows = record_length // row_length
            # Converts bytes to ints and make a matrix
            record = (numpy.asarray(record_raw, dtype="uint8").
                      view(dtype="<i4")).reshape((n_rows, (n_neurons + 1)))
            # Check if you have the expected data
            if missing_data or n_rows != expected_rows:
                missing_str += "({}, {}, {}); ".format(
                    placement.x, placement.y, placement.p)
                # Start the fragment for this slice empty
                fragment = numpy.empty((expected_rows, n_neurons))
                for i in xrange(0, expected_rows):
                    time = i * sampling_interval
                    # Check if there is data for this timestep
                    indexes = numpy.where(record[:, 0] == time)
                    if len(indexes[0]) > 0:
                        # Set row to data for that timestep
                        fragment[i] = record[indexes[0][0], 1:]
                    else:
                        # Set row to nan
                        fragment[i] = numpy.full(n_neurons, numpy.nan)
            else:
                # Just cut the timestamps off to get the fragment
                fragment = (record[:, 1:] / float(DataType.S1615.scale))
            if data is None:
                data = fragment
            else:
                # Add the slice fragment on axis 1 which is ids/ channel_index
                data = numpy.append(data, fragment, axis=1)
        return (data, indexes, sampling_interval)

    def get_spikes(
            self, label, buffer_manager, region, placements, graph_mapper,
            application_vertex, machine_time_step):

        spike_times = list()
        spike_ids = list()
        ms_per_tick = machine_time_step / 1000.0

        vertices = graph_mapper.get_machine_vertices(application_vertex)
        missing_str = ""
        progress = ProgressBar(vertices,
                               "Getting spikes for {}".format(label))
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)

            # Read the spikes
            n_words = int(math.ceil(vertex_slice.n_atoms / 32.0))
            n_bytes = n_words * self.N_BYTES_PER_WORD
            n_words_with_timestamp = n_words + 1

            # for buffering output info is taken form the buffer manager
            neuron_param_region_data_pointer, data_missing = \
                buffer_manager.get_data_for_vertex(
                    placement, region)
            if data_missing:
                missing_str += "({}, {}, {}); ".format(
                    placement.x, placement.y, placement.p)
            record_raw = neuron_param_region_data_pointer.read_all()
            raw_data = (numpy.asarray(record_raw, dtype="uint8").
                        view(dtype="<i4")).reshape(
                [-1, n_words_with_timestamp])
            if len(raw_data) > 0:
                record_time = raw_data[:, 0] * float(ms_per_tick)
                spikes = raw_data[:, 1].byteswap().view("uint8")
                bits = numpy.fliplr(numpy.unpackbits(spikes).reshape(
                    (-1, 32))).reshape((-1, n_bytes * 8))
                time_indices, local_indices = numpy.where(bits == 1)
                if self._indexes[SPIKES] is None:
                    indices = local_indices + vertex_slice.lo_atom
                    times = record_time[time_indices].reshape((-1))
                    spike_ids.extend(indices)
                    spike_times.extend(times)
                else:
                    neurons = self._neurons_recording(SPIKES, vertex_slice)
                    n_neurons = len(neurons)
                    for time_indice, local in zip(time_indices, local_indices):
                        if local < n_neurons:
                            spike_ids.append(neurons[local])
                            spike_times.append(record_time[time_indice])

        if len(missing_str) > 0:
            logger.warn(
                "Population {} is missing spike data in region {} from the"
                " following cores: {}".format(label, region, missing_str))

        if len(spike_ids) == 0:
            return numpy.zeros((0, 2), dtype="float")

        result = numpy.column_stack((spike_ids, spike_times))
        return result[numpy.lexsort((spike_times, spike_ids))]

    def get_recordable_variables(self):
        return self._sampling_rates.keys()

    def is_recording(self, variable):
        return self._sampling_rates[variable] > 0

    @property
    def recording_variables(self):
        results = list()
        for key in self._sampling_rates:
            if self.is_recording(key):
                results.append(key)
        return results

    def set_recording(self, variable, new_state, sampling_interval=None,
                      indexes=None):
        if variable == "all":
            for key in self._sampling_rates.keys():
                self.set_recording(key, new_state, sampling_interval, indexes)
        elif variable in self._sampling_rates:
            self._sampling_rates[variable] = \
                    recording_utils.compute_rate(new_state, sampling_interval)
            self._indexes[variable] = indexes
        else:
            msg = "Variable {} is not supported ".format(variable)
            raise fec_excceptions.ConfigurationException(msg)

    def get_buffered_sdram_per_timestep(self, variable, slice):
        """
        Returns the sdram used per timestep

        In the case where sampling is used it returns the average
        for recording and none recording based on the recording rate

        :param variable:
        :param slice:
        :return:
        """
        n_neurons = self._count_recording_per_slice(variable, slice)
        if n_neurons == 0:
            return 0
        rate = self._sampling_rates[variable]
        if variable == SPIKES:
            out_spike_words = int(math.ceil(n_neurons / 32.0))
            out_spike_bytes = out_spike_words * self.N_BYTES_PER_WORD
            return self.N_BYTES_FOR_TIMESTAMP + out_spike_bytes
        else:
            data_size = self.N_BYTES_FOR_TIMESTAMP + \
                        n_neurons * self.N_BYTES_PER_VALUE
        return data_size / rate

    def get_extra_buffered_sdram(self, variable, slice):
        """
        Returns the maximum extra sdram where sampling is used.

        The assumption here is that the there has been a previous run which
        stopped just before the recording timestep.

        Then it is run for one timestep so a whole row of data must fit.
        This method returns the cost for a whole row
        minus the average returned by get_buffered_sdram_per_timestep

        :param variable:
        :param slice:
        :return:
        """
        rate = self._sampling_rates[variable]
        if rate <= 1:
            # No sampling so get_buffered_sdram_per_timestep was correct
            return 0
        per_timestep = self.get_buffered_sdram(variable, slice)
        return per_timestep / rate * (rate - 1)

    def get_sdram_usage_for_global_parameters_in_bytes(self):
        return len(self._sampling_rates) * \
               self.N_BYTES_PER_RATE + self.N_BYTES_PER_INDEX

    def get_sdram_usage_per_neuron_in_bytes(self):
        """
        Gets the sdram usage for indexing and other controls
        :return:
        """
        return len(self._sampling_rates) * self.N_BYTES_PER_INDEX

    def get_dtcm_usage_in_bytes(self, vertex_slice):
        total_neurons = vertex_slice.hi_atom - vertex_slice.lo_atom + 1
        # global_record_params_t
        usage = self.get_sdram_usage_for_global_parameters_in_bytes()
        # indexes_t
        usage += self.get_sdram_usage_per_neuron_in_bytes() + total_neurons
        # *_index + *_increment
        usage += len(self._sampling_rates) * self.N_BYTES_PER_RATE * 2
        # out_spikes voltages inputs_excitatory inputs_inhibitory
        for variable in self._sampling_rates:
            n_neurons = self._count_recording_per_slice(variable, vertex_slice)
            if variable == SPIKES:
                out_spike_words = int(math.ceil(n_neurons / 32.0))
                out_spike_bytes = out_spike_words * self.N_BYTES_PER_WORD
                usage += self.N_BYTES_FOR_TIMESTAMP + out_spike_bytes
            else:
                usage += self.N_BYTES_FOR_TIMESTAMP + \
                         n_neurons * self.N_BYTES_PER_VALUE
        # sizes
        usage += len(self._sampling_rates) * self.N_BYTES_PER_SIZE
        # random_backoff  time_between_spikes expected_time
        # n_recordings_outstanding
        usage += self.N_BYTES_PER_WORD * 4
        return usage

    def get_n_cpu_cycles(self, n_neurons):
        return n_neurons * self.N_CPU_CYCLES_PER_NEURON * \
                len(self.recording_variables)

    def get_global_parameters(self, slice):
        params = []
        for variable in self._sampling_rates:
            params.append(NeuronParameter(
                self._sampling_rates[variable], DataType.UINT32))
        for variable in self._sampling_rates:
            n_recording = self._count_recording_per_slice(variable, slice)
            params.append(NeuronParameter(n_recording, DataType.UINT8))
        return params

    def get_index_parameters(self, vertex_slice):
        params = []
        for variable in self._sampling_rates:
            if self._sampling_rates[variable] > 0:
                if self._indexes[variable] is None:
                    local_indexes = IndexIsValue()
                else:
                    local_indexes = []
                    n_recording = sum((index >= vertex_slice.lo_atom and
                                       index <= vertex_slice.hi_atom)
                                      for index in self._indexes[variable])
                    indexes = self._indexes[variable]
                    local_index = 0
                    for index in xrange(
                            vertex_slice.lo_atom, vertex_slice.hi_atom+1):
                        if index in indexes:
                            local_indexes.append(local_index)
                            local_index += 1
                        else:
                            # write to one beyond recording range
                            local_indexes.append(n_recording)
            else:
                local_indexes = 0
            params.append(NeuronParameter(local_indexes, DataType.UINT8))
        return params
