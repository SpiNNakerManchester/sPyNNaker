import scipy.stats
import logging
import math
import random
import numpy
from enum import Enum

from spinn_utilities.overrides import overrides

from data_specification.enums import DataType

from pacman.executor.injection_decorator import inject_items
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

# start_scaled, end_scaled, is_fast_source, exp_minus_lambda, isi_val,
# time_to_spike
PARAMS_WORDS_PER_NEURON = 6

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


class SpikeSourcePoisson(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary, AbstractSpikeRecordable,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractChangableAfterRun, AbstractReadParametersBeforeSet,
        AbstractRewritesDataSpecification, SimplePopulationSettable,
        ProvidesKeyToAtomMappingImpl):
    """ A Poisson Spike source object
    """

    _N_POPULATION_RECORDING_REGIONS = 1
    _DEFAULT_MALLOCS_USED = 2
    SPIKE_RECORDING_REGION_ID = 0

    # Technically, this is ~2900 in terms of DTCM, but is timescale dependent
    # in terms of CPU (2900 at 10 times slow down is fine, but not at
    # real-time)
    DEFAULT_MAX_ATOMS_PER_CORE = 32
    _model_based_max_atoms_per_core = DEFAULT_MAX_ATOMS_PER_CORE

    # A count of the number of poisson vertices, to work out the random
    # back off range
    _n_poisson_machine_vertices = 0

    # parameters expected by PyNN
    default_parameters = {
        'start': 0.0, 'duration': None, 'rate': 1.0}

    # parameters expected by spinnaker
    non_pynn_default_parameters = {
        'constraints': None, 'seed': None, 'label': None}

    def __init__(
            self, n_neurons,
            constraints=non_pynn_default_parameters['constraints'],
            label=non_pynn_default_parameters['label'],
            rate=default_parameters['rate'],
            start=default_parameters['start'],
            duration=default_parameters['duration'],
            seed=non_pynn_default_parameters['seed']):
        # pylint: disable=too-many-arguments
        super(SpikeSourcePoisson, self).__init__(
            label, constraints, self._model_based_max_atoms_per_core)

        config = globals_variables.get_simulator().config

        # atoms params
        self._n_atoms = n_neurons
        self._model_name = "SpikeSourcePoisson"
        self._seed = None

        # check for changes parameters
        self._change_requires_mapping = True
        self._change_requires_neuron_parameters_reload = False

        # Store the parameters
        self._rate = utility_calls.convert_param_to_numpy(rate, n_neurons)
        self._start = utility_calls.convert_param_to_numpy(start, n_neurons)
        self._duration = utility_calls.convert_param_to_numpy(
            duration, n_neurons)
        self._time_to_spike = utility_calls.convert_param_to_numpy(
            0, n_neurons)
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

    def _max_spikes_per_ts(
            self, vertex_slice, n_machine_time_steps, machine_time_step):
        max_rate = numpy.amax(self._rate[vertex_slice.as_slice])
        if max_rate == 0:
            return 0
        ts_per_second = MICROSECONDS_PER_SECOND / float(machine_time_step)
        max_spikes_per_ts = scipy.stats.poisson.ppf(
            1.0 - (1.0 / float(n_machine_time_steps)),
            float(max_rate) / ts_per_second)
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
                    vertex_slice, n_machine_time_steps, machine_time_step),
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
        SpikeSourcePoisson._n_poisson_machine_vertices += 1
        buffered_sdram_per_timestep =\
            self._spike_recorder.get_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self._max_spikes_per_ts(
                    vertex_slice, n_machine_time_steps, machine_time_step), 1)
        minimum_buffer_sdram = recording_utilities.get_minimum_buffer_sdram(
            [buffered_sdram_per_timestep * n_machine_time_steps],
            self._minimum_buffer_sdram)
        return SpikeSourcePoissonMachineVertex(
            resources_required, self._spike_recorder.record,
            minimum_buffer_sdram[0], buffered_sdram_per_timestep,
            constraints, label)

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, rate):
        self._rate = utility_calls.convert_param_to_numpy(rate, self._n_atoms)

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = utility_calls.convert_param_to_numpy(
            start, self._n_atoms)

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, duration):
        self._duration = utility_calls.convert_param_to_numpy(
            duration, self._n_atoms)

    @property
    def seed(self):
        return self._seed

    @seed.setter
    def seed(self, seed):
        self._seed = seed

    @staticmethod
    def set_model_max_atoms_per_core(new_value=DEFAULT_MAX_ATOMS_PER_CORE):
        SpikeSourcePoisson._model_based_max_atoms_per_core = new_value

    @staticmethod
    def get_max_atoms_per_core():
        return SpikeSourcePoisson._model_based_max_atoms_per_core

    @staticmethod
    def get_params_bytes(vertex_slice):
        """ Gets the size of the poisson parameters in bytes

        :param vertex_slice:
        """
        return (PARAMS_BASE_WORDS +
                (vertex_slice.n_atoms * PARAMS_WORDS_PER_NEURON)) * 4

    def reserve_memory_regions(self, spec, placement, graph_mapper):
        """ Reserve memory regions for poisson source parameters and output\
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

        # reserve poisson params dsg region
        self._reserve_poisson_params_region(placement, graph_mapper, spec)

        spec.reserve_memory_region(
            region=_REGIONS.SPIKE_HISTORY_REGION.value,
            size=recording_utilities.get_recording_header_size(1),
            label="Recording")
        placement.vertex.reserve_provenance_data_region(spec)

    def _reserve_poisson_params_region(self, placement, graph_mapper, spec):
        """ does the allocation for the poisson params region itself, as\
            it can be reused for setters after an initial run

        :param placement: the location on machine for this vertex
        :param graph_mapper: the mapping between machine and application graphs
        :param spec: the dsg writer
        :return:  None
        """
        spec.reserve_memory_region(
            region=_REGIONS.POISSON_PARAMS_REGION.value,
            size=self.get_params_bytes(graph_mapper.get_slice(
                placement.vertex)), label='PoissonParams')

    def _write_poisson_parameters(
            self, spec, graph, placement, routing_info,
            vertex_slice, machine_time_step, time_scale_factor):
        """ Generate Neuron Parameter data for Poisson spike sources

        :param spec: the data specification writer
        :param key: the routing key for this vertex
        :param vertex_slice:\
            the slice of atoms a machine vertex holds from its application\
            vertex
        :param machine_time_step: the time between timer tick updates.
        :param time_scale_factor:\
            the scaling between machine time step and real time
        :return: None
        """
        # pylint: disable=too-many-arguments, too-many-locals
        spec.comment("\nWriting Neuron Parameters for {} poisson sources:\n"
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
        total_mean_rate = numpy.sum(self._rate)
        if total_mean_rate > 0:
            max_spikes = numpy.sum(scipy.stats.poisson.ppf(
                1.0 - (1.0 / self._rate), self._rate))
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

        # Write the lo_atom id
        spec.write_value(data=vertex_slice.lo_atom)

        # Write the number of sources
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the random seed (4 words), generated randomly!
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))
        spec.write_value(data=self._rng.randint(0x7FFFFFFF))

        # Compute the start times in machine time steps
        start = self._start[vertex_slice.as_slice]
        start_scaled = self._convert_ms_to_n_timesteps(
            start, machine_time_step)

        # Compute the end times as start times + duration in machine time steps
        # (where duration is not None)
        duration = self._duration[vertex_slice.as_slice]
        end_scaled = numpy.zeros(len(duration), dtype="uint32")
        none_positions = numpy.isnan(duration)
        positions = numpy.invert(none_positions)
        end_scaled[none_positions] = 0xFFFFFFFF
        end_scaled[positions] = self._convert_ms_to_n_timesteps(
            start[positions] + duration[positions], machine_time_step)

        # Get the rates for the atoms
        rates = self._rate[vertex_slice.as_slice].astype("float")

        # Compute the spikes per tick for each atom
        spikes_per_tick = (
            rates * (float(machine_time_step) / MICROSECONDS_PER_SECOND))

        # Determine which sources are fast and which are slow
        is_fast_source = spikes_per_tick > SLOW_RATE_PER_TICK_CUTOFF

        # Compute the e^-(spikes_per_tick) for fast sources to allow fast
        # computation of the Poisson distribution to get the number of spikes
        # per timestep
        exp_minus_lambda = numpy.zeros(len(spikes_per_tick), dtype="float")
        exp_minus_lambda[is_fast_source] = numpy.exp(
            -1.0 * spikes_per_tick[is_fast_source])
        # Compute the inter-spike-interval for slow sources to get the average
        # number of timesteps between spikes
        isi_val = numpy.zeros(len(spikes_per_tick), dtype="float")
        elements = numpy.logical_not(is_fast_source) & (spikes_per_tick > 0)
        isi_val[elements] = 1.0 / spikes_per_tick[elements]

        # Get the time to spike value
        time_to_spike = self._time_to_spike[vertex_slice.as_slice]

        # Merge the arrays as parameters per atom
        data = numpy.dstack((
            start_scaled.astype("uint32"),
            end_scaled.astype("uint32"),
            is_fast_source.astype("uint32"),
            (exp_minus_lambda * (2 ** 32)).astype("uint32"),
            (isi_val * (2 ** 15)).astype("uint32"),
            (time_to_spike * (2 ** 15)).astype("uint32")
        ))[0]

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
        """ calculates total sdram usage for a set of atoms

        :param vertex_slice: the atoms to calculate sdram usage for
        :return: sdram usage as a number of bytes
        """
        poisson_params_sz = self.get_params_bytes(vertex_slice)
        total_size = (
            SYSTEM_BYTES_REQUIREMENT +
            SpikeSourcePoissonMachineVertex.get_provenance_data_size(0) +
            poisson_params_sz)
        total_size += self._get_number_of_mallocs_used_by_dsg() * \
            SARK_PER_MALLOC_SDRAM_USAGE
        return total_size

    def _get_number_of_mallocs_used_by_dsg(self):
        """ Works out how many allocation requests are required by the tools

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
        self._reserve_poisson_params_region(placement, graph_mapper, spec)

        # allocate parameters
        self._write_poisson_parameters(
            spec=spec, graph=graph, placement=placement,
            routing_info=routing_info,
            vertex_slice=graph_mapper.get_slice(placement.vertex),
            machine_time_step=machine_time_step,
            time_scale_factor=time_scale_factor)

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

        # locate sdram address to where the neuron parameters are stored
        poisson_parameter_region_sdram_address = \
            helpful_functions.locate_memory_region_for_placement(
                placement, _REGIONS.POISSON_PARAMS_REGION.value, transceiver)

        # shift past the extra stuff before neuron parameters that we don't
        # need to read
        poisson_parameter_parameters_sdram_address = \
            poisson_parameter_region_sdram_address + \
            START_OF_POISSON_GENERATOR_PARAMETERS

        # get size of poisson params
        size_of_region = self.get_params_bytes(vertex_slice)
        size_of_region -= START_OF_POISSON_GENERATOR_PARAMETERS

        # get data from the machine
        byte_array = transceiver.read_memory(
            placement.x, placement.y,
            poisson_parameter_parameters_sdram_address, size_of_region)

        # Convert the data to parameter values
        param_types = [item.data_type() for item in _PoissonStruct]
        values, _ = utility_calls.translate_parameters(
            param_types, byte_array, 0, vertex_slice)

        # Convert start values as timesteps into milliseconds
        self._start[vertex_slice.as_slice] = self._convert_n_timesteps_to_ms(
            values[0], self._machine_time_step)

        # Convert end values as timesteps to durations in milliseconds
        self._duration[vertex_slice.as_slice] = \
            self._convert_n_timesteps_to_ms(
                values[1], self._machine_time_step) - \
            self._start[vertex_slice.as_slice]

        # Work out the spikes per tick depending on if the source is slow
        # or fast
        is_fast_source = values[2] == 1.0
        spikes_per_tick = numpy.zeros(len(is_fast_source), dtype="float")
        spikes_per_tick[is_fast_source] = numpy.log(
            values[3][is_fast_source]) * -1.0
        slow_elements = values[4] > 0
        spikes_per_tick[slow_elements] = 1.0 / values[4][slow_elements]

        # Convert spikes per tick to rates
        self._rate[vertex_slice.as_slice] = (
            spikes_per_tick *
            (MICROSECONDS_PER_SECOND / float(self._machine_time_step)))

        # Store the updated time until next spike so that it can be
        # rewritten when the parameters are loaded
        self._time_to_spike[vertex_slice.as_slice] = values[5]

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
                    vertex_slice, n_machine_time_steps, machine_time_step),
                n_machine_time_steps)],
            self._maximum_sdram_for_buffering)
        spec.write_array(recording_utilities.get_recording_header_array(
            recorded_region_sizes, self._time_between_requests,
            self._buffer_size_before_receive, ip_tags))

        # write parameters
        self._write_poisson_parameters(
            spec, graph, placement, routing_info, vertex_slice,
            machine_time_step, time_scale_factor)

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
            SpikeSourcePoisson.SPIKE_RECORDING_REGION_ID,
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
                SpikeSourcePoisson.SPIKE_RECORDING_REGION_ID)

    def describe(self):
        """
        Returns a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template
        together with an associated template engine
        (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template context
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
