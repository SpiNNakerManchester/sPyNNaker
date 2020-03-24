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
from spinn_front_end_common.utilities.constants import \
    MICRO_TO_SECOND_CONVERSION

from collections import defaultdict
from six import iteritems
import math
import struct
import numpy
import scipy.stats  # @UnresolvedImport
from scipy import special  # @UnresolvedImport
from pyNN.random import RandomDistribution
from data_specification.enums import DataType
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.models.neuron.generator_data import GeneratorData
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from .synapse_dynamics import (
    AbstractSynapseDynamics, AbstractSynapseDynamicsStructural,
    AbstractGenerateOnMachine, SynapseDynamicsStructuralSTDP)
from spynnaker.pyNN.models.neuron.synapse_io import SynapseIORowBased
from spynnaker.pyNN.models.spike_source.spike_source_poisson_vertex import (
    SpikeSourcePoissonVertex)
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
from spynnaker.pyNN.utilities.constants import (
    POPULATION_BASED_REGIONS, POSSION_SIGMA_SUMMATION_LIMIT)
from spynnaker.pyNN.utilities.utility_calls import (
    get_maximum_probable_value, get_n_bits)
from spynnaker.pyNN.utilities.running_stats import RunningStats
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector)
from spynnaker.pyNN.models.neuron.synapse_dynamics import SynapseDynamicsStatic
from .key_space_tracker import KeySpaceTracker
from pacman.model.graphs.common.slice import Slice
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.models.neuron.master_pop_table import (
    MasterPopTableAsBinarySearch)

TIME_STAMP_BYTES = BYTES_PER_WORD

# TODO: Make sure these values are correct (particularly CPU cycles)
_SYNAPSES_BASE_DTCM_USAGE_IN_BYTES = 7 * BYTES_PER_WORD
_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES = 0
_SYNAPSES_BASE_N_CPU_CYCLES_PER_NEURON = 10
_SYNAPSES_BASE_N_CPU_CYCLES = 8

# 4 for n_edges
# 8 for post_vertex_slice.lo_atom, post_vertex_slice.n_atoms
# 4 for n_synapse_types
# 4 for n_synapse_type_bits
# 4 for n_synapse_index_bits
_SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES = 6 * BYTES_PER_WORD

# Amount to scale synapse SDRAM estimate by to make sure the synapses fit
_SYNAPSE_SDRAM_OVERSCALE = 1.1

# Struct to read or write a word
_ONE_WORD = struct.Struct("<I")

# A padding byte
_PADDING_BYTE = 0xDD

# Address to indicate that the synaptic region is unused
_SYN_REGION_UNUSED = 0xFFFFFFFF


class SynapticManager(object):
    """ Deals with synapses
    """
    # pylint: disable=too-many-arguments, too-many-locals
    __slots__ = [
        "__delay_key_index",
        "__n_synapse_types",
        "__one_to_one_connection_dtcm_max_bytes",
        "__poptable_type",
        "__pre_run_connection_holders",
        "__retrieved_blocks",
        "__ring_buffer_sigma",
        "__spikes_per_second",
        "__synapse_dynamics",
        "__synapse_io",
        "__weight_scales",
        "__ring_buffer_shifts",
        "__gen_on_machine",
        "__max_row_info",
        "__synapse_indices",
        "__app_edge_info",
        "__delay_edge_info",
        "__m_edge_info",
        "__delay_m_edge_info"]

    def __init__(self, n_synapse_types, ring_buffer_sigma, spikes_per_second,
                 config, population_table_type=None, synapse_io=None):
        self.__n_synapse_types = n_synapse_types
        self.__ring_buffer_sigma = ring_buffer_sigma
        self.__spikes_per_second = spikes_per_second

        # Get the type of population table
        self.__poptable_type = population_table_type
        if population_table_type is None:
            self.__poptable_type = MasterPopTableAsBinarySearch()

        # Get the synapse IO
        self.__synapse_io = synapse_io
        if synapse_io is None:
            self.__synapse_io = SynapseIORowBased()

        if self.__ring_buffer_sigma is None:
            self.__ring_buffer_sigma = config.getfloat(
                "Simulation", "ring_buffer_sigma")

        if self.__spikes_per_second is None:
            self.__spikes_per_second = config.getfloat(
                "Simulation", "spikes_per_second")

        # Prepare for dealing with STDP - there can only be one (non-static)
        # synapse dynamics per vertex at present
        self.__synapse_dynamics = None

        # Keep the details once computed to allow reading back
        self.__weight_scales = dict()
        self.__ring_buffer_shifts = None
        self.__delay_key_index = dict()
        self.__app_edge_info = dict()
        self.__delay_edge_info = dict()
        self.__m_edge_info = dict()
        self.__delay_m_edge_info = dict()
        self.__retrieved_blocks = dict()

        # A list of connection holders to be filled in pre-run, indexed by
        # the edge the connection is for
        self.__pre_run_connection_holders = defaultdict(list)

        # Limit the DTCM used by one-to-one connections
        self.__one_to_one_connection_dtcm_max_bytes = config.getint(
            "Simulation", "one_to_one_connection_dtcm_max_bytes")

        # Whether to generate on machine or not for a given vertex slice
        self.__gen_on_machine = dict()

        # A map of synapse information to maximum row / delayed row length and
        # size in bytes
        self.__max_row_info = dict()

        # A map of synapse information for each machine pre vertex to index
        self.__synapse_indices = dict()

    @property
    def synapse_dynamics(self):
        return self.__synapse_dynamics

    def __combine_structural_stdp_dynamics(self, structural, stdp):
        return SynapseDynamicsStructuralSTDP(
            structural.partner_selection, structural.formation,
            structural.elimination,
            stdp.timing_dependence, stdp.weight_dependence,
            # voltage dependence is not supported
            None, stdp.dendritic_delay_fraction,
            structural.f_rew, structural.initial_weight,
            structural.initial_delay, structural.s_max, structural.seed)

    @synapse_dynamics.setter
    def synapse_dynamics(self, synapse_dynamics):

        if self.__synapse_dynamics is None:
            self.__synapse_dynamics = synapse_dynamics
        else:
            self.__synapse_dynamics = self.__synapse_dynamics.merge(
                synapse_dynamics)

    @property
    def ring_buffer_sigma(self):
        return self.__ring_buffer_sigma

    @ring_buffer_sigma.setter
    def ring_buffer_sigma(self, ring_buffer_sigma):
        self.__ring_buffer_sigma = ring_buffer_sigma

    @property
    def spikes_per_second(self):
        return self.__spikes_per_second

    @spikes_per_second.setter
    def spikes_per_second(self, spikes_per_second):
        self.__spikes_per_second = spikes_per_second

    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        return self.__synapse_io.get_maximum_delay_supported_in_ms(
            machine_time_step)

    @property
    def vertex_executable_suffix(self):
        if self.__synapse_dynamics is None:
            return ""
        return self.__synapse_dynamics.get_vertex_executable_suffix()

    def add_pre_run_connection_holder(
            self, connection_holder, edge, synapse_info):
        self.__pre_run_connection_holders[edge, synapse_info].append(
            connection_holder)

    def get_connection_holders(self):
        return self.__pre_run_connection_holders

    def get_n_cpu_cycles(self):
        # TODO: Calculate this correctly
        return 0

    def get_dtcm_usage_in_bytes(self):
        # TODO: Calculate this correctly
        return 0

    def _get_synapse_params_size(self):
        return (_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES +
                (BYTES_PER_WORD * self.__n_synapse_types))

    def _get_static_synaptic_matrix_sdram_requirements(self):

        # 4 for address of direct addresses, and
        # 4 for the size of the direct addresses matrix in bytes
        return 2 * BYTES_PER_WORD

    def __get_max_row_info(
            self, synapse_info, post_vertex_slice, app_edge,
            machine_time_step):
        """ Get the maximum size of each row for a given slice of the vertex

        :rtype: MaxRowInfo
        """
        key = (synapse_info, post_vertex_slice.lo_atom,
               post_vertex_slice.hi_atom)
        if key not in self.__max_row_info:
            self.__max_row_info[key] = self.__synapse_io.get_max_row_info(
                synapse_info, post_vertex_slice,
                app_edge.n_delay_stages, self.__poptable_type,
                machine_time_step, app_edge)
        return self.__max_row_info[key]

    def _get_synaptic_blocks_size(
            self, post_vertex_slice, in_edges, machine_time_step):
        """ Get the size of the synaptic blocks in bytes
        """
        memory_size = self._get_static_synaptic_matrix_sdram_requirements()
        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionApplicationEdge):
                for synapse_info in in_edge.synapse_information:
                    memory_size = self.__add_synapse_size(
                        memory_size, synapse_info, post_vertex_slice, in_edge,
                        machine_time_step)
        return int(memory_size * _SYNAPSE_SDRAM_OVERSCALE)

    def __add_synapse_size(self, memory_size, synapse_info, post_vertex_slice,
                           in_edge, machine_time_step):
        max_row_info = self.__get_max_row_info(
            synapse_info, post_vertex_slice, in_edge, machine_time_step)
        n_atoms = in_edge.pre_vertex.n_atoms
        memory_size = self.__poptable_type.get_next_allowed_address(
            memory_size)
        memory_size += max_row_info.undelayed_max_bytes * n_atoms
        memory_size = self.__poptable_type.get_next_allowed_address(
            memory_size)
        memory_size += (
            max_row_info.delayed_max_bytes * n_atoms * in_edge.n_delay_stages)
        return memory_size

    def _get_size_of_generator_information(self, in_edges):
        """ Get the size of the synaptic expander parameters
        """
        gen_on_machine = False
        size = 0
        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionApplicationEdge):
                for synapse_info in in_edge.synapse_information:

                    # Get the number of likely vertices
                    max_atoms = in_edge.pre_vertex.get_max_atoms_per_core()
                    if in_edge.pre_vertex.n_atoms < max_atoms:
                        max_atoms = in_edge.pre_vertex.n_atoms
                    n_edge_vertices = int(math.ceil(
                        float(in_edge.pre_vertex.n_atoms) / float(max_atoms)))

                    # Get the size
                    connector = synapse_info.connector
                    dynamics = synapse_info.synapse_dynamics
                    connector_gen = isinstance(
                        connector, AbstractGenerateConnectorOnMachine) and \
                        connector.generate_on_machine(
                            synapse_info.weights, synapse_info.delays)
                    synapse_gen = isinstance(
                        dynamics, AbstractGenerateOnMachine)
                    if connector_gen and synapse_gen:
                        gen_on_machine = True
                        gen_size = sum((
                            GeneratorData.BASE_SIZE,
                            connector.gen_delay_params_size_in_bytes(
                                synapse_info.delays),
                            connector.gen_weight_params_size_in_bytes(
                                synapse_info.weights),
                            connector.gen_connector_params_size_in_bytes,
                            dynamics.gen_matrix_params_size_in_bytes
                        ))
                        size += gen_size * n_edge_vertices
        if gen_on_machine:
            size += _SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES
            size += self.__n_synapse_types * BYTES_PER_WORD
        return size

    def _get_synapse_dynamics_parameter_size(
            self, vertex_slice, application_graph, app_vertex):
        """ Get the size of the synapse dynamics region
        """
        if self.__synapse_dynamics is None:
            return 0

        # Does the size of the parameters area depend on presynaptic
        # connections in any way?
        if isinstance(self.__synapse_dynamics,
                      AbstractSynapseDynamicsStructural):
            return self.__synapse_dynamics\
                .get_structural_parameters_sdram_usage_in_bytes(
                     application_graph, app_vertex, vertex_slice.n_atoms,
                     self.__n_synapse_types)
        else:
            return self.__synapse_dynamics.get_parameters_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self.__n_synapse_types)

    def get_sdram_usage_in_bytes(
            self, vertex_slice, machine_time_step, application_graph,
            app_vertex):
        in_edges = application_graph.get_edges_ending_at_vertex(app_vertex)
        return (
            self._get_synapse_params_size() +
            self._get_synapse_dynamics_parameter_size(
                vertex_slice, application_graph, app_vertex) +
            self._get_synaptic_blocks_size(
                vertex_slice, in_edges, machine_time_step) +
            self.__poptable_type.get_master_population_table_size(in_edges) +
            self._get_size_of_generator_information(in_edges))

    def _reserve_memory_regions(
            self, spec, vertex_slice, all_syn_block_sz, application_graph,
            application_vertex):
        spec.reserve_memory_region(
            region=POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value,
            size=self._get_synapse_params_size(),
            label='SynapseParams')

        if all_syn_block_sz > 0:
            spec.reserve_memory_region(
                region=POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
                size=all_syn_block_sz, label='SynBlocks')

        synapse_dynamics_sz = self._get_synapse_dynamics_parameter_size(
            vertex_slice, application_graph, application_vertex)
        if synapse_dynamics_sz != 0:
            spec.reserve_memory_region(
                region=POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value,
                size=synapse_dynamics_sz, label='synapseDynamicsParams')

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
        steps_per_second = MICRO_TO_SECOND_CONVERSION / machine_timestep
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
            # pylint: disable=no-member
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
            self, application_vertex, application_graph, machine_timestep,
            weight_scale):
        """ Get the scaling of the ring buffer to provide as much accuracy as\
            possible without too much overflow
        """
        weight_scale_squared = weight_scale * weight_scale
        n_synapse_types = self.__n_synapse_types
        running_totals = [RunningStats() for _ in range(n_synapse_types)]
        delay_running_totals = [RunningStats() for _ in range(n_synapse_types)]
        total_weights = numpy.zeros(n_synapse_types)
        biggest_weight = numpy.zeros(n_synapse_types)
        weights_signed = False
        rate_stats = [RunningStats() for _ in range(n_synapse_types)]
        steps_per_second = MICRO_TO_SECOND_CONVERSION / machine_timestep

        for app_edge in application_graph.get_edges_ending_at_vertex(
                application_vertex):
            if isinstance(app_edge, ProjectionApplicationEdge):
                for synapse_info in app_edge.synapse_information:
                    synapse_type = synapse_info.synapse_type
                    synapse_dynamics = synapse_info.synapse_dynamics
                    connector = synapse_info.connector

                    weight_mean = (
                        synapse_dynamics.get_weight_mean(
                            connector, synapse_info) * weight_scale)
                    n_connections = \
                        connector.get_n_connections_to_post_vertex_maximum(
                            synapse_info)
                    weight_variance = synapse_dynamics.get_weight_variance(
                        connector, synapse_info.weights) * weight_scale_squared
                    running_totals[synapse_type].add_items(
                        weight_mean, weight_variance, n_connections)

                    delay_variance = synapse_dynamics.get_delay_variance(
                        connector, synapse_info.delays)
                    delay_running_totals[synapse_type].add_items(
                        0.0, delay_variance, n_connections)

                    weight_max = (synapse_dynamics.get_weight_maximum(
                        connector, synapse_info) * weight_scale)
                    biggest_weight[synapse_type] = max(
                        biggest_weight[synapse_type], weight_max)

                    spikes_per_tick = max(
                        1.0, self.__spikes_per_second / steps_per_second)
                    spikes_per_second = self.__spikes_per_second
                    if isinstance(app_edge.pre_vertex,
                                  SpikeSourcePoissonVertex):
                        rate = app_edge.pre_vertex.max_rate
                        # If non-zero rate then use it; otherwise keep default
                        if rate != 0:
                            spikes_per_second = rate
                        if hasattr(spikes_per_second, "__getitem__"):
                            spikes_per_second = numpy.max(spikes_per_second)
                        elif isinstance(spikes_per_second, RandomDistribution):
                            spikes_per_second = get_maximum_probable_value(
                                spikes_per_second, app_edge.pre_vertex.n_atoms)
                        prob = 1.0 - (
                            (1.0 / 100.0) / app_edge.pre_vertex.n_atoms)
                        spikes_per_tick = spikes_per_second / steps_per_second
                        spikes_per_tick = scipy.stats.poisson.ppf(
                            prob, spikes_per_tick)
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
                        self.__ring_buffer_sigma),
                    total_weights[synapse_type])
                max_weights[synapse_type] = max(
                    max_weights[synapse_type], biggest_weight[synapse_type])

        # Convert these to powers
        max_weight_powers = (
            0 if w <= 0 else int(math.ceil(max(0, math.log(w, 2))))
            for w in max_weights)

        # If 2^max_weight_power equals the max weight, we have to add another
        # power, as range is 0 - (just under 2^max_weight_power)!
        max_weight_powers = (
            w + 1 if (2 ** w) <= a else w
            for w, a in zip(max_weight_powers, max_weights))

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
            self, spec, ring_buffer_shifts, weight_scale):
        """Get the ring buffer shifts and scaling factors."""

        # Write the ring buffer shifts
        spec.switch_write_focus(POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value)
        spec.write_array(ring_buffer_shifts)

        # Return the weight scaling factors
        return numpy.array([
            self._get_weight_scale(r) * weight_scale
            for r in ring_buffer_shifts])

    def _write_pop_table_padding(self, spec, next_block_start_address):
        next_block_allowed_address = self.__poptable_type\
            .get_next_allowed_address(next_block_start_address)
        padding = next_block_allowed_address - next_block_start_address
        if padding != 0:

            # Pad out data file with the added alignment bytes:
            spec.comment("\nWriting population table required padding\n")
            spec.write_array(numpy.repeat(
                numpy.array(_PADDING_BYTE, dtype="uint8"), padding).view(
                    "uint32"))
            return next_block_allowed_address
        return next_block_start_address

    def _write_synaptic_matrix_and_master_population_table(
            self, spec, post_slices, post_slice_index, machine_vertex,
            post_vertex_slice, all_syn_block_sz, weight_scales,
            routing_info, graph_mapper, machine_graph, machine_time_step):
        """ Simultaneously generates both the master population table and
            the synaptic matrix.
        """
        spec.comment(
            "\nWriting Synaptic Matrix and Master Population Table:\n")

        # Track writes inside the synaptic matrix region:
        block_addr = 0

        # Get the application projection edges incoming to this machine vertex
        in_machine_edges = machine_graph.get_edges_ending_at_vertex(
            machine_vertex)
        in_edges_by_app_edge, key_space_tracker = self.__in_edges_by_app_edge(
            in_machine_edges, routing_info, graph_mapper)

        # Set up the master population table
        self.__poptable_type.initialise_table()

        # Set up for single synapses
        # The list is seeded with an empty array so we can just concatenate
        # later (as numpy doesn't let you concatenate nothing)
        single_synapses = [numpy.array([], dtype="uint32")]
        single_addr = 0

        # Lets write some synapses
        spec.switch_write_focus(POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value)

        # Store a list of synapse info to be generated on the machine
        generate_on_machine = list()

        # For each machine edge in the vertex, create a synaptic list
        for app_edge, m_edges in iteritems(in_edges_by_app_edge):

            spec.comment("\nWriting matrix for edge:{}\n".format(
                app_edge.label))
            app_key_info = self.__app_key_and_mask(
                graph_mapper, m_edges, app_edge, routing_info,
                key_space_tracker)
            d_app_key_info = self.__delay_app_key_and_mask(
                graph_mapper, m_edges, app_edge, key_space_tracker)
            pre_slices = graph_mapper.get_slices(app_edge.pre_vertex)

            for synapse_info in app_edge.synapse_information:

                # If we can generate the connector on the machine, do so
                if self.__can_generate_on_machine(
                        app_edge, synapse_info, m_edges, graph_mapper,
                        post_vertex_slice, single_addr):
                    generate_on_machine.append(
                        (app_edge, m_edges, synapse_info, app_key_info,
                         d_app_key_info, pre_slices))
                else:
                    block_addr, single_addr = self.__write_matrix(
                        m_edges, graph_mapper, synapse_info, pre_slices,
                        post_slices, post_slice_index, post_vertex_slice,
                        app_edge, weight_scales, machine_time_step,
                        app_key_info, d_app_key_info, block_addr, single_addr,
                        spec, all_syn_block_sz, single_synapses, routing_info)

        # Skip blocks that will be written on the machine, but add them
        # to the master population table
        generator_data = list()
        for gen_data in generate_on_machine:
            (app_edge, m_edges, synapse_info, app_key_info, d_app_key_info,
             pre_slices) = gen_data
            block_addr = self.__write_on_chip_matrix_data(
                m_edges, graph_mapper, synapse_info, pre_slices, post_slices,
                post_slice_index, post_vertex_slice, app_edge,
                machine_time_step, app_key_info, d_app_key_info, block_addr,
                all_syn_block_sz, generator_data, routing_info)

        # Finish the master population table
        self.__poptable_type.finish_master_pop_table(
            spec, POPULATION_BASED_REGIONS.POPULATION_TABLE.value)

        # Write the size and data of single synapses to the direct region
        single_data = numpy.concatenate(single_synapses)
        single_data_words = len(single_data)
        spec.reserve_memory_region(
            region=POPULATION_BASED_REGIONS.DIRECT_MATRIX.value,
            size=(single_data_words + 1) * BYTES_PER_WORD,
            label='DirectMatrix')
        spec.switch_write_focus(POPULATION_BASED_REGIONS.DIRECT_MATRIX.value)
        spec.write_value(single_data_words * BYTES_PER_WORD)
        if single_data_words:
            spec.write_array(single_data)

        return generator_data

    def __in_edges_by_app_edge(
            self, in_machine_edges, routing_info, graph_mapper):
        """ Get machine edges by application edge dictionary
        """
        in_edges_by_app_edge = defaultdict(list)
        key_space_tracker = KeySpaceTracker()
        for edge in in_machine_edges:
            rinfo = routing_info.get_routing_info_for_edge(edge)
            key_space_tracker.allocate_keys(rinfo)
            app_edge = graph_mapper.get_application_edge(edge)
            if isinstance(app_edge, ProjectionApplicationEdge):
                in_edges_by_app_edge[app_edge].append(edge)
        return in_edges_by_app_edge, key_space_tracker

    def __can_generate_on_machine(
            self, app_edge, s_info, m_edges, graph_mapper, post_vertex_slice,
            single_addr):
        """ Determine if an app edge can be generated on the machine
        """
        return (
            isinstance(
                s_info.connector, AbstractGenerateConnectorOnMachine) and
            s_info.connector.generate_on_machine(
                s_info.weights, s_info.delays) and
            isinstance(s_info.synapse_dynamics, AbstractGenerateOnMachine) and
            s_info.synapse_dynamics.generate_on_machine and
            not self.__is_app_edge_direct(
                app_edge, s_info, m_edges, graph_mapper, post_vertex_slice,
                single_addr) and
            not isinstance(
                self.synapse_dynamics, AbstractSynapseDynamicsStructural)
        )

    def __is_app_edge_direct(
            self, app_edge, synapse_info, m_edges, graph_mapper,
            post_vertex_slice, single_addr):
        """ Determine if an app edge can use the direct matrix for all of its\
            synapse information
        """
        next_single_addr = single_addr
        for m_edge in m_edges:
            pre_slice = graph_mapper.get_slice(m_edge.pre_vertex)
            if not self.__is_direct(
                    next_single_addr, synapse_info, pre_slice,
                    post_vertex_slice, app_edge.n_delay_stages > 0):
                return False
            next_single_addr += pre_slice.n_atoms * BYTES_PER_WORD
        return True

    def __write_matrix(
            self, m_edges, graph_mapper, synapse_info, pre_slices, post_slices,
            post_slice_index, post_vertex_slice, app_edge, weight_scales,
            machine_time_step, app_key_info, delay_app_key_info, block_addr,
            single_addr, spec, all_syn_block_sz, single_synapses,
            routing_info):
        """ Write a synaptic matrix from host
        """
        # Write the synaptic matrix for an incoming application vertex
        max_row_info = self.__get_max_row_info(
            synapse_info, post_vertex_slice, app_edge, machine_time_step)
        is_undelayed = bool(max_row_info.undelayed_max_n_synapses)
        is_delayed = bool(max_row_info.delayed_max_n_synapses)
        undelayed_matrix_data = list()
        delayed_matrix_data = list()
        for m_edge in m_edges:
            # Get a synaptic matrix for each machine edge
            pre_idx = graph_mapper.get_machine_vertex_index(m_edge.pre_vertex)
            pre_slice = graph_mapper.get_slice(m_edge.pre_vertex)
            row_data, delay_row_data = self.__get_row_data(
                synapse_info, pre_slices, pre_idx, post_slices,
                post_slice_index, pre_slice, post_vertex_slice, app_edge,
                self.__n_synapse_types, weight_scales, machine_time_step,
                m_edge, max_row_info)

            # If there is a single edge here, we allow the one-to-one direct
            # matrix to be used by using write_machine_matrix; it will make
            # no difference if this isn't actually a direct edge since there
            # is only one anyway...
            if app_key_info is None or len(m_edges) == 1:
                r_info = routing_info.get_routing_info_for_edge(m_edge)
                block_addr, single_addr = self.__write_machine_matrix(
                    block_addr, single_addr, spec,
                    max_row_info.undelayed_max_n_synapses,
                    max_row_info.undelayed_max_words, r_info, row_data,
                    synapse_info, pre_slice, post_vertex_slice,
                    single_synapses, all_syn_block_sz, is_delayed,
                    m_edge, self.__m_edge_info)
            elif is_undelayed:
                # If there is an app_key, save the data to be written later
                # Note: row_data will not be blank here since we told it to
                # generate a matrix of a given size
                undelayed_matrix_data.append((m_edge, pre_slice, row_data))

            if delay_app_key_info is None:
                delay_key = (app_edge.pre_vertex,
                             pre_slice.lo_atom, pre_slice.hi_atom)
                r_info = self.__delay_key_index.get(delay_key, None)
                block_addr, single_addr = self.__write_machine_matrix(
                    block_addr, single_addr, spec,
                    max_row_info.delayed_max_n_synapses,
                    max_row_info.delayed_max_words, r_info,
                    delay_row_data, synapse_info, pre_slice,
                    post_vertex_slice, single_synapses, all_syn_block_sz,
                    True, m_edge, self.__delay_m_edge_info)
            elif is_delayed:
                # If there is a delay_app_key, save the data for delays
                # Note delayed_row_data will not be blank as above.
                delayed_matrix_data.append((m_edge, pre_slice, delay_row_data))

        # If there is an app key, add a single matrix and entry
        # to the population table but also put in padding
        # between tables when necessary
        if app_key_info is not None and len(m_edges) > 1:
            n_delay_stages = 1
            block_addr = self.__write_app_matrix(
                block_addr, spec, max_row_info.undelayed_max_words,
                max_row_info.undelayed_max_bytes, app_key_info,
                undelayed_matrix_data, all_syn_block_sz, n_delay_stages,
                post_vertex_slice, synapse_info, app_edge,
                self.__app_edge_info)
        if delay_app_key_info is not None:
            block_addr = self.__write_app_matrix(
                block_addr, spec, max_row_info.delayed_max_words,
                max_row_info.delayed_max_bytes, delay_app_key_info,
                delayed_matrix_data, all_syn_block_sz, app_edge.n_delay_stages,
                post_vertex_slice, synapse_info, app_edge,
                self.__delay_edge_info)

        return block_addr, single_addr

    def __update_synapse_index(self, synapse_info, post_slice, index):
        """ Update the index of a synapse, checking it matches against indices\
            for other synapse_info for the same edge
        """
        if (synapse_info, post_slice.lo_atom) not in self.__synapse_indices:
            self.__synapse_indices[synapse_info, post_slice.lo_atom] = index
        elif self.__synapse_indices[synapse_info, post_slice.lo_atom] != index:
            # This should never happen as things should be aligned over all
            # machine vertices, but check just in case!
            raise Exception("Index of " + synapse_info + " has changed!")

    def __write_app_matrix(
            self, block_addr, spec, max_words, max_bytes, app_key_info,
            matrix_data, all_syn_block_sz, n_ranges, post_slice, synapse_info,
            app_edge, edge_info):
        """ Write a matrix for a whole incoming application vertex as one
        """

        # If there are no synapses, just write an invalid pop table entry
        if max_words == 0:
            self.__poptable_type.add_invalid_entry(
                app_key_info.key_and_mask, app_key_info.core_mask,
                app_key_info.core_shift, app_key_info.n_neurons)
            return block_addr

        # Write a matrix for the whole application vertex
        block_addr = self._write_pop_table_padding(spec, block_addr)
        index = self.__poptable_type.update_master_population_table(
            block_addr, max_words, app_key_info.key_and_mask,
            app_key_info.core_mask, app_key_info.core_shift,
            app_key_info.n_neurons)
        self.__update_synapse_index(synapse_info, post_slice, index)
        syn_mat_addr = block_addr

        # Write all the row data for each machine vertex one after the other.
        # Implicit assumption that no machine-level row_data is ever empty;
        # this must be true in the current code, because the row length is
        # fixed for all synaptic matrices from the same source application
        # vertex
        for _, pre_slice, row_data in matrix_data:
            spec.write_array(row_data)
            n_rows = pre_slice.n_atoms * n_ranges
            block_addr = block_addr + (max_bytes * n_rows)
            if block_addr > all_syn_block_sz:
                raise Exception(
                    "Too much synaptic memory has been written: {} of {} "
                    .format(block_addr, all_syn_block_sz))

        # Store the data to be used to read synapses
        key = (app_edge, synapse_info, post_slice.lo_atom)
        size = block_addr - syn_mat_addr
        edge_info[key] = (syn_mat_addr, max_words, size)
        return block_addr

    def __write_machine_matrix(
            self, block_addr, single_addr, spec, max_synapses, max_words,
            r_info, row_data, synapse_info, pre_slice, post_vertex_slice,
            single_synapses, all_syn_block_sz, is_delayed, m_edge,
            m_edge_info):
        """ Write a matrix for an incoming machine vertex
        """
        # If there are no synapses, don't write anything
        if max_synapses == 0:
            # If there is routing information, write an invalid entry
            if r_info is not None:
                self.__poptable_type.add_invalid_entry(
                    r_info.first_key_and_mask)
            return block_addr, single_addr

        # If the matrix is direct, write direct
        if max_synapses == 1 and self.__is_direct(
                single_addr, synapse_info, pre_slice, post_vertex_slice,
                is_delayed):
            return self.__write_single_machine_matrix(
                block_addr, single_addr, max_words, r_info, row_data,
                synapse_info, post_vertex_slice, single_synapses, m_edge,
                m_edge_info)

        block_addr = self._write_pop_table_padding(spec, block_addr)
        index = self.__poptable_type.update_master_population_table(
            block_addr, max_words, r_info.first_key_and_mask, 0, 0, 0)
        self.__update_synapse_index(synapse_info, post_vertex_slice, index)
        spec.write_array(row_data)
        syn_mat_addr = block_addr
        block_addr = block_addr + (len(row_data) * 4)
        if block_addr > all_syn_block_sz:
            raise Exception(
                "Too much synaptic memory has been written: {} of {} "
                .format(block_addr, all_syn_block_sz))

        key = (m_edge, synapse_info, post_vertex_slice.lo_atom)
        size = block_addr - syn_mat_addr
        m_edge_info[key] = (syn_mat_addr, max_words, size, False)
        return block_addr, single_addr

    def __write_single_machine_matrix(
            self, block_addr, single_addr, max_words, r_info, row_data,
            synapse_info, post_vertex_slice, single_synapses, m_edge,
            m_edge_info):
        """ Write a direct (single synapse) matrix for an incoming machine\
            vertex
        """
        single_rows = row_data.reshape(-1, 4)[:, 3]
        index = self.__poptable_type.update_master_population_table(
            single_addr, max_words, r_info.first_key_and_mask, 0, 0, 0,
            is_single=True)
        self.__update_synapse_index(synapse_info, post_vertex_slice, index)
        single_synapses.append(single_rows)
        syn_mat_addr = single_addr
        single_addr = single_addr + (len(single_rows) * 4)
        size = single_addr - syn_mat_addr
        key = (m_edge, synapse_info, post_vertex_slice.lo_atom)
        m_edge_info[key] = (syn_mat_addr, max_words, size, True)
        return block_addr, single_addr

    @staticmethod
    def __check_keys_adjacent(keys, mask_size):
        """ Check that keys are all adjacent
        """
        key_increment = (1 << mask_size)
        last_key = None
        last_slice = None
        for i, (key, v_slice) in enumerate(keys):
            # If the first round, we can skip the checks and just store
            if last_key is not None:
                # Fail if next key is not adjacent to last key
                if (last_key + key_increment) != key:
                    return False

                # Fail if this is not the last key and the number of atoms
                # don't match the other keys (last is OK to be different)
                elif ((i + 1) < len(keys) and
                        last_slice.n_atoms != v_slice.n_atoms):
                    return False

                # Fail if the atoms are not adjacent
                elif (last_slice.hi_atom + 1) != v_slice.lo_atom:
                    return False

            # Store for the next round
            last_key = key
            last_slice = v_slice

        # Pass if nothing failed
        return True

    def __get_app_key_and_mask(self, keys, mask, n_stages, key_space_tracker):
        """ Get a key and mask for an incoming application vertex as a whole,\
            or say it isn't possible (return None)
        """

        # Can be merged only if keys are adjacent outside the mask
        keys = sorted(keys, key=lambda item: item[0])
        mask_size = KeySpaceTracker.count_trailing_0s(mask)
        if not self.__check_keys_adjacent(keys, mask_size):
            return None

        # Get the key as the first key and the mask as the mask that covers
        # enough keys
        key = keys[0][0]
        n_extra_mask_bits = int(math.ceil(math.log(len(keys), 2)))
        core_mask = (2 ** n_extra_mask_bits) - 1
        new_mask = mask & ~(core_mask << mask_size)

        # Final check because adjacent keys don't mean they all fit under a
        # single mask
        if key & new_mask != key:
            return None

        # Check that the key doesn't cover other keys that it shouldn't
        next_key = keys[-1][0] + (2 ** mask_size)
        max_key = key + (2 ** (mask_size + n_extra_mask_bits))
        n_unused = max_key - (next_key & mask)
        if n_unused > 0 and key_space_tracker.is_allocated(next_key, n_unused):
            return None

        return _AppKeyInfo(key, new_mask, core_mask, mask_size,
                           keys[0][1].n_atoms * n_stages)

    def __check_key_slices(self, n_atoms, slices):
        """ Check if a list of slices cover all n_atoms without any gaps
        """
        slices = sorted(slices, key=lambda s: s.lo_atom)
        slice_atoms = slices[-1].hi_atom - slices[0].lo_atom + 1
        if slice_atoms != n_atoms:
            return False

        # Check that all slices are also there in between, and that all are
        # the same size (except the last one)
        next_high = 0
        n_atoms_per_core = None
        last_slice = slices[-1]
        for s in slices:
            if s.lo_atom != next_high:
                return False
            if (n_atoms_per_core is not None and s != last_slice and
                    n_atoms_per_core != s.n_atoms):
                return None
            next_high = s.hi_atom + 1
            n_atoms_per_core = s.n_atoms

        # If the number of atoms per core is too big, this can't be done
        if n_atoms_per_core > self.__poptable_type.max_n_neurons_per_core:
            return False
        return True

    def __app_key_and_mask(self, graph_mapper, m_edges, app_edge, routing_info,
                           key_space_tracker):
        """ Get a key and mask for an incoming application vertex as a whole,\
            or say it isn't possible (return None)
        """
        # If there are too many pre-cores, give up now
        if len(m_edges) > self.__poptable_type.max_core_mask:
            return None

        # Work out if the keys allow the machine vertices to be merged
        mask = None
        keys = list()

        # Can be merged only if all the masks are the same
        pre_slices = list()
        for m_edge in m_edges:
            rinfo = routing_info.get_routing_info_for_edge(m_edge)
            vertex_slice = graph_mapper.get_slice(m_edge.pre_vertex)
            pre_slices.append(vertex_slice)
            # No routing info at all? Odd but doesn't work...
            if rinfo is None:
                return None
            # Mask is not the same as the last mask?  Doesn't work...
            if mask is not None and rinfo.first_mask != mask:
                return None
            mask = rinfo.first_mask
            keys.append((rinfo.first_key, vertex_slice))

        if mask is None:
            return None

        if not self.__check_key_slices(
                app_edge.pre_vertex.n_atoms, pre_slices):
            return None

        return self.__get_app_key_and_mask(keys, mask, 1, key_space_tracker)

    def __delay_app_key_and_mask(self, graph_mapper, m_edges, app_edge,
                                 key_space_tracker):
        """ Get a key and mask for a whole incoming delayed application\
            vertex, or say it isn't possible (return None)
        """
        # Work out if the keys allow the machine vertices to be
        # merged
        mask = None
        keys = list()

        # Can be merged only if all the masks are the same
        pre_slices = list()
        for m_edge in m_edges:
            pre_vertex_slice = graph_mapper.get_slice(m_edge.pre_vertex)
            pre_slices.append(pre_vertex_slice)
            delay_info_key = (app_edge.pre_vertex, pre_vertex_slice.lo_atom,
                              pre_vertex_slice.hi_atom)
            rinfo = self.__delay_key_index.get(delay_info_key, None)
            if rinfo is None:
                return None
            if mask is not None and rinfo.first_mask != mask:
                return None
            mask = rinfo.first_mask
            keys.append((rinfo.first_key, pre_vertex_slice))

        if not self.__check_key_slices(
                app_edge.pre_vertex.n_atoms, pre_slices):
            return None

        return self.__get_app_key_and_mask(keys, mask, app_edge.n_delay_stages,
                                           key_space_tracker)

    def __write_on_chip_matrix_data(
            self, m_edges, graph_mapper, synapse_info, pre_slices, post_slices,
            post_slice_index, post_vertex_slice, app_edge, machine_time_step,
            app_key_info, delay_app_key_info, block_addr, all_syn_block_sz,
            generator_data, routing_info):
        """ Prepare to write a matrix using an on-chip generator
        """
        max_row_info = self.__get_max_row_info(
            synapse_info, post_vertex_slice, app_edge, machine_time_step)
        is_undelayed = bool(max_row_info.undelayed_max_n_synapses)
        is_delayed = bool(max_row_info.delayed_max_n_synapses)

        # Reserve the space in the matrix for an application-level key,
        # and tell the pop table
        (block_addr, syn_addr, delay_addr, syn_max_addr,
         delay_max_addr) = self.__reserve_app_blocks(
             is_undelayed, is_delayed, app_key_info, delay_app_key_info,
             block_addr, max_row_info, all_syn_block_sz, app_edge,
             post_vertex_slice, synapse_info)

        # Go through the edges of the application edge and write data for the
        # generator
        for m_edge in m_edges:
            # Store the address to generate the matrix from, assuming an
            # application vertex matrix; this will change later if not
            syn_mat_offset = syn_addr
            d_mat_offset = delay_addr

            # Get machine pre-vertex information
            pre_idx = graph_mapper.get_machine_vertex_index(m_edge.pre_vertex)
            pre_slice = graph_mapper.get_slice(m_edge.pre_vertex)

            # Write the information needed to generate delays
            self.__write_on_chip_delay_data(
                max_row_info, app_edge, pre_slices, pre_idx, post_slices,
                post_slice_index, pre_slice, post_vertex_slice, synapse_info,
                machine_time_step)

            # Update addresses for undelayed vertices
            r_info = routing_info.get_routing_info_for_edge(m_edge)
            syn_addr, block_addr, syn_mat_offset = self.__on_chip_addresses(
                is_undelayed, app_key_info, syn_addr, pre_slice.n_atoms,
                max_row_info.undelayed_max_bytes,
                max_row_info.undelayed_max_words, syn_max_addr, r_info,
                m_edge, block_addr, all_syn_block_sz, post_vertex_slice,
                synapse_info, syn_mat_offset, self.__m_edge_info)

            # Update addresses for delayed vertices
            delay_key = (app_edge.pre_vertex, pre_slice.lo_atom,
                         pre_slice.hi_atom)
            delay_r_info = self.__delay_key_index.get(delay_key, None)
            delay_addr, block_addr, d_mat_offset = self.__on_chip_addresses(
                is_delayed, delay_app_key_info, delay_addr,
                pre_slice.n_atoms * app_edge.n_delay_stages,
                max_row_info.delayed_max_bytes, max_row_info.delayed_max_words,
                delay_max_addr, delay_r_info, m_edge, block_addr,
                all_syn_block_sz, post_vertex_slice, synapse_info,
                d_mat_offset, self.__delay_m_edge_info)

            # Create the generator data and note it exists for this post vertex
            # Note generator data is written per machine-edge even when a whole
            # application vertex matrix exists, because these are just appended
            # to each other in the latter case; this makes it easier to
            # generate since it is still doing it in chunks, so less local
            # memory is needed.
            generator_data.append(GeneratorData(
                syn_mat_offset, d_mat_offset,
                max_row_info.undelayed_max_words,
                max_row_info.delayed_max_words,
                max_row_info.undelayed_max_n_synapses,
                max_row_info.delayed_max_n_synapses, pre_slices, pre_idx,
                post_slices, post_slice_index, pre_slice, post_vertex_slice,
                synapse_info, app_edge.n_delay_stages + 1, machine_time_step))
            key = (post_vertex_slice.lo_atom, post_vertex_slice.hi_atom)
            self.__gen_on_machine[key] = True
        return block_addr

    def __on_chip_addresses(
            self, is_synapses, app_key_info, syn_block_addr, n_rows,
            max_bytes, max_words, max_addr, r_info, m_edge,
            block_addr, all_syn_block_sz, post_vertex_slice, synapse_info,
            syn_mat_offset, m_edge_info):
        """ Get and update addresses where data is to be written to by the\
            on-chip expander.
        """
        if is_synapses and app_key_info is not None:
            # If there is a single matrix for the app vertex, jump over the
            # matrix and any padding space
            syn_block_addr = self.__next_app_syn_block_addr(
                syn_block_addr, n_rows, max_bytes, max_addr)
            return syn_block_addr, block_addr, syn_mat_offset

        if app_key_info is None:
            # If there isn't a single matrix, add master population table
            # entries for each incoming machine vertex
            if is_synapses:
                block_addr, syn_mat_offset = self.__reserve_machine_block(
                    r_info, block_addr, max_bytes, max_words, all_syn_block_sz,
                    n_rows, post_vertex_slice, synapse_info, m_edge,
                    m_edge_info)
                return syn_block_addr, block_addr, syn_mat_offset

            if r_info is not None:
                self.__poptable_type.add_invalid_entry(
                    r_info.first_key_and_mask)

        return syn_block_addr, block_addr, syn_mat_offset

    def __reserve_app_blocks(
            self, is_undelayed, is_delayed, app_key_info, delay_app_key_info,
            block_addr, max_row_info, all_syn_block_sz, app_edge,
            post_vertex_slice, synapse_info):
        """ Reserve blocks for a whole-application-vertex matrix if possible,\
            and tell the master population table
        """
        syn_block_addr = _SYN_REGION_UNUSED
        syn_max_addr = None
        if is_undelayed and app_key_info is not None:
            block_addr, syn_block_addr = self.__reserve_app_block(
                block_addr, max_row_info.undelayed_max_bytes,
                max_row_info.undelayed_max_words, app_key_info,
                all_syn_block_sz, app_edge, app_edge.pre_vertex.n_atoms,
                post_vertex_slice, synapse_info, self.__app_edge_info)
            syn_max_addr = block_addr
        elif app_key_info is not None:
            self.__poptable_type.add_invalid_entry(
                app_key_info.key_and_mask, app_key_info.core_mask,
                app_key_info.core_shift, app_key_info.n_neurons)

        delay_block_addr = _SYN_REGION_UNUSED
        delay_max_addr = None
        if is_delayed and delay_app_key_info is not None:
            block_addr, delay_block_addr = self.__reserve_app_block(
                block_addr, max_row_info.delayed_max_bytes,
                max_row_info.delayed_max_words, delay_app_key_info,
                all_syn_block_sz, app_edge,
                app_edge.pre_vertex.n_atoms * app_edge.n_delay_stages,
                post_vertex_slice, synapse_info, self.__delay_edge_info)
            delay_max_addr = block_addr
        elif delay_app_key_info is not None:
            self.__poptable_type.add_invalid_entry(
                delay_app_key_info.key_and_mask, delay_app_key_info.core_mask,
                delay_app_key_info.core_shift, delay_app_key_info.n_neurons)
        return (block_addr, syn_block_addr, delay_block_addr, syn_max_addr,
                delay_max_addr)

    def __reserve_app_block(
            self, block_addr, max_bytes, max_words, app_key_info,
            all_syn_block_sz, app_edge, n_rows, post_vertex_slice,
            synapse_info, edge_info):
        """ Reserve a block for the matrix of an incoming application vertex,\
            and store the details for later retrieval
        """
        block_addr, syn_block_addr = self.__reserve_mpop_block(
            block_addr, max_bytes, max_words, app_key_info.key_and_mask,
            all_syn_block_sz, n_rows, post_vertex_slice,
            synapse_info, app_key_info.core_mask, app_key_info.core_shift,
            app_key_info.n_neurons)
        key = (app_edge, synapse_info, post_vertex_slice.lo_atom)
        size = block_addr - syn_block_addr
        edge_info[key] = (syn_block_addr, max_words, size)
        return block_addr, syn_block_addr

    def __reserve_machine_block(
            self, r_info, block_addr, max_bytes, max_words, all_syn_block_sz,
            n_rows, post_vertex_slice, synapse_info, m_edge, m_edge_info):
        """ Reserve a block for the matrix of an incoming machine vertex,\
            and store the details for later retrieval
        """
        block_addr, syn_mat_offset = self.__reserve_mpop_block(
            block_addr, max_bytes, max_words, r_info.first_key_and_mask,
            all_syn_block_sz, n_rows, post_vertex_slice, synapse_info)
        key = (m_edge, synapse_info, post_vertex_slice.lo_atom)
        size = block_addr - syn_mat_offset
        m_edge_info[key] = (syn_mat_offset, max_words, size, False)
        return block_addr, syn_mat_offset

    def __reserve_mpop_block(
            self, block_addr, max_bytes, max_words, key_and_mask,
            all_syn_block_sz, n_rows, post_slice, synapse_info,
            core_mask=0, core_shift=0, n_neurons=0):
        """ Reserve a block in the master population table and check it hasn't\
            overrun the allocation
        """
        block_addr = self.__poptable_type.get_next_allowed_address(
            block_addr)
        index = self.__poptable_type.update_master_population_table(
            block_addr, max_words, key_and_mask, core_mask, core_shift,
            n_neurons)
        self.__update_synapse_index(synapse_info, post_slice, index)
        syn_block_addr = block_addr
        block_addr += max_bytes * n_rows
        if block_addr > all_syn_block_sz:
            raise Exception(
                "Too much synaptic memory has been reserved: {} of {}".format(
                    block_addr, all_syn_block_sz))
        return block_addr, syn_block_addr

    @staticmethod
    def __next_app_syn_block_addr(block_addr, n_rows, max_bytes, max_pos):
        """ Get a block address for a sub-block of an application synaptic\
            matrix and check it hasn't overflowed the allocation
        """
        block_addr += (max_bytes * n_rows)
        if block_addr > max_pos:
            raise Exception(
                "Too much synaptic memory has been reserved: {} of {}".format(
                    block_addr, max_pos))
        return block_addr

    @staticmethod
    def __write_on_chip_delay_data(
            max_row_info, app_edge, pre_slices, pre_slice_index,
            post_slices, post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_info, machine_time_step):
        """ Write data for delayed on-chip generation
        """
        # If delay edge exists, tell this about the data too, so it can
        # generate its own data
        if (max_row_info.delayed_max_n_synapses > 0 and
                app_edge.delay_edge is not None):
            app_edge.delay_edge.pre_vertex.add_generator_data(
                max_row_info.undelayed_max_n_synapses,
                max_row_info.delayed_max_n_synapses,
                pre_slices, pre_slice_index, post_slices, post_slice_index,
                pre_vertex_slice, post_vertex_slice, synapse_info,
                app_edge.n_delay_stages + 1, machine_time_step)
        elif max_row_info.delayed_max_n_synapses != 0:
            raise Exception(
                "Found delayed items but no delay "
                "machine edge for {}".format(app_edge.label))

    def __get_row_data(
            self, synapse_info, pre_slices, pre_slice_idx, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice, app_edge,
            n_synapse_types, weight_scales, machine_time_step, machine_edge,
            max_row_info):
        """ Generate the row data for a synaptic matrix from the description
        """
        (row_data, delayed_row_data, delayed_source_ids,
         delay_stages) = self.__synapse_io.get_synapses(
            synapse_info, pre_slices, pre_slice_idx, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            app_edge.n_delay_stages, n_synapse_types, weight_scales,
            machine_time_step, app_edge, machine_edge, max_row_info)

        if app_edge.delay_edge is not None:
            app_edge.delay_edge.pre_vertex.add_delays(
                pre_vertex_slice, delayed_source_ids, delay_stages)
        elif delayed_source_ids.size != 0:
            raise Exception(
                "Found delayed source IDs but no delay "
                "machine edge for {}".format(app_edge.label))

        if (app_edge, synapse_info) in self.__pre_run_connection_holders:
            for conn_holder in self.__pre_run_connection_holders[
                    app_edge, synapse_info]:
                conn_holder.add_connections(
                    self.__synapse_io.read_all_synapses(
                        synapse_info, pre_vertex_slice, post_vertex_slice,
                        max_row_info.undelayed_max_words,
                        max_row_info.delayed_max_words, n_synapse_types,
                        weight_scales, row_data, delayed_row_data,
                        machine_time_step))
                conn_holder.finish()

        return (row_data, delayed_row_data)

    def __is_direct(
            self, single_addr, s_info, pre_vertex_slice, post_vertex_slice,
            is_delayed):
        """ Determine if the given connection can be done with a "direct"\
            synaptic matrix - this must have an exactly 1 entry per row
        """
        return (
            not is_delayed and
            isinstance(s_info.connector, OneToOneConnector) and
            isinstance(s_info.synapse_dynamics, SynapseDynamicsStatic) and
            (single_addr + (pre_vertex_slice.n_atoms * BYTES_PER_WORD) <=
                self.__one_to_one_connection_dtcm_max_bytes) and
            (pre_vertex_slice.lo_atom == post_vertex_slice.lo_atom) and
            (pre_vertex_slice.hi_atom == post_vertex_slice.hi_atom) and
            not s_info.prepop_is_view and
            not s_info.postpop_is_view)

    def _get_ring_buffer_shifts(
            self, application_vertex, application_graph, machine_timestep,
            weight_scale):
        """ Get the ring buffer shifts for this vertex
        """
        if self.__ring_buffer_shifts is None:
            self.__ring_buffer_shifts = \
                self._get_ring_buffer_to_input_left_shifts(
                    application_vertex, application_graph, machine_timestep,
                    weight_scale)
        return self.__ring_buffer_shifts

    def write_data_spec(
            self, spec, application_vertex, post_vertex_slice, machine_vertex,
            placement, machine_graph, application_graph, routing_info,
            graph_mapper, weight_scale, machine_time_step):
        # Create an index of delay keys into this vertex
        for m_edge in machine_graph.get_edges_ending_at_vertex(machine_vertex):
            app_edge = graph_mapper.get_application_edge(m_edge)
            if isinstance(app_edge.pre_vertex, DelayExtensionVertex):
                pre_vertex_slice = graph_mapper.get_slice(
                    m_edge.pre_vertex)
                self.__delay_key_index[app_edge.pre_vertex.source_vertex,
                                       pre_vertex_slice.lo_atom,
                                       pre_vertex_slice.hi_atom] = \
                    routing_info.get_routing_info_for_edge(m_edge)

        post_slices = graph_mapper.get_slices(application_vertex)
        post_slice_idx = graph_mapper.get_machine_vertex_index(machine_vertex)

        # Reserve the memory
        in_edges = application_graph.get_edges_ending_at_vertex(
            application_vertex)
        all_syn_block_sz = self._get_synaptic_blocks_size(
            post_vertex_slice, in_edges, machine_time_step)
        self._reserve_memory_regions(
            spec, post_vertex_slice, all_syn_block_sz, application_graph,
            application_vertex)

        ring_buffer_shifts = self._get_ring_buffer_shifts(
            application_vertex, application_graph, machine_time_step,
            weight_scale)
        weight_scales = self._write_synapse_parameters(
            spec, ring_buffer_shifts, weight_scale)

        gen_data = self._write_synaptic_matrix_and_master_population_table(
            spec, post_slices, post_slice_idx, machine_vertex,
            post_vertex_slice, all_syn_block_sz, weight_scales,
            routing_info, graph_mapper, machine_graph, machine_time_step)

        if self.__synapse_dynamics is not None:
            if isinstance(self.__synapse_dynamics,
                          AbstractSynapseDynamicsStructural):
                self.__synapse_dynamics.write_structural_parameters(
                    spec, POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value,
                    machine_time_step, weight_scales, application_graph,
                    application_vertex, post_vertex_slice, graph_mapper,
                    routing_info, self.__synapse_indices)
            else:
                self.__synapse_dynamics.write_parameters(
                    spec,
                    POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value,
                    machine_time_step, weight_scales)

        self.__weight_scales[placement] = weight_scales

        self._write_on_machine_data_spec(
            spec, post_vertex_slice, weight_scales, gen_data)

    def clear_connection_cache(self):
        self.__retrieved_blocks = dict()

    def _get_block(self, transceiver, placement, address, size):
        key = (placement, address, size)
        if key in self.__retrieved_blocks:
            return self.__retrieved_blocks[key]
        block = transceiver.read_memory(
            placement.x, placement.y, address, size)
        self.__retrieved_blocks[key] = block
        return block

    def _read_connections(
            self, row_len, block_sz, transceiver, placement,
            address, synapse_info, pre_slice, post_slice, machine_time_step,
            delayed):
        block = self._get_block(transceiver, placement, address, block_sz)
        return self.__synapse_io.read_some_synapses(
            synapse_info, pre_slice, post_slice, row_len,
            self.__n_synapse_types, self.__weight_scales[placement], block,
            machine_time_step, delayed)

    def _get_single_block(self, transceiver, placement, address, size):
        block = self._get_block(transceiver, placement, address, size)
        numpy_data = numpy.asarray(block, dtype="uint8").view("uint32")
        n_rows = len(numpy_data)
        numpy_block = numpy.zeros((n_rows, BYTES_PER_WORD), dtype="uint32")
        numpy_block[:, 3] = numpy_data
        numpy_block[:, 1] = 1
        return numpy_block.tobytes()

    def _read_single_connections(
            self, block_sz, transceiver, placement, address, synapse_info,
            pre_slice, post_slice, machine_time_step, delayed):
        block = self._get_single_block(
            transceiver, placement, address, block_sz)
        return self.__synapse_io.read_some_synapses(
            synapse_info, pre_slice, post_slice, 1,
            self.__n_synapse_types, self.__weight_scales[placement], block,
            machine_time_step, delayed)

    def _get_connections(
            self, app_edge, synapse_info, post_slice, transceiver, placement,
            direct_synapses, indirect_synapses, machine_time_step,
            graph_mapper, edge_info, m_edge_info, delayed):
        key = (app_edge, synapse_info, post_slice.lo_atom)
        connections = []
        if key in edge_info:
            offset, row_len, block_sz = edge_info[key]
            pre_slice = Slice(0, app_edge.pre_vertex.n_atoms - 1)
            connections.append(self._read_connections(
                row_len, block_sz, transceiver, placement,
                indirect_synapses + offset, synapse_info, pre_slice,
                post_slice, machine_time_step, delayed))
        else:
            m_edges = graph_mapper.get_machine_edges(app_edge)
            for m_edge in m_edges:
                m_key = (m_edge, synapse_info, post_slice.lo_atom)
                if m_key not in m_edge_info:
                    continue
                offset, row_len, block_sz, single = m_edge_info[m_key]
                pre_slice = graph_mapper.get_slice(m_edge.pre_vertex)
                if single:
                    connections.append(self._read_single_connections(
                        block_sz, transceiver,
                        placement, direct_synapses + offset, synapse_info,
                        pre_slice, post_slice, machine_time_step, delayed))
                else:
                    connections.append(self._read_connections(
                        row_len, block_sz, transceiver,
                        placement, indirect_synapses + offset, synapse_info,
                        pre_slice, post_slice, machine_time_step, delayed))
        return connections

    def get_connections_from_machine(
            self, vertex, transceiver, placements, app_edge, graph_mapper,
            synapse_info, machine_time_step):

        if not isinstance(app_edge, ProjectionApplicationEdge):
            raise Exception("Unknown edge type for {}".format(app_edge))

        post_vertices = graph_mapper.get_machine_vertices(vertex)
        # Start with something in the list so that concatenate works
        connections = [numpy.zeros(
                0, dtype=AbstractSynapseDynamics.NUMPY_CONNECTORS_DTYPE)]
        progress = ProgressBar(
            len(post_vertices),
            "Getting synaptic data between {} and {}".format(
                app_edge.pre_vertex.label, vertex.label))
        for post_vertex in progress.over(post_vertices):
            post_slice = graph_mapper.get_slice(post_vertex)
            placement = placements.get_placement_of_vertex(post_vertex)
            direct_synapses, indirect_synapses = \
                self.__compute_addresses(transceiver, placement)

            connections.extend(self._get_connections(
                app_edge, synapse_info, post_slice,
                transceiver, placement, direct_synapses, indirect_synapses,
                machine_time_step, graph_mapper, self.__app_edge_info,
                self.__m_edge_info, delayed=False))
            connections.extend(self._get_connections(
                app_edge, synapse_info, post_slice,
                transceiver, placement, direct_synapses, indirect_synapses,
                machine_time_step, graph_mapper, self.__delay_edge_info,
                self.__delay_m_edge_info, delayed=True))
        return numpy.concatenate(connections)

    @staticmethod
    def __compute_addresses(transceiver, placement):
        """ Helper for computing the addresses of the master pop table and\
            synaptic-matrix-related bits.
        """
        synaptic_matrix = locate_memory_region_for_placement(
            placement, POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
            transceiver)
        direct_synapses = locate_memory_region_for_placement(
            placement, POPULATION_BASED_REGIONS.DIRECT_MATRIX.value,
            transceiver) + BYTES_PER_WORD
        return direct_synapses, synaptic_matrix

    # inherited from AbstractProvidesIncomingPartitionConstraints
    def get_incoming_partition_constraints(self):
        return self.__poptable_type.get_edge_constraints()

    def _write_on_machine_data_spec(
            self, spec, post_vertex_slice, weight_scales, generator_data):
        """ Write the data spec for the synapse expander

        :param spec: The specification to write to
        :param post_vertex_slice: The slice of the vertex being written
        :param weight_scales: scaling of weights on each synapse
        """
        if not generator_data:
            return

        n_bytes = (
            _SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES +
            (self.__n_synapse_types * BYTES_PER_WORD))
        for data in generator_data:
            n_bytes += data.size

        spec.reserve_memory_region(
            region=POPULATION_BASED_REGIONS.CONNECTOR_BUILDER.value,
            size=n_bytes, label="ConnectorBuilderRegion")
        spec.switch_write_focus(
            region=POPULATION_BASED_REGIONS.CONNECTOR_BUILDER.value)

        spec.write_value(len(generator_data))
        spec.write_value(post_vertex_slice.lo_atom)
        spec.write_value(post_vertex_slice.n_atoms)
        spec.write_value(self.__n_synapse_types)
        spec.write_value(get_n_bits(self.__n_synapse_types))
        n_neuron_id_bits = get_n_bits(post_vertex_slice.n_atoms)
        spec.write_value(n_neuron_id_bits)
        for w in weight_scales:
            # if the weights are high enough and the population size large
            # enough, then weight_scales < 1 will result in a zero scale
            # if converted to an int, so this needs to be an S1615
            dtype = DataType.S1615
            if w > dtype.max:
                spec.write_value(data=dtype.max, data_type=dtype)
            else:
                spec.write_value(data=w, data_type=dtype)

        for data in generator_data:
            spec.write_array(data.gen_data)

    def gen_on_machine(self, vertex_slice):
        """ True if the synapses should be generated on the machine
        """
        key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        return self.__gen_on_machine.get(key, False)

    def reset_ring_buffer_shifts(self):
        self.__ring_buffer_shifts = None

    @property
    def changes_during_run(self):
        if self.__synapse_dynamics is None:
            return False
        return self.__synapse_dynamics.changes_during_run


class _AppKeyInfo(object):

    __slots__ = ["app_key", "app_mask", "core_mask", "core_shift", "n_neurons"]

    def __init__(self, app_key, app_mask, core_mask, core_shift, n_neurons):
        self.app_key = app_key
        self.app_mask = app_mask
        self.core_mask = core_mask
        self.core_shift = core_shift
        self.n_neurons = n_neurons

    @property
    def key_and_mask(self):
        return BaseKeyAndMask(self.app_key, self.app_mask)
