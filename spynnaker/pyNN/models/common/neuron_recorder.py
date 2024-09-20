# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import itertools
import logging
import math
from types import MappingProxyType
from typing import (
    Collection, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple)

import numpy
from numpy import float64, uint8, uint16, uint32
from numpy.typing import NDArray

from spinn_utilities.log import FormatAdapter

from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.common import Slice
from pacman.model.resources import AbstractSDRAM, VariableSDRAM
from pacman.model.placements import Placement

from spinn_front_end_common.interface.ds import (
    DataType, DataSpecificationBase)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BITS_PER_WORD)

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.buffer_data_type import BufferDataType

logger = FormatAdapter(logging.getLogger(__name__))

# The number to add to generate that all neurons are in the given state
_REPEAT_PER_NEURON_RECORDED = 0x7FFFFFFF

# The number to add to generate that all neurons are recorded
_REPEAT_PER_NEURON = 0xFFFFFFFF

# The flag to add to generate that the count is recorded
_RECORDED_FLAG = 0x80000000

# The flag (or lack thereof) to add to generate that the count is not recorded
_NOT_RECORDED_FLAG = 0x00000000


def get_sampling_interval(sampling_rate):
    """
    Return the current sampling interval given a sampling rate.

    :param float sampling_rate: The sampling rate in time steps
    :return: Sampling interval in microseconds
    :rtype: float
    """
    return sampling_rate * SpynnakerDataView.get_simulation_time_step_ms()


class NeuronRecorder(object):
    """
    Methods related to recording of neuron data.
    """
    __slots__ = (
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
        "__offset_added")

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
            self, allowed_variables: List[str],
            data_types: Mapping[str, DataType],
            bitfield_variables: Sequence[str],
            n_neurons: int, per_timestep_variables: Sequence[str],
            per_timestep_datatypes: Mapping[str, DataType],
            events_per_core_variables: Sequence[str],
            events_per_core_datatypes: Mapping[str, DataType]):
        """
        :param list(str) allowed_variables:
        :param dict(str,~data_specification.enums.DataType) data_types:
        :param list(str) bitfield_variables:
        :param int n_neurons:
        :param list(str) per_timestep_variables:
        :param per_timestep_datatypes:
        :type per_timestep_datatypes:
            dict(str,~data_specification.enums.DataType)
        :param list(str) events_per_core_variables:
        :param events_per_core_datatypes:
        :type events_per_core_datatypes:
            dict(str,~data_specification.enums.DataType)
        """
        self.__sampling_rates: Dict[str, int] = dict()
        self.__indexes: Dict[str, Optional[Sequence[int]]] = dict()
        self.__data_types = data_types
        self.__n_neurons = n_neurons
        self.__bitfield_variables = bitfield_variables

        self.__per_timestep_variables = per_timestep_variables
        self.__per_timestep_datatypes = per_timestep_datatypes
        self.__per_timestep_recording: Set[str] = set()

        self.__events_per_core_variables = events_per_core_variables
        self.__events_per_core_datatypes = events_per_core_datatypes
        self.__events_per_core_recording: Set[str] = set()
        self.__events_per_ts: Dict[str, int] = dict()
        self.__events_per_ts[self.MAX_REWIRES] = 0  # record('all')

        # Get info on variables like these
        for variable in itertools.chain(allowed_variables, bitfield_variables):
            self.__sampling_rates[variable] = 0
            self.__indexes[variable] = None

        # Get region ids for all variables
        self.__region_ids = {
            variable: region_id
            for region_id, variable in enumerate(itertools.chain(
                allowed_variables, bitfield_variables,
                events_per_core_variables, per_timestep_variables))}

        self.__offset_added = False

    def add_region_offset(self, offset: int):
        """
        Add an offset to the regions.
        Used when there are multiple recorders on a single core.

        :param int offset: The offset to add
        """
        if not self.__offset_added:
            self.__region_ids = dict(
                (var, region + offset)
                for var, region in self.__region_ids.items())

        self.__offset_added = True

    def get_region(self, variable: str) -> int:
        """
        Get the region of a variable.

        :param str variable: The variable to get the region of
        :rtype: int
        """
        return self.__region_ids[variable]

    def _rate_and_count_per_slice(
            self, variable: str,
            vertex_slice: Optional[Slice]) -> Tuple[int, int]:
        if variable not in self.__sampling_rates:
            return 0, 0
        if self.__sampling_rates[variable] == 0:
            return 0, 0
        indices = self.__indexes.get(variable)
        if indices is None:
            n_atoms = self.__n_neurons if vertex_slice is None \
                else vertex_slice.n_atoms
            return self.__sampling_rates[variable], n_atoms
        assert vertex_slice is not None
        count = len(numpy.intersect1d(
            vertex_slice.get_raster_ids(), indices))
        if count:
            return self.__sampling_rates[variable], count
        return 0, 0

    def _max_recording_per_slice(
            self, variable: str, n_atoms: int) -> Optional[int]:
        """
        :param str variable:
        :param int n_atoms:
        """
        if variable not in self.__sampling_rates:
            return None
        if self.__sampling_rates[variable] == 0:
            return 0
        indices = self.__indexes.get(variable)
        if indices is None:
            return n_atoms
        max_index = numpy.amax(indices)
        existence = numpy.zeros(max_index + 1, dtype=numpy.int32)
        existence[indices] = 1
        splits = numpy.arange(n_atoms, max_index + 1, n_atoms)
        split_array = numpy.array_split(existence, splits)
        return max([int(numpy.sum(s)) for s in split_array])

    def neurons_recording(
            self, variable: str,
            vertex_slice: Slice) -> Optional[Collection[int]]:
        """
        :param str variable:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: None or iterable(int)
        """
        if variable not in self.__sampling_rates:
            return None
        if self.__sampling_rates[variable] == 0:
            return []
        indices = self.__indexes.get(variable)
        if indices is None:
            return vertex_slice.get_raster_ids()
        all_set = set(indices)
        ids = set(map(int, vertex_slice.get_raster_ids()))
        return sorted(all_set & ids)

    def _convert_placement_matrix_data(
            self, row_data: NDArray[uint8], n_rows: int, data_row_length: int,
            n_neurons: int, data_type: DataType) -> NDArray[float64]:
        surplus_bytes = self._N_BYTES_FOR_TIMESTAMP
        var_data = row_data[:, surplus_bytes:].reshape(
            n_rows * data_row_length)
        placement_data = data_type.decode_array(var_data).reshape(
            n_rows, n_neurons)
        return placement_data

    @staticmethod
    def _process_missing_data(
            missing_str: str, placement: Placement, expected_rows: int,
            n_neurons: int, times: NDArray[uint32], sampling_rate: int,
            label: str, placement_data: NDArray[float64], region: int
            ) -> NDArray[float64]:
        missing_str += f"({placement.x}, {placement.y}, {placement.p}); "
        # Start the fragment for this slice empty
        fragment = numpy.empty((expected_rows, n_neurons))
        for i in range(expected_rows):
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
                # Set row to Nan
                fragment[i] = numpy.full(n_neurons, numpy.nan)
        return fragment

    def _get_placement_matrix_data(
            self, vertex: MachineVertex, region: int, expected_rows: int,
            missing_str: str, sampling_rate: int, label: str,
            data_type: DataType, n_per_timestep: int) -> Optional[
                NDArray[float64]]:
        """
        Processes a placement for matrix data.

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
        record_raw, missing_data = buffer_manager.get_recording(
            placement, region)
        record_length = len(record_raw)

        # If there is no data, return empty for all timesteps
        if record_length == 0:
            return numpy.zeros((expected_rows, n_per_timestep), dtype=float64)

        # There is one column for time and one for each neuron recording
        data_row_length = n_per_timestep * data_type.size
        full_row_length = data_row_length + self._N_BYTES_FOR_TIMESTAMP
        n_rows = record_length // full_row_length
        row_data = numpy.asarray(record_raw, dtype=uint8).reshape(
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
        times: NDArray[uint32] = time_bytes.view("<i4").reshape(n_rows, 1)

        # process data from core for missing data
        placement_data = self._process_missing_data(
            missing_str, placement, expected_rows, n_per_timestep, times,
            sampling_rate, label, placement_data, region)
        return placement_data

    def get_recorded_indices(
            self, application_vertex: ApplicationVertex,
            variable: str) -> Iterable[int]:
        """
        Get the indices being recorded for a given variable.

        :param application_vertex: The vertex being recorded
        :type application_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :param str variable: The name of the variable to get the indices of
        :rtype: iterable(int)
        """
        if variable not in self.__sampling_rates:
            return []
        indices = self.__indexes.get(variable)
        if indices is None:
            return range(application_vertex.n_atoms)
        return indices

    def get_sampling_interval_ms(self, variable: str) -> float:
        """
        Get the sampling interval of a variable.

        :param str variable: The variable to get the sampling interval of
        :rtype: float
        """
        if (variable in self.__per_timestep_variables or
                variable in self.__events_per_core_variables):
            return get_sampling_interval(1)

        return get_sampling_interval(self.__sampling_rates[variable])

    def get_buffer_data_type(self, variable: str) -> BufferDataType:
        """
        :param str variable:
        :rtype: BufferDataType
        """
        if variable == self.SPIKES:
            return BufferDataType.NEURON_SPIKES
        elif variable == self.REWIRING:
            return BufferDataType.REWIRES
        elif variable in self.__events_per_core_variables:
            raise NotImplementedError(
                f"Unexpected Event variable: {variable}")
        else:
            return BufferDataType.MATRIX

    def get_data_type(self, variable: str) -> Optional[DataType]:
        """
        :param str variable:
        :rtype: ~data_specification.enums.DataType
        """
        if variable in self.__per_timestep_variables:
            return self.__per_timestep_datatypes[variable]
        if variable in self.__data_types:
            return self.__data_types[variable]
        return None

    def get_recordable_variables(self) -> List[str]:
        """
        :rtype: list(str)
        """
        return [
            *self.__sampling_rates.keys(),
            *self.__events_per_core_variables,
            *self.__per_timestep_variables]

    def get_event_recordable_variables(self) -> List[str]:
        """
        :rtype: list(str)
        """
        return list(self.__events_per_core_variables)

    def is_recording(self, variable: str) -> bool:
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

    def is_recordable(self, variable: str) -> bool:
        """
        Identify if the given variable can be recorded.

        :param str variable: The variable to check for
        :rtype: bool
        """
        return (variable in self.__sampling_rates or
                variable in self.__per_timestep_variables or
                variable in self.__events_per_core_variables)

    @property
    def recording_variables(self) -> Iterable[str]:
        """
        :rtype: iterable(str)
        """
        for variable, rate in self.__sampling_rates.items():
            if rate > 0:
                yield variable
        for variable in self.__events_per_core_variables:
            if variable in self.__events_per_core_recording:
                yield variable
        for variable in self.__per_timestep_variables:
            if variable in self.__per_timestep_recording:
                yield variable

    @property
    def recorded_region_ids(self) -> Iterable[int]:
        """
        :rtype: iterable(int)
        """
        for variable, rate in self.__sampling_rates.items():
            if rate > 0:
                yield self.__region_ids[variable]
        # events per core regions come after normal regions
        for variable in self.__events_per_core_variables:
            if variable in self.__events_per_core_recording:
                yield self.__region_ids[variable]
        # Per timestep regions come next
        for variable in self.__per_timestep_variables:
            if variable in self.__per_timestep_recording:
                yield self.__region_ids[variable]

    def _is_recording(self, variable: str, vertex_slice: Slice) -> bool:
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
        indices = self.__indexes.get(variable)
        if indices is None:
            return True
        return any(numpy.isin(vertex_slice.get_raster_ids(), indices))

    def recorded_ids_by_slice(self, vertex_slice: Slice) -> List[int]:
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: list(int)
        """
        # This needs to produce a new list every time; callers modify it
        variables = [
            self.__region_ids[variable]
            for variable in self.__sampling_rates
            if self._is_recording(variable, vertex_slice)]
        # event per core variables are always defined, but the region is
        # declared after the other variables
        variables.extend(
            self.__region_ids[variable]
            for variable in self.__events_per_core_variables
            if variable in self.__events_per_core_recording)
        # per-timestep variables are always defined, but the region is declared
        # after the other variables
        variables.extend(
            self.__region_ids[variable]
            for variable in self.__per_timestep_variables
            if variable in self.__per_timestep_recording)
        return variables

    def _compute_rate(self, sampling_interval: Optional[float]) -> int:
        """
        Convert a sampling interval into a rate.
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
            raise ConfigurationException(
                f"sampling_interval {sampling_interval} is not an an "
                f"integer multiple of the simulation timestep {step}")
        if rate > self._MAX_RATE:
            raise ConfigurationException(
                f"sampling_interval {sampling_interval} higher than "
                f"max allowed which is {step * self._MAX_RATE}")
        return rate

    def _check_indexes(self, indexes: Optional[Collection[int]]):
        """
        :param set(int) indexes:
        """
        if indexes is None:
            return

        if len(indexes) == 0:
            raise ConfigurationException("Empty indexes list")

        found = False
        warning = True
        for index in indexes:
            if index < 0:
                raise ConfigurationException(
                    "Negative indexes are not supported")
            elif index >= self.__n_neurons:
                if warning:
                    logger.warning(
                        "Ignoring indexes greater than population size")
                warning = False
            else:
                found = True
        if not found:
            raise ConfigurationException(
                "All indexes larger than population size")

    def __check_per_timestep_params(
            self, variable: str, sampling_interval: Optional[float],
            indexes: Optional[Collection[int]]):
        """
        Check if certain parameters have been provided for a per-timestep
        variable and if so, raise an Exception.

        :param str variable:
        :param int sampling_interval:
        :param iterable(int) indexes:
        """
        if sampling_interval is not None:
            raise ValueError(
                f"Variable {variable} does not support a sampling interval")
        if indexes is not None:
            raise ValueError(
                f"Variable {variable} can only be recorded "
                "on the whole population")

    def __check_events_per_core_params(
            self, variable: str, sampling_interval: Optional[float],
            indexes: Optional[Collection[int]]):
        """
        Check if certain parameters have been provided for an
        events-per-core variable and if so, raise an Exception.

        :param str variable:
        :param int sampling_interval:
        :param iterable(int) indexes:
        """
        if sampling_interval is not None:
            raise ValueError(
                f"Variable {variable} does not support a sampling interval")
        if indexes is not None:
            raise ValueError(
                f"Variable {variable} can only be recorded "
                "on the whole population")

    def _turn_off_recording(
            self, variable: str, sampling_interval: Optional[float],
            remove_indexes: Optional[Collection[int]]):
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

        indexes = self.__indexes.get(variable)
        if indexes is None:
            # start with all indexes
            indexes = range(self.__n_neurons)

        # remove the indexes not recording
        indexes = [
            index
            for index in indexes
            if index not in remove_indexes]

        # Check is at least one index still recording
        if len(indexes) == 0:
            self.__sampling_rates[variable] = 0
            self.__indexes[variable] = None
        else:
            self.__indexes[variable] = indexes

    def _check_complete_overwrite(
            self, variable: str, indexes: Optional[Collection[int]]):
        """
        :param str variable:
        :param iterable(int) indexes:
        """
        if indexes is None:
            # overwriting all OK!
            return
        current = self.__indexes.get(variable)
        if current is None:
            if set(range(self.__n_neurons)).issubset(set(indexes)):
                # overwriting all previous so OK!
                return
        else:
            if set(current).issubset(set(indexes)):
                # overwriting all previous so OK!
                return
        raise ConfigurationException(
            "Current implementation does not support multiple "
            f"sampling_intervals for {variable} on one population.")

    def _turn_on_recording(
            self, variable: str, sampling_interval: Optional[float],
            indexes: Optional[Collection[int]]):
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
            indices = set(indexes)
            self._check_indexes(indices)
            current = self.__indexes.get(variable)
            if current:
                # merge the two indexes
                indices.update(current)
            # Keep in numerical order
            self.__indexes[variable] = sorted(indices)

    def set_recording(self, variable: str, new_state: bool,
                      sampling_interval: Optional[float] = None,
                      indexes: Optional[Collection[int]] = None):
        """
        :param str variable: PyNN variable name
        :param bool new_state:
        :param int sampling_interval:
        :param iterable(int) indexes:
        """
        if variable == "all":
            for key in self.__sampling_rates:
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
            raise ConfigurationException(
                f"Variable {variable} is not supported")

    def get_region_sizes(self, vertex_slice: Slice) -> List[int]:
        """
        Get the sizes of the regions for the variables, whether they are
        recorded or not, with those that are not having a size of 0.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: list(int)
        """
        return [
            self.get_buffered_sdram(variable, vertex_slice)
            for variable in itertools.chain(
                self.__sampling_rates, self.__events_per_core_variables,
                self.__per_timestep_variables)]

    def write_neuron_recording_region(
            self, spec: DataSpecificationBase,
            neuron_recording_region: int, vertex_slice: Slice):
        """
        Recording data specification.

        :param ~data_specification.DataSpecificationGenerator spec:
            where to write the data specification
        :param int neuron_recording_region: the recording region
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            the vertex slice
        """
        spec.switch_write_focus(neuron_recording_region)

        # Write the number of variables and bitfields (ignore per-timestep)
        n_vars = len(self.__sampling_rates) - len(self.__bitfield_variables)
        spec.write_value(data=n_vars)
        spec.write_value(data=len(self.__bitfield_variables))

        # Write the recording data
        recording_data = self._get_data(vertex_slice)
        spec.write_array(recording_data)

    def _get_buffered_sdram_per_record(
            self, variable: str, n_neurons: int) -> int:
        """
        Return the SDRAM used per record.

        :param str variable: PyNN variable name
        :return: usage
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
            self, variable: str, vertex_slice: Slice) -> int:
        """
        Return the SDRAM used per record.

        :param str variable: PyNN variable name
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :return: usage
        :rtype: int
        """
        _, n_neurons = self._rate_and_count_per_slice(variable, vertex_slice)
        return self._get_buffered_sdram_per_record(variable, n_neurons)

    def get_max_buffered_sdram_per_record(
            self, variable: str, n_atoms: int) -> int:
        """
        Return the SDRAM used per record.

        :param str variable: PyNN variable name
        :return: usage
        :rtype: int
        """
        n_neurons = self._max_recording_per_slice(variable, n_atoms) or 0
        return self._get_buffered_sdram_per_record(variable, n_neurons)

    def get_buffered_sdram_per_timestep(
            self, variable: str, vertex_slice: Slice) -> int:
        """
        Return the SDRAM used per timestep.

        In the case where sampling is used it returns the average
        for recording and none recording based on the recording rate

        :param str variable: PyNN variable name
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :return: usage
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

    def get_sampling_overflow_sdram(self, vertex_slice: Slice) -> int:
        """
        Get the extra SDRAM that should be reserved if using per_timestep.

        This is the extra that must be reserved if per_timestep is an average
        rather than fixed for every timestep.

        When sampling the average * time_steps may not be quite enough.
        This returns the extra space in the worst case
        where time_steps is a multiple of sampling rate + 1,
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
            self, variable: str, vertex_slice: Slice) -> int:
        """
        Returns the SDRAM used for this many time steps for a variable.

        If required the total is rounded up so the space will always fit.

        :param str variable: The PyNN variable name to get buffered SDRAM of
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

    def get_metadata_sdram_usage_in_bytes(self, n_atoms: int) -> int:
        """
        Get the SDRAM usage of the metadata for recording.

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

    def get_generator_sdram_usage_in_bytes(self, n_atoms: int) -> int:
        """
        Get the SDRAM usage of the generator data for recording metadata.

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

    def get_variable_sdram_usage(self, vertex_slice: Slice) -> AbstractSDRAM:
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: ~pacman.model.resources.VariableSDRAM
        """
        fixed_sdram = 0.0
        per_timestep_sdram = 0.0
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
        return VariableSDRAM(
            math.ceil(fixed_sdram), math.ceil(per_timestep_sdram))

    def get_max_variable_sdram_usage(self, n_atoms: int) -> AbstractSDRAM:
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: ~pacman.model.resources.VariableSDRAM
        """
        fixed_sdram = 0.0
        per_timestep_sdram = 0.0
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
        return VariableSDRAM(
            math.ceil(fixed_sdram), math.ceil(per_timestep_sdram))

    def __ceil_n_indices(self, n_neurons: int) -> int:
        """
        The number of indices rounded up to a whole number of words.

        :param int n_neurons: The number of neurons to account for
        :rtype: int
        """
        # Assumes that BYTES_PER_WORD is divisible by _N_BYTES_PER_INDEX
        n_bytes = n_neurons * self._N_BYTES_PER_INDEX
        ceil_bytes = int(math.ceil(n_bytes / BYTES_PER_WORD)) * BYTES_PER_WORD
        return ceil_bytes // self._N_BYTES_PER_INDEX

    def __add_indices(
            self, data: List[NDArray[uint32]], variable: str, rate: int,
            n_recording: int, vertex_slice: Slice):
        """
        :param list(~numpy.ndarray) data:
        :param str variable:
        :param int rate:
        :param int n_recording:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        """
        n_indices = self.__ceil_n_indices(vertex_slice.n_atoms)
        if rate == 0:
            # Not recording anything so all indices are 0
            data.append(numpy.zeros(n_indices, dtype=uint16).view(uint32))
        elif (indexes := self.__indexes.get(variable)) is None:
            # Recording everything so indices are identity
            data.append(numpy.arange(n_indices, dtype=uint16).view(uint32))
        else:
            local_index = 0
            local_indexes: List[int] = list()
            # Add indices based on the raster ids
            index = 0
            for index in vertex_slice.get_raster_ids():
                if index in indexes:
                    # Recording so write the local index to record to
                    local_indexes.append(local_index)
                    local_index += 1
                else:
                    # Not recording so write to one beyond recording range
                    local_indexes.append(n_recording)
            # Any extra indices should be filled in
            for _ in range(len(local_indexes), n_indices):
                local_indexes.append(n_recording)
            data.append(
                numpy.array(local_indexes, dtype=uint16).view(uint32))

    def _get_data(self, vertex_slice: Slice) -> NDArray[uint32]:
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: ~numpy.ndarray
        """
        # There is no data here for per-timestep variables by design
        data: List[NDArray[uint32]] = list()
        for variable in self.__sampling_rates:
            rate, n_recording = self._rate_and_count_per_slice(
                variable, vertex_slice)
            if variable in self.__bitfield_variables:
                data.append(numpy.array([rate, n_recording], dtype=uint32))
            else:
                dtype = self.__data_types[variable]
                data.append(numpy.array(
                    [rate, n_recording, dtype.size], dtype=uint32))
            self.__add_indices(data, variable, rate, n_recording, vertex_slice)

        return numpy.concatenate(data)

    def set_max_rewires_per_ts(self, max_rewires_per_ts: int):
        """
        :param int max_rewires_per_ts: the maximum rewires per timestep
        """
        self.__events_per_ts[self.MAX_REWIRES] = max_rewires_per_ts

    @property
    def _indexes(self) -> Mapping:  # for testing only
        return MappingProxyType(self.__indexes)

    @property
    def is_global_generatable(self) -> bool:
        """
        Whether the data for all neurons the same, i.e., all or none of the
        neurons are recorded for all variables.

        :rtype: bool
        """
        for variable in self.__sampling_rates:
            if variable in self.__indexes:
                return False
        return True

    def get_generator_data(
            self, vertex_slice: Optional[Slice] = None) -> NDArray[uint32]:
        """
        Get the recorded data as a generatable data set.

        :param vertex_slice:
            The slice to generate the data for, or `None` to generate for
            all neurons (assuming all the same, otherwise error)
        :type vertex_slice: ~pacman.model.graphs.common.Slice or None
        :rtype: numpy.ndarray
        """
        n_vars = len(self.__sampling_rates) - len(self.__bitfield_variables)
        data = [n_vars, len(self.__bitfield_variables)]
        for variable in self.__sampling_rates:
            rate = self.__sampling_rates[variable]
            if variable in self.__bitfield_variables:
                data.append(rate)
            else:
                data.extend([rate, self.__data_types[variable].size])
            if rate == 0:
                data.extend([0, 0])
            else:
                data.extend(self.__get_generator_indices(
                    variable, vertex_slice))
        return numpy.array(data, dtype=uint32)

    def __get_generator_indices(
            self, variable: str,
            vertex_slice: Optional[Slice]) -> Iterable[int]:
        """
        Get the indices of the variables to record in run-length-encoded form.
        """
        index = self.__indexes.get(variable)

        # If there is no index, add that all variables are recorded
        if index is None:
            return [_REPEAT_PER_NEURON, 1,
                    _REPEAT_PER_NEURON_RECORDED | _RECORDED_FLAG]

        assert (vertex_slice is not None)

        # Find slice-relative indices in the index
        indices = numpy.intersect1d(
            vertex_slice.get_raster_ids(), index, return_indices=True)[1]

        # If there is no overlap, nothing is recorded
        if len(indices) == 0:
            return [_REPEAT_PER_NEURON, 1,
                    _REPEAT_PER_NEURON_RECORDED | _NOT_RECORDED_FLAG]

        # Split the indices into consecutive ranges
        ranges = numpy.split(
            indices, numpy.where(numpy.diff(indices) > 1)[0] + 1)

        # Generate a run-length-encoded list
        # Initially there are no items, but this will be updated
        # Also keep track of the number recorded, also 0 initially
        data = [0, 0]
        n_items = 0

        last_index = 0
        n_recorded = 0
        for r in ranges:
            # Add the last non-recorded range
            if r[0] > last_index:
                data.append((r[0] - last_index) | _NOT_RECORDED_FLAG)
                n_items += 1

            # Add this recorded range
            data.append(((r[-1] - r[0]) + 1) | _RECORDED_FLAG)
            n_items += 1
            n_recorded += (r[-1] - r[0]) + 1
            last_index = r[-1] + 1

        # Add the final range if needed
        if last_index < vertex_slice.n_atoms:
            data.append((vertex_slice.n_atoms - last_index) |
                        _NOT_RECORDED_FLAG)
            n_items += 1

        data[0] = n_recorded
        data[1] = n_items
        return numpy.array(data, dtype=uint32)
