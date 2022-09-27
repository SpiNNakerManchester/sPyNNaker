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

import logging
import math
import numpy
import scipy.stats
from pyNN.space import Grid2D, Grid3D
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinn_utilities.ranged import RangeDictionary, RangedList
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI
from pacman.model.resources import ConstantSDRAM
from spinn_utilities.config_holder import get_config_int
from spinn_front_end_common.interface.buffer_management import (
    recording_utilities)
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT)
from spinn_front_end_common.interface.profiling import profile_utils
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.common import MultiSpikeRecorder
from .spike_source_poisson_machine_vertex import (
    SpikeSourcePoissonMachineVertex, _flatten, get_rates_bytes,
    get_sdram_edge_params_bytes, get_expander_rates_bytes)
from spynnaker.pyNN.utilities.utility_calls import create_mars_kiss_seeds
from spynnaker.pyNN.models.abstract_models import SupportsStructure
from spynnaker.pyNN.models.abstract_models import (
    PopulationApplicationVertex, ParameterHolder, RecordingType)

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


class SpikeSourcePoissonVertex(
        PopulationApplicationVertex,
        LegacyPartitionerAPI, SupportsStructure):
    """ A Poisson Spike source object
    """

    __slots__ = [
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
        "__allowed_parameters"]

    SPIKE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons, label, seed, max_atoms_per_core, model,
            rate=None, start=None, duration=None, rates=None, starts=None,
            durations=None, max_rate=None, splitter=None):
        """
        :param int n_neurons:
        :param str label:
        :param float seed:
        :param int max_atoms_per_core:
        :param ~spynnaker.pyNN.models.spike_source.SpikeSourcePoisson model:
        :param iterable(float) rate:
        :param iterable(int) start:
        :param iterable(int) duration:
        :param splitter:
        :type splitter:
            ~pacman.model.partitioner_splitters.abstract_splitters.AbstractSplitterCommon
        """
        # pylint: disable=too-many-arguments
        super().__init__(label, max_atoms_per_core, splitter)

        # atoms params
        self.__n_atoms = self.round_n_atoms(n_neurons, "n_neurons")
        self.__model_name = "SpikeSourcePoisson"
        self.__model = model
        self.__seed = seed
        self.__kiss_seed = dict()

        self.__spike_recorder = MultiSpikeRecorder()

        # Check for disallowed pairs of parameters
        if (rates is not None) and (rate is not None):
            raise Exception("Exactly one of rate and rates can be specified")
        if (starts is not None) and (start is not None):
            raise Exception("Exactly one of start and starts can be specified")
        if (durations is not None) and (duration is not None):
            raise Exception(
                "Exactly one of duration and durations can be specified")
        if rate is None and rates is None:
            raise Exception("One of rate or rates must be specified")

        # Normalise the parameters
        self.__is_variable_rate = rates is not None
        if rates is None:
            if hasattr(rate, "__len__"):
                # Single rate per neuron for whole simulation
                rates = [numpy.array([r]) for r in rate]
            else:
                # Single rate for all neurons for whole simulation
                rates = numpy.array([rate])
        elif hasattr(rates[0], "__len__"):
            # Convert each list to numpy array
            rates = [numpy.array(r) for r in rates]
        else:
            rates = numpy.array(rates)
        if starts is None and start is not None:
            if hasattr(start, "__len__"):
                starts = [numpy.array([s]) for s in start]
            elif start is None:
                starts = numpy.array([0])
            else:
                starts = numpy.array([start])
        elif starts is not None and hasattr(starts[0], "__len__"):
            starts = [numpy.array(s) for s in starts]
        elif starts is not None:
            starts = numpy.array(starts)
        if durations is None and duration is not None:
            if hasattr(duration, "__len__"):
                durations = [numpy.array([d]) for d in duration]
            else:
                durations = numpy.array([duration])
        elif durations is not None and hasattr(durations[0], "__len__"):
            durations = [numpy.array(d) for d in durations]
        elif durations is not None:
            durations = numpy.array(durations)
        else:
            if hasattr(rates[0], "__len__"):
                durations = [numpy.array([0 for r in _rate])
                             for _rate in rates]
            else:
                durations = numpy.array([0 for _rate in rates])

        # Check that there is either one list for all neurons,
        # or one per neuron
        if hasattr(rates[0], "__len__") and len(rates) != n_neurons:
            raise Exception(
                "Must specify one rate for all neurons or one per neuron")
        if (starts is not None and hasattr(starts[0], "__len__") and
                len(starts) != n_neurons):
            raise Exception(
                "Must specify one start for all neurons or one per neuron")
        if (durations is not None and hasattr(durations[0], "__len__") and
                len(durations) != n_neurons):
            raise Exception(
                "Must specify one duration for all neurons or one per neuron")

        # Check that for each rate there is a start and duration if needed
        # TODO: Could be more efficient for case where parameters are not one
        #       per neuron
        for i in range(n_neurons):
            rate_set = rates
            if hasattr(rates[0], "__len__"):
                rate_set = rates[i]
            if not hasattr(rate_set, "__len__"):
                raise Exception("Multiple rates must be a list")
            if starts is None and len(rate_set) > 1:
                raise Exception(
                    "When multiple rates are specified,"
                    " each must have a start")
            elif starts is not None:
                start_set = starts
                if hasattr(starts[0], "__len__"):
                    start_set = starts[i]
                if len(start_set) != len(rate_set):
                    raise Exception("Each rate must have a start")
                if any(s is None for s in start_set):
                    raise Exception("Start must not be None")
            if durations is not None:
                duration_set = durations
                if hasattr(durations[0], "__len__"):
                    duration_set = durations[i]
                if len(duration_set) != len(rate_set):
                    raise Exception("Each rate must have its own duration")

        self.__data = RangeDictionary(n_neurons)
        self.__data["rates"] = RangedList(
            n_neurons, rates,
            use_list_as_value=not hasattr(rates[0], "__len__"))
        self.__data["starts"] = RangedList(
            n_neurons, starts,
            use_list_as_value=not hasattr(starts[0], "__len__"))
        self.__data["durations"] = RangedList(
            n_neurons, durations,
            use_list_as_value=not hasattr(durations[0], "__len__"))
        self.__rng = numpy.random.RandomState(seed)

        self.__n_profile_samples = get_config_int(
            "Reports", "n_profile_samples")

        # Prepare for recording, and to get spikes
        self.__spike_recorder = MultiSpikeRecorder()

        all_rates = list(_flatten(self.__data["rates"]))
        self.__max_rate = max_rate
        if max_rate is None and len(all_rates):
            self.__max_rate = numpy.amax(all_rates)
        elif max_rate is None:
            self.__max_rate = 0
        self.__max_n_rates = max(len(r) for r in self.__data["rates"])

        # Keep track of how many outgoing projections exist
        self.__outgoing_projections = list()
        self.__incoming_control_edge = None

        self.__structure = None

        if self.__is_variable_rate:
            self.__allowed_parameters = {"rates", "durations", "starts"}
        else:
            self.__allowed_parameters = {"rate", "duration", "start"}

        self.__last_rate_read_time = None

    @overrides(SupportsStructure.set_structure)
    def set_structure(self, structure):
        self.__structure = structure

    def add_outgoing_projection(self, projection):
        """ Add an outgoing projection from this vertex

        :param PyNNProjectionCommon projection: The projection to add
        """
        self.__outgoing_projections.append(projection)

    @property
    def outgoing_projections(self):
        """ The projections outgoing from this vertex

        :rtype: list(PyNNProjectionCommon)
        """
        return self.__outgoing_projections

    @property
    def n_profile_samples(self):
        return self.__n_profile_samples

    @property
    def time_to_spike(self):
        return self.__data["time_to_spike"]

    def __read_parameters_now(self):
        # If we already read the parameters at this time, don't do it again
        current_time = SpynnakerDataView().get_current_run_time_ms()
        if self.__last_rate_read_time == current_time:
            return

        self.__last_rate_read_time = current_time
        for m_vertex in self.machine_vertices:
            placement = SpynnakerDataView.get_placement_of_vertex(m_vertex)
            m_vertex.read_parameters_from_machine(placement)

    def __read_parameter(self, name, selector):
        if (SpynnakerDataView.is_ran_last() and
                SpynnakerDataView.has_transceiver()):
            self.__read_parameters_now()
        return self.__data[name].get_values(selector)

    def __fix_names(self, names):
        if self.__is_variable_rate:
            return names
        return [f"{name}s" for name in self._as_list(names)]

    @overrides(PopulationApplicationVertex.get_parameter_values)
    def get_parameter_values(self, names, selector=None):
        self._check_parameters(names, self.__allowed_parameters)
        return ParameterHolder(
            self.__fix_names(names), self.__read_parameter, selector)

    @overrides(PopulationApplicationVertex.set_parameter_values)
    def set_parameter_values(self, name, value, selector=None):
        self._check_parameters(name, self.__allowed_parameters)
        if self.__is_variable_rate:
            raise KeyError(f"Cannot set the {name} of a variable rate Poisson")

        # If we have just run, we need to read parameters to avoid overwrite
        if SpynnakerDataView().is_ran_last():
            self.__read_parameters_now()
            SpynnakerDataView.set_requires_data_generation()
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
    def get_parameters(self):
        return self.__allowed_parameters

    @overrides(PopulationApplicationVertex.get_units)
    def get_units(self, name):
        if name == "spikes":
            return ""
        if name == "rates" or name == "rates":
            return "Hz"
        if (name == "duration" or name == "start" or name == "durations" or
                name == "starts"):
            return "ms"
        raise KeyError(f"Units for {name} unknown")

    @overrides(PopulationApplicationVertex.get_recordable_variables)
    def get_recordable_variables(self):
        return ["spikes"]

    @overrides(PopulationApplicationVertex.can_record)
    def can_record(self, name):
        return name == "spikes"

    @overrides(PopulationApplicationVertex.set_recording)
    def set_recording(self, name, sampling_interval=None, indices=None):
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
    def get_recording_variables(self):
        if self.__spike_recorder.record:
            return ["spikes"]
        return []

    @overrides(PopulationApplicationVertex.is_recording_variable)
    def is_recording_variable(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return self.__spike_recorder.record

    @overrides(PopulationApplicationVertex.set_not_recording)
    def set_not_recording(self, name, indices=None):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        if indices is not None:
            logger.warning("Indices currently not supported for "
                           "SpikeSourceArray so being ignored")
        self.__spike_recorder.record = False

    @overrides(PopulationApplicationVertex.get_recorded_data)
    def get_recorded_data(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return self.__spike_recorder.get_spikes(
            self.label,
            SpikeSourcePoissonVertex.SPIKE_RECORDING_REGION_ID,
            self)

    @overrides(PopulationApplicationVertex.get_recording_sampling_interval)
    def get_recording_sampling_interval(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return SpynnakerDataView.get_simulation_time_step_us()

    @overrides(PopulationApplicationVertex.get_recording_indices)
    def get_recording_indices(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return range(self.n_atoms)

    @overrides(PopulationApplicationVertex.get_recording_type)
    def get_recording_type(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return RecordingType.BIT_FIELD

    @overrides(PopulationApplicationVertex.clear_recording_data)
    def clear_recording_data(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        buffer_manager = SpynnakerDataView.get_buffer_manager()
        for machine_vertex in self.machine_vertices:
            placement = SpynnakerDataView.get_placement_of_vertex(
                machine_vertex)
            buffer_manager.clear_recorded_data(
                placement.x, placement.y, placement.p,
                SpikeSourcePoissonVertex.SPIKE_RECORDING_REGION_ID)

    def max_spikes_per_ts(self):
        ts_per_second = SpynnakerDataView.get_simulation_time_step_per_s()
        if float(self.__max_rate) / ts_per_second < \
                SLOW_RATE_PER_TICK_CUTOFF:
            return 1

        # Experiments show at 1000 this result is typically higher than actual
        chance_ts = 1000
        max_spikes_per_ts = scipy.stats.poisson.ppf(
            1.0 - (1.0 / float(chance_ts)),
            float(self.__max_rate) / ts_per_second)
        return int(math.ceil(max_spikes_per_ts)) + 1.0

    def get_recording_sdram_usage(self, vertex_slice):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        """
        variable_sdram = self.__spike_recorder.get_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self.max_spikes_per_ts())
        constant_sdram = ConstantSDRAM(
            variable_sdram.per_timestep * OVERFLOW_TIMESTEPS_FOR_SDRAM)
        return variable_sdram + constant_sdram

    @overrides(LegacyPartitionerAPI.get_sdram_used_by_atoms)
    def get_sdram_used_by_atoms(self, vertex_slice):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        """
        poisson_params_sz = get_rates_bytes(
            vertex_slice.n_atoms, vertex_slice.n_atoms * self.__max_n_rates)
        poisson_expander_sz = get_expander_rates_bytes(
            vertex_slice.n_atoms, vertex_slice.n_atoms * self.__max_n_rates)
        sdram_sz = get_sdram_edge_params_bytes(vertex_slice)
        other = ConstantSDRAM(
            SYSTEM_BYTES_REQUIREMENT +
            SpikeSourcePoissonMachineVertex.get_provenance_data_size(0) +
            poisson_params_sz + poisson_expander_sz +
            recording_utilities.get_recording_header_size(1) +
            recording_utilities.get_recording_data_constant_size(1) +
            profile_utils.get_profile_region_size(self.__n_profile_samples) +
            sdram_sz)

        recording = self.get_recording_sdram_usage(vertex_slice)
        return recording + other

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    @overrides(PopulationApplicationVertex.atoms_shape)
    def atoms_shape(self):
        if isinstance(self.__structure, (Grid2D, Grid3D)):
            return self.__structure.calculate_size(self.__n_atoms)
        return super(SpikeSourcePoissonVertex, self).atoms_shape

    @overrides(LegacyPartitionerAPI.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, sdram, label=None):
        # pylint: disable=arguments-differ
        return SpikeSourcePoissonMachineVertex(
            sdram, self.__spike_recorder.record,
            label, self, vertex_slice)

    @property
    def max_rate(self):
        return self.__max_rate

    @property
    def max_n_rates(self):
        return self.__max_n_rates

    @property
    def seed(self):
        return self.__seed

    @seed.setter
    def seed(self, seed):
        self.__seed = seed
        self.__kiss_seed = dict()
        self.__rng = numpy.random.RandomState(seed)

    def kiss_seed(self, vertex_slice):
        if vertex_slice not in self.__kiss_seed:
            self.__kiss_seed[vertex_slice] = create_mars_kiss_seeds(
                self.__rng)
        return self.__kiss_seed[vertex_slice]

    def update_kiss_seed(self, vertex_slice, seed):
        """ updates a kiss seed from the machine

        :param vertex_slice: the vertex slice to update seed of
        :param seed: the seed
        :rtype: None
        """
        self.__kiss_seed[vertex_slice] = seed

    def describe(self):
        """ Return a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template\
        together with an associated template engine\
        (see :py:mod:`pyNN.descriptions`).

        If template is None, then a dictionary containing the template context\
        will be returned.

        :rtype: dict(str, ...)
        """

        parameters = self.get_parameter_values(self.__model.default_parameters)

        context = {
            "name": self.__model_name,
            "default_parameters": self.__model.default_parameters,
            "default_initial_values": self.__model.default_parameters,
            "parameters": parameters,
        }
        return context

    def set_live_poisson_control_edge(self, edge):
        if self.__incoming_control_edge is not None:
            raise Exception("The Poisson can only be controlled by one source")
        self.__incoming_control_edge = edge

    @property
    def incoming_control_edge(self):
        return self.__incoming_control_edge

    @property
    def data(self):
        return self.__data
