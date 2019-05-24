from __future__ import division
try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict
import logging
import math
import numpy
from six import raise_from, iteritems
from six.moves import range, xrange
from spinn_utilities.index_is_value import IndexIsValue
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.resources.variable_sdram import VariableSDRAM
from data_specification.enums import DataType
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities import globals_variables
from spynnaker.pyNN.models.neural_properties import NeuronParameter

logger = logging.getLogger(__name__)
SPIKES = "spikes"


class _ReadOnlyDict(dict):
    def __readonly__(self, *args, **kwargs):
        raise RuntimeError("Cannot modify ReadOnlyDict")

    __setitem__ = __readonly__
    __delitem__ = __readonly__
    pop = __readonly__
    popitem = __readonly__
    clear = __readonly__
    update = __readonly__
    setdefault = __readonly__
    del __readonly__


class NeuronRecorder(object):
    __slots__ = [
        "__indexes", "__n_neurons", "__sampling_rates"]

    N_BYTES_FOR_TIMESTAMP = 4
    N_BYTES_PER_VALUE = 4
    N_BYTES_PER_RATE = 4  # uint32
    N_BYTES_PER_INDEX = 1  # currently uint8
    N_BYTES_PER_SIZE = 4
    N_CPU_CYCLES_PER_NEURON = 8
    N_BYTES_PER_WORD = 4
    N_BYTES_PER_POINTER = 4
    SARK_BLOCK_SIZE = 8  # Seen in sark.c

    MAX_RATE = 2 ** 32 - 1  # To allow a unit32_t to be used to store the rate

    def __init__(self, allowed_variables, n_neurons):
        self.__sampling_rates = OrderedDict()
        self.__indexes = dict()
        self.__n_neurons = n_neurons
        for variable in allowed_variables:
            self.__sampling_rates[variable] = 0
            self.__indexes[variable] = None

    def _count_recording_per_slice(self, variable, vertex_slice):
        if self.__sampling_rates[variable] == 0:
            return 0
        if self.__indexes[variable] is None:
            return vertex_slice.n_atoms
        return sum(vertex_slice.lo_atom <= index <= vertex_slice.hi_atom
                   for index in self.__indexes[variable])

    def _neurons_recording(self, variable, vertex_slice):
        if self.__sampling_rates[variable] == 0:
            return []
        if self.__indexes[variable] is None:
            return range(vertex_slice.lo_atom, vertex_slice.hi_atom+1)
        recording = []
        indexes = self.__indexes[variable]
        for index in xrange(vertex_slice.lo_atom, vertex_slice.hi_atom+1):
            if index in indexes:
                recording.append(index)
        return recording

    def get_neuron_sampling_interval(self, variable):
        """ Return the current sampling interval for this variable

        :param variable: PyNN name of the variable
        :return: Sampling interval in micro seconds
        """
        step = globals_variables.get_simulator().machine_time_step / 1000
        return self.__sampling_rates[variable] * step

    def get_matrix_data(
            self, label, buffer_manager, region, placements, graph_mapper,
            application_vertex, variable, n_machine_time_steps):
        """ Read a uint32 mapped to time and neuron IDs from the SpiNNaker\
            machine.

        :param label: vertex label
        :param buffer_manager: the manager for buffered data
        :param region: the DSG region ID used for this data
        :param placements: the placements object
        :param graph_mapper: \
            the mapping between application and machine vertices
        :param application_vertex:
        :param variable: PyNN name for the variable (V, gsy_inh etc.)
        :type variable: str
        :param n_machine_time_steps:
        :return:
        """
        if variable == SPIKES:
            msg = "Variable {} is not supported use get_spikes".format(SPIKES)
            raise ConfigurationException(msg)
        vertices = graph_mapper.get_machine_vertices(application_vertex)
        progress = ProgressBar(
            vertices, "Getting {} for {}".format(variable, label))
        sampling_rate = self.__sampling_rates[variable]
        expected_rows = int(math.ceil(
            n_machine_time_steps / sampling_rate))
        missing_str = ""
        data = None
        indexes = []
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)
            neurons = self._neurons_recording(variable, vertex_slice)
            n_neurons = len(neurons)
            if n_neurons == 0:
                continue
            indexes.extend(neurons)
            # for buffering output info is taken form the buffer manager
            record_raw, missing_data = buffer_manager.get_data_by_placement(
                    placement, region)
            record_length = len(record_raw)

            row_length = self.N_BYTES_FOR_TIMESTAMP + \
                n_neurons * self.N_BYTES_PER_VALUE

            # There is one column for time and one for each neuron recording
            n_rows = record_length // row_length
            if record_length > 0:
                # Converts bytes to ints and make a matrix
                record = (numpy.asarray(record_raw, dtype="uint8").
                          view(dtype="<i4")).reshape((n_rows, (n_neurons + 1)))
            else:
                record = numpy.empty((0, n_neurons))
            # Check if you have the expected data
            if not missing_data and n_rows == expected_rows:
                # Just cut the timestamps off to get the fragment
                fragment = (record[:, 1:] / float(DataType.S1615.scale))
            else:
                missing_str += "({}, {}, {}); ".format(
                    placement.x, placement.y, placement.p)
                # Start the fragment for this slice empty
                fragment = numpy.empty((expected_rows, n_neurons))
                for i in xrange(0, expected_rows):
                    time = i * sampling_rate
                    # Check if there is data for this timestep
                    local_indexes = numpy.where(record[:, 0] == time)
                    if len(local_indexes[0]) == 1:
                        fragment[i] = (record[local_indexes[0], 1:] /
                                       float(DataType.S1615.scale))
                    elif len(local_indexes[0]) > 1:
                        logger.warning(
                            "Population {} on multiple recorded data for "
                            "time {}".format(label, time))
                    else:
                        # Set row to nan
                        fragment[i] = numpy.full(n_neurons, numpy.nan)
            if data is None:
                data = fragment
            else:
                # Add the slice fragment on axis 1 which is IDs/channel_index
                data = numpy.append(data, fragment, axis=1)
        if len(missing_str) > 0:
            logger.warning(
                "Population {} is missing recorded data in region {} from the"
                " following cores: {}".format(label, region, missing_str))
        sampling_interval = self.get_neuron_sampling_interval(variable)
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

            if self.__indexes[SPIKES] is None:
                neurons_recording = vertex_slice.n_atoms
            else:
                neurons_recording = sum(
                    (index >= vertex_slice.lo_atom and
                     index <= vertex_slice.hi_atom)
                    for index in self.__indexes[SPIKES])
                if neurons_recording == 0:
                    continue
            # Read the spikes
            n_words = int(math.ceil(neurons_recording / 32.0))
            n_bytes = n_words * self.N_BYTES_PER_WORD
            n_words_with_timestamp = n_words + 1

            # for buffering output info is taken form the buffer manager
            record_raw, data_missing = buffer_manager.get_data_by_placement(
                    placement, region)
            if data_missing:
                missing_str += "({}, {}, {}); ".format(
                    placement.x, placement.y, placement.p)
            if len(record_raw) > 0:
                raw_data = (numpy.asarray(record_raw, dtype="uint8").
                            view(dtype="<i4")).reshape(
                    [-1, n_words_with_timestamp])
            else:
                raw_data = record_raw
            if len(raw_data) > 0:
                record_time = raw_data[:, 0] * float(ms_per_tick)
                spikes = raw_data[:, 1:].byteswap().view("uint8")
                bits = numpy.fliplr(numpy.unpackbits(spikes).reshape(
                    (-1, 32))).reshape((-1, n_bytes * 8))
                time_indices, local_indices = numpy.where(bits == 1)
                if self.__indexes[SPIKES] is None:
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
            logger.warning(
                "Population {} is missing spike data in region {} from the"
                " following cores: {}".format(label, region, missing_str))

        if len(spike_ids) == 0:
            return numpy.zeros((0, 2), dtype="float")

        result = numpy.column_stack((spike_ids, spike_times))
        return result[numpy.lexsort((spike_times, spike_ids))]

    def get_recordable_variables(self):
        return self.__sampling_rates.keys()

    def is_recording(self, variable):
        try:
            return self.__sampling_rates[variable] > 0
        except KeyError as e:
            msg = "Variable {} is not supported. Supported variables are {}" \
                  "".format(variable, self.get_recordable_variables())
            raise_from(ConfigurationException(msg), e)

    @property
    def recording_variables(self):
        results = list()
        for region, rate in self.__sampling_rates.items():
            if rate > 0:
                results.append(region)
        return results

    @property
    def recorded_region_ids(self):
        results = list()
        for id, rate in enumerate(self.__sampling_rates.values()):
            if rate > 0:
                results.append(id)
        return results

    def _compute_rate(self, sampling_interval):
        """ Convert a sampling interval into a rate. \
            Remember, machine time step is in nanoseconds

        :param sampling_interval: interval between samples in microseconds
        :return: rate
        """
        if sampling_interval is None:
            return 1

        step = globals_variables.get_simulator().machine_time_step / 1000
        rate = int(sampling_interval / step)
        if sampling_interval != rate * step:
            msg = "sampling_interval {} is not an an integer multiple of the "\
                  "simulation timestep {}".format(sampling_interval, step)
            raise ConfigurationException(msg)
        if rate > self.MAX_RATE:
            msg = "sampling_interval {} higher than max allowed which is {}" \
                  "".format(sampling_interval, step * self.MAX_RATE)
            raise ConfigurationException(msg)
        return rate

    def check_indexes(self, indexes):
        if indexes is None:
            return

        if len(indexes) == 0:
            raise ConfigurationException("Empty indexes list")

        found = False
        warning = None
        for index in indexes:
            if index < 0:
                raise ConfigurationException(
                    "Negative indexes are not supported")
            elif index >= self.__n_neurons:
                warning = "Ignoring indexes greater than population size."
            else:
                found = True
            if warning is not None:
                logger.warning(warning)
        if not found:
            raise ConfigurationException(
                "All indexes larger than population size")

    def _turn_off_recording(self, variable, sampling_interval, remove_indexes):
        if self.__sampling_rates[variable] == 0:
            # Already off so ignore other parameters
            return

        if remove_indexes is None:
            # turning all off so ignoring sampling interval
            self.__sampling_rates[variable] = 0
            self.__indexes[variable] = None
            return

        # No good reason to specify_interval when turning off
        if sampling_interval is not None:
            rate = self._compute_rate(sampling_interval)
            # But if they do make sure it is the same as before
            if rate != self.__sampling_rates[variable]:
                raise ConfigurationException(
                    "Illegal sampling_interval parameter while turning "
                    "off recording")

        if self.__indexes[variable] is None:
            # start with all indexes
            self.__indexes[variable] = range(self.__n_neurons)

        # remove the indexes not recording
        self.__indexes[variable] = \
            [index for index in self.__indexes[variable]
                if index not in remove_indexes]

        # Check is at least one index still recording
        if len(self.__indexes[variable]) == 0:
            self.__sampling_rates[variable] = 0
            self.__indexes[variable] = None

    def _check_complete_overwrite(self, variable, indexes):
        if indexes is None:
            # overwriting all OK!
            return
        if self.__indexes[variable] is None:
            if set(set(range(self.__n_neurons))).issubset(set(indexes)):
                # overwriting all previous so OK!
                return
        else:
            if set(self.__indexes[variable]).issubset(set(indexes)):
                # overwriting all previous so OK!
                return
        raise ConfigurationException(
            "Current implementation does not support multiple "
            "sampling_intervals for {} on one population.".format(
                variable))

    def _turn_on_recording(self, variable, sampling_interval, indexes):

        rate = self._compute_rate(sampling_interval)
        if self.__sampling_rates[variable] == 0:
            # Previously not recording so OK
            self.__sampling_rates[variable] = rate
        elif rate != self.__sampling_rates[variable]:
            self._check_complete_overwrite(variable, indexes)
        # else rate not changed so no action

        if indexes is None:
            # previous recording indexes does not matter as now all (None)
            self.__indexes[variable] = None
        else:
            # make sure indexes is not a generator like range
            indexes = list(indexes)
            self.check_indexes(indexes)
            if self.__indexes[variable] is not None:
                # merge the two indexes
                indexes = self.__indexes[variable] + indexes
            # Avoid duplicates and keep in numerical order
            self.__indexes[variable] = list(set(indexes))
            self.__indexes[variable].sort()

    def set_recording(self, variable, new_state, sampling_interval=None,
                      indexes=None):
        if variable == "all":
            for key in self.__sampling_rates.keys():
                self.set_recording(key, new_state, sampling_interval, indexes)
        elif variable in self.__sampling_rates:
            if new_state:
                self._turn_on_recording(variable, sampling_interval, indexes)
            else:
                self._turn_off_recording(variable, sampling_interval, indexes)
        else:
            raise ConfigurationException("Variable {} is not supported".format(
                variable))

    def get_buffered_sdram_per_record(self, variable, vertex_slice):
        """ Return the SDRAM used per record

        :param variable:
        :param vertex_slice:
        :return:
        """
        n_neurons = self._count_recording_per_slice(variable, vertex_slice)
        if n_neurons == 0:
            return 0
        if variable == SPIKES:
            # Overflow can be ignored as it is not save if in an extra word
            out_spike_words = int(math.ceil(n_neurons / 32.0))
            out_spike_bytes = out_spike_words * self.N_BYTES_PER_WORD
            return self.N_BYTES_FOR_TIMESTAMP + out_spike_bytes
        else:
            return self.N_BYTES_FOR_TIMESTAMP + \
                        n_neurons * self.N_BYTES_PER_VALUE

    def get_buffered_sdram_per_timestep(self, variable, vertex_slice):
        """ Return the SDRAM used per timestep.

        In the case where sampling is used it returns the average\
        for recording and none recording based on the recording rate

        :param variable:
        :param vertex_slice:
        :return:
        """
        rate = self.__sampling_rates[variable]
        if rate == 0:
            return 0

        data_size = self.get_buffered_sdram_per_record(variable, vertex_slice)
        if rate == 1:
            return data_size
        else:
            return data_size // rate

    def get_sampling_overflow_sdram(self, vertex_slice):
        """ Get the extra SDRAM that should be reserved if using per_timestep

        This is the extra that must be reserved if per_timestep is an average\
        rather than fixed for every timestep.

        When sampling the average * time_steps may not be quite enough.\
        This returns the extra space in the worst case\
        where time_steps is a multiple of sampling rate + 1,\
        and recording is done in the first and last time_step

        :param vertex_slice:
        :return: Highest possible overflow needed
        """
        overflow = 0
        for variable, rate in iteritems(self.__sampling_rates):
            # If rate is 0 no recording so no overflow
            # If rate is 1 there is no overflow as average is exact
            if rate > 1:
                data_size = self.get_buffered_sdram_per_record(
                    variable,  vertex_slice)
                overflow += data_size // rate * (rate - 1)
        return overflow

    def get_buffered_sdram(self, variable, vertex_slice, n_machine_time_steps):
        """ Returns the SDRAM used for this may timesteps

        If required the total is rounded up so the space will always fit

        :param variable: The
        :param vertex_slice:
        :return:
        """
        rate = self.__sampling_rates[variable]
        if rate == 0:
            return 0
        data_size = self.get_buffered_sdram_per_record(variable, vertex_slice)
        records = n_machine_time_steps // rate
        if n_machine_time_steps % rate > 0:
            records = records + 1
        return data_size * records

    def get_sdram_usage_in_bytes(self, vertex_slice):
        n_words_for_n_neurons = (vertex_slice.n_atoms + 3) // 4
        n_bytes_for_n_neurons = n_words_for_n_neurons * 4
        return (8 + n_bytes_for_n_neurons) * len(self.__sampling_rates)

    def _get_fixed_sdram_usage(self, vertex_slice):
        total_neurons = vertex_slice.hi_atom - vertex_slice.lo_atom + 1
        fixed_sdram = 0
        # Recording rate for each neuron
        fixed_sdram += self.N_BYTES_PER_RATE
        # Number of recording neurons
        fixed_sdram += self.N_BYTES_PER_INDEX
        # index_parameters one per neuron
        # even if not recording as also act as a gate
        fixed_sdram += self.N_BYTES_PER_INDEX * total_neurons
        return fixed_sdram

    def get_variable_sdram_usage(self, vertex_slice):
        fixed_sdram = 0
        per_timestep_sdram = 0
        for variable in self.__sampling_rates:
            rate = self.__sampling_rates[variable]
            fixed_sdram += self._get_fixed_sdram_usage(vertex_slice)
            if rate > 0:
                fixed_sdram += self.SARK_BLOCK_SIZE
                per_record = self.get_buffered_sdram_per_record(
                    variable, vertex_slice)
                if rate == 1:
                    # Add size for one record as recording every timestep
                    per_timestep_sdram += per_record
                else:
                    # Get the average cost per timestep
                    average_per_timestep = per_record / rate
                    per_timestep_sdram += average_per_timestep
                    # Add the rest once to fixed for worst case
                    fixed_sdram += (per_record - average_per_timestep)
        return VariableSDRAM(fixed_sdram, per_timestep_sdram)

    def get_dtcm_usage_in_bytes(self, vertex_slice):
        # *_rate + n_neurons_recording_* + *_indexes
        usage = self.get_sdram_usage_in_bytes(vertex_slice)
        # *_count + *_increment
        usage += len(self.__sampling_rates) * self.N_BYTES_PER_POINTER * 2
        # out_spikes, *_values
        for variable in self.__sampling_rates:
            if variable == SPIKES:
                out_spike_words = int(math.ceil(vertex_slice.n_atoms / 32.0))
                out_spike_bytes = out_spike_words * self.N_BYTES_PER_WORD
                usage += self.N_BYTES_FOR_TIMESTAMP + out_spike_bytes
            else:
                usage += (self.N_BYTES_FOR_TIMESTAMP +
                          vertex_slice.n_atoms * self.N_BYTES_PER_VALUE)
        # *_size
        usage += len(self.__sampling_rates) * self.N_BYTES_PER_SIZE
        # n_recordings_outstanding
        usage += self.N_BYTES_PER_WORD * 4
        return usage

    def get_n_cpu_cycles(self, n_neurons):
        return n_neurons * self.N_CPU_CYCLES_PER_NEURON * \
                len(self.recording_variables)

    def get_data(self, vertex_slice):
        data = list()
        n_words_for_n_neurons = (vertex_slice.n_atoms + 3) // 4
        n_bytes_for_n_neurons = n_words_for_n_neurons * 4
        for variable in self.__sampling_rates:
            rate = self.__sampling_rates[variable]
            n_recording = self._count_recording_per_slice(
                variable, vertex_slice)
            data.append(numpy.array([rate, n_recording], dtype="uint32"))
            if rate == 0:
                data.append(numpy.zeros(n_words_for_n_neurons, dtype="uint32"))
            elif self.__indexes[variable] is None:
                data.append(numpy.arange(
                    n_bytes_for_n_neurons, dtype="uint8").view("uint32"))
            else:
                indexes = self.__indexes[variable]
                local_index = 0
                local_indexes = list()
                for index in xrange(n_bytes_for_n_neurons):
                    if index + vertex_slice.lo_atom in indexes:
                        local_indexes.append(local_index)
                        local_index += 1
                    else:
                        # write to one beyond recording range
                        local_indexes.append(n_recording)
                data.append(
                    numpy.array(local_indexes, dtype="uint8").view("uint32"))
        return numpy.concatenate(data)

    def get_global_parameters(self, vertex_slice):
        params = []
        for variable in self.__sampling_rates:
            params.append(NeuronParameter(
                self.__sampling_rates[variable], DataType.UINT32))
        for variable in self.__sampling_rates:
            n_recording = self._count_recording_per_slice(
                variable, vertex_slice)
            params.append(NeuronParameter(n_recording, DataType.UINT8))
        return params

    def get_index_parameters(self, vertex_slice):
        params = []
        for variable in self.__sampling_rates:
            if self.__sampling_rates[variable] <= 0:
                local_indexes = 0
            elif self.__indexes[variable] is None:
                local_indexes = IndexIsValue()
            else:
                local_indexes = []
                n_recording = sum(
                    vertex_slice.lo_atom <= index <= vertex_slice.hi_atom
                    for index in self.__indexes[variable])
                indexes = self.__indexes[variable]
                local_index = 0
                for index in xrange(
                        vertex_slice.lo_atom, vertex_slice.hi_atom+1):
                    if index in indexes:
                        local_indexes.append(local_index)
                        local_index += 1
                    else:
                        # write to one beyond recording range
                        local_indexes.append(n_recording)
            params.append(NeuronParameter(local_indexes, DataType.UINT8))
        return params

    @property
    def _indexes(self):  # for testing only
        return _ReadOnlyDict(self.__indexes)
