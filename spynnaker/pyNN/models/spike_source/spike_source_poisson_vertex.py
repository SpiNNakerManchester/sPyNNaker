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
import struct

from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from pacman.executor.injection_decorator import inject_items
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint)
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)
from spinn_front_end_common.abstract_models import (
    AbstractChangableAfterRun, AbstractProvidesOutgoingPartitionConstraints,
    AbstractGeneratesDataSpecification, AbstractHasAssociatedBinary,
    AbstractRewritesDataSpecification)
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl)
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.interface.buffer_management import (
    recording_utilities)
from spinn_front_end_common.utilities import (
    helpful_functions, globals_variables)
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT, SIMULATION_N_BYTES, BYTES_PER_WORD)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.interface.profiling import profile_utils
from spynnaker.pyNN.models.common import (
    AbstractSpikeRecordable, MultiSpikeRecorder, SimplePopulationSettable)
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models import (
    AbstractReadParametersBeforeSet)
from .spike_source_poisson_machine_vertex import (
    SpikeSourcePoissonMachineVertex)
from spynnaker.pyNN.utilities.utility_calls import validate_mars_kiss_64_seed
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.utilities.ranged.spynnaker_ranged_dict \
    import SpynnakerRangeDictionary
from spynnaker.pyNN.utilities.ranged.spynnaker_ranged_list \
    import SpynnakerRangedList

logger = logging.getLogger(__name__)

# uint32_t has_key; uint32_t key; uint32_t set_rate_neuron_id_mask;
# uint32_t random_backoff_us; uint32_t time_between_spikes;
# UFRACT seconds_per_tick; REAL ticks_per_second;
# REAL slow_rate_per_tick_cutoff; REAL fast_rate_per_tick_cutoff;
# uint32_t first_source_id; uint32_t n_spike_sources;
# mars_kiss64_seed_t (uint[4]) spike_source_seed;
PARAMS_BASE_WORDS = 15

# Seed offset in parameters and size on bytes
SEED_OFFSET_BYTES = 11 * 4
SEED_SIZE_BYTES = 4 * 4

# uint32_t n_rates; uint32_t index
PARAMS_WORDS_PER_NEURON = 2

# start_scaled, end_scaled, next_scaled, is_fast_source, exp_minus_lambda,
# sqrt_lambda, isi_val, time_to_spike
PARAMS_WORDS_PER_RATE = 8

MICROSECONDS_PER_SECOND = 1000000.0
MICROSECONDS_PER_MILLISECOND = 1000.0
SLOW_RATE_PER_TICK_CUTOFF = 0.01  # as suggested by MH (between Exp and Knuth)
FAST_RATE_PER_TICK_CUTOFF = 10  # between Knuth algorithm and Gaussian approx.
_REGIONS = SpikeSourcePoissonMachineVertex.POISSON_SPIKE_SOURCE_REGIONS
OVERFLOW_TIMESTEPS_FOR_SDRAM = 5

# The microseconds per timestep will be divided by this to get the max offset
_MAX_OFFSET_DENOMINATOR = 10

# The maximum timestep - this is the maximum value of a uint32
_MAX_TIMESTEP = 0xFFFFFFFF


_PoissonStruct = Struct([
    DataType.UINT32,  # Start Scaled
    DataType.UINT32,  # End Scaled
    DataType.UINT32,  # Next Scaled
    DataType.UINT32,  # is_fast_source
    DataType.U032,    # exp^(-spikes_per_tick)
    DataType.S1615,   # sqrt(spikes_per_tick)
    DataType.UINT32,   # inter-spike-interval
    DataType.UINT32])  # timesteps to next spike


def _flatten(alist):
    for item in alist:
        if hasattr(item, "__iter__"):
            for subitem in _flatten(item):
                yield subitem
        else:
            yield item


class SpikeSourcePoissonVertex(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary, AbstractSpikeRecordable,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractChangableAfterRun, AbstractReadParametersBeforeSet,
        AbstractRewritesDataSpecification, SimplePopulationSettable,
        ProvidesKeyToAtomMappingImpl):
    """ A Poisson Spike source object
    """
    __slots__ = [
        "__change_requires_mapping",
        "__change_requires_neuron_parameters_reload",
        "__duration",
        "__machine_time_step",
        "__model",
        "__model_name",
        "__n_atoms",
        "__rate",
        "__rng",
        "__seed",
        "__spike_recorder",
        "__start",
        "__time_to_spike",
        "__kiss_seed",
        "__n_subvertices",
        "__n_data_specs",
        "__max_rate",
        "__rate_change",
        "__n_profile_samples",
        "__data",
        "__is_variable_rate",
        "__max_spikes"]

    SPIKE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons, constraints, label, seed,
            max_atoms_per_core, model, rate=None, start=None,
            duration=None, rates=None, starts=None, durations=None,
            max_rate=None):
        # pylint: disable=too-many-arguments
        super(SpikeSourcePoissonVertex, self).__init__(
            label, constraints, max_atoms_per_core)

        # atoms params
        self.__n_atoms = n_neurons
        self.__model_name = "SpikeSourcePoisson"
        self.__model = model
        self.__seed = seed
        self.__kiss_seed = dict()
        self.__rng = None
        self.__n_subvertices = 0
        self.__n_data_specs = 0

        # check for changes parameters
        self.__change_requires_mapping = True
        self.__change_requires_neuron_parameters_reload = False

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
                durations = [numpy.array([None for r in _rate])
                             for _rate in rates]
            else:
                durations = numpy.array([None for _rate in rates])

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

        if hasattr(rates[0], "__len__"):
            time_to_spike = [
                numpy.array([0 for _ in range(len(rates[i]))])
                for i in range(len(rates))]
        else:
            time_to_spike = numpy.array([0 for _ in range(len(rates))])

        self.__data = SpynnakerRangeDictionary(n_neurons)
        self.__data["rates"] = SpynnakerRangedList(
            n_neurons, rates,
            use_list_as_value=not hasattr(rates[0], "__len__"))
        self.__data["starts"] = SpynnakerRangedList(
            n_neurons, starts,
            use_list_as_value=not hasattr(starts[0], "__len__"))
        self.__data["durations"] = SpynnakerRangedList(
            n_neurons, durations,
            use_list_as_value=not hasattr(durations[0], "__len__"))
        self.__data["time_to_spike"] = SpynnakerRangedList(
            n_neurons, time_to_spike,
            use_list_as_value=not hasattr(time_to_spike[0], "__len__"))
        self.__rng = numpy.random.RandomState(seed)
        self.__rate_change = numpy.zeros(n_neurons)
        self.__machine_time_step = None

        # get config from simulator
        config = globals_variables.get_simulator().config
        self.__n_profile_samples = helpful_functions.read_config_int(
            config, "Reports", "n_profile_samples")

        # Prepare for recording, and to get spikes
        self.__spike_recorder = MultiSpikeRecorder()

        all_rates = list(_flatten(self.__data["rates"]))
        self.__max_rate = max_rate
        if max_rate is None and len(all_rates):
            self.__max_rate = numpy.amax(all_rates)
        elif max_rate is None:
            self.__max_rate = 0

        total_rate = numpy.sum(all_rates)
        self.__max_spikes = 0
        if total_rate > 0:
            # Note we have to do this per rate, as the whole array is not numpy
            max_rates = numpy.array(
                [numpy.max(r) for r in self.__data["rates"]])
            self.__max_spikes = numpy.sum(scipy.stats.poisson.ppf(
                1.0 - (1.0 / max_rates), max_rates))

    @property
    def rate(self):
        if self.__is_variable_rate:
            raise Exception("Get variable rate poisson rates with .rates")
        return list(_flatten(self.__data["rates"]))

    @rate.setter
    def rate(self, rate):
        if self.__is_variable_rate:
            raise Exception("Cannot set rate of a variable rate poisson")
        self.__rate_change = rate - numpy.array(
            list(_flatten(self.__data["rates"])))
        # Normalise parameter
        if hasattr(rate, "__len__"):
            # Single rate per neuron for whole simulation
            self.__data["rates"].set_value([numpy.array([r]) for r in rate])
        else:
            # Single rate for all neurons for whole simulation
            self.__data["rates"].set_value(
                numpy.array([rate]), use_list_as_value=True)
        all_rates = list(_flatten(self.__data["rates"]))
        new_max = 0
        if len(all_rates):
            new_max = numpy.amax(all_rates)
        if self.__max_rate is None:
            self.__max_rate = new_max
        # Setting record forces reset so OK to go over if not recording
        elif self.__spike_recorder.record and new_max > self.__max_rate:
            logger.info('Increasing spike rate while recording requires a '
                        '"reset unless additional_parameters "max_rate" is '
                        'set')
            self.__change_requires_mapping = True
            self.__max_rate = new_max

    @property
    def start(self):
        if self.__is_variable_rate:
            raise Exception("Get variable rate poisson starts with .starts")
        return self.__data["starts"]

    @start.setter
    def start(self, start):
        if self.__is_variable_rate:
            raise Exception("Cannot set start of a variable rate poisson")
        # Normalise parameter
        if hasattr(start, "__len__"):
            # Single start per neuron for whole simulation
            self.__data["starts"].set_value([numpy.array([s]) for s in start])
        else:
            # Single start for all neurons for whole simulation
            self.__data["starts"].set_value(
                numpy.array([start]), use_list_as_value=True)

    @property
    def duration(self):
        if self.__is_variable_rate:
            raise Exception(
                "Get variable rate poisson durations with .durations")
        return self.__data["durations"]

    @duration.setter
    def duration(self, duration):
        if self.__is_variable_rate:
            raise Exception("Cannot set duration of a variable rate poisson")
        # Normalise parameter
        if hasattr(duration, "__len__"):
            # Single duration per neuron for whole simulation
            self.__data["durations"].set_value(
                [numpy.array([d]) for d in duration])
        else:
            # Single duration for all neurons for whole simulation
            self.__data["durations"].set_value(
                numpy.array([duration]), use_list_as_value=True)

    @property
    def rates(self):
        return self.__data["rates"]

    @rates.setter
    def rates(self, _rates):
        if self.__is_variable_rate:
            raise Exception("Cannot set rates of a variable rate poisson")
        raise Exception("Set the rate of a Poisson source using rate")

    @property
    def starts(self):
        return self.__data["starts"]

    @starts.setter
    def starts(self, _starts):
        if self.__is_variable_rate:
            raise Exception("Cannot set starts of a variable rate poisson")
        raise Exception("Set the start of a Poisson source using start")

    @property
    def durations(self):
        return self.__data["durations"]

    @durations.setter
    def durations(self, _durations):
        if self.__is_variable_rate:
            raise Exception("Cannot set durations of a variable rate poisson")
        raise Exception("Set the duration of a Poisson source using duration")

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self.__change_requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        self.__change_requires_mapping = False

    @overrides(SimplePopulationSettable.set_value)
    def set_value(self, key, value):
        SimplePopulationSettable.set_value(self, key, value)
        self.__change_requires_neuron_parameters_reload = True

    def _max_spikes_per_ts(self, machine_time_step):
        ts_per_second = MICROSECONDS_PER_SECOND / float(machine_time_step)
        if float(self.__max_rate) / ts_per_second < \
                SLOW_RATE_PER_TICK_CUTOFF:
            return 1

        # Experiments show at 1000 this result is typically higher than actual
        chance_ts = 1000
        max_spikes_per_ts = scipy.stats.poisson.ppf(
            1.0 - (1.0 / float(chance_ts)),
            float(self.__max_rate) / ts_per_second)
        return int(math.ceil(max_spikes_per_ts)) + 1.0

    def get_recording_sdram_usage(self, vertex_slice, machine_time_step):
        variable_sdram = self.__spike_recorder.get_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self._max_spikes_per_ts(machine_time_step))
        constant_sdram = ConstantSDRAM(
            variable_sdram.per_timestep * OVERFLOW_TIMESTEPS_FOR_SDRAM)
        return variable_sdram + constant_sdram

    @inject_items({
        "machine_time_step": "MachineTimeStep"
    })
    @overrides(
        ApplicationVertex.get_resources_used_by_atoms,
        additional_arguments={"machine_time_step"}
    )
    def get_resources_used_by_atoms(self, vertex_slice, machine_time_step):
        # pylint: disable=arguments-differ

        poisson_params_sz = self.get_rates_bytes(vertex_slice)
        other = ConstantSDRAM(
            SYSTEM_BYTES_REQUIREMENT +
            SpikeSourcePoissonMachineVertex.get_provenance_data_size(0) +
            poisson_params_sz +
            recording_utilities.get_recording_header_size(1) +
            recording_utilities.get_recording_data_constant_size(1) +
            profile_utils.get_profile_region_size(self.__n_profile_samples))

        recording = self.get_recording_sdram_usage(
            vertex_slice, machine_time_step)
        # build resources as i currently know
        container = ResourceContainer(
            sdram=recording + other,
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms()),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms()))

        return container

    @property
    def n_atoms(self):
        return self.__n_atoms

    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        # pylint: disable=too-many-arguments, arguments-differ
        self.__n_subvertices += 1
        return SpikeSourcePoissonMachineVertex(
            resources_required, self.__spike_recorder.record,
            constraints, label)

    @property
    def max_rate(self):
        return self.__max_rate

    @property
    def seed(self):
        return self.__seed

    @seed.setter
    def seed(self, seed):
        self.__seed = seed
        self.__kiss_seed = dict()
        self.__rng = None

    def get_rates_bytes(self, vertex_slice):
        """ Gets the size of the Poisson rates in bytes

        :param vertex_slice:
        """
        n_rates = sum(len(self.__data["rates"][i]) for i in range(
            vertex_slice.lo_atom, vertex_slice.hi_atom + 1))
        return ((vertex_slice.n_atoms * PARAMS_WORDS_PER_NEURON) +
                (n_rates * PARAMS_WORDS_PER_RATE)) * BYTES_PER_WORD

    def reserve_memory_regions(self, spec, placement, graph_mapper):
        """ Reserve memory regions for Poisson source parameters and output\
            buffer.

        :param spec: the data specification writer
        :param placement: the location this vertex resides on in the machine
        :param graph_mapper: the mapping between app and machine graphs
        :return: None
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=_REGIONS.SYSTEM_REGION.value,
            size=SIMULATION_N_BYTES,
            label='setup')

        # reserve poisson parameters and rates DSG region
        self._reserve_poisson_params_rates_region(
            placement, graph_mapper, spec)

        spec.reserve_memory_region(
            region=_REGIONS.SPIKE_HISTORY_REGION.value,
            size=recording_utilities.get_recording_header_size(1),
            label="Recording")

        profile_utils.reserve_profile_region(
            spec, _REGIONS.PROFILER_REGION.value, self.__n_profile_samples)

        placement.vertex.reserve_provenance_data_region(spec)

    def _reserve_poisson_params_rates_region(
                self, placement, graph_mapper, spec):
        """ Allocate space for the Poisson parameters and rates regions as\
            they can be reused for setters after an initial run

        :param placement: the location on machine for this vertex
        :param graph_mapper: the mapping between machine and application graphs
        :param spec: the DSG writer
        :return:  None
        """
        spec.reserve_memory_region(
            region=_REGIONS.POISSON_PARAMS_REGION.value,
            size=PARAMS_BASE_WORDS * 4, label="PoissonParams")
        spec.reserve_memory_region(
            region=_REGIONS.RATES_REGION.value,
            size=self.get_rates_bytes(graph_mapper.get_slice(
                placement.vertex)), label='PoissonRates')

    def _write_poisson_parameters(
            self, spec, graph, placement, routing_info,
            vertex_slice, machine_time_step, time_scale_factor):
        """ Generate Parameter data for Poisson spike sources

        :param spec: the data specification writer
        :param key: the routing key for this vertex
        :param vertex_slice:\
            the slice of atoms a machine vertex holds from its application\
            vertex
        :param machine_time_step: the time between timer tick updates.
        :param time_scale_factor:\
            the scaling between machine time step and real time
        """
        # pylint: disable=too-many-arguments, too-many-locals
        spec.comment("\nWriting Parameters for {} poisson sources:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(_REGIONS.POISSON_PARAMS_REGION.value)

        # Write Key info for this core:
        key = routing_info.get_first_key_from_pre_vertex(
            placement.vertex, constants.SPIKE_PARTITION_ID)
        spec.write_value(data=1 if key is not None else 0)
        spec.write_value(data=key if key is not None else 0)

        # Write the incoming mask if there is one
        in_edges = graph.get_edges_ending_at_vertex_with_partition_name(
            placement.vertex, constants.LIVE_POISSON_CONTROL_PARTITION_ID)
        if len(in_edges) > 1:
            raise ConfigurationException(
                "Only one control edge can end at a Poisson vertex")
        incoming_mask = 0
        if len(in_edges) == 1:
            in_edge = in_edges[0]

            # Get the mask of the incoming keys
            incoming_mask = \
                routing_info.get_routing_info_for_edge(in_edge).first_mask
            incoming_mask = ~incoming_mask & 0xFFFFFFFF
        spec.write_value(incoming_mask)

        # Write the offset value
        max_offset = (
            machine_time_step * time_scale_factor) // _MAX_OFFSET_DENOMINATOR
        spec.write_value(
            int(math.ceil(max_offset / self.__n_subvertices)) *
            self.__n_data_specs)
        self.__n_data_specs += 1

        if self.__max_spikes > 0:
            spikes_per_timestep = (
                self.__max_spikes /
                (MICROSECONDS_PER_SECOND // machine_time_step))
            # avoid a possible division by zero / small number (which may
            # result in a value that doesn't fit in a uint32) by only
            # setting time_between_spikes if spikes_per_timestep is > 1
            time_between_spikes = 1.0
            if spikes_per_timestep > 1:
                time_between_spikes = (
                    (machine_time_step * time_scale_factor) /
                    (spikes_per_timestep * 2.0))

            spec.write_value(data=int(time_between_spikes))
        else:

            # If the rate is 0 or less, set a "time between spikes" of 1
            # to ensure that some time is put between spikes in event
            # of a rate change later on
            spec.write_value(data=1)

        # Write the number of seconds per timestep (unsigned long fract)
        spec.write_value(
            data=float(machine_time_step) / MICROSECONDS_PER_SECOND,
            data_type=DataType.U032)

        # Write the number of timesteps per second (integer)
        spec.write_value(
            data=int(MICROSECONDS_PER_SECOND / float(machine_time_step)))

        # Write the slow-rate-per-tick-cutoff (accum)
        spec.write_value(
            data=SLOW_RATE_PER_TICK_CUTOFF, data_type=DataType.S1615)

        # Write the fast-rate-per-tick-cutoff (accum)
        spec.write_value(
            data=FAST_RATE_PER_TICK_CUTOFF, data_type=DataType.S1615)

        # Write the lo_atom ID
        spec.write_value(data=vertex_slice.lo_atom)

        # Write the number of sources
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the random seed (4 words), generated randomly!
        kiss_key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        if kiss_key not in self.__kiss_seed:
            if self.__rng is None:
                self.__rng = numpy.random.RandomState(self.__seed)
            self.__kiss_seed[kiss_key] = validate_mars_kiss_64_seed([
                self.__rng.randint(-0x80000000, 0x7FFFFFFF) + 0x80000000
                for _ in range(4)])
        for value in self.__kiss_seed[kiss_key]:
            spec.write_value(data=value)

    def _write_poisson_rates(self, spec, vertex_slice, machine_time_step,
                             first_machine_time_step):
        """ Generate Rate data for Poisson spike sources

        :param spec: the data specification writer
        :param vertex_slice:\
            the slice of atoms a machine vertex holds from its application\
            vertex
        :param machine_time_step: the time between timer tick updates.
        :param first_machine_time_step:\
            First machine time step to start from the correct index
        """
        spec.comment("\nWriting Rates for {} poisson sources:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(_REGIONS.RATES_REGION.value)

        # Extract the data on which to work and convert to appropriate form
        starts = numpy.array(list(_flatten(
            self.__data["starts"][vertex_slice.as_slice]))).astype("float")
        durations = numpy.array(list(_flatten(
            self.__data["durations"][vertex_slice.as_slice]))).astype("float")
        local_rates = self.__data["rates"][vertex_slice.as_slice]
        n_rates = numpy.array([len(r) for r in local_rates])
        splits = numpy.cumsum(n_rates)
        rates = numpy.array(list(_flatten(local_rates)))
        time_to_spike = numpy.array(list(_flatten(
            self.__data["time_to_spike"][vertex_slice.as_slice]))).astype("u4")
        rate_change = self.__rate_change[vertex_slice.as_slice]

        # Convert start times to start time steps
        starts_scaled = self._convert_ms_to_n_timesteps(
            starts, machine_time_step)

        # Convert durations to end time steps, using the maximum for "None"
        # duration (which means "until the end")
        no_duration = numpy.isnan(durations)
        durations_filtered = numpy.where(no_duration, 0, durations)
        ends_scaled = self._convert_ms_to_n_timesteps(
            durations_filtered, machine_time_step) + starts_scaled
        ends_scaled = numpy.where(no_duration, _MAX_TIMESTEP, ends_scaled)

        # Work out the timestep at which the next rate activates, using
        # the maximum value at the end (meaning there is no "next")
        starts_split = numpy.array_split(starts_scaled, splits)
        next_scaled = numpy.concatenate([numpy.append(s[1:], _MAX_TIMESTEP)
                                         for s in starts_split[:-1]])

        # Compute the spikes per tick for each rate for each atom
        spikes_per_tick = rates * (float(machine_time_step) /
                                   MICROSECONDS_PER_SECOND)

        # Determine the properties of the sources
        is_fast_source = spikes_per_tick >= SLOW_RATE_PER_TICK_CUTOFF
        is_faster_source = spikes_per_tick >= FAST_RATE_PER_TICK_CUTOFF
        not_zero = spikes_per_tick > 0
        # pylint: disable=assignment-from-no-return
        is_slow_source = numpy.logical_not(is_fast_source)

        # Compute the e^-(spikes_per_tick) for fast sources to allow fast
        # computation of the Poisson distribution to get the number of
        # spikes per timestep
        exp_minus_lambda = DataType.U032.encode_as_numpy_int_array(
            numpy.where(is_fast_source, numpy.exp(-1.0 * spikes_per_tick), 0))

        # Compute sqrt(lambda) for "faster" sources to allow Gaussian
        # approximation of the Poisson distribution to get the number of
        # spikes per timestep
        sqrt_lambda = DataType.S1615.encode_as_numpy_int_array(
            numpy.where(is_faster_source, numpy.sqrt(spikes_per_tick), 0))

        # Compute the inter-spike-interval for slow sources to get the
        # average number of timesteps between spikes
        isi_val = numpy.where(
            not_zero & is_slow_source,
            (1.0 / spikes_per_tick).astype(int), 0).astype("uint32")

        # Reuse the time-to-spike read from the machine (if has been run)
        # or don't if the rate has since been changed
        time_to_spike_split = numpy.array_split(time_to_spike, splits)
        time_to_spike = numpy.concatenate(
            [t if rate_change[i] else numpy.repeat(0, len(t))
             for i, t in enumerate(time_to_spike_split[:-1])])

        # Turn the fast source booleans into uint32
        is_fast_source = is_fast_source.astype("uint32")

        # Group together the rate data for the core by rate
        core_data = numpy.dstack((
            starts_scaled, ends_scaled, next_scaled, is_fast_source,
            exp_minus_lambda, sqrt_lambda, isi_val, time_to_spike))[0]

        # Group data by neuron id
        core_data_split = numpy.array_split(core_data, splits)

        # Work out the index where the core should start based on the given
        # first timestep
        ends_scaled_split = numpy.array_split(ends_scaled, splits)
        indices = [numpy.argmax(e > first_machine_time_step)
                   for e in ends_scaled_split[:-1]]

        # Build the final data for this core, and write it
        final_data = numpy.concatenate([
            numpy.concatenate(([len(d), indices[i]], numpy.concatenate(d)))
            for i, d in enumerate(core_data_split[:-1])])
        spec.write_array(final_data)

    @staticmethod
    def _convert_ms_to_n_timesteps(value, machine_time_step):
        return numpy.round(
            value * (MICROSECONDS_PER_MILLISECOND /
                     float(machine_time_step))).astype("uint32")

    @staticmethod
    def _convert_n_timesteps_to_ms(value, machine_time_step):
        return (
            value / (MICROSECONDS_PER_MILLISECOND / float(machine_time_step)))

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self.__spike_recorder.record

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported for "
                           "SpikeSourcePoisson so being ignored")
        if indexes is not None:
            logger.warning("indexes not supported for "
                           "SpikeSourcePoisson so being ignored")
        if new_state and not self.__spike_recorder.record:
            self.__change_requires_mapping = True
        self.__spike_recorder.record = new_state

    @overrides(AbstractSpikeRecordable.get_spikes_sampling_interval)
    def get_spikes_sampling_interval(self):
        return globals_variables.get_simulator().machine_time_step

    @staticmethod
    def get_dtcm_usage_for_atoms():
        return 0

    @staticmethod
    def get_cpu_usage_for_atoms():
        return 0

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "routing_info": "MemoryRoutingInfos",
        "graph": "MemoryMachineGraph",
        "first_machine_time_step": "FirstMachineTimeStep"})
    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "routing_info", "graph", "first_machine_time_step"})
    def regenerate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, routing_info, graph, first_machine_time_step):
        # pylint: disable=too-many-arguments, arguments-differ

        # reserve the neuron parameters data region
        self._reserve_poisson_params_rates_region(
            placement, graph_mapper, spec)

        # write parameters
        vertex_slice = graph_mapper.get_slice(placement.vertex)
        self._write_poisson_parameters(
            spec=spec, graph=graph, placement=placement,
            routing_info=routing_info,
            vertex_slice=vertex_slice,
            machine_time_step=machine_time_step,
            time_scale_factor=time_scale_factor)

        # write rates
        self._write_poisson_rates(spec, vertex_slice, machine_time_step,
                                  first_machine_time_step)

        # end spec
        spec.end_specification()

    @inject_items({"first_machine_time_step": "FirstMachineTimeStep"})
    @overrides(AbstractRewritesDataSpecification
               .requires_memory_regions_to_be_reloaded,
               additional_arguments={"first_machine_time_step"})
    def requires_memory_regions_to_be_reloaded(self, first_machine_time_step):
        # pylint: disable=arguments-differ
        return (self.__change_requires_neuron_parameters_reload or
                first_machine_time_step == 0)

    @overrides(AbstractRewritesDataSpecification.mark_regions_reloaded)
    def mark_regions_reloaded(self):
        self.__change_requires_neuron_parameters_reload = False

    @overrides(AbstractReadParametersBeforeSet.read_parameters_from_machine)
    def read_parameters_from_machine(
            self, transceiver, placement, vertex_slice):

        # locate SDRAM address where parameters are stored
        poisson_params = \
            helpful_functions.locate_memory_region_for_placement(
                placement, _REGIONS.POISSON_PARAMS_REGION.value, transceiver)
        seed_array = transceiver.read_memory(
            placement.x, placement.y, poisson_params + SEED_OFFSET_BYTES,
            SEED_SIZE_BYTES)
        kiss_key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        self.__kiss_seed[kiss_key] = struct.unpack_from("<4I", seed_array)

        # locate SDRAM address where the rates are stored
        poisson_rate_region_sdram_address = \
            helpful_functions.locate_memory_region_for_placement(
                placement, _REGIONS.RATES_REGION.value, transceiver)

        # get size of poisson params
        size_of_region = self.get_rates_bytes(vertex_slice)

        # get data from the machine
        byte_array = transceiver.read_memory(
            placement.x, placement.y,
            poisson_rate_region_sdram_address, size_of_region)

        # For each atom, read the number of rates and the rate parameters
        offset = 0
        for i in range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1):
            n_values = struct.unpack_from("<I", byte_array, offset)[0]
            offset += 4

            # Skip reading the index, as it will be recalculated on data write
            offset += 4

            (_start, _end, _next, is_fast_source, exp_minus_lambda,
             sqrt_lambda, isi, time_to_next_spike) = _PoissonStruct.read_data(
                 byte_array, offset, n_values)
            offset += _PoissonStruct.get_size_in_whole_words(n_values) * 4

            # Work out the spikes per tick depending on if the source is
            # slow (isi), fast (exp) or faster (sqrt)
            is_fast_source = is_fast_source == 1.0
            spikes_per_tick = numpy.zeros(len(is_fast_source), dtype="float")
            spikes_per_tick[is_fast_source] = numpy.log(
                exp_minus_lambda[is_fast_source]) * -1.0
            is_faster_source = sqrt_lambda > 0
            # pylint: disable=assignment-from-no-return
            spikes_per_tick[is_faster_source] = numpy.square(
                sqrt_lambda[is_faster_source])
            slow_elements = isi > 0
            spikes_per_tick[slow_elements] = 1.0 / isi[slow_elements]

            # Convert spikes per tick to rates
            self.__data["rates"].set_value_by_id(
                i,
                spikes_per_tick *
                (MICROSECONDS_PER_SECOND / float(self.__machine_time_step)))

            # Store the updated time until next spike so that it can be
            # rewritten when the parameters are loaded
            self.__data["time_to_spike"].set_value_by_id(
                i, time_to_next_spike)

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "routing_info": "MemoryRoutingInfos",
        "data_n_time_steps": "DataNTimeSteps",
        "graph": "MemoryMachineGraph",
        "first_machine_time_step": "FirstMachineTimeStep"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "routing_info", "data_n_time_steps", "graph",
            "first_machine_time_step"
        }
    )
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, routing_info, data_n_time_steps, graph,
            first_machine_time_step):
        # pylint: disable=too-many-arguments, arguments-differ
        self.__machine_time_step = machine_time_step
        vertex = placement.vertex
        vertex_slice = graph_mapper.get_slice(vertex)

        spec.comment("\n*** Spec for SpikeSourcePoisson Instance ***\n\n")

        # Reserve SDRAM space for memory areas:
        self.reserve_memory_regions(spec, placement, graph_mapper)

        # write setup data
        spec.switch_write_focus(_REGIONS.SYSTEM_REGION.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name(), machine_time_step,
            time_scale_factor))

        # write recording data
        spec.switch_write_focus(_REGIONS.SPIKE_HISTORY_REGION.value)
        sdram = self.get_recording_sdram_usage(
            vertex_slice, machine_time_step)
        recorded_region_sizes = [sdram.get_total_sdram(data_n_time_steps)]
        spec.write_array(recording_utilities.get_recording_header_array(
            recorded_region_sizes))

        # write parameters
        self._write_poisson_parameters(
            spec, graph, placement, routing_info, vertex_slice,
            machine_time_step, time_scale_factor)

        # write rates
        self._write_poisson_rates(spec, vertex_slice, machine_time_step,
                                  first_machine_time_step)

        # write profile data
        profile_utils.write_profile_region_data(
            spec, _REGIONS.PROFILER_REGION.value,
            self.__n_profile_samples)

        # End-of-Spec:
        spec.end_specification()

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return "spike_source_poisson.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(
            self, placements, graph_mapper, buffer_manager, machine_time_step):
        return self.__spike_recorder.get_spikes(
            self.label, buffer_manager,
            SpikeSourcePoissonVertex.SPIKE_RECORDING_REGION_ID,
            placements, graph_mapper, self, machine_time_step)

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [ContiguousKeyRangeContraint()]

    @overrides(AbstractSpikeRecordable.clear_spike_recording)
    def clear_spike_recording(self, buffer_manager, placements, graph_mapper):
        machine_vertices = graph_mapper.get_machine_vertices(self)
        for machine_vertex in machine_vertices:
            placement = placements.get_placement_of_vertex(machine_vertex)
            buffer_manager.clear_recorded_data(
                placement.x, placement.y, placement.p,
                SpikeSourcePoissonVertex.SPIKE_RECORDING_REGION_ID)

    def describe(self):
        """ Return a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template\
        together with an associated template engine\
        (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template context\
        will be returned.
        """

        parameters = dict()
        for parameter_name in self.__model.default_parameters:
            parameters[parameter_name] = self.get_value(parameter_name)

        context = {
            "name": self.__model_name,
            "default_parameters": self.__model.default_parameters,
            "default_initial_values": self.__model.default_parameters,
            "parameters": parameters,
        }
        return context
