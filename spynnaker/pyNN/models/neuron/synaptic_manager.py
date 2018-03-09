import math
import binascii
import scipy.stats  # @UnresolvedImport
import struct
import sys
from collections import defaultdict
from scipy import special  # @UnresolvedImport
import numpy

# pacmna imports
from pacman.model.abstract_classes import AbstractHasGlobalMaxAtoms
from pacman.model.graphs.common import Slice

# spinn utils
from spinn_utilities.helpful_functions import get_valid_components

# fec
from spinn_front_end_common.utilities.helpful_functions \
    import locate_memory_region_for_placement
from spinn_front_end_common.utilities.globals_variables import get_simulator

# dsg
from data_specification.enums import DataType

# spynnaker
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neural_projections.connectors \
    import OneToOneConnector
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.models.neuron import master_pop_table_generators
from spynnaker.pyNN.models.neuron.synapse_dynamics import SynapseDynamicsStatic
from spynnaker.pyNN.models.neuron.synapse_io import SynapseIORowBased
from spynnaker.pyNN.models.spike_source import SpikeSourcePoisson
from spynnaker.pyNN.models.utility_models import DelayExtensionVertex
from spynnaker.pyNN.utilities.constants \
    import POPULATION_BASED_REGIONS, POSSION_SIGMA_SUMMATION_LIMIT
from spynnaker.pyNN.utilities.utility_calls \
    import get_maximum_probable_value, write_parameters_per_neuron, \
    translate_parameters
from spynnaker.pyNN.utilities.running_stats import RunningStats


TIME_STAMP_BYTES = 4

DEFAULT_CONN_PARAMS_KEYS = {'uniform': ['low', 'high'],
                            'normal':  ['mean', 'std_dev'],
                            'normal_clipped': ['mean', 'std_dev', 'low',
                                               'high'],
                            'exponential': ['beta']
                           }

DEFAULT_CONN_PARAMS_VALS = {'constants': {'values': 1.},
                            'uniform': {'low': 0., 'high': 1.},
                            'normal':  {'mean': 0., 'std_dev': 1.},
                            'normal_clipped': {'mean': 0., 'std_dev': 1.,
                                               'low':  0., 'high': 0.5},
                            'exponential': {'beta': 1.}
                           }
STATIC_HASH  = numpy.uint32(binascii.crc32("StaticSynapticMatrix"))
PLASTIC_HASH  = numpy.uint32(binascii.crc32("PlasticSynapticMatrix"))
MAX_32 = numpy.uint32(0xFFFFFFFF)

# TODO: Make sure these values are correct (particularly CPU cycles)
_SYNAPSES_BASE_DTCM_USAGE_IN_BYTES = 28
_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES = 0
_SYNAPSES_BASE_N_CPU_CYCLES_PER_NEURON = 10
_SYNAPSES_BASE_N_CPU_CYCLES = 8

# Amount to scale synapse SDRAM estimate by to make sure the synapses fit
_SYNAPSE_SDRAM_OVERSCALE = 1.1

_ONE_WORD = struct.Struct("<I")


class SynapticManager(object):
    """ Deals with synapses
    """
    # pylint: disable=too-many-arguments, too-many-locals
    __slots__ = [
        "_delay_key_index",
        "_one_to_one_connection_dtcm_max_bytes",
        "_poptable_type",
        "_pre_run_connection_holders",
        "_retrieved_blocks",
        "_ring_buffer_sigma",
        "_spikes_per_second",
        "_synapse_dynamics",
        "_synapse_io",
        "_synapse_type",
        "_weight_scales"]

    def __init__(self, synapse_type, ring_buffer_sigma,
                 spikes_per_second, config, population_table_type=None,
                 synapse_io=None):
        self._synapse_type = synapse_type
        self._ring_buffer_sigma = ring_buffer_sigma
        self._spikes_per_second = spikes_per_second

        # Get the type of population table
        self._poptable_type = population_table_type
        if population_table_type is None:
            population_table_type = ("MasterPopTableAs" + config.get(
                "MasterPopTable", "generator"))
            algorithms = get_valid_components(
                master_pop_table_generators, "master_pop_table_as")
            self._poptable_type = algorithms[population_table_type]()

        # Get the synapse IO
        self._synapse_io = synapse_io
        if synapse_io is None:
            self._synapse_io = SynapseIORowBased()

        if self._ring_buffer_sigma is None:
            self._ring_buffer_sigma = config.getfloat(
                "Simulation", "ring_buffer_sigma")

        if self._spikes_per_second is None:
            self._spikes_per_second = config.getfloat(
                "Simulation", "spikes_per_second")

        # Prepare for dealing with STDP - there can only be one (non-static)
        # synapse dynamics per vertex at present
        self._synapse_dynamics = SynapseDynamicsStatic()

        # Keep the details once computed to allow reading back
        self._weight_scales = dict()
        self._delay_key_index = dict()
        self._retrieved_blocks = dict()

        # A list of connection holders to be filled in pre-run, indexed by
        # the edge the connection is for
        self._pre_run_connection_holders = defaultdict(list)

        # Limit the DTCM used by one-to-one connections
        self._one_to_one_connection_dtcm_max_bytes = config.getint(
            "Simulation", "one_to_one_connection_dtcm_max_bytes")

        # TODO: Hard-coded to 0 to disable as currently broken!
        self._one_to_one_connection_dtcm_max_bytes = 0

        self._max_per_pre = 0
        self._pop_table = None
        self._address_list = None
        self._any_gen_on_machine = False
        self._matrix_size = 0
        self._num_post_targets = {}
        self._num_words_per_weight = {}

    @property
    def synapse_dynamics(self):
        return self._synapse_dynamics

    @synapse_dynamics.setter
    def synapse_dynamics(self, synapse_dynamics):

        # We can always override static dynamics or None
        if isinstance(self._synapse_dynamics, SynapseDynamicsStatic):
            self._synapse_dynamics = synapse_dynamics

        # We can ignore a static dynamics trying to overwrite a plastic one
        elif isinstance(synapse_dynamics, SynapseDynamicsStatic):
            pass

        # Otherwise, the dynamics must be equal
        elif not synapse_dynamics.is_same_as(self._synapse_dynamics):
            raise SynapticConfigurationException(
                "Synapse dynamics must match exactly when using multiple edges"
                "to the same population")

    @property
    def synapse_type(self):
        return self._synapse_type

    @property
    def ring_buffer_sigma(self):
        return self._ring_buffer_sigma

    @ring_buffer_sigma.setter
    def ring_buffer_sigma(self, ring_buffer_sigma):
        self._ring_buffer_sigma = ring_buffer_sigma

    @property
    def spikes_per_second(self):
        return self._spikes_per_second

    @spikes_per_second.setter
    def spikes_per_second(self, spikes_per_second):
        self._spikes_per_second = spikes_per_second

    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        return self._synapse_io.get_maximum_delay_supported_in_ms(
            machine_time_step)

    @property
    def vertex_executable_suffix(self):
        return self._synapse_dynamics.get_vertex_executable_suffix()

    def add_pre_run_connection_holder(
            self, connection_holder, edge, synapse_info):
        self._pre_run_connection_holders[edge, synapse_info].append(
            connection_holder)

    def get_n_cpu_cycles(self):
        # TODO: Calculate this correctly
        return 0

    def get_dtcm_usage_in_bytes(self):
        # TODO: Calculate this correctly
        return 0

    def _get_synapse_params_size(self, vertex_slice):
        per_neuron_usage = (
            self._synapse_type.get_sdram_usage_per_neuron_in_bytes())
        return (_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES +
                (per_neuron_usage * vertex_slice.n_atoms) +
                (4 * self._synapse_type.get_n_synapse_types()))

    def _get_static_synaptic_matrix_sdram_requirements(self):

        # 4 for address of direct addresses, and
        # 4 for the size of the direct addresses matrix in bytes
        return 8

    def _get_exact_synaptic_blocks_size(
            self, post_slices, post_slice_index, post_vertex_slice,
            graph_mapper, in_edges, machine_time_step):
        """ Get the exact size all of the synaptic blocks
        """
        memory_size = self._get_static_synaptic_matrix_sdram_requirements()

        # Go through the edges and add up the memory
        for machine_edge in in_edges:
            application_edge = graph_mapper.get_application_edge(machine_edge)
            if isinstance(application_edge, ProjectionApplicationEdge):

                # Add on the size of the tables to be generated
                pre_vertex_slice = graph_mapper.get_slice(
                    machine_edge.pre_vertex)
                pre_slices = \
                    graph_mapper.get_slices(application_edge.pre_vertex)
                pre_slice_index = graph_mapper.get_machine_vertex_index(
                    machine_edge.pre_vertex)

                memory_size += self._get_size_of_synapse_information(
                    application_edge.synapse_information, pre_slices,
                    pre_slice_index, post_slices, post_slice_index,
                    pre_vertex_slice, post_vertex_slice,
                    application_edge.n_delay_stages, machine_time_step,
                    machine_edge)

        return memory_size

    def _get_estimate_synaptic_blocks_size(
            self, post_vertex_slice, in_edges, machine_time_step):
        """ Get an estimate of the synaptic blocks memory size
        """

        memory_size = self._get_static_synaptic_matrix_sdram_requirements()

        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionApplicationEdge):

                # Get an estimate of the number of post vertices by
                # assuming that all of them are the same size as this one
                post_slices = [Slice(
                    lo_atom, min(
                        in_edge.post_vertex.n_atoms,
                        lo_atom + post_vertex_slice.n_atoms - 1))
                    for lo_atom in range(
                        0, in_edge.post_vertex.n_atoms,
                        post_vertex_slice.n_atoms)]
                post_slice_index = int(math.floor(
                    float(post_vertex_slice.lo_atom) /
                    float(post_vertex_slice.n_atoms)))

                # Get an estimate of the number of pre-vertices - clearly
                # this will not be correct if the SDRAM usage is high!
                n_atoms_per_machine_vertex = sys.maxint
                if isinstance(in_edge.pre_vertex, AbstractHasGlobalMaxAtoms):
                    n_atoms_per_machine_vertex = \
                        in_edge.pre_vertex.get_max_atoms_per_core()
                if in_edge.pre_vertex.n_atoms < n_atoms_per_machine_vertex:
                    n_atoms_per_machine_vertex = in_edge.pre_vertex.n_atoms

                pre_slices = [Slice(0, in_edge.pre_vertex.n_atoms - 1)]
                pre_slice_index = 0
                memory_size += self._get_size_of_synapse_information(
                    in_edge.synapse_information, pre_slices,
                    pre_slice_index, post_slices, post_slice_index,
                    pre_slices[pre_slice_index], post_vertex_slice,
                    in_edge.n_delay_stages, machine_time_step,
                    in_edge)

        return memory_size * _SYNAPSE_SDRAM_OVERSCALE

    def _get_size_of_synapse_information(
            self, synapse_information, pre_slices, pre_slice_index,
            post_slices, post_slice_index, pre_vertex_slice, post_vertex_slice,
            n_delay_stages, machine_time_step, in_edge):
        memory_size = 0
        for synapse_info in synapse_information:
            undelayed_size, delayed_size = \
                self._synapse_io.get_sdram_usage_in_bytes(
                    synapse_info, pre_slices,
                    pre_slice_index, post_slices, post_slice_index,
                    pre_vertex_slice, post_vertex_slice,
                    n_delay_stages, self._poptable_type,
                    machine_time_step, in_edge)

            memory_size = self._poptable_type.get_next_allowed_address(
                memory_size)
            memory_size += undelayed_size
            memory_size = self._poptable_type.get_next_allowed_address(
                memory_size)
            memory_size += delayed_size
        return memory_size

    def _get_synapse_dynamics_parameter_size(self, vertex_slice):
        """ Get the size of the synapse dynamics region
        """
        return self._synapse_dynamics.get_parameters_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self._synapse_type.get_n_synapse_types())

    def get_sdram_usage_in_bytes(
            self, vertex_slice, in_edges, machine_time_step):
        return (
            self._get_synapse_params_size(vertex_slice) +
            self._get_synapse_dynamics_parameter_size(vertex_slice) +
            self._get_estimate_synaptic_blocks_size(
                vertex_slice, in_edges, machine_time_step) +
            self._poptable_type.get_master_population_table_size(
                vertex_slice, in_edges))

    def _reserve_memory_regions(
            self, spec, machine_vertex, vertex_slice,
            machine_graph, all_syn_block_sz, graph_mapper):
        spec.reserve_memory_region(
            region=POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value,
            size=self._get_synapse_params_size(vertex_slice),
            label='SynapseParams')

        master_pop_table_sz = \
            self._poptable_type.get_exact_master_population_table_size(
                machine_vertex, machine_graph, graph_mapper)
        if master_pop_table_sz > 0:
            spec.reserve_memory_region(
                region=POPULATION_BASED_REGIONS.POPULATION_TABLE.value,
                size=master_pop_table_sz, label='PopTable')
        if all_syn_block_sz > 0:
            spec.reserve_memory_region(
                region=POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
                size=all_syn_block_sz, label='SynBlocks')

        synapse_dynamics_sz = \
            self._get_synapse_dynamics_parameter_size(vertex_slice)
        if synapse_dynamics_sz != 0:
            spec.reserve_memory_region(
                region=POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value,
                size=synapse_dynamics_sz, label='synapseDynamicsParams')

    def get_number_of_mallocs_used_by_dsg(self):
        return 4

    @staticmethod
    def _ring_buffer_expected_upper_bound(
            weight_mean, weight_std_dev, spikes_per_second,
            machine_timestep, n_synapses_in, sigma):
        """ Provides expected upper bound on accumulated values in a ring\
            buffer element.

        Requires an assessment of maximum Poisson input rate.

        Assumes knowledge of mean and SD of weight distribution, fan-in\
        and timestep.

        All arguments should be assumed real values except n_synapses_in\
        which will be an integer.

        :param weight_mean: Mean of weight distribution (in either nA or\
            microSiemens as required)
        :param weight_std_dev: SD of weight distribution
        :param spikes_per_second: Maximum expected Poisson rate in Hz
        :param machine_timestep: in us
        :param n_synapses_in: No of connected synapses
        :param sigma: How many SD above the mean to go for upper bound; a\
            good starting choice is 5.0. Given length of simulation we can\
            set this for approximate number of saturation events.
        """
        # E[ number of spikes ] in a timestep
        steps_per_second = 1000000.0 / machine_timestep
        average_spikes_per_timestep = (
            float(n_synapses_in * spikes_per_second) / steps_per_second)

        # Exact variance contribution from inherent Poisson variation
        poisson_variance = average_spikes_per_timestep * (weight_mean ** 2)

        # Upper end of range for Poisson summation required below
        # upper_bound needs to be an integer
        upper_bound = int(round(average_spikes_per_timestep +
                                POSSION_SIGMA_SUMMATION_LIMIT *
                                math.sqrt(average_spikes_per_timestep)))

        # Closed-form exact solution for summation that gives the variance
        # contributed by weight distribution variation when modulated by
        # Poisson PDF.  Requires scipy.special for gamma and incomplete gamma
        # functions. Beware: incomplete gamma doesn't work the same as
        # Mathematica because (1) it's regularised and needs a further
        # multiplication and (2) it's actually the complement that is needed
        # i.e. 'gammaincc']

        weight_variance = 0.0

        if weight_std_dev > 0:
            lngamma = special.gammaln(1 + upper_bound)
            gammai = special.gammaincc(
                1 + upper_bound, average_spikes_per_timestep)

            big_ratio = (math.log(average_spikes_per_timestep) * upper_bound -
                         lngamma)

            if -701.0 < big_ratio < 701.0 and big_ratio != 0.0:
                log_weight_variance = (
                    -average_spikes_per_timestep +
                    math.log(average_spikes_per_timestep) +
                    2.0 * math.log(weight_std_dev) +
                    math.log(math.exp(average_spikes_per_timestep) * gammai -
                             math.exp(big_ratio)))
                weight_variance = math.exp(log_weight_variance)

        # upper bound calculation -> mean + n * SD
        return ((average_spikes_per_timestep * weight_mean) +
                (sigma * math.sqrt(poisson_variance + weight_variance)))

    def _get_ring_buffer_to_input_left_shifts(
            self, machine_vertex, machine_graph, graph_mapper, post_slices,
            post_slice_index, post_vertex_slice, machine_timestep,
            weight_scale):
        """ Get the scaling of the ring buffer to provide as much accuracy as\
            possible without too much overflow
        """
        weight_scale_squared = weight_scale * weight_scale
        n_synapse_types = self._synapse_type.get_n_synapse_types()
        running_totals = [RunningStats() for _ in range(n_synapse_types)]
        delay_running_totals = [RunningStats() for _ in range(n_synapse_types)]
        total_weights = numpy.zeros(n_synapse_types)
        biggest_weight = numpy.zeros(n_synapse_types)
        weights_signed = False
        rate_stats = [RunningStats() for _ in range(n_synapse_types)]
        steps_per_second = 1000000.0 / machine_timestep

        for m_edge in machine_graph.get_edges_ending_at_vertex(machine_vertex):

            pre_vertex_slice = graph_mapper.get_slice(m_edge.pre_vertex)
            app_edge = graph_mapper.get_application_edge(m_edge)
            pre_slices = [
                graph_mapper.get_slice(internal_machine_vertex)
                for internal_machine_vertex in
                graph_mapper.get_machine_vertices(app_edge.pre_vertex)]
            pre_slice_index = pre_slices.index(pre_vertex_slice)
            if isinstance(app_edge, ProjectionApplicationEdge):
                for synapse_info in app_edge.synapse_information:
                    synapse_type = synapse_info.synapse_type
                    synapse_dynamics = synapse_info.synapse_dynamics
                    connector = synapse_info.connector
                    weight_mean = abs(synapse_dynamics.get_weight_mean(
                        connector, pre_slices, pre_slice_index,
                        post_slices, post_slice_index, pre_vertex_slice,
                        post_vertex_slice) * weight_scale)
                    n_connections = \
                        connector.get_n_connections_to_post_vertex_maximum(
                            pre_slices, pre_slice_index, post_slices,
                            post_slice_index, pre_vertex_slice,
                            post_vertex_slice)
                    weight_variance = abs(synapse_dynamics.get_weight_variance(
                        connector, pre_slices, pre_slice_index,
                        post_slices, post_slice_index, pre_vertex_slice,
                        post_vertex_slice) * weight_scale_squared)
                    running_totals[synapse_type].add_items(
                        weight_mean, weight_variance, n_connections)

                    delay_variance = synapse_dynamics.get_delay_variance(
                        connector, pre_slices, pre_slice_index,
                        post_slices, post_slice_index, pre_vertex_slice,
                        post_vertex_slice)
                    delay_running_totals[synapse_type].add_items(
                        0.0, delay_variance, n_connections)

                    weight_max = (synapse_dynamics.get_weight_maximum(
                        connector, pre_slices, pre_slice_index,
                        post_slices, post_slice_index, pre_vertex_slice,
                        post_vertex_slice) * weight_scale)
                    biggest_weight[synapse_type] = max(
                        biggest_weight[synapse_type], weight_max)

                    spikes_per_tick = max(
                        1.0, self._spikes_per_second / steps_per_second)
                    spikes_per_second = self._spikes_per_second
                    if isinstance(app_edge.pre_vertex, SpikeSourcePoisson):
                        spikes_per_second = app_edge.pre_vertex.rate
                        if hasattr(spikes_per_second, "__getitem__"):
                            spikes_per_second = numpy.max(spikes_per_second)
                        elif get_simulator().is_a_pynn_random(
                                spikes_per_second):
                            spikes_per_second = get_maximum_probable_value(
                                spikes_per_second, pre_vertex_slice.n_atoms)
                        prob = 1.0 - ((1.0 / 100.0) / pre_vertex_slice.n_atoms)
                        spikes_per_tick = spikes_per_second / steps_per_second
                        spikes_per_tick = scipy.stats.poisson.ppf(
                            prob, spikes_per_tick)

                        if n_connections == 1 and spikes_per_tick == 0.:
                            spikes_per_tick = 1.


                    rate_stats[synapse_type].add_items(
                        spikes_per_second, 0, n_connections)
                    total_weights[synapse_type] += spikes_per_tick * (
                        weight_max * n_connections)

                    if synapse_dynamics.are_weights_signed():
                        weights_signed = True

        max_weights = numpy.zeros(n_synapse_types)
        for synapse_type in range(n_synapse_types):
            stats = running_totals[synapse_type]
            rates = rate_stats[synapse_type]
            if delay_running_totals[synapse_type].variance == 0.0:
                max_weights[synapse_type] = max(total_weights[synapse_type],
                                                biggest_weight[synapse_type])
            else:
                max_weights[synapse_type] = min(
                    self._ring_buffer_expected_upper_bound(
                        stats.mean, stats.standard_deviation, rates.mean,
                        machine_timestep, stats.n_items,
                        self._ring_buffer_sigma),
                    total_weights[synapse_type])
                max_weights[synapse_type] = max(
                    max_weights[synapse_type], biggest_weight[synapse_type])

        # Convert these to powers
        max_weight_powers = (
            0 if w <= 1 else int(math.ceil(max(0, math.log(w, 2))))
            for w in max_weights)

        # If 2^max_weight_power equals the max weight, we have to add another
        # power, as range is 0 - (just under 2^max_weight_power)!
        max_weight_powers = (
            p + 1 if (2 ** p) <= w else p
            for p, w in zip(max_weight_powers, max_weights))

        # If we have synapse dynamics that uses signed weights,
        # Add another bit of shift to prevent overflows
        if weights_signed:
            max_weight_powers = (m + 1 for m in max_weight_powers)

        return list(max_weight_powers)

    @staticmethod
    def _get_weight_scale(ring_buffer_to_input_left_shift):
        """ Return the amount to scale the weights by to convert them from \
            floating point values to 16-bit fixed point numbers which can be \
            shifted left by ring_buffer_to_input_left_shift to produce an\
            s1615 fixed point number
        """
        return float(math.pow(2, 16 - (ring_buffer_to_input_left_shift + 1)))

    def _write_synapse_parameters(
            self, spec, machine_vertex, machine_graph, graph_mapper,
            post_slices, post_slice_index, post_vertex_slice, input_type,
            machine_time_step):
        # Get the ring buffer shifts and scaling factors
        weight_scale = input_type.get_global_weight_scale()
        ring_buffer_shifts = self._get_ring_buffer_to_input_left_shifts(
            machine_vertex, machine_graph, graph_mapper, post_slices,
            post_slice_index, post_vertex_slice, machine_time_step,
            weight_scale)

        spec.switch_write_focus(POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value)
        write_parameters_per_neuron(
            spec, post_vertex_slice,
            self._synapse_type.get_synapse_type_parameters())

        spec.write_array(ring_buffer_shifts)

        weight_scales = numpy.array([
            self._get_weight_scale(r) * weight_scale
            for r in ring_buffer_shifts])
        return weight_scales

    def _write_padding(
            self, spec, synaptic_matrix_region, next_block_start_address):
        next_block_allowed_address = self._poptable_type\
            .get_next_allowed_address(next_block_start_address)
        if next_block_allowed_address != next_block_start_address:

            # Pad out data file with the added alignment bytes:
            spec.comment("\nWriting population table required padding\n")
            spec.switch_write_focus(synaptic_matrix_region)
            spec.set_register_value(
                register_id=15,
                data=next_block_allowed_address - next_block_start_address)
            spec.write_repeat_value(
                data=0xDD, repeats=15, repeats_is_register=True,
                data_type=DataType.UINT8)
            return next_block_allowed_address
        return next_block_start_address

    def _write_synaptic_matrix_and_master_population_table(
            self, spec, post_slices, post_slice_index, machine_vertex,
            post_vertex_slice, all_syn_block_sz, weight_scales,
            master_pop_table_region, synaptic_matrix_region, routing_info,
            graph_mapper, machine_graph, machine_time_step):
        """ Simultaneously generates both the master population table and
            the synaptic matrix.
        """
        spec.comment(
            "\nWriting Synaptic Matrix and Master Population Table:\n")

        # Track writes inside the synaptic matrix region:
        block_addr = 0
        n_synapse_types = self._synapse_type.get_n_synapse_types()

        # Get the edges
        in_edges = machine_graph.get_edges_ending_at_vertex(machine_vertex)

        # Set up the master population table
        self._poptable_type.initialise_table(spec, master_pop_table_region)

        # Set up for single synapses - write the offset of the single synapses
        # initially 0
        single_synapses = list()
        spec.switch_write_focus(synaptic_matrix_region)
        spec.write_value(0)
        single_addr = 0

        # For each machine edge in the vertex, create a synaptic list
        for machine_edge in in_edges:
            app_edge = graph_mapper.get_application_edge(machine_edge)
            if isinstance(app_edge, ProjectionApplicationEdge):
                spec.comment("\nWriting matrix for m_edge:{}\n".format(
                    machine_edge.label))

                pre_vertex_slice = graph_mapper.get_slice(
                    machine_edge.pre_vertex)
                pre_slices = graph_mapper.get_slices(app_edge.pre_vertex)
                pre_slice_idx = graph_mapper.get_machine_vertex_index(
                    machine_edge.pre_vertex)

                for synapse_info in app_edge.synapse_information:
                    block_addr, single_addr = self.__write_row(
                        spec, synaptic_matrix_region, synapse_info, pre_slices,
                        pre_slice_idx, post_slices, post_slice_index,
                        pre_vertex_slice, post_vertex_slice, app_edge,
                        n_synapse_types, single_synapses,
                        master_pop_table_region, weight_scales,
                        machine_time_step,
                        routing_info.get_routing_info_for_edge(machine_edge),
                        all_syn_block_sz, block_addr, single_addr)

        pt, al = self._poptable_type.finish_master_pop_table(
            spec, master_pop_table_region)
        self._pop_table = pt
        self._address_list = al

        # Write the size and data of single synapses to the end of the region
        spec.switch_write_focus(synaptic_matrix_region)
        if single_synapses:
            single_data = numpy.concatenate(single_synapses)
            spec.write_value(len(single_data) * 4)
            spec.write_array(single_data)
        else:
            spec.write_value(0)

        # Write the position of the single synapses
        spec.set_write_pointer(0)
        spec.write_value(block_addr)

    def __write_row(
            self, spec, synaptic_matrix_region, synapse_info, pre_slices,
            pre_slice_idx, post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, app_edge, n_synapse_types, single_synapses,
            master_pop_table_region, weight_scales, machine_time_step,
            rinfo, all_syn_block_sz, block_addr, single_addr):
        max_row_length = 0

        conn = synapse_info.connector
        gen_in_spinn = conn.generate_on_machine()
        self._any_gen_on_machine |= gen_in_spinn

        # print("\n\n%s\n"%synapse_info.connector)
        # If connector is being built on SpiNNaker, compute PopulationTable
        # sizes only.
        if gen_in_spinn:
            # print("\n\n******************Faking data!!!***************\n")

            # 32-bit words required by each pre neuron to connect to
            # X post neurons
            conns_per_row = conn.get_n_connections_from_pre_vertex_maximum\
                                     (pre_slices, pre_slice_idx,
                                      post_slices, post_slice_index,
                                      pre_vertex_slice, post_vertex_slice)
            # print("MAX ROW LENGTH %d"%(max_row_length))
            if conns_per_row == 0:
                continue

            self._num_post_targets[synapse_info] = conns_per_row

            if synapse_info.synapse_dynamics.is_plastic:
                # print("does syn_dyn have n_header_words?")
                # print(dir(syn_info.synapse_dynamics))
                try:
                    header_bytes = synapse_info.\
                                            synapse_dynamics._n_header_bytes
                except:
                    # print("aparently not!")
                    header_bytes = 0

                n_32bit_header_words = numpy.uint32(
                                       header_bytes // 4 +
                                       (1 if header_bytes % 4 > 0 else 0) )
                # print("number of 32-bit header words: "
                #       "%d"%n_32bit_header_words)

                bytes_per_weight = synapse_info.synapse_dynamics.\
                                     timing_dependence._synapse_structure.\
                                     get_n_bytes_per_connection()

                half_words_per_weight = bytes_per_weight//2 + \
                                        bytes_per_weight%2
                half_words_per_row = half_words_per_weight*conns_per_row
                weight_words_per_row = half_words_per_row//2 + \
                                       half_words_per_row%2
                self._num_words_per_weight[synapse_info] = \
                                                        half_words_per_weight
                # 16-bit control vars in 32-bit words
                control_words_per_row = \
                            (conns_per_row//2 + conns_per_row % 2)

                max_row_length = weight_words_per_row
                max_row_length += control_words_per_row
                max_row_length += n_32bit_header_words
            else:
                max_row_length = conns_per_row
                self._num_words_per_weight[synapse_info] = 0

            max_conn_delay = synapse_info.connector.get_delay_maximum()

            #todo: get 16 from global config
            n_stages = max_conn_delay // 16

            if (max_conn_delay % 16) == 0:
                n_stages -= 1

            n_stages = max(1, n_stages)

            # print("next block address 0x%08x"%next_block_start_address)
            # print("num stages = %d"%n_stages)
            # 32-bit words needed for the entire connection
            # plus num plastic-plastic, num static, num fixed-plastic

            # num_pre = synapse_info.connector._n_pre_neurons
            num_pre = pre_vertex_slice.n_atoms*n_stages
            # print("should have %d"%(num_pre * n_stages))
            # num_pre = num_pre * stages
            # print("Num pre = %d"%num_pre)
            # print("Max row length = %d"%max_row_length)
            #add 3 due to format of matrix
            data_length = num_pre * (max_row_length + 3)
            # print("Data length = %d"%data_length)

            block_addr = self._write_padding(
                                            spec, synaptic_matrix_region,
                                            block_addr)
            # print("next block address after padding = %d"%
            #       next_block_start_address)

            self._poptable_type.update_master_population_table(
                                            spec, block_addr,
                                            max_row_length, rinfo.first_key_and_mask,
                                            master_pop_table_region)

            block_addr += (data_length * 4) #bytes

            if block_addr > all_syn_block_sz:
                raise Exception(
                    "Too much synaptic memory has been written:"
                    " {} of {} ".format(
                        block_addr, all_syn_block_sz))

            # SKIP DATA GENERATION IF IT'S ANYWAYS HAPPENING ON SPINNAKER
            # print("\n------------------------------ done faking data ---")
            continue

        ### GENERATE SYNAPTIC DATA only IF NEEDED ###
        (row_data, row_length, delayed_row_data, delayed_row_length,
         delayed_source_ids, delay_stages) = self._synapse_io.get_synapses(
             synapse_info, pre_slices, pre_slice_idx, post_slices,
             post_slice_index, pre_vertex_slice, post_vertex_slice,
             app_edge.n_delay_stages, self._poptable_type, n_synapse_types,
             weight_scales, machine_time_step)

        if app_edge.delay_edge is not None:
            app_edge.delay_edge.pre_vertex.add_delays(
                pre_vertex_slice, delayed_source_ids, delay_stages)
        elif delayed_source_ids.size != 0:
            raise Exception(
                "Found delayed source ids but no delay "
                "machine edge for {}".format(app_edge.label))

        if (app_edge, synapse_info) in self._pre_run_connection_holders:
            for conn_holder in self._pre_run_connection_holders[
                    app_edge, synapse_info]:
                conn_holder.add_connections(self._synapse_io.read_synapses(
                    synapse_info, pre_vertex_slice, post_vertex_slice,
                    row_length, delayed_row_length, n_synapse_types,
                    weight_scales, row_data, delayed_row_data,
                    app_edge.n_delay_stages, machine_time_step))
                conn_holder.finish()

        if row_data.size:
            block_addr, single_addr = self.__write_row_data(
                spec, synapse_info, row_length, row_data, rinfo,
                single_synapses, master_pop_table_region,
                synaptic_matrix_region, block_addr, single_addr)
        elif rinfo is not None:
            self._poptable_type.update_master_population_table(
                spec, 0, 0, rinfo.first_key_and_mask, master_pop_table_region)
        del row_data

        if block_addr > all_syn_block_sz:
            raise Exception(
                "Too much synaptic memory has been written: {} of {} ".format(
                    block_addr, all_syn_block_sz))

        delay_rinfo = None
        delay_key = (app_edge.pre_vertex, pre_vertex_slice.lo_atom,
                     pre_vertex_slice.hi_atom)
        if delay_key in self._delay_key_index:
            delay_rinfo = self._delay_key_index[delay_key]
        if delayed_row_data.size:
            block_addr, single_addr = self.__write_row_data(
                spec, synapse_info, delayed_row_length, delayed_row_data,
                delay_rinfo, single_synapses, master_pop_table_region,
                synaptic_matrix_region, block_addr, single_addr)
        elif delay_rinfo is not None:
            self._poptable_type.update_master_population_table(
                spec, 0, 0, delay_rinfo.first_key_and_mask,
                master_pop_table_region)
        del delayed_row_data

        if block_addr > all_syn_block_sz:
            raise Exception(
                "Too much synaptic memory has been written: {} of {} ".format(
                    block_addr, all_syn_block_sz))
        return block_addr, single_addr

    def __write_row_data(
            self, spec, synapse_info, row_length, row_data, rinfo,
            single_synapses, master_pop_table_region, synaptic_matrix_region,
            block_addr, single_addr):
        if (row_length == 1 and
                isinstance(synapse_info.connector, OneToOneConnector) and
                single_addr + len(row_data) <=
                self._one_to_one_connection_dtcm_max_bytes):
            single_rows = row_data.reshape(-1, 4)[:, 3]
            single_synapses.append(single_rows)
            self._poptable_type.update_master_population_table(
                spec, single_addr, 1, rinfo.first_key_and_mask,
                master_pop_table_region, is_single=True)
            single_addr += len(single_rows) * 4
        else:
            block_addr = self._write_padding(
                spec, synaptic_matrix_region, block_addr)
            spec.switch_write_focus(synaptic_matrix_region)
            spec.write_array(row_data)
            self._poptable_type.update_master_population_table(
                spec, block_addr, row_length,
                rinfo.first_key_and_mask, master_pop_table_region)
            block_addr += len(row_data) * 4
        return block_addr, single_addr

    def write_data_spec(
            self, spec, application_vertex, post_vertex_slice, machine_vertex,
            placement, machine_graph, application_graph, routing_info,
            graph_mapper, input_type, machine_time_step, placements):
        # Create an index of delay keys into this vertex
        for m_edge in machine_graph.get_edges_ending_at_vertex(machine_vertex):
            app_edge = graph_mapper.get_application_edge(m_edge)
            if isinstance(app_edge.pre_vertex, DelayExtensionVertex):
                pre_vertex_slice = graph_mapper.get_slice(
                    m_edge.pre_vertex)
                self._delay_key_index[app_edge.pre_vertex.source_vertex,
                                      pre_vertex_slice.lo_atom,
                                      pre_vertex_slice.hi_atom] = \
                    routing_info.get_routing_info_for_edge(m_edge)

        post_slices = graph_mapper.get_slices(application_vertex)
        post_slice_idx = graph_mapper.get_machine_vertex_index(machine_vertex)

        # Reserve the memory
        in_edges = machine_graph.get_edges_ending_at_vertex(machine_vertex)
        all_syn_block_sz = self._get_exact_synaptic_blocks_size(
            post_slices, post_slice_idx, post_vertex_slice, graph_mapper,
            in_edges, machine_time_step)
        self._reserve_memory_regions(
            spec, machine_vertex, post_vertex_slice, machine_graph,
            all_syn_block_sz, graph_mapper)

        weight_scales = self._write_synapse_parameters(
            spec, machine_vertex, machine_graph, graph_mapper, post_slices,
            post_slice_idx, post_vertex_slice, input_type, machine_time_step)

        self._write_synaptic_matrix_and_master_population_table(
            spec, post_slices, post_slice_idx, machine_vertex,
            post_vertex_slice, all_syn_block_sz, weight_scales,
            POPULATION_BASED_REGIONS.POPULATION_TABLE.value,
            POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
            routing_info, graph_mapper, machine_graph, machine_time_step)

        self._synapse_dynamics.write_parameters(
            spec, POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value,
            machine_time_step, weight_scales)

        self._weight_scales[placement] = weight_scales

        on_machine_dict = {}
        flags, n_edges = self._generate_on_machine_flags(in_edges, graph_mapper)
        on_machine_dict['flags'] = flags
        on_machine_dict['n_edges'] = n_edges
        on_machine_dict['delay_placement'] = self._get_placements_for_delayed(
                                                   in_edges, graph_mapper, placements)
        on_machine_dict['weight_scales'] = weight_scales
        on_machine_dict['data_block'] = self._generate_on_machine_params(
                                              machine_vertex, in_edges, graph_mapper,
                                              routing_info, placements, weight_scales)

        self._write_on_machine_data_spec(spec, on_machine_dict, post_vertex_slice)

    def clear_connection_cache(self):
        self._retrieved_blocks = dict()

    def get_connections_from_machine(
            self, transceiver, placement, machine_edge, graph_mapper,
            routing_infos, synapse_info, machine_time_step,
            using_extra_monitor_cores, placements=None, data_receiver=None,
            sender_extra_monitor_core_placement=None,
            extra_monitor_cores_for_router_timeout=None,
            handle_time_out_configuration=True, fixed_routes=None):
        app_edge = graph_mapper.get_application_edge(machine_edge)
        if not isinstance(app_edge, ProjectionApplicationEdge):
            return None

        # Get details for extraction
        pre_vertex_slice = graph_mapper.get_slice(machine_edge.pre_vertex)
        post_vertex_slice = graph_mapper.get_slice(machine_edge.post_vertex)
        n_synapse_types = self._synapse_type.get_n_synapse_types()

        # Get the key for the pre_vertex
        key = routing_infos.get_first_key_for_edge(machine_edge)

        # Get the key for the delayed pre_vertex
        delayed_key = None
        if app_edge.delay_edge is not None:
            delayed_key = self._delay_key_index[
                app_edge.pre_vertex, pre_vertex_slice.lo_atom,
                pre_vertex_slice.hi_atom].first_key

        # Get the block for the connections from the pre_vertex
        master_pop_table, direct_synapses, indirect_synapses = \
            self.__compute_addresses(transceiver, placement)
        data, max_row_length = self._retrieve_synaptic_block(
            transceiver, placement, master_pop_table, indirect_synapses,
            direct_synapses, key, pre_vertex_slice.n_atoms, synapse_info.index,
            using_extra_monitor_cores, placements, data_receiver,
            sender_extra_monitor_core_placement,
            extra_monitor_cores_for_router_timeout, fixed_routes)

        # Get the block for the connections from the delayed pre_vertex
        delayed_data = None
        delayed_max_row_len = 0
        if delayed_key is not None:
            delayed_data, delayed_max_row_len = self._retrieve_synaptic_block(
                transceiver, placement, master_pop_table, indirect_synapses,
                direct_synapses, delayed_key,
                pre_vertex_slice.n_atoms * app_edge.n_delay_stages,
                synapse_info.index, using_extra_monitor_cores, placements,
                data_receiver, sender_extra_monitor_core_placement,
                extra_monitor_cores_for_router_timeout,
                handle_time_out_configuration, fixed_routes)

        # Convert the blocks into connections
        return self._synapse_io.read_synapses(
            synapse_info, pre_vertex_slice, post_vertex_slice,
            max_row_length, delayed_max_row_len, n_synapse_types,
            self._weight_scales[placement], data, delayed_data,
            app_edge.n_delay_stages, machine_time_step)

    def __compute_addresses(self, transceiver, placement):
        """ Helper for computing the addresses of the master pop table and\
            synaptic-matrix-related bits.
        """
        master_pop_table = locate_memory_region_for_placement(
            placement, POPULATION_BASED_REGIONS.POPULATION_TABLE.value,
            transceiver)
        synaptic_matrix = locate_memory_region_for_placement(
            placement, POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
            transceiver)
        direct_synapses = (
            self._get_static_synaptic_matrix_sdram_requirements() +
            synaptic_matrix + _ONE_WORD.unpack_from(str(
                transceiver.read_memory(
                    placement.x, placement.y, synaptic_matrix, 4)))[0])
        indirect_synapses = synaptic_matrix + 4
        return master_pop_table, direct_synapses, indirect_synapses

    def _retrieve_synaptic_block(
            self, transceiver, placement, master_pop_table_address,
            indirect_synapses_address, direct_synapses_address,
            key, n_rows, index, using_extra_monitor_cores, placements=None,
            data_receiver=None, sender_extra_monitor_core_placement=None,
            extra_monitor_cores_for_router_timeout=None,
            handle_time_out_configuration=True, fixed_routes=None):
        """ Read in a synaptic block from a given processor and vertex on\
            the machine
        """
        # See if we have already got this block
        if (placement, key, index) in self._retrieved_blocks:
            return self._retrieved_blocks[placement, key, index]

        items = self._poptable_type.extract_synaptic_matrix_data_location(
            key, master_pop_table_address, transceiver,
            placement.x, placement.y)
        if index >= len(items):
            return None, None

        max_row_length, synaptic_block_offset, is_single = items[index]
        if max_row_length == 0:
            return None, None

        block = None
        if max_row_length > 0 and synaptic_block_offset is not None:
            # if exploiting the extra monitor cores, need to set the machine
            # for data extraction mode
            if using_extra_monitor_cores and handle_time_out_configuration:
                data_receiver.set_cores_for_data_extraction(
                    transceiver, extra_monitor_cores_for_router_timeout,
                    placements)

            # read in the synaptic block
            if not is_single:
                block = self.__read_multiple_synaptic_blocks(
                    transceiver, data_receiver, placement, n_rows,
                    max_row_length,
                    indirect_synapses_address + synaptic_block_offset,
                    using_extra_monitor_cores,
                    sender_extra_monitor_core_placement, fixed_routes)
            else:
                block, max_row_length = self.__read_single_synaptic_block(
                    transceiver, data_receiver, placement, n_rows,
                    direct_synapses_address + synaptic_block_offset,
                    using_extra_monitor_cores,
                    sender_extra_monitor_core_placement, fixed_routes)

            if using_extra_monitor_cores and handle_time_out_configuration:
                data_receiver.unset_cores_for_data_extraction(
                    transceiver, extra_monitor_cores_for_router_timeout,
                    placements)

        self._retrieved_blocks[placement, key, index] = (block, max_row_length)
        return block, max_row_length

    def __read_multiple_synaptic_blocks(
            self, transceiver, data_receiver, placement, n_rows,
            max_row_length, address, using_extra_monitor_cores,
            sender_extra_monitor_core_placement, fixed_routes):
        """ Read in an array of synaptic blocks.
        """
        # calculate the synaptic block size in bytes
        synaptic_block_size = self._synapse_io.get_block_n_bytes(
            max_row_length, n_rows)

        # read in the synaptic block
        if using_extra_monitor_cores:
            return data_receiver.get_data(
                transceiver, sender_extra_monitor_core_placement, address,
                synaptic_block_size, fixed_routes)
        return transceiver.read_memory(
            placement.x, placement.y, address, synaptic_block_size)

    def __read_single_synaptic_block(
            self, transceiver, data_receiver, placement, n_rows, address,
            using_extra_monitor_cores, sender_extra_monitor_core_placement,
            fixed_routes):
        """ Read in a single synaptic block.
        """
        # The data is one per row
        synaptic_block_size = n_rows * 4

        # read in the synaptic row data
        if using_extra_monitor_cores:
            single_block = data_receiver.get_data(
                transceiver, sender_extra_monitor_core_placement, address,
                synaptic_block_size, fixed_routes)
        else:
            single_block = transceiver.read_memory(
                placement.x, placement.y, address, synaptic_block_size)

        # Convert the block into a set of rows
        numpy_block = numpy.zeros((n_rows, 4), dtype="uint32")
        numpy_block[:, 3] = numpy.asarray(
            single_block, dtype="uint8").view("uint32")
        numpy_block[:, 1] = 1
        return bytearray(numpy_block.tobytes()), 1

    # inherited from AbstractProvidesIncomingPartitionConstraints
    def get_incoming_partition_constraints(self):
        return self._poptable_type.get_edge_constraints()

    def read_parameters_from_machine(
            self, transceiver, placement, vertex_slice):
        # locate sdram address to where the synapse parameters are stored
        synapse_region_sdram_address = locate_memory_region_for_placement(
            placement, POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value,
            transceiver)

        # get size of synapse params
        size_of_region = (
            self._synapse_type.get_sdram_usage_per_neuron_in_bytes() *
            vertex_slice.n_atoms)

        # get data from the machine
        byte_array = transceiver.read_memory(
            placement.x, placement.y, synapse_region_sdram_address,
            size_of_region)

        synapse_params, _ = translate_parameters(
            self._synapse_type.get_synapse_type_parameter_types(),
            byte_array, 0, vertex_slice)
        self._synapse_type.set_synapse_type_parameters(
            synapse_params, vertex_slice)

    def regenerate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            vertex_slice):
        spec.reserve_memory_region(
            region=POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value,
            size=self._get_synapse_params_size(vertex_slice),
            label='SynapseParams')
        spec.switch_write_focus(POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value)
        write_parameters_per_neuron(
            spec, vertex_slice,
            self._synapse_type.get_synapse_type_parameters())

    def _generate_on_machine_flags(self, in_edges, graph_mapper):
        if not self._any_gen_on_machine:
            return None, None

        syn_infos = []
        for edg in in_edges:
            app_edge = graph_mapper.get_application_edge(edg)
            if isinstance(app_edge, ProjectionApplicationEdge):
                for synapse_info in app_edge.synapse_information:
                    syn_infos.append(synapse_info)

        num_edges = len(syn_infos)
        num_words = int(numpy.ceil(num_edges/32.))
        flags = numpy.zeros(num_words, dtype=numpy.uint32)
        e = 0
        for syn_info in syn_infos:
            # syn_info = edg.synapse_information[0]
            conn = syn_info.connector
            word = e//32
            shift = e%32
            if conn.generate_on_machine():
                flags[word] |= 1 << shift
            e += 1

        return flags, num_edges

    def _get_placements_for_delayed(self, in_edges, graph_mapper, placements):
        if not self._any_gen_on_machine:
            return None

        places = []

        for edg in in_edges:
            app_edge = graph_mapper.get_application_edge(edg)
            if isinstance(app_edge, ProjectionApplicationEdge):
                place = placements.get_placement_of_vertex(edg.pre_vertex)
                for synapse_info in app_edge.synapse_information:
                    if self._is_delayed(synapse_info):
                        if place not in places:
                            places.append(place)

        return places


    def _get_place_for_delay_edge(self, app_edge, graph_mapper, placements):
        if not self._any_gen_on_machine:
            return None, None

        if hasattr(app_edge, 'delay_edge') and app_edge.delay_edge is not None:
            vertices = graph_mapper.get_machine_vertices(
                                             app_edge.delay_edge.pre_vertex)
            delayed_placements = []
            delayed_slices     = []
            for machine_vertex in vertices:
                delayed_slices.append(
                            graph_mapper.get_slice(machine_vertex))
                delayed_placements.append(
                            placements.get_placement_of_vertex(machine_vertex))

            return delayed_placements, delayed_slices

        return [], []


    def _get_key_mask_for_edge(self, mch_edge, graph_mapper, routing_infos):
        if not self._any_gen_on_machine:
            return None

        app_edge = graph_mapper.get_application_edge(mch_edge)
        slice = graph_mapper.get_slice(mch_edge.pre_vertex)
        if hasattr(app_edge, 'delay_edge') and app_edge.delay_edge is not None:
            dly_mch_edges = graph_mapper.get_machine_edges(app_edge.delay_edge)

            for de in dly_mch_edges:
                s = graph_mapper.get_slice(de.pre_vertex)

                if s.as_slice == slice.as_slice:
                    ri = routing_infos.get_routing_info_for_edge(de)

                    return ri.first_key_and_mask
        else:
            routing_info = routing_infos.get_routing_info_for_edge(mch_edge)
            return routing_info.first_key_and_mask


    def _generate_on_machine_params(self, machine_post_vertex, in_edges, graph_mapper,
                                    routing_infos, placements, weight_scales):
        if not self._any_gen_on_machine:
            return None

        #TODO:   This should probably be merged with another loop so we don't visit
        #todo:   the same data many times
        # print("\n\nPopulation Table / Address List")
        # print(self._pop_table)
        # print(self._address_list)
        addresses   = [(a & 0x7FFFFF00) >> 8 for a in self._address_list]
        row_lengths = [(a & 0xFF) for a in self._address_list]
        # print("Addresses")
        # print(addresses)
        # print("Row Lengths")
        # print(row_lengths)

        syn_infos = []
        param_block = []
        slices = []
        delayed_places = []
        delayed_slices = []
        keys = []
        masks = []
        num_seeds = 4
        post_slice = graph_mapper.get_slice(machine_post_vertex)
        any_delayed = False
        for edg in in_edges:
            app_edge = graph_mapper.get_application_edge(edg)

            if isinstance(app_edge, ProjectionApplicationEdge):
                pre_vertex_slice = graph_mapper.get_slice(edg.pre_vertex)
                dplaces, dslices = self._get_place_for_delay_edge(app_edge,
                                                                graph_mapper,
                                                                placements)
                key_and_mask = self._get_key_mask_for_edge(edg, graph_mapper,
                                                           routing_infos)
                key  = key_and_mask.key
                mask = key_and_mask.mask
                for synapse_info in app_edge.synapse_information:
                    keys.append(numpy.uint32(key))
                    masks.append(numpy.uint32(mask))
                    delayed_places.append(dplaces)
                    delayed_slices.append(dslices)
                    syn_infos.append(synapse_info)
                    slices.append(pre_vertex_slice)
                    any_delayed |= (synapse_info.connector.get_delay_maximum() > 16)

        conn = None
        dist = None
        max_per_dyn_type = [0, 0]
        n_32bit_header_words = 0
        max_n_pre_neurons = 0
        for i in range(len(syn_infos)):

            syn_info = syn_infos[i]

            slice_start = numpy.uint32(slices[i].lo_atom)
            slice_count = numpy.uint32(slices[i].n_atoms)
            key = keys[i]
            mask = masks[i]

            address_delta = 0
            row_len = 0
            # print(key, mask)
            # print(self._pop_table)
            for addr_idx in range(len(self._pop_table)):

                if key == self._pop_table[addr_idx][0] and \
                   mask == self._pop_table[addr_idx][1]:
                    # print("key curr %s == pop %s" % (key, self._pop_table[addr_idx][0]))
                    address_delta = addresses[addr_idx]
                    row_len = row_lengths[addr_idx]
                    # print("\n*********++++++++++++++++++++++++++++++++++")
                    # print(address_delta, row_len)
                    # print("\n*********++++++++++++++++++++++++++++++++++")
                    break

            address_delta = numpy.uint32(address_delta)
            conn = syn_info.connector
            direct = numpy.uint32(isinstance(syn_info.connector, OneToOneConnector))
            # WRONG! should be 16*machine_time_step/1000.0
            delayed = self._is_delayed(syn_info)
            num_delayed = len(delayed_places[i])
            dly_places = [self._placement_to_uint32(dp) for dp in delayed_places[i]]
            dly_slices = [ds for ds in delayed_slices[i]]

            # max_conns = numpy.uint32(conn.get_max_num_connections(slices[i], post_slice))
            dyn_type = STATIC_HASH if syn_info.synapse_dynamics.is_static \
                       else PLASTIC_HASH
            # print("syn_info.synapse_type", syn_info.synapse_type)
            syn_type = numpy.uint32(syn_info.synapse_type)

            int_dyn_type = numpy.uint32(syn_info.synapse_dynamics.is_plastic)
            # max_per_pre = numpy.uint32(conn.get_max_per_neuron_connections(
            #                                                      slices[i], post_slice))
            n_pre_neurons = numpy.uint32(conn._n_pre_neurons)
            if max_n_pre_neurons < n_pre_neurons:
                max_n_pre_neurons = n_pre_neurons

            max_per_pre = numpy.uint32(self._max_per_pre)
            # if isinstance(conn, FixedProbabilityConnector):
            #     max_per_pre -= 1


            # if max_per_dyn_type[int_dyn_type] < max_per_pre:
            #     max_per_dyn_type[int_dyn_type] = max_per_pre

            if conn.generate_on_machine() and syn_info in self._num_post_targets :#\
               # and self._num_post_targets[synapse_info] > 0 \
               # and row_len > 0:

                for _ in range(num_seeds):
                    rnd_int = numpy.random.randint(1323, 2 ** 32)
                    param_block.append(numpy.uint32(rnd_int))

                param_block.append(conn.name_hash())
                param_block.append(key)#todo: don't need?
                param_block.append(mask)#todo: don't need?
                param_block.append(address_delta)
                param_block.append(row_len)
                param_block.append(n_pre_neurons)
                param_block.append(numpy.uint32(self._num_post_targets[syn_info]))
                param_block.append(numpy.uint32(self._num_words_per_weight[syn_info]))
                param_block.append(slice_start)
                param_block.append(slice_count)
                param_block.append(direct)
                param_block.append(delayed)
                param_block.append(num_delayed)

                for i in range(num_delayed):
                    param_block.append(dly_places[i])

                for i in range(num_delayed):
                    param_block.append(dly_slices[i].lo_atom)

                for i in range(num_delayed):
                    param_block.append(dly_slices[i].n_atoms)


                # hash names of synapse, weights and delay types
                param_block.append(dyn_type) #static or plastic
                param_block.append(syn_type) #inhibitory, excitatory, etc.
                param_block.append(conn._param_hash(conn._weights)) #const, random, etc.
                param_block.append(conn._param_hash(conn._delays))  #const, random, etc.

                # using signed weights or not (kernel yes, everything else no)
                if isinstance(conn, KernelConnector) and \
                   isinstance(conn._weights, ConvolutionKernel):
                    use_signed_weights = numpy.uint32(True)
                else:
                    use_signed_weights = numpy.uint32(False)

                param_block.append(use_signed_weights)


                # header words for synapse row
                if syn_info.synapse_dynamics.is_plastic:
                    # print("does syn_dyn have n_header_words?")
                    # print(dir(syn_info.synapse_dynamics))
                    try:
                        header_bytes = syn_info.synapse_dynamics._n_header_bytes
                    except:
                        # print("aparently not!")
                        header_bytes = 0

                    n_32bit_header_words = numpy.uint32(header_bytes//4 +
                                                        (1 if header_bytes%4 > 0 else 0))
                    # print("\n\nheader bytes: %d"%header_bytes)
                    # print("number of 32-bit header words: %d\n\n"%n_32bit_header_words)
                else:
                    n_32bit_header_words = 0

                param_block.append(n_32bit_header_words)


                #TODO: add a gen_on_machine_info method per connector
                # connector-specific data
                param_block += conn.gen_on_machine_info()

                #weights in u1616 or s1516 fixed-point
                if numpy.isscalar(conn._weights):
                    ws  = float(weight_scales[syn_type])
                    ws *= float(conn._weights)
                    w = numpy.uint32(ws)
                    w = w << 16
                    param_block.append(w)

                elif isinstance(conn, KernelConnector) and \
                     isinstance(conn._weights, ConvolutionKernel):

                    param_block += conn.gen_on_machine_info()

                    for r in range(conn._weights.shape[0]):
                        for c in range(conn._weights.shape[1]):
                            w = numpy.int32(float(conn._weights[r, c]) * (1 << 16))
                            param_block.append(w)
                else:
                    dist = conn._weights.name

                    for i in range(len(DEFAULT_CONN_PARAMS_KEYS[dist])):
                        # stupid non-named parameters!
                        if i < len(conn._weights.parameters):
                            v = conn._weights.parameters[i]
                        else:
                            p = DEFAULT_CONN_PARAMS_KEYS[dist][i]
                            v = DEFAULT_CONN_PARAMS_VALS[dist][p]

                        param_block.append(v)

                #delays (needed to be in
                if numpy.isscalar(conn._delays):
                    param_block.append(numpy.uint32(conn._delays)<<16)

                elif isinstance(conn, KernelConnector) and \
                     isinstance(conn._delays, ConvolutionKernel):
                    param_block += conn.gen_on_machine_info()
                    for r in range(conn._delays.shape[0]):
                        for c in range(conn._delays.shape[1]):
                            d = numpy.uint32(conn._delays[r, c])
                            d = d << 16
                            param_block.append(d)
                else:
                    dist = conn._delays.name

                    for i in range(len(DEFAULT_CONN_PARAMS_KEYS[dist])):
                        # stupid non-named parameters!
                        if i < len(conn._delays.parameters):
                            v = float(conn._delays.parameters[i])
                        else:
                            p = DEFAULT_CONN_PARAMS_KEYS[dist][i]
                            v = DEFAULT_CONN_PARAMS_VALS[dist][p]

                        param_block.append(v)

        # print(max_per_dyn_type)
        # sys.exit(0)
        # param_block = max_per_dyn_type + param_block

        # print("in generate_on_machine_params:")
        # print("\t- param_block -")
        # for i in param_block:
        #     if isinstance(i, numpy.uint32) or isinstance(i, (int, long)):
        #         print("\t\t%010u" % i)
        #     else:
        #         print("\t\t%f" % i)

        return param_block

    def _placement_to_uint32(self, placement):
        if placement is None:
            return 0

        # [  placement x  |  placement y   |  placement p  ]
        # [    13 bit     |     13 bit     |     6 bit     ]
        PBITS  = 6
        XYBITS = (32 - PBITS)//2
        plc = numpy.uint32(0)
        plc  = numpy.uint32(placement.p & ((1 << PBITS) - 1))       | \
               numpy.uint32((placement.y & ((1 << XYBITS) - 1)) << PBITS) | \
               numpy.uint32((placement.x & ((1 << XYBITS) - 1)) << (XYBITS+PBITS))
        # print("==============_placement_to_uint32-=================")
        # print("{0:d}, {1:d}, {2:d} == 0x{3:08x}".format(
        #       placement.x, placement.y, placement.p, plc ))
        return plc


    def _is_delayed(self, synapse_info):
        conn = synapse_info.connector
        return numpy.uint32(conn.get_delay_maximum() > 16)

    def _write_on_machine_data_spec(self, spec, conn_dict, post_vertex_slice):
        """dictionary keys mean
        'n_edges': how many edges in total land in this vertex
        'flags': which of the edges requires on machine generation, encoded as bits
                 in 32-bit words
        'delay_placements': if the delays are larger than max per core, we need to
                            know the delay extension cores (unused here!)
        'data_block': data needed to generate connections, weights and delays
        'weight_scales': shifts from U88 fixed point to make better use of bits
        """
        if not self._any_gen_on_machine:
            return

        # print("WEIGHT SCALES ----------------------------------")
        # print(conn_dict['weight_scales'])
        # print("post count")
        # print( post_vertex_slice.n_atoms )
        # print("------------------------------------------------")
        if numpy.sum(conn_dict['flags']) == 0:
            return

        word_count = len(conn_dict['flags']) + len(conn_dict['data_block']) + \
                     len(conn_dict['weight_scales'])

        total_count = word_count + 2 + 1 + 1 + 1 + 1 + 1
                     # 2 for post_vertex_slice.lo_atom, post_vertex_slice.n_atoms
                     # 1 for n_edges
                     # 1 for size of data_block
                     # 1 for num_synapse_types
                     # 1 for synapse_bits
                     # 1 for num header words for plastic weights
        # print("in _write_on_machine_data_spec")
        # print(total_count)
        # print("Reserving connector builder region")
        spec.reserve_memory_region(
            region=POPULATION_BASED_REGIONS.CONNECTOR_BUILDER.value,
            size=total_count*4, label="ConnectorBuilderRegion")

        #TODO: all 32-bit words =( we can compress many of these!!!

        # print("Writing connector builder region")
        # print("Reserved a total of %u bytes"%(total_count*4))
        spec.switch_write_focus(
            region=POPULATION_BASED_REGIONS.CONNECTOR_BUILDER.value)

        spec.write_value(numpy.uint32(conn_dict['n_edges']), data_type=DataType.UINT32)
        for w in conn_dict['flags']:
            spec.write_value(w, data_type=DataType.UINT32)

        spec.write_value(post_vertex_slice.lo_atom, data_type=DataType.UINT32)
        spec.write_value(post_vertex_slice.n_atoms, data_type=DataType.UINT32)

        #how many synapse types do we have
        spec.write_value(len(conn_dict['weight_scales']), data_type=DataType.UINT32)

        #how many bits needed to encode all synapse types
        spec.write_value(int(numpy.ceil(numpy.log2(len(conn_dict['weight_scales'])))),
                         data_type=DataType.UINT32)

        #what are the weight scales for each synapse type
        for w in conn_dict['weight_scales']:
            # print("Weights scales %f"%w)
            v = numpy.log2(w)
            if v < 0:
                v = 0.
            else:
                v = numpy.ceil(v)
            v = numpy.int32(v)
            spec.write_value(v, data_type=DataType.INT32)

        # how many bytes we need to copy the data-block
        spec.write_value(len(conn_dict['data_block'])*4, data_type=DataType.UINT32)

        for i in range(len(conn_dict['data_block'])):
            w = conn_dict['data_block'][i]
            if numpy.issubdtype(type(w), numpy.integer):
                conn_dict['data_block'][i] = w#numpy.int32(w)
            else:
                conn_dict['data_block'][i] = numpy.int32(numpy.abs(
                                                numpy.round(w*(1<<16))))

        spec.write_array(conn_dict['data_block'])

        # for w in conn_dict['data_block']:
        #     if numpy.issubdtype(type(w), numpy.integer):
        #         spec.write_value(int(w), data_type=DataType.UINT32)
        #     else:
        #         spec.write_value(w, data_type=DataType.U1616)


        conn_dict['data_block'][:] = []
        del conn_dict['data_block']

        del conn_dict['weight_scales']

        del conn_dict['flags']

        conn_dict.clear()
        del conn_dict

        # print("Writing connector builder region --- finished")
