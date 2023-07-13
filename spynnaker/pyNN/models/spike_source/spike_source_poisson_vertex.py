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

import logging
import math
from typing import (
    Any, Collection, Dict, List, Optional, Sequence, Sized, Tuple, Union, cast)
from typing_extensions import TypeGuard
import numpy
from numpy.typing import NDArray
import scipy.stats
from pyNN.space import Grid2D, Grid3D, BaseStructure
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinn_utilities.ranged import RangeDictionary, RangedList
from spinn_utilities.config_holder import get_config_int
from pacman.model.graphs.application import ApplicationEdge
from pacman.model.graphs.common import Slice
from pacman.model.resources import AbstractSDRAM, ConstantSDRAM
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI
from pacman.model.partitioner_splitters import AbstractSplitterCommon
from spinn_front_end_common.interface.buffer_management import (
    recording_utilities)
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT)
from spinn_front_end_common.interface.profiling import profile_utils
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.common import MultiSpikeRecorder
from spynnaker.pyNN.utilities.utility_calls import create_mars_kiss_seeds
from spynnaker.pyNN.models.abstract_models import SupportsStructure
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.models.common import ParameterHolder
from spynnaker.pyNN.utilities.buffer_data_type import BufferDataType
from .spike_source_poisson_machine_vertex import (
    SpikeSourcePoissonMachineVertex, _flatten, get_rates_bytes,
    get_sdram_edge_params_bytes, get_expander_rates_bytes, get_params_bytes)
from .spike_source_poisson import SpikeSourcePoisson
from .spike_source_poisson_variable import SpikeSourcePoissonVariable
from spynnaker.pyNN.models.projection import Projection

logger = FormatAdapter(logging.getLogger(__name__))

# uint32_t n_rates; uint32_t index
PARAMS_WORDS_PER_NEURON = 2

# start_scaled, end_scaled, next_scaled, is_fast_source, exp_minus_lambda,
# sqrt_lambda, isi_val, time_to_spike
PARAMS_WORDS_PER_RATE = 8

SLOW_RATE_PER_TICK_CUTOFF = (
    SpikeSourcePoissonMachineVertex.SLOW_RATE_PER_TICK_CUTOFF)

OVERFLOW_TIMESTEPS_FOR_SDRAM = 5

# The microseconds per timestep will be divided by this to get the max offset
_MAX_OFFSET_DENOMINATOR = 10

# Indicates a duration that never ends
DURATION_FOREVER = 0xFFFFFFFF


def _is_list_of_lists(value: Any) -> TypeGuard[
        Sequence[Sequence[Union[int, float]]]]:
    return isinstance(value, Sequence) and isinstance(value[0], Sequence)


def _normalize_rates(
        rate: Union[float, Sequence[float], None],
        rates: Union[Sequence[float], NDArray[numpy.floating], None]
        ) -> Union[NDArray[numpy.floating], List[NDArray[numpy.floating]]]:
    if rates is None:
        if isinstance(rate, Sequence):
            # Single rate per neuron for whole simulation
            return [numpy.array([r]) for r in rate]
        else:
            # Single rate for all neurons for whole simulation
            return numpy.array([rate])
    elif _is_list_of_lists(rates):
        # Convert each list to numpy array
        return [numpy.array(r) for r in rates]
    else:
        return numpy.array(rates)


def _normalize_times(
        time: Union[int, Sequence[int], None],
        times: Union[Sequence[int], NDArray[numpy.integer], None]
        ) -> Union[NDArray[numpy.integer], List[NDArray[numpy.integer]], None]:
    if times is None:
        if time is None:
            return None
        if isinstance(time, Sequence):
            # Single time per neuron for whole simulation
            return [numpy.array([r]) for r in time]
        else:
            # Single time for all neurons for whole simulation
            return numpy.array([time])
    elif _is_list_of_lists(times):
        # Convert each list to numpy array
        return [numpy.array(r) for r in times]
    else:
        return numpy.array(times)


class SpikeSourcePoissonVertex(
        PopulationApplicationVertex,
        LegacyPartitionerAPI, SupportsStructure):
    """
    A SpiNNaker vertex that is a Poisson-distributed Spike source.
    """

    __slots__ = (
        "__last_rate_read_time",
        "__model",
        "__model_name",
        "__n_atoms",
        "__rng",
        "__seed",
        "__spike_recorder",
        "__kiss_seed",  # dict indexed by vertex slice
        "__max_rate",
        "__max_n_rates",
        "__n_profile_samples",
        "__data",
        "__is_variable_rate",
        "__outgoing_projections",
        "__incoming_control_edge",
        "__structure",
        "__allowed_parameters",
        "__n_colour_bits")

    SPIKE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons: int, label: str, seed: Optional[int],
            max_atoms_per_core: Optional[int],
            model: Union[SpikeSourcePoisson, SpikeSourcePoissonVariable],
            rate: Union[float, Sequence[float], None] = None,
            start: Union[int, Sequence[int], None] = None,
            duration: Union[int, Sequence[int], None] = None,
            rates: Union[
                Sequence[float], NDArray[numpy.floating], None] = None,
            starts: Union[Sequence[int], NDArray[numpy.integer], None] = None,
            durations: Union[
                Sequence[int], NDArray[numpy.integer], None] = None,
            max_rate: Optional[float] = None,
            splitter: Optional[AbstractSplitterCommon] = None,
            n_colour_bits: Optional[int] = None):
        """
        :param int n_neurons:
        :param str label:
        :param float seed:
        :param int max_atoms_per_core:
        :param ~spynnaker.pyNN.models.spike_source.SpikeSourcePoisson model:
        :param float rate:
        :param int start:
        :param int duration:
        :param iterable(float) rates:
        :param iterable(int) starts:
        :param iterable(int) durations:
        :param float max_rate:
        :param splitter:
        :type splitter:
            ~pacman.model.partitioner_splitters.AbstractSplitterCommon or None
        :param int n_colour_bits:
        """
        # pylint: disable=too-many-arguments
        super().__init__(label, max_atoms_per_core, splitter)

        # atoms params
        self.__n_atoms = self.round_n_atoms(n_neurons, "n_neurons")
        self.__model_name = "SpikeSourcePoisson"
        self.__model = model
        self.__seed = seed
        self.__kiss_seed: Dict[Slice, Tuple[int, ...]] = dict()

        self.__spike_recorder = MultiSpikeRecorder()

        # Check for disallowed pairs of parameters
        if (rates is not None) and (rate is not None):
            raise ValueError("Exactly one of rate and rates can be specified")
        if (starts is not None) and (start is not None):
            raise ValueError(
                "Exactly one of start and starts can be specified")
        if (durations is not None) and (duration is not None):
            raise ValueError(
                "Exactly one of duration and durations can be specified")
        if rate is None and rates is None:
            raise ValueError("One of rate or rates must be specified")

        # Normalise the parameters
        self.__is_variable_rate = rates is not None
        _rates = _normalize_rates(rate, rates)
        _starts = _normalize_times(start, starts)
        _durations = _normalize_times(duration, durations)
        if _durations is None:
            if _is_list_of_lists(_rates):
                _durations = [numpy.array([DURATION_FOREVER for _r in _rate])
                              for _rate in _rates]
            else:
                _durations = numpy.array(
                    [DURATION_FOREVER for _rate in _rates])

        # Check that there is either one list for all neurons,
        # or one per neuron
        if _is_list_of_lists(_rates) and len(_rates) != n_neurons:
            raise ValueError(
                "Must specify one rate for all neurons or one per neuron")
        if _is_list_of_lists(_starts) and len(_starts) != n_neurons:
            raise ValueError(
                "Must specify one start for all neurons or one per neuron")
        if _is_list_of_lists(_durations) and len(_durations) != n_neurons:
            raise ValueError(
                "Must specify one duration for all neurons or one per neuron")

        # Check that for each rate there is a start and duration if needed
        # TODO: Could be more efficient for case where parameters are not one
        #       per neuron
        for i in range(n_neurons):
            rate_set = _rates[i] if _is_list_of_lists(_rates) else _rates
            if not isinstance(rate_set, Sized):
                raise ValueError("Multiple rates must be a list")
            if starts is None and len(rate_set) > 1:
                raise ValueError(
                    "When multiple rates are specified,"
                    " each must have a start")
            elif _starts is not None:
                start_set = (
                    _starts[i] if _is_list_of_lists(_starts) else _starts)
                if len(start_set) != len(rate_set):
                    raise ValueError("Each rate must have a start")
                if any(s is None for s in start_set):
                    raise ValueError("Start must not be None")
            if _durations is not None:
                duration_set = (
                    _durations[i] if _is_list_of_lists(_durations)
                    else _durations)
                if len(duration_set) != len(rate_set):
                    raise ValueError("Each rate must have its own duration")

        self.__data: RangeDictionary[
            Union[NDArray[numpy.floating], NDArray[numpy.integer]]
            ] = RangeDictionary(n_neurons)
        self.__data["rates"] = RangedList(
            n_neurons, _rates,
            use_list_as_value=not _is_list_of_lists(_rates))
        self.__data["starts"] = RangedList(
            n_neurons, _starts,
            use_list_as_value=not _is_list_of_lists(_starts))
        self.__data["durations"] = RangedList(
            n_neurons, _durations,
            use_list_as_value=not _is_list_of_lists(_durations))
        self.__rng = numpy.random.RandomState(seed)

        self.__n_profile_samples = get_config_int(
            "Reports", "n_profile_samples") or 0

        # Prepare for recording, and to get spikes
        self.__spike_recorder = MultiSpikeRecorder()

        if max_rate is None:
            all_rates = list(_flatten(self.__data["rates"]))
            self.__max_rate = numpy.amax(all_rates) if len(all_rates) else 0
        else:
            self.__max_rate = max_rate
        self.__max_n_rates = max(
            len(r)
            for r in self.__data["rates"])  # pylint: disable=not-an-iterable

        # Keep track of how many outgoing projections exist
        self.__outgoing_projections: List[Projection] = list()
        self.__incoming_control_edge: Optional[ApplicationEdge] = None

        self.__structure: Optional[BaseStructure] = None

        if self.__is_variable_rate:
            self.__allowed_parameters = {"rates", "durations", "starts"}
        else:
            self.__allowed_parameters = {"rate", "duration", "start"}

        self.__last_rate_read_time: Optional[float] = None

        if n_colour_bits is None:
            n_colour_bits = get_config_int("Simulation", "n_colour_bits")
        self.__n_colour_bits = 0 if n_colour_bits is None else n_colour_bits

    @overrides(SupportsStructure.set_structure)
    def set_structure(self, structure: BaseStructure):
        self.__structure = structure

    @property
    def rates(self) -> RangedList[NDArray[numpy.floating]]:
        """
        Get the rates.

        :rtype: spinn_utilities.ranged.RangedList
        """
        return cast(Any, self.__data["rates"])

    def add_outgoing_projection(self, projection: Projection):
        """
        Add an outgoing projection from this vertex.

        :param Projection projection: The projection to add
        """
        self.__outgoing_projections.append(projection)

    @property
    def outgoing_projections(self) -> Sequence[Projection]:
        """
        The projections outgoing from this vertex.

        :rtype: list(Projection)
        """
        return self.__outgoing_projections

    @property
    def n_profile_samples(self) -> int:
        return self.__n_profile_samples

    @property
    def time_to_spike(self) -> RangedList:
        return self.__data["time_to_spike"]

    def __read_parameters_now(self) -> None:
        # If we already read the parameters at this time, don't do it again
        current_time = SpynnakerDataView().get_current_run_time_ms()
        if self.__last_rate_read_time == current_time:
            return

        self.__last_rate_read_time = current_time
        for m_vertex in self.machine_vertices:
            placement = SpynnakerDataView.get_placement_of_vertex(m_vertex)
            m_vertex.read_parameters_from_machine(placement)

    def __read_parameter(self, name: str, selector):
        if (SpynnakerDataView.is_ran_last() and
                SpynnakerDataView.has_transceiver()):
            self.__read_parameters_now()
        return self.__data[self.__full_name(name)].get_values(selector)

    def __full_name(self, name: str) -> str:
        if self.__is_variable_rate:
            return name
        return f"{name}s"

    @overrides(PopulationApplicationVertex.get_parameter_values)
    def get_parameter_values(self, names: Sequence[str], selector=None):
        self._check_parameters(names, self.__allowed_parameters)
        return ParameterHolder(names, self.__read_parameter, selector)

    @overrides(PopulationApplicationVertex.set_parameter_values)
    def set_parameter_values(self, name: str, value, selector=None):
        self._check_parameters(name, self.__allowed_parameters)
        if self.__is_variable_rate:
            raise KeyError(f"Cannot set the {name} of a variable rate Poisson")

        # If we have just run, we need to read parameters to avoid overwrite
        if SpynnakerDataView().is_ran_last():
            self.__read_parameters_now()
        for m_vertex in self.machine_vertices:
            m_vertex.set_rate_changed()

        # Must be parameter without the s
        fixed_name = f"{name}s"
        if hasattr(value, "__len__"):
            # Single start per neuron for whole simulation
            self.__data[fixed_name].set_value_by_selector(
                selector, [numpy.array([s]) for s in value])
        else:
            # Single start for all neurons for whole simulation
            self.__data[fixed_name].set_value_by_selector(
                selector, numpy.array([value]), use_list_as_value=True)

    @overrides(PopulationApplicationVertex.get_parameters)
    def get_parameters(self) -> Collection[str]:
        return self.__allowed_parameters

    @overrides(PopulationApplicationVertex.get_units)
    def get_units(self, name: str) -> str:
        if name == "spikes":
            return ""
        if name == "rates" or name == "rates":
            return "Hz"
        if (name == "duration" or name == "start" or name == "durations" or
                name == "starts"):
            return "ms"
        raise KeyError(f"Units for {name} unknown")

    @overrides(PopulationApplicationVertex.get_recordable_variables)
    def get_recordable_variables(self) -> List[str]:
        return ["spikes"]

    def get_buffer_data_type(self, name: str) -> BufferDataType:
        if name == "spikes":
            return BufferDataType.MULTI_SPIKES
        raise KeyError(f"Cannot record {name}")

    def get_recording_region(self, name: str) -> int:
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return 0

    @overrides(PopulationApplicationVertex.set_recording)
    def set_recording(self, name: str, sampling_interval=None, indices=None):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported for "
                           "SpikeSourcePoisson so being ignored")
        if indices is not None:
            logger.warning("Indices currently not supported for "
                           "SpikeSourcePoisson so being ignored")
        if not self.__spike_recorder.record:
            SpynnakerDataView.set_requires_mapping()
        self.__spike_recorder.record = True

    @overrides(PopulationApplicationVertex.get_recording_variables)
    def get_recording_variables(self) -> List[str]:
        if self.__spike_recorder.record:
            return ["spikes"]
        return []

    @overrides(PopulationApplicationVertex.set_not_recording)
    def set_not_recording(self, name: str, indices=None):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        if indices is not None:
            logger.warning("Indices currently not supported for "
                           "SpikeSourceArray so being ignored")
        self.__spike_recorder.record = False

    @overrides(PopulationApplicationVertex.get_sampling_interval_ms)
    def get_sampling_interval_ms(self, name: str) -> int:
        # TODO microseconds or milliseconds?
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return SpynnakerDataView.get_simulation_time_step_us()

    @overrides(PopulationApplicationVertex.get_data_type)
    def get_data_type(self, name: str) -> None:
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return None

    @overrides(PopulationApplicationVertex.get_neurons_recording)
    def get_neurons_recording(self, name: str, vertex_slice: Slice) -> NDArray:
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return vertex_slice.get_raster_ids()

    def max_spikes_per_ts(self) -> float:
        """
        Compute the maximum spike rate.

        :return: The maximum number of spikes per simulation timestep.
        :rtype: float
        """
        ts_per_second = SpynnakerDataView.get_simulation_time_step_per_s()
        if float(self.__max_rate) / ts_per_second < SLOW_RATE_PER_TICK_CUTOFF:
            return 1.0

        # Experiments show at 1000 this result is typically higher than actual
        chance_ts = 1000
        max_spikes_per_ts = scipy.stats.poisson.ppf(
            1.0 - (1.0 / float(chance_ts)),
            float(self.__max_rate) / ts_per_second)
        return int(math.ceil(max_spikes_per_ts)) + 1.0

    def get_recording_sdram_usage(self, vertex_slice: Slice) -> AbstractSDRAM:
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: ~pacman.model.resources.AbstractSDRAM
        """
        variable_sdram = self.__spike_recorder.get_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self.max_spikes_per_ts())
        constant_sdram = ConstantSDRAM(
            variable_sdram.per_timestep * OVERFLOW_TIMESTEPS_FOR_SDRAM)
        return variable_sdram + constant_sdram

    @overrides(LegacyPartitionerAPI.get_sdram_used_by_atoms)
    def get_sdram_used_by_atoms(self, vertex_slice: Slice) -> AbstractSDRAM:
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        """
        poisson_params_sz = get_params_bytes(vertex_slice.n_atoms)
        poisson_rates_sz = get_rates_bytes(
            vertex_slice.n_atoms, vertex_slice.n_atoms * self.__max_n_rates)
        poisson_expander_sz = get_expander_rates_bytes(
            vertex_slice.n_atoms, vertex_slice.n_atoms * self.__max_n_rates)
        sdram_sz = get_sdram_edge_params_bytes(vertex_slice)
        other = ConstantSDRAM(
            SYSTEM_BYTES_REQUIREMENT +
            SpikeSourcePoissonMachineVertex.get_provenance_data_size(0) +
            poisson_params_sz + poisson_rates_sz + poisson_expander_sz +
            recording_utilities.get_recording_header_size(1) +
            recording_utilities.get_recording_data_constant_size(1) +
            profile_utils.get_profile_region_size(self.__n_profile_samples) +
            sdram_sz)

        recording = self.get_recording_sdram_usage(vertex_slice)
        return recording + other

    @property
    def n_atoms(self) -> int:
        return self.__n_atoms

    @property
    @overrides(PopulationApplicationVertex.atoms_shape)
    def atoms_shape(self) -> Tuple[int, ...]:
        if isinstance(self.__structure, (Grid2D, Grid3D)):
            return self.__structure.calculate_size(self.__n_atoms)
        return super().atoms_shape

    @overrides(LegacyPartitionerAPI.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice: Slice, sdram: AbstractSDRAM,
            label: Optional[str] = None) -> SpikeSourcePoissonMachineVertex:
        return SpikeSourcePoissonMachineVertex(
            sdram, self.__spike_recorder.record,
            label, self, vertex_slice)

    @property
    def max_rate(self) -> float:
        return float(self.__max_rate)

    @property
    def max_n_rates(self) -> int:
        return self.__max_n_rates

    @property
    def seed(self) -> Optional[int]:
        return self.__seed

    @seed.setter
    def seed(self, seed: int):
        self.__seed = seed
        self.__kiss_seed = dict()
        self.__rng = numpy.random.RandomState(seed)

    def kiss_seed(self, vertex_slice: Slice) -> Tuple[int, ...]:
        if vertex_slice not in self.__kiss_seed:
            self.__kiss_seed[vertex_slice] = create_mars_kiss_seeds(self.__rng)
        return self.__kiss_seed[vertex_slice]

    def update_kiss_seed(self, vertex_slice: Slice, seed: Sequence[int]):
        """
        Updates a KISS seed from the machine.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            the vertex slice to update seed of
        :param list(int) seed: the seed
        """
        self.__kiss_seed[vertex_slice] = tuple(seed)

    def clear_spike_recording(self) -> None:
        buffer_manager = SpynnakerDataView.get_buffer_manager()
        for machine_vertex in self.machine_vertices:
            placement = SpynnakerDataView.get_placement_of_vertex(
                machine_vertex)
            buffer_manager.clear_recorded_data(
                placement.x, placement.y, placement.p,
                SpikeSourcePoissonVertex.SPIKE_RECORDING_REGION_ID)

    def describe(self):
        """
        Return a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template
        together with an associated template engine
        (see :py:mod:`pyNN.descriptions`).

        If template is `None`, then a dictionary containing the template
        context will be returned.

        :rtype: dict(str, ...)
        """
        parameters = self.get_parameter_values(self.__model.default_parameters)

        return {
            "name": self.__model_name,
            "default_parameters": self.__model.default_parameters,
            "default_initial_values": self.__model.default_parameters,
            "parameters": parameters,
        }

    def set_live_poisson_control_edge(self, edge: ApplicationEdge):
        if self.__incoming_control_edge is not None:
            raise ValueError(
                "The Poisson generator can only be controlled by one source")
        self.__incoming_control_edge = edge

    @property
    def incoming_control_edge(self) -> Optional[ApplicationEdge]:
        return self.__incoming_control_edge

    @property
    def data(self) -> RangeDictionary[
            Union[NDArray[numpy.floating], NDArray[numpy.integer]]]:
        return self.__data

    @property
    def n_colour_bits(self) -> int:
        return self.__n_colour_bits
