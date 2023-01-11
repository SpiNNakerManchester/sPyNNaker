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
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase
from .population_application_vertex import RecordingType

logger = FormatAdapter(logging.getLogger(__name__))

# The number to add to generate that all neurons are in the given state
_REPEAT_PER_NEURON_RECORDED = 0x7FFFFFFF

# The number to add to generate that all neurons are recorded
_REPEAT_PER_NEURON = 0xFFFFFFFF

# The flag to add to generate that the count is recorded
_RECORDED_FLAG = 0x80000000

# The flag (or lack thereof) to add to generate that the count is not recorded
_NOT_RECORDED_FLAG = 0x00000000


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
    return sampling_rate * SpynnakerDataView.get_simulation_time_step_ms()


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
        "__region_ids",
        "__offset_added"]

    _N_BYTES_FOR_TIMESTAMP = BYTES_PER_WORD
    _N_BYTES_PER_RATE = BYTES_PER_WORD
    _N_BYTES_PER_ENUM = BYTES_PER_WORD
    _N_BYTES_PER_GEN_ITEM = BYTES_PER_WORD

    #: size of a index in terms of position into recording array
    _N_BYTES_PER_INDEX = DataType.UINT16.size  # currently uint16

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
        self.__sampling_rates = dict()
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

        self.__offset_added = False

    def add_region_offset(self, offset):
        """ Add an offset to the regions.  Used when there are multiple\
            recorders on a single core

        :param int offset: The offset to add
        """
        if not self.__offset_added:
            self.__region_ids = dict(
                (var, region + offset)
                for var, region in self.__region_ids.items())

        self.__offset_added = True

    def get_region(self, variable):
        """ Get the region of a variable

        :param str variable: The variable to get the region of
        :rtype: int
        """
        return self.__region_ids[variable]

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

    def _neurons_recording(self, variable, vertex_slice, atoms_shape):
        """
        :param str variable:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param tuple(int) atoms_shape:
        :rtype: iterable(int)
        """
        if self.__sampling_rates[variable] == 0:
            return []
        if self.__indexes[variable] is None:
            return vertex_slice.get_raster_ids(atoms_shape)
        indexes = self.__indexes[variable]
        return [
            i for i in vertex_slice.get_raster_ids(atoms_shape)
            if i in indexes]

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
            self, vertex, region, expected_rows,
            missing_str, sampling_rate, label, data_type, n_per_timestep):
        """ processes a placement for matrix data

        :param ~pacman.model.placements.Placements placements:
            the placements object
        :param ~pacman.model.graphs.machine.MachineVertex vertex:
            the vertex to read from
        :param int region: the recording region id
        :param int expected_rows:
            how many rows the tools think should be recorded
        :param str missing_str: string for reporting missing stuff
        :param int sampling_rate: the rate of sampling
        :param str label: the vertex label.
        :return: placement data
        :rtype: ~numpy.ndarray
        """
        placement = SpynnakerDataView.get_placement_of_vertex(vertex)
        if n_per_timestep == 0:
            return None

        # for buffering output info is taken form the buffer manager
        buffer_manager = SpynnakerDataView.get_buffer_manager()
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

    def get_recorded_indices(self, application_vertex, variable):
        """ Get the indices being recorded for a given variable

        :param ApplicationVertex application_vertex: The vertex being recorded
        :param str variable: The name of the variable to get the indices of
        :rtype: list(int)
        """
        if variable not in self.__sampling_rates:
            return []
        if self.__indexes[variable] is None:
            return range(application_vertex.n_atoms)
        return self.__indexes[variable]

    def get_sampling_interval(self, variable):
        """ Get the sampling interval of a variable

        :param str variable: The variable to get the sampling interval of
        :rtype: float
        """
        if (variable in self.__per_timestep_variables or
                variable in self.__events_per_core_variables):
            return get_sampling_interval(1)

        return get_sampling_interval(self.__sampling_rates[variable])

    def __read_data(
            self, label, application_vertex,
            sampling_rate, data_type, variable):
        n_machine_time_steps = SpynnakerDataView.get_current_run_timesteps()
        vertices = (
            application_vertex.splitter.machine_vertices_for_recording(
                variable))
        region = self.__region_ids[variable]
        missing_str = ""
        pop_level_data = None

        progress = ProgressBar(
            vertices, "Getting {} for {}".format(variable, label))

        indexes = []
        for i, vertex in enumerate(progress.over(vertices)):
            expected_rows = int(
                math.ceil(n_machine_time_steps / sampling_rate))

            n_items_per_timestep = 1
            if variable in self.__sampling_rates:
                neurons = self._neurons_recording(
                    variable, vertex.vertex_slice,
                    application_vertex.atoms_shape)
                n_items_per_timestep = len(neurons)
                indexes.extend(neurons)
            else:
                indexes.append(i)
            placement_data = self._get_placement_matrix_data(
                vertex, region, expected_rows,
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

        indexes = numpy.array(indexes)
        order = numpy.argsort(indexes)
        return pop_level_data[:, order]

    def get_recorded_data_type(self, variable):
        if variable in self.__bitfield_variables:
            return RecordingType.BIT_FIELD
        if variable in self.__events_per_core_variables:
            return RecordingType.EVENT
        if (variable in self.__sampling_rates or
                variable in self.__per_timestep_variables):
            return RecordingType.MATRIX
        raise KeyError(f"This vertex cannot record {variable}")

    def __write_matrix_metadata(
            self, application_vertex,
            sampling_interval_ms, data_type, variable, population):
        """
        Write the metadata to retrieve matrix data based on just the database

        :param ApplicationVertex application_vertex:
        :param float sampling_interval:
            The simulation time in ms between sampling.
            Typically the sampling rate * simulation_timestep_ms
        :param DataType data_type: type of data being recorded
        :param str variable: name of the variable.
        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        """
        vertices = (
            application_vertex.splitter.machine_vertices_for_recording(
                variable))
        region = self.__region_ids[variable]

        for i, vertex in enumerate(vertices):
            if variable in self.__sampling_rates:
                neurons = self._neurons_recording(
                    variable, vertex.vertex_slice,
                    application_vertex.atoms_shape)
            else:
                neurons = [i]
            with NeoBufferDatabase() as db:
                db.write_matrix_metadata(
                    vertex, variable, region, population,
                    sampling_interval_ms, neurons, data_type)

    def _write_matrix_metadata(self, application_vertex, variable, population):
        if variable in self.__per_timestep_variables:
            sampling_rate = 1
            data_type = self.__per_timestep_datatypes[variable]
        else:
            sampling_rate = self.__sampling_rates[variable]
            data_type = self.__data_types[variable]
        sampling_interval_ms = sampling_rate * \
            SpynnakerDataView.get_simulation_time_step_ms()
        self.__write_matrix_metadata(
            application_vertex, sampling_interval_ms, data_type, variable,
            population)

    def _write_spike_metadata(self, application_vertex, population):
        """
        Write the metadata to retreive spikes based on just the database

        :param ApplicationVertex application_vertex:
            vertex which will supply the data
        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        """
        sampling_interval_ms = self.__sampling_rates[self.SPIKES] * \
            SpynnakerDataView.get_simulation_time_step_ms()
        vertices = (
            application_vertex.splitter.machine_vertices_for_recording(
                self.SPIKES))
        region = self.__region_ids[self.SPIKES]

        with NeoBufferDatabase() as db:
            for vertex in vertices:
                neurons = self._neurons_recording(
                    self.SPIKES, vertex.vertex_slice,
                    application_vertex.atoms_shape)
                db.write_spikes_metadata(
                    vertex, self.SPIKES, region, population,
                    sampling_interval_ms, neurons)

    def __write_rewires_metadata(self, application_vertex, population):
        """
        Write the metadata to retrieve rewires data based on just the database

        :param ApplicationVeretx application_vertex:
        :param str variable: name of the variable.
        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        """
        vertices = (
            application_vertex.splitter.machine_vertices_for_recording(
                self.REWIRING))
        region = self.__region_ids[self.REWIRING]

        for i, vertex in enumerate(vertices):
            with NeoBufferDatabase() as db:
                db.write_rewires_metadata(
                    vertex, self.REWIRING, region, population)

    def write_recording_metadata(self, application_vertex, population):
        """
        Write the metdatabase to the database so it can be used standalone

        :param application_vertex:
        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        :return:
        """
        for variable in self.recording_variables:
            if variable == self.SPIKES:
                self._write_spike_metadata(application_vertex, population)
            elif variable == self.REWIRING:
                self.__write_rewires_metadata(application_vertex, population)
            elif variable in self.__events_per_core_variables:
                raise NotImplementedError(
                    f"Unexpected Event variable: {variable}")
            else:
                self._write_matrix_metadata(
                    application_vertex, variable, population)

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

        step = SpynnakerDataView.get_simulation_time_step_ms()
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

    def get_region_sizes(self, vertex_slice):
        """ Get the sizes of the regions for the variables, whether they are
            recorded or not, with those that are not having a size of 0

        :param ~pacman.model.graphs.commmon.Slice vertex_slice:
        :rtype: list(int)
        """
        values = list()
        for variable in itertools.chain(
                self.__sampling_rates, self.__events_per_core_variables,
                self.__per_timestep_variables):
            values.append(self.get_buffered_sdram(
                variable, vertex_slice))
        return values

    def write_neuron_recording_region(
            self, spec, neuron_recording_region, vertex_slice, atoms_shape):
        """ recording data specification

        :param ~data_specification.DataSpecificationGenerator spec: dsg spec
        :param int neuron_recording_region: the recording region
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            the vertex slice
        :param tuple(int) atoms_shape:
            the shape of the atoms in the application vertex
        :rtype: None
        """
        spec.switch_write_focus(neuron_recording_region)

        # Write the number of variables and bitfields (ignore per-timestep)
        n_vars = len(self.__sampling_rates) - len(self.__bitfield_variables)
        spec.write_value(data=n_vars)
        spec.write_value(data=len(self.__bitfield_variables))

        # Write the recording data
        recording_data = self._get_data(vertex_slice, atoms_shape)
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
            self, variable, vertex_slice):
        """ Returns the SDRAM used for this many time steps for a variable

        If required the total is rounded up so the space will always fit

        :param str variable: The PyNN variable name to get buffered sdram of
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :return: data size
        :rtype: int
        """
        n_machine_time_steps = SpynnakerDataView.get_max_run_time_steps()
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

    def get_metadata_sdram_usage_in_bytes(self, n_atoms):
        """ Get the SDRAM usage of the metadata for recording

        :param int n_atoms: The number of atoms to record
        :rtype: int
        """
        # This calculates the size of the metadata only; thus no reference to
        # per-timestep variables which have no metadata
        n_indices = self.__ceil_n_indices(n_atoms)
        n_bytes_for_indices = n_indices * self._N_BYTES_PER_INDEX
        var_bytes = (
            (self._N_BYTES_PER_RATE + self._N_BYTES_PER_SIZE +
             self._N_BYTES_PER_ENUM + n_bytes_for_indices) *
            (len(self.__sampling_rates) - len(self.__bitfield_variables)))
        bitfield_bytes = (
            (self._N_BYTES_PER_RATE + self._N_BYTES_PER_SIZE +
             n_bytes_for_indices) *
            len(self.__bitfield_variables))
        return ((self._N_ITEM_TYPES * DataType.UINT32.size) + var_bytes +
                bitfield_bytes)

    def get_generator_sdram_usage_in_bytes(self, n_atoms):
        """ Get the SDRAM usage of the generator data for recording metadata

        :param int n_atoms: The number of atoms to be recorded
        :rtype: int
        """
        n_indices = self.__ceil_n_indices(n_atoms)
        n_bytes_for_indices = n_indices * self._N_BYTES_PER_INDEX
        var_bytes = (
            (self._N_BYTES_PER_RATE + self._N_BYTES_PER_SIZE +
             self._N_BYTES_PER_ENUM + self._N_BYTES_PER_GEN_ITEM +
             n_bytes_for_indices) *
            (len(self.__sampling_rates) - len(self.__bitfield_variables)))
        bitfield_bytes = (
            (self._N_BYTES_PER_RATE + self._N_BYTES_PER_SIZE +
             self._N_BYTES_PER_GEN_ITEM + n_bytes_for_indices) *
            len(self.__bitfield_variables))
        return ((self._N_ITEM_TYPES * DataType.UINT32.size) + var_bytes +
                bitfield_bytes)

    def get_variable_sdram_usage(self, vertex_slice):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: ~pacman.model.resources.VariableSDRAM
        """
        fixed_sdram = 0
        per_timestep_sdram = 0
        for variable in self.__sampling_rates:
            rate = self.__sampling_rates[variable]
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
            # fixed_sdram += self._get_fixed_sdram_usage(n_atoms)
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

    def __ceil_n_indices(self, n_neurons):
        """ The number of indices rounded up to a whole number of words

        :param int n_neurons: The number of neurons to account for
        :rtype: int
        """
        # Assumes that BYTES_PER_WORD is divisible by _N_BYTES_PER_INDEX
        n_bytes = n_neurons * self._N_BYTES_PER_INDEX
        ceil_bytes = int(math.ceil(n_bytes / BYTES_PER_WORD)) * BYTES_PER_WORD
        return ceil_bytes // self._N_BYTES_PER_INDEX

    def __add_indices(self, data, variable, rate, n_recording, vertex_slice):
        """
        :param list(~numpy.ndarray) data:
        :param str variable:
        :param int rate:
        :param int n_recording:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        """
        n_indices = self.__ceil_n_indices(vertex_slice.n_atoms)
        if rate == 0:
            data.append(numpy.zeros(n_indices, dtype="uint16").view("uint32"))
        elif self.__indexes[variable] is None:
            data.append(numpy.arange(n_indices, dtype="uint16").view("uint32"))
        else:
            indexes = self.__indexes[variable]
            local_index = 0
            local_indexes = list()
            for index in range(n_indices):
                if index + vertex_slice.lo_atom in indexes:
                    local_indexes.append(local_index)
                    local_index += 1
                else:
                    # write to one beyond recording range
                    local_indexes.append(n_recording)
            data.append(
                numpy.array(local_indexes, dtype="uint16").view("uint32"))

    def _get_data(self, vertex_slice, atoms_shape):
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

    @property
    def is_global_generatable(self):
        """ Is the data for all neurons the same i.e. all or none of the
            neurons are recorded for all variables

        :rtype: bool
        """
        for variable in self.__sampling_rates:
            if variable in self.__indexes:
                return False
        return True

    def get_generator_data(self, vertex_slice=None, atoms_shape=None):
        """ Get the recorded data as a generatable data set

        :param vertex_slice:
            The slice to generate the data for, or None to generate for
            all neurons (assuming all the same, otherwise error)
        :type vertex_slice: Slice or None
        :param atoms_shape:
            The shape of the atoms in the vertex; if vertex_slice is not None,
            atoms_shape must be not None
        :rtype: numpy.ndarray
        """
        n_vars = len(self.__sampling_rates) - len(self.__bitfield_variables)
        data = [n_vars, len(self.__bitfield_variables)]
        for variable in self.__sampling_rates:
            if variable in self.__bitfield_variables:
                continue
            rate = self.__sampling_rates[variable]
            data.extend([rate, self.__data_types[variable].size])
            if rate == 0:
                data.extend([0, 0])
            else:
                data.extend(self.__get_generator_indices(
                    variable, vertex_slice, atoms_shape))
        for variable in self.__bitfield_variables:
            rate = self.__sampling_rates[variable]
            data.append(rate)
            if rate == 0:
                data.extend([0, 0])
            else:
                data.extend(self.__get_generator_indices(
                    variable, vertex_slice, atoms_shape))
        return numpy.array(data, dtype="uint32")

    def __get_generator_indices(
            self, variable, vertex_slice=None, atoms_shape=None):
        """ Get the indices of the variables to record in run-length-encoded
            form
        """
        index = self.__indexes.get(variable)

        # If there is no index, add that all variables are recorded
        if index is None:
            return [_REPEAT_PER_NEURON, 1,
                    _REPEAT_PER_NEURON_RECORDED | _RECORDED_FLAG]

        # This must be non-global data, so we need a slice
        if vertex_slice is None or atoms_shape is None:
            raise ValueError(
                "The parameters vertex_slice and atoms_shape must both not be"
                " None")

        # Generate a run-length-encoded list
        # Initially there are no items, but this will be updated
        # Also keep track of the number recorded, also 0 initially
        data = [0, 0]
        n_items = 0

        # Go through the indices and ids, assuming both are in order (they are)
        id_iter = iter(enumerate(vertex_slice.get_raster_ids(atoms_shape)))
        index_iter = iter(index)
        # Keep the id and the position in the id list (as this is a RLE)
        next_id, i = next(id_iter, (None, 0))
        next_index = next(index_iter, None)
        last_recorded = i
        n_recorded = 0
        while next_id is not None and next_index is not None:

            # Find the next index to be recorded
            while (next_id is not None and next_index is not None and
                   next_id != next_index):
                if next_index < next_id:
                    next_index = next(index_iter, None)
                elif next_id < next_index:
                    next_id, i = next(id_iter, (None, i + 1))

            # If we have moved the index onward, mark not recorded
            if i != last_recorded:
                data.append((i - last_recorded) | _NOT_RECORDED_FLAG)
                n_items += 1

            if next_id is not None and next_index is not None:
                start_i = i

                # Find the next index not recorded
                while (next_id is not None and next_index is not None and
                       next_id == next_index):
                    next_index = next(index_iter, None)
                    next_id, i = next(id_iter, (None, i + 1))

                # Add the count of things to be recorded
                data.append((i - start_i) | _RECORDED_FLAG)
                n_recorded += (i - start_i)
                last_recorded = i
                n_items += 1

        # If there are more items in the vertex slice, they must be
        # non-recorded items
        if next_id is not None:
            data.append((vertex_slice.n_atoms - i) | _NOT_RECORDED_FLAG)
            n_items += 1

        data[0] = n_recorded
        data[1] = n_items
        return numpy.array(data, dtype="uint32")
