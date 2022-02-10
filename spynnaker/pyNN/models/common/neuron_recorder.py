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
from collections import OrderedDict
import itertools
import logging
import math
import numpy
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.resources.variable_sdram import VariableSDRAM
from data_specification.enums import DataType
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BITS_PER_WORD)
from spinn_front_end_common.utilities.globals_variables import (
    machine_time_step_ms)

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


def get_sampling_interval(sampling_rate):
    """ Return the current sampling interval given a sampling rate

    :param float sampling_rate: The sampling rate in time steps
    :return: Sampling interval in microseconds
    :rtype: float
    """
    return sampling_rate * machine_time_step_ms()


class NeuronRecorder(object):
    __slots__ = [
        "__indexes",
        "__n_neurons",
        "__sampling_rates",
        "__data_types",
        "__bitfield_variables",
        "__per_timestep_variables",
        "__per_timestep_datatypes",
        "__per_timestep_recording",
        "__events_per_core_variables",
        "__events_per_core_datatypes",
        "__events_per_core_recording",
        "__events_per_ts",
        "__region_ids"]

    _N_BYTES_FOR_TIMESTAMP = BYTES_PER_WORD
    _N_BYTES_PER_RATE = BYTES_PER_WORD
    _N_BYTES_PER_ENUM = BYTES_PER_WORD

    #: size of a index in terms of position into recording array
    _N_BYTES_PER_INDEX = DataType.UINT8.size  # currently uint8

    #: size of the counter for spike recording
    _N_BYTES_PER_COUNT = BYTES_PER_WORD

    #: size of the increment for spike recording
    _N_BYTES_PER_INCREMENT = BYTES_PER_WORD

    _N_BYTES_PER_SIZE = BYTES_PER_WORD
    # sampling temporal value size (how many ticks between recordings)
    _N_CPU_CYCLES_PER_NEURON = 8
    _N_BYTES_PER_POINTER = BYTES_PER_WORD
    _SARK_BLOCK_SIZE = 2 * BYTES_PER_WORD  # Seen in sark.c

    #: size of the counter for outstanding recording
    _N_BYTES_PER_OUTSTANDING_RECORDING = BYTES_PER_WORD

    #: number of items types (currently non-bitfield and bitfield)
    _N_ITEM_TYPES = 2

    #: flag for spikes
    SPIKES = "spikes"

    #: packets-per-timestep
    PACKETS = "packets-per-timestep"

    #: packets-per-timestep data type
    PACKETS_TYPE = DataType.UINT32

    #: rewiring
    REWIRING = "rewiring"

    #: rewiring data type
    REWIRING_TYPE = DataType.UINT32

    #: max_rewires
    MAX_REWIRES = "max_rewires"

    #: number of words per rewiring entry
    REWIRING_N_WORDS = 2

    #: rewiring: shift values to decode recorded value
    _PRE_ID_SHIFT = 9
    _POST_ID_SHIFT = 1
    _POST_ID_FACTOR = 2 ** 8
    _FIRST_BIT = 1

    _MAX_RATE = 2 ** 32 - 1  # To allow a unit32_t to be used to store the rate

    def __init__(
            self, allowed_variables, data_types, bitfield_variables,
            n_neurons, per_timestep_variables, per_timestep_datatypes,
            events_per_core_variables, events_per_core_datatypes):
        """
        :param list(str) allowed_variables:
        :param list(str) data_types:
        :param list(str) bitfield_variables:
        :param int n_neurons:
        """
        self.__sampling_rates = OrderedDict()
        self.__indexes = dict()
        self.__data_types = data_types
        self.__n_neurons = n_neurons
        self.__bitfield_variables = bitfield_variables

        self.__per_timestep_variables = per_timestep_variables
        self.__per_timestep_datatypes = per_timestep_datatypes
        self.__per_timestep_recording = set()

        self.__events_per_core_variables = events_per_core_variables
        self.__events_per_core_datatypes = events_per_core_datatypes
        self.__events_per_core_recording = set()
        self.__events_per_ts = dict()
        self.__events_per_ts[self.MAX_REWIRES] = 0  # record('all')

        # Get info on variables like these
        for variable in itertools.chain(allowed_variables, bitfield_variables):
            self.__sampling_rates[variable] = 0
            self.__indexes[variable] = None

        # Get region ids for all variables
        self.__region_ids = dict()
        for region_id, variable in enumerate(itertools.chain(
                    allowed_variables, bitfield_variables,
                    events_per_core_variables, per_timestep_variables)):
            self.__region_ids[variable] = region_id

    def add_region_offset(self, offset):
        """ Add an offset to the regions.  Used when there are multiple\
            recorders on a single core

        :param int offset: The offset to add
        """
        self.__region_ids = dict((var, region + offset)
                                 for var, region in self.__region_ids.items())

    def _count_recording_per_slice(
            self, variable, vertex_slice):
        """
        :param str variable:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: int or None
        """
        if variable not in self.__sampling_rates:
            return None
        if self.__sampling_rates[variable] == 0:
            return 0
        if self.__indexes[variable] is None:
            return vertex_slice.n_atoms
        return sum(vertex_slice.lo_atom <= index <= vertex_slice.hi_atom
                   for index in self.__indexes[variable])

    def _max_recording_per_slice(self, variable, n_atoms):
        """
        """
        if variable not in self.__sampling_rates:
            return None
        if self.__sampling_rates[variable] == 0:
            return 0
        if self.__indexes[variable] is None:
            return n_atoms
        indices = self.__indexes[variable]
        max_index = numpy.amax(indices)
        existence = numpy.zeros(max_index + 1)
        existence[indices] = 1
        splits = numpy.arange(n_atoms, max_index + 1, n_atoms)
        split_array = numpy.array_split(existence, splits)
        return max([numpy.sum(s) for s in split_array])

    def _neurons_recording(self, variable, vertex_slice):
        """
        :param str variable:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: iterable(int)
        """
        if self.__sampling_rates[variable] == 0:
            return []
        if self.__indexes[variable] is None:
            return range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1)
        indexes = self.__indexes[variable]
        return [
            i for i in range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1)
            if i in indexes]

    def get_neuron_sampling_interval(self, variable):
        """ Return the current sampling interval for this variable

        :param str variable: PyNN name of the variable
        :return: Sampling interval in microseconds
        :rtype: float
        """
        if variable in self.__per_timestep_variables:
            return get_sampling_interval(1)
        return get_sampling_interval(self.__sampling_rates[variable])

    def _convert_placement_matrix_data(
            self, row_data, n_rows, data_row_length, n_neurons, data_type):

        surplus_bytes = self._N_BYTES_FOR_TIMESTAMP
        var_data = (row_data[:, surplus_bytes:].reshape(
            n_rows * data_row_length))
        placement_data = data_type.decode_array(var_data).reshape(
            n_rows, n_neurons)
        return placement_data

    @staticmethod
    def _process_missing_data(
            missing_str, placement, expected_rows, n_neurons, times,
            sampling_rate, label, placement_data, region):
        missing_str += "({}, {}, {}); ".format(
            placement.x, placement.y, placement.p)
        # Start the fragment for this slice empty
        fragment = numpy.empty((expected_rows, n_neurons))
        for i in range(0, expected_rows):
            time = i * sampling_rate
            # Check if there is data for this time step
            local_indexes = numpy.where(times == time)
            if len(local_indexes[0]) == 1:
                fragment[i] = placement_data[local_indexes[0]]
            elif len(local_indexes[0]) > 1:
                fragment[i] = placement_data[local_indexes[0][0]]
                logger.warning(
                    "Population {} has multiple recorded data for time {}"
                    " in region {} ", label, time, region)
            else:
                # Set row to nan
                fragment[i] = numpy.full(n_neurons, numpy.nan)
        return fragment

    def _get_placement_matrix_data(
            self, placements, vertex, region, buffer_manager, expected_rows,
            missing_str, sampling_rate, label, data_type, n_per_timestep):
        """ processes a placement for matrix data

        :param ~pacman.model.placements.Placements placements:
            the placements object
        :param ~pacman.model.graphs.machine.MachineVertex vertex:
            the vertex to read from
        :param int region: the recording region id
        :param ~.BufferManager buffer_manager: the buffer manager
        :param int expected_rows:
            how many rows the tools think should be recorded
        :param str missing_str: string for reporting missing stuff
        :param int sampling_rate: the rate of sampling
        :param str label: the vertex label.
        :return: placement data
        :rtype: ~numpy.ndarray
        """

        placement = placements.get_placement_of_vertex(vertex)
        if n_per_timestep == 0:
            return None

        # for buffering output info is taken form the buffer manager
        record_raw, missing_data = buffer_manager.get_data_by_placement(
            placement, region)
        record_length = len(record_raw)

        # If there is no data, return empty for all timesteps
        if record_length == 0:
            return numpy.zeros((expected_rows, n_per_timestep),
                               dtype="float64")

        # There is one column for time and one for each neuron recording
        data_row_length = n_per_timestep * data_type.size
        full_row_length = data_row_length + self._N_BYTES_FOR_TIMESTAMP
        n_rows = record_length // full_row_length
        row_data = numpy.asarray(record_raw, dtype="uint8").reshape(
            n_rows, full_row_length)
        placement_data = self._convert_placement_matrix_data(
            row_data, n_rows, data_row_length, n_per_timestep, data_type)

        # If everything is there, return it
        if not missing_data and n_rows == expected_rows:
            return placement_data

        # Got data but its missing bits, so get times
        time_bytes = (
            row_data[:, 0: self._N_BYTES_FOR_TIMESTAMP].reshape(
                n_rows * self._N_BYTES_FOR_TIMESTAMP))
        times = time_bytes.view("<i4").reshape(n_rows, 1)

        # process data from core for missing data
        placement_data = self._process_missing_data(
            missing_str, placement, expected_rows, n_per_timestep, times,
            sampling_rate, label, placement_data, region)
        return placement_data

    def __read_data(
            self, label, buffer_manager, placements, application_vertex,
            sampling_rate, data_type, variable, n_machine_time_steps):
        vertices = (
            application_vertex.splitter.machine_vertices_for_recording(
                variable))
        region = self.__region_ids[variable]
        missing_str = ""
        pop_level_data = None
        sampling_interval = get_sampling_interval(sampling_rate)

        progress = ProgressBar(
            vertices, "Getting {} for {}".format(variable, label))

        indexes = []
        for i, vertex in enumerate(progress.over(vertices)):
            expected_rows = int(
                math.ceil(n_machine_time_steps / sampling_rate))

            n_items_per_timestep = 1
            if variable in self.__sampling_rates:
                neurons = self._neurons_recording(
                    variable, vertex.vertex_slice)
                n_items_per_timestep = len(neurons)
                indexes.extend(neurons)
            else:
                indexes.append(i)
            placement_data = self._get_placement_matrix_data(
                placements, vertex, region, buffer_manager, expected_rows,
                missing_str, sampling_rate, label, data_type,
                n_items_per_timestep)

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

    def get_matrix_data(
            self, label, buffer_manager, placements,
            application_vertex, variable, n_machine_time_steps):
        """ Read a data mapped to time and neuron IDs from the SpiNNaker\
            machine and converts to required data types with scaling if needed.

        :param str label: vertex label
        :param buffer_manager: the manager for buffered data
        :type buffer_manager:
            ~spinn_front_end_common.interface.buffer_management.BufferManager
        :param ~pacman.model.placements.Placements placements:
            the placements object
        :param application_vertex:
        :type application_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :param str variable: PyNN name for the variable (`V`, `gsy_inh`, etc.)
        :param int n_machine_time_steps:
        :return: (data, recording_indices, sampling_interval)
        :rtype: tuple(~numpy.ndarray, list(int), float)
        """
        if variable in self.__bitfield_variables:
            msg = ("Variable {} is not supported by get_matrix_data, use "
                   "get_spikes(...)").format(variable)
            raise ConfigurationException(msg)
        if variable in self.__events_per_core_variables:
            msg = ("Variable {} is not supported by get_matrix_data, use "
                   "get_events(...)").format(variable)
            raise ConfigurationException(msg)
        if variable in self.__per_timestep_variables:
            sampling_rate = 1
            data_type = self.__per_timestep_datatypes[variable]
        else:
            sampling_rate = self.__sampling_rates[variable]
            data_type = self.__data_types[variable]
        return self.__read_data(
            label, buffer_manager, placements, application_vertex,
            sampling_rate, data_type, variable, n_machine_time_steps)

    def get_spikes(
            self, label, buffer_manager, placements, application_vertex,
            variable):
        """ Read spikes mapped to time and neuron IDs from the SpiNNaker\
            machine.

        :param str label: vertex label
        :param buffer_manager: the manager for buffered data
        :type buffer_manager:
            ~spinn_front_end_common.interface.buffer_management.BufferManager
        :param ~pacman.model.placements.Placements placements:
            the placements object
        :param application_vertex:
        :type application_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :param str variable:
        :return:
        :rtype: ~numpy.ndarray(tuple(int,int))
        """
        if variable not in self.__bitfield_variables:
            msg = "Variable {} is not supported, use get_matrix_data".format(
                variable)
            raise ConfigurationException(msg)

        spike_times = list()
        spike_ids = list()

        vertices = (
            application_vertex.splitter.machine_vertices_for_recording(
                variable))
        missing_str = ""
        progress = ProgressBar(vertices, "Getting spikes for {}".format(label))
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = vertex.vertex_slice

            neurons = list(self._neurons_recording(variable, vertex_slice))
            neurons_recording = len(neurons)
            if neurons_recording == 0:
                continue

            # Read the spikes
            n_words = int(math.ceil(neurons_recording / BITS_PER_WORD))
            n_bytes = n_words * BYTES_PER_WORD
            n_words_with_timestamp = n_words + 1

            # for buffering output info is taken form the buffer manager
            region = self.__region_ids[variable]
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
                record_time = raw_data[:, 0] * machine_time_step_ms()
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

    def get_events(
            self, label, buffer_manager, placements,
            application_vertex, variable):
        """ Read events mapped to time and neuron IDs from the SpiNNaker\
            machine.

        :param str label: vertex label
        :param buffer_manager: the manager for buffered data
        :type buffer_manager:
            ~spinn_front_end_common.interface.buffer_management.BufferManager
        :param ~pacman.model.placements.Placements placements:
            the placements object
        :param application_vertex:
        :type application_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :param str variable:
        :return:
        :rtype: ~numpy.ndarray(tuple(int,int,int,int))
        """
        if variable == self.REWIRING:
            return self._get_rewires(
                label, buffer_manager, placements, application_vertex,
                variable)
        else:
            # Unspecified event variable
            msg = (
                "Variable {} is not supported. Supported event variables are: "
                "{}".format(variable, self.get_event_recordable_variables()))
            raise ConfigurationException(msg)

    def _get_rewires(
            self, label, buffer_manager, placements, application_vertex,
            variable):
        """ Read rewires mapped to time and neuron IDs from the SpiNNaker\
            machine.

        :param str label: vertex label
        :param buffer_manager: the manager for buffered data
        :type buffer_manager:
            ~spinn_front_end_common.interface.buffer_management.BufferManager
        :param ~pacman.model.placements.Placements placements:
            the placements object
        :param application_vertex:
        :type application_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :param str variable:
        :return:
        :rtype: ~numpy.ndarray(tuple(int,int,int,int))
        """
        rewire_times = list()
        rewire_values = list()
        rewire_postids = list()
        rewire_preids = list()

        vertices = (
            application_vertex.splitter.machine_vertices_for_recording(
                variable))
        missing_str = ""
        progress = ProgressBar(
            vertices, "Getting rewires for {}".format(label))
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = vertex.vertex_slice

            neurons = list(
                range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1))
            neurons_recording = len(neurons)
            if neurons_recording == 0:
                continue

            # for buffering output info is taken form the buffer manager
            region = self.__region_ids[variable]
            record_raw, data_missing = buffer_manager.get_data_by_placement(
                    placement, region)
            if data_missing:
                missing_str += "({}, {}, {}); ".format(
                    placement.x, placement.y, placement.p)
            if len(record_raw) > 0:
                raw_data = (
                    numpy.asarray(record_raw, dtype="uint8").view(
                        dtype="<i4")).reshape([-1, self.REWIRING_N_WORDS])
            else:
                raw_data = record_raw

            if len(raw_data) > 0:
                record_time = raw_data[:, 0] * machine_time_step_ms()
                rewires_raw = raw_data[:, 1:]
                rew_length = len(rewires_raw)
                # rewires is 0 (elimination) or 1 (formation) in the first bit
                rewires = [rewires_raw[i][0] & self._FIRST_BIT
                           for i in range(rew_length)]
                # the post-neuron ID is stored in the next 8 bytes
                post_ids = [((int(rewires_raw[i]) >> self._POST_ID_SHIFT) %
                            self._POST_ID_FACTOR) + vertex_slice.lo_atom
                            for i in range(rew_length)]
                # the pre-neuron ID is stored in the remaining 23 bytes
                pre_ids = [int(rewires_raw[i]) >> self._PRE_ID_SHIFT
                           for i in range(rew_length)]

                rewire_values.extend(rewires)
                rewire_postids.extend(post_ids)
                rewire_preids.extend(pre_ids)
                rewire_times.extend(record_time)

        if len(missing_str) > 0:
            logger.warning(
                "Population {} is missing rewiring data in region {} from the"
                " following cores: {}", label, region, missing_str)

        if len(rewire_values) == 0:
            return numpy.zeros((0, 4), dtype="float")

        result = numpy.column_stack(
            (rewire_times, rewire_preids, rewire_postids, rewire_values))
        return result[numpy.lexsort(
            (rewire_values, rewire_postids, rewire_preids, rewire_times))]

    def get_recordable_variables(self):
        """
        :rtype: iterable(str)
        """
        variables = list(self.__sampling_rates.keys())
        variables.extend(self.__events_per_core_variables)
        variables.extend(self.__per_timestep_variables)
        return variables

    def get_event_recordable_variables(self):
        """
        :rtype: iterable(str)
        """
        variables = list(self.__events_per_core_variables)
        return variables

    def is_recording(self, variable):
        """
        :param str variable:
        :rtype: bool
        """
        try:
            return self.__sampling_rates[variable] > 0
        except KeyError:
            if (variable in self.__events_per_core_recording or
                    variable in self.__per_timestep_recording):
                return True
        return False

    def is_recordable(self, variable):
        """ Identify if the given variable can be recorded

        :param str variable: The variable to check for
        :rtype: bool
        """
        return (variable in self.__sampling_rates or
                variable in self.__per_timestep_variables or
                variable in self.__events_per_core_variables)

    @property
    def recording_variables(self):
        """
        :rtype: list(str)
        """
        results = list()
        for variable, rate in self.__sampling_rates.items():
            if rate > 0:
                results.append(variable)
        for variable in self.__events_per_core_variables:
            if variable in self.__events_per_core_recording:
                results.append(variable)
        for variable in self.__per_timestep_variables:
            if variable in self.__per_timestep_recording:
                results.append(variable)
        return results

    @property
    def recorded_region_ids(self):
        """
        :rtype: list(int)
        """
        results = list()
        for variable, rate in self.__sampling_rates.items():
            if rate > 0:
                results.append(self.__region_ids[variable])
        # events per core regions come after normal regions
        for variable in self.__events_per_core_variables:
            if variable in self.__events_per_core_recording:
                results.append(self.__region_ids[variable])
        # Per timestep regions come next
        for variable in self.__per_timestep_variables:
            if variable in self.__per_timestep_recording:
                results.append(self.__region_ids[variable])
        return results

    def _is_recording(self, variable, vertex_slice):
        """
        :param str variable:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: bool
        """
        # event per core and per_timestep variables are not recorded by slice,
        # so True if present
        if variable in self.__events_per_core_recording:
            return True
        if variable in self.__per_timestep_recording:
            return True
        if self.__sampling_rates[variable] == 0:
            return False
        if self.__indexes[variable] is None:
            return True
        indexes = self.__indexes[variable]
        for index in range(vertex_slice.lo_atom, vertex_slice.hi_atom+1):
            if index in indexes:
                return True
        return False

    def recorded_ids_by_slice(self, vertex_slice):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: list(int)
        """
        variables = [
            self.__region_ids[variable]
            for variable in self.__sampling_rates
            if self._is_recording(variable, vertex_slice)]
        # event per core variables are always defined, but the region is
        # declared after the other variables
        variables.extend([
            self.__region_ids[variable]
            for variable in self.__events_per_core_variables
            if variable in self.__events_per_core_recording])
        # per-timestep variables are always defined, but the region is declared
        # after the other variables
        variables.extend([
            self.__region_ids[variable]
            for variable in self.__per_timestep_variables
            if variable in self.__per_timestep_recording])
        return variables

    def _compute_rate(self, sampling_interval):
        """ Convert a sampling interval into a rate. \
            Remember, machine time step is in nanoseconds

        :param int sampling_interval: interval between samples in microseconds
        :return: rate
        :rtype: int
        """
        if sampling_interval is None:
            return 1

        step = machine_time_step_ms()
        rate = int(sampling_interval / step)
        if sampling_interval != rate * step:
            msg = "sampling_interval {} is not an an integer multiple of the "\
                  "simulation timestep {}".format(sampling_interval, step)
            raise ConfigurationException(msg)
        if rate > self._MAX_RATE:
            msg = "sampling_interval {} higher than max allowed which is {}" \
                  "".format(sampling_interval, step * self._MAX_RATE)
            raise ConfigurationException(msg)
        return rate

    def check_indexes(self, indexes):
        """
        :param list(int) indexes:
        """
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

    def __check_per_timestep_params(
            self, variable, sampling_interval, indexes):
        """ Check if certain parameters have been provided for a per-timestep
            variable and if so, raise an Exception

        :param str variable:
        :param int sampling_interval:
        :param iterable(int) indexes:
        """
        if sampling_interval is not None:
            raise Exception(
                "Variable {} does not support a sampling interval".format(
                    variable))
        if indexes is not None:
            raise Exception(
                "Variable {} can only be recorded on the whole population"
                .format(variable))

    def __check_events_per_core_params(
            self, variable, sampling_interval, indexes):
        """ Check if certain parameters have been provided for an
            events-per-core variable and if so, raise an Exception

        :param str variable:
        :param int sampling_interval:
        :param iterable(int) indexes:
        """
        if sampling_interval is not None:
            raise Exception(
                "Variable {} does not support a sampling interval".format(
                    variable))
        if indexes is not None:
            raise Exception(
                "Variable {} can only be recorded on the whole population"
                .format(variable))

    def _turn_off_recording(self, variable, sampling_interval, remove_indexes):
        """
        :param str variable:
        :param int sampling_interval:
        :param iterable(int) remove_indexes:
        """
        # If a per-timestep variable, remove it and return
        if variable in self.__per_timestep_variables:
            if variable in self.__per_timestep_recording:
                self.__per_timestep_recording.remove(variable)
            return

        # If an events-per-core variable, remove it and return
        if variable in self.__events_per_core_variables:
            if variable in self.__events_per_core_recording:
                self.__events_per_core_recording.remove(variable)
            return

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
        """
        :param str variable:
        :param iterable(int) indexes:
        """
        if indexes is None:
            # overwriting all OK!
            return
        if self.__indexes[variable] is None:
            if set(range(self.__n_neurons)).issubset(set(indexes)):
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
        """
        :param str variable:
        :param int sampling_interval:
        :param iterable(int) indexes:
        """
        # If a per-timestep variable, update
        if variable in self.__per_timestep_variables:
            self.__check_per_timestep_params(
                variable, sampling_interval, indexes)
            self.__per_timestep_recording.add(variable)
            return

        # If an events-per-core variable, update
        if variable in self.__events_per_core_variables:
            self.__check_events_per_core_params(
                variable, sampling_interval, indexes)
            self.__events_per_core_recording.add(variable)
            return

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
        """
        :param str variable: PyNN variable name
        :param bool new_state:
        :param int sampling_interval:
        :param iterable(int) indexes:
        """
        if variable == "all":
            for key in self.__sampling_rates.keys():
                self.set_recording(key, new_state, sampling_interval, indexes)
            for var in self.__events_per_core_variables:
                # Skip the unsupported items for an events-per-core variable
                self.set_recording(var, new_state)
            for var in self.__per_timestep_variables:
                # Skip the unsupported items for a per-timestep variable
                self.set_recording(var, new_state)
        elif (variable in self.__sampling_rates or
                variable in self.__per_timestep_variables or
                variable in self.__events_per_core_variables):
            if new_state:
                self._turn_on_recording(variable, sampling_interval, indexes)
            else:
                self._turn_off_recording(variable, sampling_interval, indexes)
        else:
            raise ConfigurationException("Variable {} is not supported".format(
                variable))

    def get_region_sizes(self, vertex_slice, n_machine_time_steps):
        """ Get the sizes of the regions for the variables, whether they are
            recorded or not, with those that are not having a size of 0

        :param ~pacman.model.graphs.commmon.Slice vertex_slice:
        :param int n_machine_time_steps:
        :rtype: list(int)
        """
        values = list()
        for variable in itertools.chain(
                self.__sampling_rates, self.__events_per_core_variables,
                self.__per_timestep_variables):
            values.append(self.get_buffered_sdram(
                variable, vertex_slice, n_machine_time_steps))
        return values

    def write_neuron_recording_region(
            self, spec, neuron_recording_region, vertex_slice):
        """ recording data specification

        :param ~data_specification.DataSpecificationGenerator spec: dsg spec
        :param int neuron_recording_region: the recording region
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            the vertex slice
        :rtype: None
        """
        spec.switch_write_focus(neuron_recording_region)

        # Write the number of variables and bitfields (ignore per-timestep)
        n_vars = len(self.__sampling_rates) - len(self.__bitfield_variables)
        spec.write_value(data=n_vars)
        spec.write_value(data=len(self.__bitfield_variables))

        # Write the recording data
        recording_data = self._get_data(vertex_slice)
        spec.write_array(recording_data)

    def _get_buffered_sdram_per_record(self, variable, n_neurons):
        """ Return the SDRAM used per record

        :param str variable: PyNN variable name
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :return:
        :rtype: int
        """
        if variable in self.__per_timestep_variables:
            if variable not in self.__per_timestep_recording:
                return 0
            size = self.__per_timestep_datatypes[variable].size
            return self._N_BYTES_FOR_TIMESTAMP + size
        if variable in self.__events_per_core_variables:
            if variable not in self.__events_per_core_recording:
                return 0
            size = self.__events_per_core_datatypes[variable].size
            return self.__events_per_ts[self.MAX_REWIRES] * (
                self._N_BYTES_FOR_TIMESTAMP + size)
        if n_neurons == 0:
            return 0
        if variable in self.__bitfield_variables:
            # Overflow can be ignored as it is not save if in an extra word
            out_spike_words = int(math.ceil(n_neurons / BITS_PER_WORD))
            out_spike_bytes = out_spike_words * BYTES_PER_WORD
            return self._N_BYTES_FOR_TIMESTAMP + out_spike_bytes
        else:
            size = self.__data_types[variable].size
            return self._N_BYTES_FOR_TIMESTAMP + (n_neurons * size)

    def get_buffered_sdram_per_record(
            self, variable, vertex_slice):
        """ Return the SDRAM used per record

        :param str variable: PyNN variable name
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :return:
        :rtype: int
        """
        n_neurons = self._count_recording_per_slice(variable, vertex_slice)
        return self._get_buffered_sdram_per_record(variable, n_neurons)

    def get_max_buffered_sdram_per_record(self, variable, n_atoms):
        """ Return the SDRAM used per record

        :param str variable: PyNN variable name
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :return:
        :rtype: int
        """
        n_neurons = self._max_recording_per_slice(variable, n_atoms)
        return self._get_buffered_sdram_per_record(variable, n_neurons)

    def get_buffered_sdram_per_timestep(
            self, variable, vertex_slice):
        """ Return the SDRAM used per timestep.

        In the case where sampling is used it returns the average\
        for recording and none recording based on the recording rate

        :param str variable: PyNN variable name
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :return:
        :rtype: int
        """
        if variable in self.__per_timestep_variables:
            if variable not in self.__per_timestep_recording:
                return 0
            rate = 1
        elif variable in self.__events_per_core_variables:
            if variable not in self.__events_per_core_recording:
                return 0
            rate = 1
        else:
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

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :return: Highest possible overflow needed
        :rtype: int
        """
        # No need to consider per-timestep variables here as they won't
        # overflow
        overflow = 0
        for variable, rate in self.__sampling_rates.items():
            # If rate is 0 no recording so no overflow
            # If rate is 1 there is no overflow as average is exact
            if rate > 1:
                data_size = self.get_buffered_sdram_per_record(
                    variable, vertex_slice)
                overflow += data_size // rate * (rate - 1)
        return overflow

    def get_buffered_sdram(
            self, variable, vertex_slice, n_machine_time_steps):
        """ Returns the SDRAM used for this many time steps for a variable

        If required the total is rounded up so the space will always fit

        :param str variable: The PyNN variable name to get buffered sdram of
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param int n_machine_time_steps:
            how many machine time steps to run for
        :return: data size
        :rtype: int
        """
        # Per timestep variables can't be done at a specific rate
        if variable in self.__per_timestep_variables:
            item = self.get_buffered_sdram_per_record(variable, vertex_slice)
            return item * n_machine_time_steps

        # Events per core variables depend on the max rewires possible
        # (this is already taken into consideration in per_record calculation)
        if variable in self.__events_per_core_variables:
            item = self.get_buffered_sdram_per_record(variable, vertex_slice)
            return item * n_machine_time_steps

        rate = self.__sampling_rates[variable]
        if rate == 0:
            return 0
        data_size = self.get_buffered_sdram_per_record(variable, vertex_slice)
        records = n_machine_time_steps // rate
        if n_machine_time_steps % rate > 0:
            records = records + 1
        return data_size * records

    @staticmethod
    def __n_bytes_to_n_words(n_bytes):
        """
        :param int n_bytes:
        :rtype: int
        """
        return (n_bytes + (BYTES_PER_WORD - 1)) // BYTES_PER_WORD

    def get_metadata_sdram_usage_in_bytes(self, n_atoms):
        """ Get the SDRAM usage of the metadata for recording

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: int
        """
        # This calculates the size of the metadata only; thus no reference to
        # per-timestep variables which have no metadata
        n_words_for_n_neurons = self.__n_bytes_to_n_words(n_atoms)
        n_bytes_for_n_neurons = n_words_for_n_neurons * BYTES_PER_WORD
        var_bytes = (
            (self._N_BYTES_PER_RATE + self._N_BYTES_PER_SIZE +
             self._N_BYTES_PER_ENUM + n_bytes_for_n_neurons) *
            (len(self.__sampling_rates) - len(self.__bitfield_variables)))
        bitfield_bytes = (
            (self._N_BYTES_PER_RATE + self._N_BYTES_PER_SIZE +
             n_bytes_for_n_neurons) *
            len(self.__bitfield_variables))
        return ((self._N_ITEM_TYPES * DataType.UINT32.size) + var_bytes +
                bitfield_bytes)

    def _get_fixed_sdram_usage(self, n_atoms):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: int
        """
        fixed_sdram = 0
        # Recording rate for each neuron
        fixed_sdram += self._N_BYTES_PER_RATE
        # Number of recording neurons
        fixed_sdram += self._N_BYTES_PER_INDEX
        # index_parameters one per neuron
        # even if not recording as also act as a gate
        fixed_sdram += self._N_BYTES_PER_INDEX * n_atoms
        return fixed_sdram

    def get_variable_sdram_usage(self, vertex_slice):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: ~pacman.model.resources.VariableSDRAM
        """
        fixed_sdram = 0
        per_timestep_sdram = 0
        for variable in self.__sampling_rates:
            rate = self.__sampling_rates[variable]
            fixed_sdram += self._get_fixed_sdram_usage(vertex_slice.n_atoms)
            if rate > 0:
                fixed_sdram += self._SARK_BLOCK_SIZE
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
        for variable in self.__per_timestep_recording:
            per_timestep_sdram += self.get_buffered_sdram_per_record(
                variable, vertex_slice)
        for variable in self.__events_per_core_recording:
            per_timestep_sdram += self.get_buffered_sdram_per_record(
                variable, vertex_slice)
        return VariableSDRAM(fixed_sdram, per_timestep_sdram)

    def get_max_variable_sdram_usage(self, n_atoms):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: ~pacman.model.resources.VariableSDRAM
        """
        fixed_sdram = 0
        per_timestep_sdram = 0
        for variable in self.__sampling_rates:
            rate = self.__sampling_rates[variable]
            fixed_sdram += self._get_fixed_sdram_usage(n_atoms)
            if rate > 0:
                fixed_sdram += self._SARK_BLOCK_SIZE
                per_record = self.get_max_buffered_sdram_per_record(
                    variable, n_atoms)
                if rate == 1:
                    # Add size for one record as recording every timestep
                    per_timestep_sdram += per_record
                else:
                    # Get the average cost per timestep
                    average_per_timestep = per_record / rate
                    per_timestep_sdram += average_per_timestep
                    # Add the rest once to fixed for worst case
                    fixed_sdram += (per_record - average_per_timestep)
        for variable in self.__per_timestep_recording:
            per_timestep_sdram += self.get_max_buffered_sdram_per_record(
                variable, n_atoms)
        for variable in self.__events_per_core_recording:
            per_timestep_sdram += self.get_max_buffered_sdram_per_record(
                variable, n_atoms)
        return VariableSDRAM(fixed_sdram, per_timestep_sdram)

    def get_dtcm_usage_in_bytes(self, n_atoms):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: int
        """
        # Note: Per-timestep variables uses no DTCM
        # *_rate + n_neurons_recording_* + *_indexes
        usage = self.get_metadata_sdram_usage_in_bytes(n_atoms)

        # *_count + *_increment
        usage += (len(self.__sampling_rates) * (
            self._N_BYTES_PER_POINTER + self._N_BYTES_PER_COUNT +
            self._N_BYTES_PER_INCREMENT))

        # out_spikes, *_values
        for variable in self.__sampling_rates:
            if variable in self.__bitfield_variables:
                out_spike_words = int(math.ceil(n_atoms / BITS_PER_WORD))
                out_spike_bytes = out_spike_words * BYTES_PER_WORD
                usage += self._N_BYTES_FOR_TIMESTAMP + out_spike_bytes
            else:
                size = self.__data_types[variable].size
                usage += self._N_BYTES_FOR_TIMESTAMP + (n_atoms * size)

        # *_size
        usage += len(self.__sampling_rates) * self._N_BYTES_PER_SIZE

        # n_recordings_outstanding
        usage += self._N_BYTES_PER_OUTSTANDING_RECORDING
        return usage

    def get_n_cpu_cycles(self, n_neurons):
        """
        :param int n_neurons:
        :rtype: int
        """
        return n_neurons * self._N_CPU_CYCLES_PER_NEURON * \
            len(self.recording_variables)

    def __add_indices(self, data, variable, rate, n_recording, vertex_slice):
        """
        :param list(~numpy.ndarray) data:
        :param str variable:
        :param int rate:
        :param int n_recording:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        """
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
            for index in range(n_bytes_for_n_neurons):
                if index + vertex_slice.lo_atom in indexes:
                    local_indexes.append(local_index)
                    local_index += 1
                else:
                    # write to one beyond recording range
                    local_indexes.append(n_recording)
            data.append(
                numpy.array(local_indexes, dtype="uint8").view("uint32"))

    def _get_data(self, vertex_slice):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: ~numpy.ndarray
        """
        # There is no data here for per-timestep variables by design
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

    def set_max_rewires_per_ts(self, max_rewires_per_ts):
        """
        :param int max_rewires_per_ts: the maximum rewires per timestep
        """
        self.__events_per_ts[self.MAX_REWIRES] = max_rewires_per_ts

    @property
    def _indexes(self):  # for testing only
        return _ReadOnlyDict(self.__indexes)
