import scipy.stats
import logging
import math
import random
import numpy
from enum import Enum

from spinn_utilities.overrides import overrides

from data_specification.enums import DataType

from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.utilities.ranged\
    import SpynnakerRangeDictionary, SpynnakerRangedList
import struct
from pacman.model.constraints.key_allocator_constraints \
    import ContiguousKeyRangeContraint
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.resources import CPUCyclesPerTickResource, DTCMResource
from pacman.model.resources import ResourceContainer, SDRAMResource

from spinn_front_end_common.abstract_models import \
    AbstractChangableAfterRun, AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.abstract_models \
    import AbstractGeneratesDataSpecification, AbstractHasAssociatedBinary
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.interface.buffer_management \
    import recording_utilities
from spinn_front_end_common.utilities.constants \
    import SYSTEM_BYTES_REQUIREMENT, SARK_PER_MALLOC_SDRAM_USAGE
from spinn_front_end_common.abstract_models \
    import AbstractRewritesDataSpecification
from spinn_front_end_common.abstract_models.impl\
    import ProvidesKeyToAtomMappingImpl
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.utilities.exceptions import ConfigurationException

from spynnaker.pyNN.models.common import AbstractSpikeRecordable
from spynnaker.pyNN.models.common import MultiSpikeRecorder
from .spike_source_poisson_machine_vertex \
    import SpikeSourcePoissonMachineVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.abstract_models\
    import AbstractReadParametersBeforeSet
from spynnaker.pyNN.models.common.simple_population_settable \
    import SimplePopulationSettable

logger = logging.getLogger(__name__)

# bool has_key; uint32_t key; uint32_t set_rate_neuron_id_mask;
# uint32_t random_backoff_us; uint32_t time_between_spikes;
# UFRACT seconds_per_tick; REAL ticks_per_second;
# REAL slow_rate_per_tick_cutoff; uint32_t first_source_id;
# uint32_t n_spike_sources; mars_kiss64_seed_t (uint[4]) spike_source_seed;
PARAMS_BASE_WORDS = 14

# start_scaled, end_scaled, next_scaled, is_fast_source, exp_minus_lambda,
# isi_val, time_to_spike
PARAMS_WORDS_PER_NEURON = 7

START_OF_POISSON_GENERATOR_PARAMETERS = PARAMS_BASE_WORDS * 4
MICROSECONDS_PER_SECOND = 1000000.0
MICROSECONDS_PER_MILLISECOND = 1000.0
SLOW_RATE_PER_TICK_CUTOFF = 1.0
_REGIONS = SpikeSourcePoissonMachineVertex.POISSON_SPIKE_SOURCE_REGIONS


class _PoissonStruct(Enum):
    """ The Poisson Data Structure
    """

    START_SCALED = (0, DataType.UINT32)
    END_SCALED = (1, DataType.UINT32)
    IS_FAST_SOURCE = (2, DataType.UINT32)
    EXP_MINUS_LAMDA = (3, DataType.U032)
    ISI_VAL = (4, DataType.S1615)
    TIME_TO_SPIKE = (5, DataType.S1615)

    def __new__(cls, value, data_type, doc=""):
        # pylint: disable=protected-access
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        obj.__doc__ = doc
        return obj

    def __init__(self, value, data_type, doc=""):
        self._value_ = value
        self._data_type = data_type
        self.__doc__ = doc

    def data_type(self):
        return self._data_type


def _flatten(alist):
    for item in alist:
        if hasattr(item, "__iter__"):
            for subitem in _flatten(item):
                yield subitem
        else:
            yield item


class SpikeSourcePoissonBase(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary, AbstractSpikeRecordable,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractChangableAfterRun, AbstractReadParametersBeforeSet,
        AbstractRewritesDataSpecification, SimplePopulationSettable,
        ProvidesKeyToAtomMappingImpl):
    """ A Poisson-distributed Spike source object
    """

    _N_POPULATION_RECORDING_REGIONS = 1
    _DEFAULT_MALLOCS_USED = 2
    SPIKE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons, model_name, constraints, label,
            max_atoms_per_core, seed=None, rate=None, start=None,
            duration=None, rates=None, starts=None, durations=None,
            max_rate=None):
        # pylint: disable=too-many-arguments
        super(SpikeSourcePoissonBase, self).__init__(
            label, constraints, max_atoms_per_core)

        config = globals_variables.get_simulator().config

        # atoms params
        self._n_atoms = n_neurons
        self._model_name = model_name
        self._seed = seed

        # check for changes parameters
        self._change_requires_mapping = True
        self._change_requires_neuron_parameters_reload = False

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

        self._data = SpynnakerRangeDictionary(n_neurons)
        self._data["rates"] = SpynnakerRangedList(
            n_neurons, rates,
            use_list_as_value=not hasattr(rates[0], "__len__"))
        self._data["starts"] = SpynnakerRangedList(
            n_neurons, starts,
            use_list_as_value=not hasattr(starts[0], "__len__"))
        self._data["durations"] = SpynnakerRangedList(
            n_neurons, durations,
            use_list_as_value=not hasattr(durations[0], "__len__"))
        self._data["time_to_spike"] = SpynnakerRangedList(
            n_neurons, time_to_spike,
            use_list_as_value=not hasattr(time_to_spike[0], "__len__"))
        self._rng = numpy.random.RandomState(seed)
        self._machine_time_step = None

        # Prepare for recording, and to get spikes
        self._spike_recorder = MultiSpikeRecorder()
        self._time_between_requests = config.getint(
            "Buffers", "time_between_requests")
        self._receive_buffer_host = config.get(
            "Buffers", "receive_buffer_host")
        self._receive_buffer_port = helpful_functions.read_config_int(
            config, "Buffers", "receive_buffer_port")
        self._minimum_buffer_sdram = config.getint(
            "Buffers", "minimum_buffer_sdram")
        self._using_auto_pause_and_resume = config.getboolean(
            "Buffers", "use_auto_pause_and_resume")

        spike_buffer_max_size = 0
        self._buffer_size_before_receive = None
        if config.getboolean("Buffers", "enable_buffered_recording"):
            spike_buffer_max_size = config.getint(
                "Buffers", "spike_buffer_size")
            self._buffer_size_before_receive = config.getint(
                "Buffers", "buffer_size_before_receive")
        self._maximum_sdram_for_buffering = [spike_buffer_max_size]

        # A count of the number of poisson vertices, to work out the random
        # back off range
        self._n_poisson_machine_vertices = 0

        all_rates = list(_flatten(self._data["rates"]))
        self._max_rate = max_rate
        if len(all_rates):
            self._max_rate = numpy.amax(all_rates)
        elif max_rate is None:
            self._max_rate = 0

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self._change_requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        self._change_requires_mapping = False

    @overrides(SimplePopulationSettable.set_value)
    def set_value(self, key, value):
        SimplePopulationSettable.set_value(self, key, value)
        self._change_requires_neuron_parameters_reload = True

    def _max_spikes_per_ts(self, machine_time_step):
        if self._max_rate == 0:
            return 0
        ts_per_second = MICROSECONDS_PER_SECOND / float(machine_time_step)
        max_spikes_per_ts = scipy.stats.poisson.ppf(
            0.999, float(self._max_rate) / ts_per_second)
        return int(math.ceil(max_spikes_per_ts)) + 1.0

    @inject_items({
        "n_machine_time_steps": "TotalMachineTimeSteps",
        "machine_time_step": "MachineTimeStep"
    })
    @overrides(
        ApplicationVertex.get_resources_used_by_atoms,
        additional_arguments={"n_machine_time_steps", "machine_time_step"}
    )
    def get_resources_used_by_atoms(
            self, vertex_slice, n_machine_time_steps, machine_time_step):
        # pylint: disable=arguments-differ

        # build resources as i currently know
        container = ResourceContainer(
            sdram=SDRAMResource(self.get_sdram_usage_for_atoms(vertex_slice)),
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms()),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms()))

        recording_sizes = recording_utilities.get_recording_region_sizes(
            [self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._max_spikes_per_ts(
                    machine_time_step),
                self._N_POPULATION_RECORDING_REGIONS) * n_machine_time_steps],
            self._minimum_buffer_sdram,
            self._maximum_sdram_for_buffering,
            self._using_auto_pause_and_resume)
        container.extend(recording_utilities.get_recording_resources(
            recording_sizes, self._receive_buffer_host,
            self._receive_buffer_port))
        return container

    @property
    def n_atoms(self):
        return self._n_atoms

    @inject_items({
        "n_machine_time_steps": "TotalMachineTimeSteps",
        "machine_time_step": "MachineTimeStep"
    })
    @overrides(
        ApplicationVertex.create_machine_vertex,
        additional_arguments={"n_machine_time_steps", "machine_time_step"}
    )
    def create_machine_vertex(
            self, vertex_slice, resources_required, n_machine_time_steps,
            machine_time_step, label=None, constraints=None):
        # pylint: disable=too-many-arguments, arguments-differ
        self._n_poisson_machine_vertices += 1
        buffered_sdram_per_timestep =\
            self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._max_spikes_per_ts(
                    machine_time_step), 1)
        minimum_buffer_sdram = recording_utilities.get_minimum_buffer_sdram(
            [buffered_sdram_per_timestep * n_machine_time_steps],
            self._minimum_buffer_sdram)
        return SpikeSourcePoissonMachineVertex(
            resources_required, self._spike_recorder.record,
            minimum_buffer_sdram[0], buffered_sdram_per_timestep,
            constraints, label)

    @property
    def seed(self):
        return self._seed

    @seed.setter
    def seed(self, seed):
        self._seed = seed
        self._rng = numpy.random.RandomState(seed)

    def get_rates_bytes(self, vertex_slice):
        """ Gets the size of the Poisson rates in bytes

        :param vertex_slice:
        """
        n_rates = sum(len(self._data["rates"][i]) for i in range(
            vertex_slice.lo_atom, vertex_slice.hi_atom + 1))
        return (vertex_slice.n_atoms + (n_rates * PARAMS_WORDS_PER_NEURON)) * 4

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
            size=SYSTEM_BYTES_REQUIREMENT,
            label='setup')

        # reserve poisson parameters and rates DSG region
        self._reserve_poisson_params_rates_region(
            placement, graph_mapper, spec)

        spec.reserve_memory_region(
            region=_REGIONS.SPIKE_HISTORY_REGION.value,
            size=recording_utilities.get_recording_header_size(1),
            label="Recording")
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

        # Write the random back off value
        spec.write_value(random.randint(0, min(
            self._n_poisson_machine_vertices,
            MICROSECONDS_PER_SECOND // machine_time_step)))

        # Write the number of microseconds between sending spikes
        all_rates = numpy.fromiter(_flatten(self._data["rates"]), numpy.float)
        total_mean_rate = numpy.sum(all_rates)
        if total_mean_rate > 0:
            max_spikes = numpy.sum(scipy.stats.poisson.ppf(
                0.999, all_rates))
            spikes_per_timestep = (
                max_spikes / (MICROSECONDS_PER_SECOND // machine_time_step))
            # avoid a possible division by zero / small number (which may
            # result in a value that doesn't fit in a uint32) by only
            # setting time_between_spikes if spikes_per_timestep is > 1
            time_between_spikes = 0.0
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

        # Write the number of timesteps per second (accum)
        spec.write_value(
            data=MICROSECONDS_PER_SECOND / float(machine_time_step),
            data_type=DataType.S1615)

        # Write the slow-rate-per-tick-cutoff (accum)
        spec.write_value(
            data=SLOW_RATE_PER_TICK_CUTOFF, data_type=DataType.S1615)

        # Write the lo_atom ID
        spec.write_value(data=vertex_slice.lo_atom)

        # Write the number of sources
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the random seed (4 words), generated randomly!
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))

    def _write_poisson_rates(self, spec, vertex_slice, machine_time_step):
        """ Generate Rate data for Poisson spike sources

        :param spec: the data specification writer
        :param vertex_slice:\
            the slice of atoms a machine vertex holds from its application\
            vertex
        :param machine_time_step: the time between timer tick updates.
        """
        spec.comment("\nWriting Rates for {} poisson sources:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(_REGIONS.RATES_REGION.value)

        # For each source, write the number of rates, followed by the rate data
        for i in range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1):
            spec.write_value(len(self._data["rates"][i]))

            # Convert start times to start time steps
            starts = self._data["starts"][i].astype("float")
            starts_scaled = self._convert_ms_to_n_timesteps(
                starts, machine_time_step)

            # Convert durations to end time steps
            durations = self._data["durations"][i].astype("float")
            ends_scaled = numpy.zeros(len(durations), dtype="uint32")
            none_positions = numpy.isnan(durations)
            positions = numpy.invert(none_positions)
            ends_scaled[none_positions] = 0xFFFFFFFF
            ends_scaled[positions] = self._convert_ms_to_n_timesteps(
                starts[positions] + durations[positions], machine_time_step)

            # Convert start times to next steps, adding max uint to end
            next_scaled = numpy.append(starts_scaled[1:], 0xFFFFFFFF)

            # Compute the spikes per tick for each atom
            rates = self._data["rates"][i].astype("float")
            spikes_per_tick = (
                rates * (float(machine_time_step) / MICROSECONDS_PER_SECOND))

            # Determine which sources are fast and which are slow
            is_fast_source = spikes_per_tick > SLOW_RATE_PER_TICK_CUTOFF

            # Compute the e^-(spikes_per_tick) for fast sources to allow fast
            # computation of the Poisson distribution to get the number of
            # spikes per timestep
            exp_minus_lambda = numpy.zeros(len(spikes_per_tick), dtype="float")
            exp_minus_lambda[is_fast_source] = numpy.exp(
                -1.0 * spikes_per_tick[is_fast_source])
            # Compute the inter-spike-interval for slow sources to get the
            # average number of timesteps between spikes
            isi_val = numpy.zeros(len(spikes_per_tick), dtype="float")
            elements = numpy.logical_not(
                is_fast_source) & (spikes_per_tick > 0)
            isi_val[elements] = 1.0 / spikes_per_tick[elements]

            # Get the time to spike value
            time_to_spike = self._data["time_to_spike"][i]

            # Merge the arrays as parameters per atom
            data = numpy.dstack((
                starts_scaled.astype("uint32"),
                ends_scaled.astype("uint32"),
                next_scaled.astype("uint32"),
                is_fast_source.astype("uint32"),
                (exp_minus_lambda * (2 ** 32)).astype("uint32"),
                (isi_val * (2 ** 15)).astype("uint32"),
                (time_to_spike * (2 ** 15)).astype("uint32")
            ))[0].flatten()
            spec.write_array(data)

    @staticmethod
    def _convert_ms_to_n_timesteps(value, machine_time_step):
        return numpy.round(
            value * (MICROSECONDS_PER_MILLISECOND / float(machine_time_step)))

    @staticmethod
    def _convert_n_timesteps_to_ms(value, machine_time_step):
        return (
            value / (MICROSECONDS_PER_MILLISECOND / float(machine_time_step)))

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self._spike_recorder.record

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported for "
                           "SpikeSourcePoisson so being ignored")
        if indexes is not None:
            logger.warning("indexes not supported for "
                           "SpikeSourcePoisson so being ignored")
        self._spike_recorder.record = new_state

    @overrides(AbstractSpikeRecordable.get_spikes_sampling_interval)
    def get_spikes_sampling_interval(self):
        return globals_variables.get_simulator().machine_time_step

    def get_sdram_usage_for_atoms(self, vertex_slice):
        """ Calculate total SDRAM usage for a set of atoms

        :param vertex_slice: the atoms to calculate SDRAM usage for
        :return: SDRAM usage as a number of bytes
        """
        poisson_params_sz = self.get_rates_bytes(vertex_slice)
        total_size = (
            SYSTEM_BYTES_REQUIREMENT + PARAMS_BASE_WORDS +
            SpikeSourcePoissonMachineVertex.get_provenance_data_size(0) +
            poisson_params_sz)
        total_size += self._get_number_of_mallocs_used_by_dsg() * \
            SARK_PER_MALLOC_SDRAM_USAGE
        return total_size

    def _get_number_of_mallocs_used_by_dsg(self):
        """ Work out how many allocation requests are required by the tools

        :return: the number of allocation requests
        """
        standard_mallocs = self._DEFAULT_MALLOCS_USED
        if self._spike_recorder.record:
            standard_mallocs += 1
        return standard_mallocs

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
        "graph": "MemoryMachineGraph"})
    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "routing_info", "graph"})
    def regenerate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, routing_info, graph):
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
        self._write_poisson_rates(spec, vertex_slice, machine_time_step)

        # end spec
        spec.end_specification()

    @overrides(AbstractRewritesDataSpecification
               .requires_memory_regions_to_be_reloaded)
    def requires_memory_regions_to_be_reloaded(self):
        return self._change_requires_neuron_parameters_reload

    @overrides(AbstractRewritesDataSpecification.mark_regions_reloaded)
    def mark_regions_reloaded(self):
        self._change_requires_neuron_parameters_reload = False

    @overrides(AbstractReadParametersBeforeSet.read_parameters_from_machine)
    def read_parameters_from_machine(
            self, transceiver, placement, vertex_slice):

        # locate SDRAM address to where the neuron parameters are stored
        poisson_rate_region_sdram_address = \
            helpful_functions.locate_memory_region_for_placement(
                placement, _REGIONS.RATES_REGION.value, transceiver)

        # get size of poisson params
        size_of_region = self.get_rates_bytes(vertex_slice)

        # get data from the machine
        byte_array = transceiver.read_memory(
            placement.x, placement.y,
            poisson_rate_region_sdram_address, size_of_region)

        # Convert the data to parameter values
        param_types = [item.data_type() for item in _PoissonStruct]

        # For each atom, read the number of rates and the rate parameters
        offset = 0
        for i in range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1):
            n_values = struct.unpack_from("<I", byte_array, offset)
            offset += 4

            values, offset = utility_calls.translate_parameters(
                param_types, byte_array, offset, n_values)

            # Work out the spikes per tick depending on if the source is slow
            # or fast
            is_fast_source = values[3] == 1.0
            spikes_per_tick = numpy.zeros(len(is_fast_source), dtype="float")
            spikes_per_tick[is_fast_source] = numpy.log(
                values[3][is_fast_source]) * -1.0
            slow_elements = values[5] > 0
            spikes_per_tick[slow_elements] = 1.0 / values[5][slow_elements]

            # Convert spikes per tick to rates
            self._data["rates"][i] = (
                spikes_per_tick *
                (MICROSECONDS_PER_SECOND / float(self._machine_time_step)))

            # Store the updated time until next spike so that it can be
            # rewritten when the parameters are loaded
            self._data["time_to_spike"][i] = values[6]

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "routing_info": "MemoryRoutingInfos",
        "tags": "MemoryTags",
        "n_machine_time_steps": "TotalMachineTimeSteps",
        "graph": "MemoryMachineGraph"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "routing_info", "tags", "n_machine_time_steps", "graph"
        }
    )
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, routing_info, tags, n_machine_time_steps, graph):
        # pylint: disable=too-many-arguments, arguments-differ
        self._machine_time_step = machine_time_step
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
        ip_tags = tags.get_ip_tags_for_vertex(vertex)
        spec.switch_write_focus(_REGIONS.SPIKE_HISTORY_REGION.value)
        recorded_region_sizes = recording_utilities.get_recorded_region_sizes(
            [self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._max_spikes_per_ts(
                    machine_time_step),
                n_machine_time_steps)],
            self._maximum_sdram_for_buffering)
        spec.write_array(recording_utilities.get_recording_header_array(
            recorded_region_sizes, self._time_between_requests,
            self._buffer_size_before_receive, ip_tags))

        # write parameters
        self._write_poisson_parameters(
            spec, graph, placement, routing_info, vertex_slice,
            machine_time_step, time_scale_factor)

        # write rates
        self._write_poisson_rates(spec, vertex_slice, machine_time_step)

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
        return self._spike_recorder.get_spikes(
            self.label, buffer_manager,
            SpikeSourcePoissonBase.SPIKE_RECORDING_REGION_ID,
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
                SpikeSourcePoissonBase.SPIKE_RECORDING_REGION_ID)

    def describe(self):
        """ Return a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template\
        together with an associated template engine\
        (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template context\
        will be returned.
        """

        parameters = dict()
        for parameter_name in self.default_parameters:
            parameters[parameter_name] = self.get_value(parameter_name)

        context = {
            "name": self._model_name,
            "default_parameters": self.default_parameters,
            "default_initial_values": self.default_parameters,
            "parameters": parameters,
        }
        return context
