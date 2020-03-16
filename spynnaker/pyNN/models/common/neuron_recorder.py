# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
from collections import OrderedDict
import logging
import math
import numpy
from six import raise_from, iteritems
from six.moves import range, xrange
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.resources.variable_sdram import VariableSDRAM
from data_specification.enums import DataType
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, MICRO_TO_MILLISECOND_CONVERSION, BITS_PER_WORD)
from spinn_front_end_common.interface.buffer_management import \
    recording_utilities
import itertools

logger = FormatAdapter(logging.getLogger(__name__))


class _ReadOnlyDict(dict):
    def __readonly__(self, *args, **kwargs):  # pylint: disable=unused-argument
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
        "__indexes",
        "__n_neurons",
        "__sampling_rates",
        "__data_types",
        "__bitfield_variables"]

    N_BYTES_FOR_TIMESTAMP = DataType.UINT32.size

    # how many time steps to wait between recordings
    N_BYTES_PER_RATE = DataType.UINT32.size

    # the enum type for the state struct
    N_BYTES_PER_ENUM = DataType.UINT32.size

    # size of a index in terms of position into recording array
    N_BYTES_PER_INDEX = DataType.UINT8.size  # currently uint8

    # size of the counter for spike recording
    N_BYTES_PER_COUNT = DataType.UINT32.size

    # size of the increment for spike recording
    N_BYTES_PER_INCREMENT = DataType.UINT32.size

    # sampling temporal value size (how many ticks between recordings)
    N_BYTES_PER_SIZE = DataType.UINT32.size
    N_CPU_CYCLES_PER_NEURON = 8
    N_BYTES_PER_POINTER = DataType.UINT32.size
    SARK_BLOCK_SIZE = 2 * BYTES_PER_WORD  # Seen in sark.c

    # size of the counter for outstanding recording
    N_BYTES_PER_OUTSTANDING_RECORDING = DataType.UINT32.size

    # number of items types (currently non-bitfield and bitfield)
    N_ITEM_TYPES = 2

    # flag for spikes
    SPIKES = "spikes"

    MAX_RATE = 2 ** 32 - 1  # To allow a unit32_t to be used to store the rate

    def __init__(
            self, allowed_variables, data_types, bitfield_variables,
            n_neurons):
        self.__sampling_rates = OrderedDict()
        self.__indexes = dict()
        self.__data_types = data_types
        self.__n_neurons = n_neurons
        self.__bitfield_variables = bitfield_variables
        for variable in itertools.chain(allowed_variables, bitfield_variables):
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
            return range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1)
        indexes = self.__indexes[variable]
        return [
            i for i in xrange(vertex_slice.lo_atom, vertex_slice.hi_atom + 1)
            if i in indexes]

    def get_neuron_sampling_interval(self, variable):
        """ Return the current sampling interval for this variable

        :param variable: PyNN name of the variable
        :return: Sampling interval in micro seconds
        """
        step = (globals_variables.get_simulator().machine_time_step /
                MICRO_TO_MILLISECOND_CONVERSION)
        return self.__sampling_rates[variable] * step

    def _convert_placement_matrix_data(
            self, row_data, n_rows, data_row_length, variable, n_neurons):

        surplus_bytes = self.N_BYTES_FOR_TIMESTAMP
        var_data = (row_data[:, surplus_bytes:].reshape(
            n_rows * data_row_length))
        dtype = self.__data_types[variable]
        placement_data = dtype.decode_array(var_data).reshape(
            n_rows, n_neurons)
        return placement_data

    @staticmethod
    def _process_missing_data(
            missing_str, placement, expected_rows, n_neurons, times,
            sampling_rate, label, placement_data):
        missing_str += "({}, {}, {}); ".format(
            placement.x, placement.y, placement.p)
        # Start the fragment for this slice empty
        fragment = numpy.empty((expected_rows, n_neurons))
        for i in xrange(0, expected_rows):
            time = i * sampling_rate
            # Check if there is data for this time step
            local_indexes = numpy.where(times == time)
            if len(local_indexes[0]) == 1:
                fragment[i] = placement_data[local_indexes[0]]
            elif len(local_indexes[0]) > 1:
                fragment[i] = placement_data[local_indexes[0], 1:]
                logger.warning(
                    "Population {} has multiple recorded data for time {}",
                    label, time)
            else:
                # Set row to nan
                fragment[i] = numpy.full(n_neurons, numpy.nan)
        return fragment

    def _get_placement_matrix_data(
            self, variable, placements, vertex, sampling_interval,
            indexes, region, graph_mapper,
            buffer_manager, expected_rows, missing_str, sampling_rate, label):
        """ processes a placement for matrix data

        :param variable: the variable to read
        :param placements: the placements object
        :param vertex: the vertex to read from
        :param sampling_interval: the interval of sampling
        :param indexes: the indexes of neurons to be added to
        :param region: the recording region id
        :param graph_mapper: the graph mapper
        :param buffer_manager: the buffer manager
        :param expected_rows: how many rows the tools think should be recorded
        :param missing_str: string for reporting missing stuff
        :param sampling_rate: the rate of sampling
        :param label: the vertex label.
        :return: placement data and sampling interval.
        """

        placement = placements.get_placement_of_vertex(vertex)
        vertex_slice = graph_mapper.get_slice(vertex)
        neurons = self._neurons_recording(variable, vertex_slice)
        n_neurons = len(neurons)
        if n_neurons == 0:
            return None, sampling_interval
        indexes.extend(neurons)

        # for buffering output info is taken form the buffer manager
        record_raw, missing_data = buffer_manager.get_data_by_placement(
            placement, region)
        record_length = len(record_raw)

        # If there is no data, return empty for all timesteps
        if record_length == 0:
            return numpy.zeros((expected_rows, n_neurons), dtype="float64")

        # There is one column for time and one for each neuron recording
        data_row_length = n_neurons * self.__data_types[variable].size
        full_row_length = data_row_length + self.N_BYTES_FOR_TIMESTAMP
        n_rows = record_length // full_row_length
        row_data = numpy.asarray(record_raw, dtype="uint8").reshape(
            n_rows, full_row_length)
        placement_data = self._convert_placement_matrix_data(
            row_data, n_rows, data_row_length, variable, n_neurons)

        # If everything is there, return it
        if not missing_data and n_rows == expected_rows:
            return placement_data

        # Got data but its missing bits, so get times
        time_bytes = (
            row_data[:, 0: self.N_BYTES_FOR_TIMESTAMP].reshape(
                n_rows * self.N_BYTES_FOR_TIMESTAMP))
        times = time_bytes.view("<i4").reshape(n_rows, 1)

        # process data from core for missing data
        placement_data = self._process_missing_data(
            missing_str, placement, expected_rows, n_neurons, times,
            sampling_rate, label, placement_data)
        return placement_data

    @staticmethod
    def expected_rows_for_a_run_time(n_machine_time_steps, sampling_rate):
        """ determines how many rows to see based off how long its ran for

        :param n_machine_time_steps: map of vertex to time steps
        :param sampling_rate: the sampling rate for a given variable
        :return: how many rows there should be.
        """
        return int(math.ceil(n_machine_time_steps / sampling_rate))

    def get_matrix_data(
            self, label, buffer_manager, region, placements, graph_mapper,
            application_vertex, variable, n_machine_time_steps):
        """ Read a uint32 mapped to time and neuron IDs from the SpiNNaker\
            machine and converts to required data types with scaling if needed.

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
        if variable in self.__bitfield_variables:
            msg = "Variable {} is not supported, use get_spikes".format(
                variable)
            raise ConfigurationException(msg)
        vertices = graph_mapper.get_machine_vertices(application_vertex)
        progress = ProgressBar(
            vertices, "Getting {} for {}".format(variable, label))
        sampling_rate = self.__sampling_rates[variable]
        missing_str = ""
        pop_level_data = None
        sampling_interval = self.get_neuron_sampling_interval(variable)

        indexes = []
        for vertex in progress.over(vertices):
            expected_rows = self.expected_rows_for_a_run_time(
                n_machine_time_steps, sampling_rate)

            placement_data = self._get_placement_matrix_data(
                variable, placements, vertex, sampling_interval, indexes,
                region, graph_mapper, buffer_manager, expected_rows,
                missing_str, sampling_rate, label)

            if placement_data is not None:
                # append to the population data
                if pop_level_data is None:
                    pop_level_data = placement_data
                else:
                    # Add the slice fragment on axis 1
                    # which is IDs/channel_index
                    pop_level_data = numpy.append(
                        pop_level_data, placement_data, axis=1)

        # warn user of missing data
        if len(missing_str) > 0:
            logger.warning(
                "Population {} is missing recorded data in region {} from the"
                " following cores: {}", label, region, missing_str)

        return pop_level_data, indexes, sampling_interval

    def get_spikes(
            self, label, buffer_manager, region, placements, graph_mapper,
            application_vertex, variable, machine_time_step):
        if variable not in self.__bitfield_variables:
            msg = "Variable {} is not supported, use get_matrix_data".format(
                variable)
            raise ConfigurationException(msg)

        spike_times = list()
        spike_ids = list()

        vertices = graph_mapper.get_machine_vertices(application_vertex)
        missing_str = ""
        progress = ProgressBar(vertices, "Getting spikes for {}".format(label))
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)

            ms_per_tick = machine_time_step / MICRO_TO_MILLISECOND_CONVERSION
            neurons = self._neurons_recording(variable, vertex_slice)
            neurons_recording = len(neurons)
            if neurons_recording == 0:
                continue

            # Read the spikes
            n_words = int(math.ceil(neurons_recording / BITS_PER_WORD))
            n_bytes = n_words * BYTES_PER_WORD
            n_words_with_timestamp = n_words + 1

            # for buffering output info is taken form the buffer manager
            record_raw, data_missing = buffer_manager.get_data_by_placement(
                    placement, region)
            if data_missing:
                missing_str += "({}, {}, {}); ".format(
                    placement.x, placement.y, placement.p)
            if len(record_raw) > 0:
                raw_data = (
                    numpy.asarray(record_raw, dtype="uint8").view(
                        dtype="<i4")).reshape([-1, n_words_with_timestamp])
            else:
                raw_data = record_raw
            if len(raw_data) > 0:
                record_time = raw_data[:, 0] * float(ms_per_tick)
                spikes = raw_data[:, 1:].byteswap().view("uint8")
                bits = numpy.fliplr(numpy.unpackbits(spikes).reshape(
                    (-1, 32))).reshape((-1, n_bytes * 8))
                time_indices, local_indices = numpy.where(bits == 1)
                if self.__indexes[variable] is None:
                    indices = local_indices + vertex_slice.lo_atom
                    times = record_time[time_indices].reshape((-1))
                    spike_ids.extend(indices)
                    spike_times.extend(times)
                else:
                    for time_indice, local in zip(time_indices, local_indices):
                        if local < neurons_recording:
                            spike_ids.append(neurons[local])
                            spike_times.append(record_time[time_indice])

        if len(missing_str) > 0:
            logger.warning(
                "Population {} is missing spike data in region {} from the"
                " following cores: {}", label, region, missing_str)

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
        for _id, rate in enumerate(self.__sampling_rates.values()):
            if rate > 0:
                results.append(_id)
        return results

    def _is_recording(self, variable, vertex_slice):
        if self.__sampling_rates[variable] == 0:
            return False
        if self.__indexes[variable] is None:
            return True
        indexes = self.__indexes[variable]
        for index in xrange(vertex_slice.lo_atom, vertex_slice.hi_atom+1):
            if index in indexes:
                return True
        return False

    def recorded_ids_by_slice(self, vertex_slice):
        return [_id
                for _id, variable in enumerate(self.__sampling_rates.keys())
                if self._is_recording(variable, vertex_slice)]

    def _compute_rate(self, sampling_interval):
        """ Convert a sampling interval into a rate. \
            Remember, machine time step is in nanoseconds

        :param sampling_interval: interval between samples in microseconds
        :return: rate
        """
        if sampling_interval is None:
            return 1

        step = (
            globals_variables.get_simulator().machine_time_step /
            MICRO_TO_MILLISECOND_CONVERSION)
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

    def _get_buffered_sdram(self, vertex_slice, n_machine_time_steps):
        values = list()
        for variable in self.__sampling_rates:
            values.append(self.get_buffered_sdram(
                variable, vertex_slice, n_machine_time_steps))
        return values

    def write_neuron_recording_region(
            self, spec, neuron_recording_region, vertex_slice,
            data_n_time_steps):
        """ recording data specification

        :param spec: dsg spec
        :param neuron_recording_region: the recording region
        :param vertex_slice: the vertex slice
        :param data_n_time_steps: how many time steps to run this time
        :rtype: None
        """
        spec.switch_write_focus(neuron_recording_region)
        spec.write_array(recording_utilities.get_recording_header_array(
            self._get_buffered_sdram(vertex_slice, data_n_time_steps)))

        # Write the number of variables and bitfields
        n_vars = len(self.__sampling_rates) - len(self.__bitfield_variables)
        spec.write_value(data=n_vars)
        spec.write_value(data=len(self.__bitfield_variables))

        # Write the recording data
        recording_data = self._get_data(vertex_slice)
        spec.write_array(recording_data)

    def get_buffered_sdram_per_record(self, variable, vertex_slice):
        """ Return the SDRAM used per record

        :param variable:
        :param vertex_slice:
        :return:
        """
        n_neurons = self._count_recording_per_slice(variable, vertex_slice)
        if n_neurons == 0:
            return 0
        if variable in self.__bitfield_variables:
            # Overflow can be ignored as it is not save if in an extra word
            out_spike_words = int(math.ceil(n_neurons / BITS_PER_WORD))
            out_spike_bytes = out_spike_words * BYTES_PER_WORD
            return self.N_BYTES_FOR_TIMESTAMP + out_spike_bytes
        else:
            size = self.__data_types[variable].size
            return self.N_BYTES_FOR_TIMESTAMP + (n_neurons * size)

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
        """ Returns the SDRAM used for this may time steps

        If required the total is rounded up so the space will always fit

        :param variable: The variable to get buffered sdram of
        :param vertex_slice: vertex slice
        :param n_machine_time_steps: how many machine time steps to run for
        :return: data size
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
        n_words_for_n_neurons = int(
            math.ceil(vertex_slice.n_atoms // BYTES_PER_WORD))
        n_bytes_for_n_neurons = n_words_for_n_neurons * BYTES_PER_WORD
        var_bytes = (
            (self.N_BYTES_PER_RATE + self.N_BYTES_PER_SIZE +
             self.N_BYTES_PER_ENUM + n_bytes_for_n_neurons) *
            (len(self.__sampling_rates) - len(self.__bitfield_variables)))
        bitfield_bytes = (
            (self.N_BYTES_PER_RATE + self.N_BYTES_PER_SIZE +
             n_bytes_for_n_neurons) *
            len(self.__bitfield_variables))
        return ((self.N_ITEM_TYPES * DataType.UINT32.size) + var_bytes +
                bitfield_bytes)

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

    def get_static_sdram_usage(self, vertex_slice):
        n_record = len(self.__sampling_rates)
        sdram = (
            recording_utilities.get_recording_header_size(n_record) +
            recording_utilities.get_recording_data_constant_size(n_record) +
            self.get_sdram_usage_in_bytes(vertex_slice))
        return int(sdram)

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
        usage += (len(self.__sampling_rates) * (
            self.N_BYTES_PER_POINTER + self.N_BYTES_PER_COUNT +
            self.N_BYTES_PER_INCREMENT))

        # out_spikes, *_values
        for variable in self.__sampling_rates:
            if variable in self.__bitfield_variables:
                out_spike_words = int(
                    math.ceil(vertex_slice.n_atoms / BITS_PER_WORD))
                out_spike_bytes = out_spike_words * BYTES_PER_WORD
                usage += self.N_BYTES_FOR_TIMESTAMP + out_spike_bytes
            else:
                size = self.__data_types[variable].size
                usage += (
                    self.N_BYTES_FOR_TIMESTAMP + vertex_slice.n_atoms * size)
        # *_size
        usage += len(self.__sampling_rates) * self.N_BYTES_PER_SIZE

        # n_recordings_outstanding
        usage += self.N_BYTES_PER_OUTSTANDING_RECORDING
        return usage

    def get_n_cpu_cycles(self, n_neurons):
        return n_neurons * self.N_CPU_CYCLES_PER_NEURON * \
                len(self.recording_variables)

    def __add_indices(self, data, variable, rate, n_recording, vertex_slice):
        n_words_for_n_neurons = int(
            math.ceil(vertex_slice.n_atoms / BYTES_PER_WORD))
        n_bytes_for_n_neurons = n_words_for_n_neurons * BYTES_PER_WORD
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

    def _get_data(self, vertex_slice):
        data = list()
        for variable in self.__sampling_rates:
            # Do bitfields afterwards
            if variable in self.__bitfield_variables:
                continue
            rate = self.__sampling_rates[variable]
            n_recording = self._count_recording_per_slice(
                variable, vertex_slice)
            dtype = self.__data_types[variable]
            data.append(numpy.array(
                [rate, n_recording, dtype.size], dtype="uint32"))
            self.__add_indices(data, variable, rate, n_recording, vertex_slice)

        for variable in self.__bitfield_variables:
            rate = self.__sampling_rates[variable]
            n_recording = self._count_recording_per_slice(
                variable, vertex_slice)
            data.append(numpy.array([rate, n_recording], dtype="uint32"))
            self.__add_indices(data, variable, rate, n_recording, vertex_slice)

        return numpy.concatenate(data)

    @property
    def _indexes(self):  # for testing only
        return _ReadOnlyDict(self.__indexes)
