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

from collections import defaultdict, namedtuple
import math
import struct
import numpy
from scipy import special  # @UnresolvedImport
from data_specification.enums import DataType
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, MICRO_TO_SECOND_CONVERSION)
from spynnaker.pyNN.models.neuron.generator_data import GeneratorData
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from .synapse_dynamics import (
    AbstractSynapseDynamicsStructural,
    AbstractGenerateOnMachine, SynapseDynamicsStructuralSTDP)
from spynnaker.pyNN.models.neuron.synapse_io import SynapseIORowBased
from spynnaker.pyNN.models.spike_source.spike_source_poisson_vertex import (
    SpikeSourcePoissonVertex)
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
from spynnaker.pyNN.utilities.constants import (
    POPULATION_BASED_REGIONS, POSSION_SIGMA_SUMMATION_LIMIT)
from spynnaker.pyNN.utilities.utility_calls import (get_n_bits)
from spynnaker.pyNN.utilities.running_stats import RunningStats
from spynnaker.pyNN.models.neuron.master_pop_table import (
    MasterPopTableAsBinarySearch)

TIME_STAMP_BYTES = BYTES_PER_WORD

# TODO: Make sure these values are correct (particularly CPU cycles)
_SYNAPSES_BASE_DTCM_USAGE_IN_BYTES = 7 * BYTES_PER_WORD

# 1 for drop late packets.
_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES = 1 * BYTES_PER_WORD
_SYNAPSES_BASE_N_CPU_CYCLES_PER_NEURON = 10
_SYNAPSES_BASE_N_CPU_CYCLES = 8

# 4 for n_edges
# 8 for post_vertex_slice.lo_atom, post_vertex_slice.n_atoms
# 4 for n_synapse_types
# 4 for n_synapse_type_bits
# 4 for n_synapse_index_bits
_SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES = (
    1 + 2 + 1 + 1 + 1) * BYTES_PER_WORD

# Amount to scale synapse SDRAM estimate by to make sure the synapses fit
_SYNAPSE_SDRAM_OVERSCALE = 1.1

_ONE_WORD = struct.Struct("<I")

# Information about a connector to be generated on machine
_Gen = namedtuple(
    "_Gen", "synapse_info, pre_slices, pre_slice, pre_index, app_edge, rinfo")


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
        "__drop_late_spikes",
        "_host_generated_block_addr",
        "_on_chip_generated_block_addr",
        # Overridable (for testing only) region IDs
        "_synapse_params_region",
        "_pop_table_region",
        "_synaptic_matrix_region",
        "_synapse_dynamics_region",
        "_struct_dynamics_region",
        "_connector_builder_region",
        "_direct_matrix_region"]

    # TODO make this right
    FUDGE = 0

    # 1. address of direct addresses, 2. size of direct addresses matrix size
    STATIC_SYNAPSE_MATRIX_SDRAM_IN_BYTES = 2 * BYTES_PER_WORD

    def __init__(self, n_synapse_types, ring_buffer_sigma, spikes_per_second,
                 config, drop_late_spikes, population_table_type=None,
                 synapse_io=None):
        """
        :param int n_synapse_types:
            number of synapse types on a neuron (e.g., 2 for excitatory and
            inhibitory)
        :param ring_buffer_sigma:
            How many SD above the mean to go for upper bound; a
            good starting choice is 5.0. Given length of simulation we can
            set this for approximate number of saturation events.
        :type ring_buffer_sigma: float or None
        :param spikes_per_second: Estimated spikes per second
        :type spikes_per_second: float or None
        :param ~configparser.RawConfigParser config: The system configuration
        :param population_table_type:
            What type of master population table is used
        :type population_table_type: MasterPopTableAsBinarySearch or None
        :param synapse_io: How IO for synapses is performed
        :type synapse_io: SynapseIORowBased or None
        :param bool drop_late_spikes: control flag for dropping late packets.
        """
        self.__n_synapse_types = n_synapse_types
        self.__ring_buffer_sigma = ring_buffer_sigma
        self.__spikes_per_second = spikes_per_second
        self.__drop_late_spikes = drop_late_spikes
        self._synapse_params_region = \
            POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value
        self._pop_table_region = \
            POPULATION_BASED_REGIONS.POPULATION_TABLE.value
        self._synaptic_matrix_region = \
            POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value
        self._synapse_dynamics_region = \
            POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value
        self._struct_dynamics_region = \
            POPULATION_BASED_REGIONS.STRUCTURAL_DYNAMICS.value
        self._connector_builder_region = \
            POPULATION_BASED_REGIONS.CONNECTOR_BUILDER.value
        self._direct_matrix_region = \
            POPULATION_BASED_REGIONS.DIRECT_MATRIX.value

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

        if self.__drop_late_spikes is None:
            self.__drop_late_spikes = config.getboolean(
                "Simulation", "drop_late_spikes")

        # Prepare for dealing with STDP - there can only be one (non-static)
        # synapse dynamics per vertex at present
        self.__synapse_dynamics = None

        # Keep the details once computed to allow reading back
        self.__weight_scales = dict()
        self.__ring_buffer_shifts = None
        self.__delay_key_index = dict()
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

        # Track writes inside the synaptic matrix region (to meet sizes):
        self._host_generated_block_addr = 0
        self._on_chip_generated_block_addr = 0

    @property
    def host_written_matrix_size(self):
        return self._host_generated_block_addr

    @property
    def on_chip_written_matrix_size(self):
        return (self._on_chip_generated_block_addr -
                self._host_generated_block_addr)

    @property
    def synapse_dynamics(self):
        """ Settable.

        :rtype: AbstractSynapseDynamics or None
        """
        return self.__synapse_dynamics

    @property
    def drop_late_spikes(self):
        return self.__drop_late_spikes

    @staticmethod
    def __combine_structural_stdp_dynamics(structural, stdp):
        """
        :param AbstractSynapseDynamicsStructural structural:
        :param SynapseDynamicsSTDP stdp:
        :rtype: SynapseDynamicsStructuralSTDP
        """
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
        """ Settable.

        :rtype: float
        """
        return self.__ring_buffer_sigma

    @ring_buffer_sigma.setter
    def ring_buffer_sigma(self, ring_buffer_sigma):
        self.__ring_buffer_sigma = ring_buffer_sigma

    @property
    def spikes_per_second(self):
        """ Settable.

        :rtype: float
        """
        return self.__spikes_per_second

    @spikes_per_second.setter
    def spikes_per_second(self, spikes_per_second):
        self.__spikes_per_second = spikes_per_second

    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        """
        :rtype: int or None
        """
        return self.__synapse_io.get_maximum_delay_supported_in_ms(
            machine_time_step)

    @property
    def vertex_executable_suffix(self):
        """ The suffix of the executable name due to the type of synapses \
            in use.

        :rtype: str
        """
        if self.__synapse_dynamics is None:
            return ""
        return self.__synapse_dynamics.get_vertex_executable_suffix()

    def add_pre_run_connection_holder(
            self, connection_holder, edge, synapse_info):
        """
        :param ConnectionHolder connection_holder:
        :param ProjectionApplicationEdge edge:
        :param SynapseInformation synapse_info:
        """
        self.__pre_run_connection_holders[edge, synapse_info].append(
            connection_holder)

    def get_connection_holders(self):
        """
        :rtype: dict(tuple(ProjectionApplicationEdge,SynapseInformation),\
            ConnectionHolder)
        """
        return self.__pre_run_connection_holders

    def get_n_cpu_cycles(self):
        """
        :rtype: int
        """
        # TODO: Calculate this correctly
        return self.FUDGE

    def get_dtcm_usage_in_bytes(self):
        """
        :rtype: int
        """
        # TODO: Calculate this correctly
        return self.FUDGE

    def _get_synapse_params_size(self):
        """
        :rtype: int
        """
        return (_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES +
                (BYTES_PER_WORD * self.__n_synapse_types))

    def _get_static_synaptic_matrix_sdram_requirements(self):
        """
        :rtype: int
        """
        # 4 for address of direct addresses, and
        # 4 for the size of the direct addresses matrix in bytes
        return self.STATIC_SYNAPSE_MATRIX_SDRAM_IN_BYTES

    def __get_max_row_info(
            self, synapse_info, post_vertex_slice, app_edge,
            machine_time_step):
        """ Get the maximum size of each row for a given slice of the vertex

        :param SynapseInformation synapse_info:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param ProjectionApplicationEdge app_edge:
        :param int machine_time_step:
        :rtype: MaxRowInfo
        """
        key = (synapse_info, post_vertex_slice)
        if key not in self.__max_row_info:
            self.__max_row_info[key] = self.__synapse_io.get_max_row_info(
                synapse_info, post_vertex_slice,
                app_edge.n_delay_stages, self.__poptable_type,
                machine_time_step, app_edge)
        return self.__max_row_info[key]

    def _get_synaptic_blocks_size(
            self, post_vertex_slice, in_edges, machine_time_step):
        """ Get the size of the synaptic blocks in bytes

        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param list(.ApplicationEdge) in_edges:
        :param int machine_time_step:
        :rtype: int
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
        """
        :param int memory_size:
        :param SynapseInformation synapse_info:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param ProjectionApplicationEdge in_edge:
        :param int machine_time_step:
        :rtype: int
        """
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

        :param list(.ApplicationEdge) in_edges:
        :rtype: int
        """
        gen_on_machine = False
        size = 0
        for in_edge in in_edges:
            if not isinstance(in_edge, ProjectionApplicationEdge):
                continue

            for synapse_info in in_edge.synapse_information:
                # Get the number of likely vertices
                max_atoms = in_edge.pre_vertex.get_max_atoms_per_core()
                if in_edge.pre_vertex.n_atoms < max_atoms:
                    max_atoms = in_edge.pre_vertex.n_atoms
                n_edge_vertices = int(math.ceil(
                    float(in_edge.pre_vertex.n_atoms) / float(max_atoms)))

                # Get the size
                if synapse_info.may_generate_on_machine():
                    gen_on_machine = True
                    connector = synapse_info.connector
                    dynamics = synapse_info.synapse_dynamics
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
            self, vertex_slice, app_graph, app_vertex):
        """ Get the size of the synapse dynamics region

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param ~.ApplicationGraph app_graph:
        :param ~.ApplicationVertex app_vertex:
        :rtype: int
        """
        if self.__synapse_dynamics is None:
            return 0

        # Does the size of the parameters area depend on presynaptic
        # connections in any way?
        if isinstance(self.__synapse_dynamics,
                      AbstractSynapseDynamicsStructural):
            return self.__synapse_dynamics\
                .get_structural_parameters_sdram_usage_in_bytes(
                     app_graph, app_vertex, vertex_slice.n_atoms,
                     self.__n_synapse_types)
        else:
            return self.__synapse_dynamics.get_parameters_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self.__n_synapse_types)

    def get_sdram_usage_in_bytes(
            self, vertex_slice, machine_time_step, application_graph,
            app_vertex):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param int machine_time_step:
        :param ~pacman.model.graphs.application.ApplicationGraph \
                application_graph:
        :param AbstractPopulationVertex app_vertex:
        :rtype: int
        """
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
            self, spec, machine_vertex, vertex_slice, machine_graph,
            all_syn_block_sz, application_graph, application_vertex):
        """
        :param ~.DataSpecificationGenerator spec:
        :param ~.MachineVertex machine_vertex:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param ~.MachineGraph machine_graph:
        :param int all_syn_block_sz:
        :param ~.ApplicationGraph application_graph:
        :param ~.ApplicationVertex application_vertex:
        """
        spec.reserve_memory_region(
            region=self._synapse_params_region,
            size=self._get_synapse_params_size(),
            label='SynapseParams')

        master_pop_table_sz = \
            self.__poptable_type.get_exact_master_population_table_size(
                machine_vertex, machine_graph)
        if master_pop_table_sz > 0:
            spec.reserve_memory_region(
                region=self._pop_table_region,
                size=master_pop_table_sz, label='PopTable')
        if all_syn_block_sz > 0:
            spec.reserve_memory_region(
                region=self._synaptic_matrix_region,
                size=all_syn_block_sz, label='SynBlocks')

        # return if not got a synapse dynamics
        if self.__synapse_dynamics is None:
            return

        synapse_dynamics_sz = \
            self.__synapse_dynamics.get_parameters_sdram_usage_in_bytes(
                vertex_slice.n_atoms, self.__n_synapse_types)
        if synapse_dynamics_sz != 0:
            spec.reserve_memory_region(
                region=self._synapse_dynamics_region,
                size=synapse_dynamics_sz, label='synapseDynamicsParams')

        # if structural, create structural region
        if isinstance(
                self.__synapse_dynamics, AbstractSynapseDynamicsStructural):

            synapse_structural_dynamics_sz = (
                self.__synapse_dynamics.
                get_structural_parameters_sdram_usage_in_bytes(
                    application_graph, application_vertex,
                    vertex_slice.n_atoms, self.__n_synapse_types))

            if synapse_structural_dynamics_sz != 0:
                spec.reserve_memory_region(
                    region=self._struct_dynamics_region,
                    size=synapse_structural_dynamics_sz,
                    label='synapseDynamicsStructuralParams')

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

        :param float weight_mean: Mean of weight distribution (in either nA or\
            microSiemens as required)
        :param float weight_std_dev: SD of weight distribution
        :param float spikes_per_second: Maximum expected Poisson rate in Hz
        :param int machine_timestep: in us
        :param int n_synapses_in: No of connected synapses
        :param float sigma: How many SD above the mean to go for upper bound;\
            a good starting choice is 5.0. Given length of simulation we can\
            set this for approximate number of saturation events.
        :rtype: float
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

        :param .ApplicationVertex application_vertex:
        :param .ApplicationGraph application_graph:
        :param int machine_timestep:
        :param float weight_scale:
        :rtype: list(int)
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
                        spikes_per_tick = \
                            app_edge.pre_vertex.max_spikes_per_ts(
                                machine_timestep)
                    rate_stats[synapse_type].add_items(
                        spikes_per_second, 0, n_connections)
                    total_weights[synapse_type] += spikes_per_tick * (
                        weight_max * n_connections)

                    if synapse_dynamics.are_weights_signed():
                        weights_signed = True

        max_weights = numpy.zeros(n_synapse_types)
        for synapse_type in range(n_synapse_types):
            if delay_running_totals[synapse_type].variance == 0.0:
                max_weights[synapse_type] = max(total_weights[synapse_type],
                                                biggest_weight[synapse_type])
            else:
                stats = running_totals[synapse_type]
                rates = rate_stats[synapse_type]
                max_weights[synapse_type] = min(
                    self._ring_buffer_expected_upper_bound(
                        stats.mean, stats.standard_deviation, rates.mean,
                        machine_timestep, stats.n_items,
                        self.__ring_buffer_sigma),
                    total_weights[synapse_type])
                max_weights[synapse_type] = max(
                    max_weights[synapse_type], biggest_weight[synapse_type])

        # Convert these to powers; we could use int.bit_length() for this if
        # they were integers, but they aren't...
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
    def __get_weight_scale(ring_buffer_to_input_left_shift):
        """ Return the amount to scale the weights by to convert them from \
            floating point values to 16-bit fixed point numbers which can be \
            shifted left by ring_buffer_to_input_left_shift to produce an\
            s1615 fixed point number

        :param int ring_buffer_to_input_left_shift:
        :rtype: float
        """
        return float(math.pow(2, 16 - (ring_buffer_to_input_left_shift + 1)))

    def _write_synapse_parameters(
            self, spec, ring_buffer_shifts, weight_scale):
        """ Get the ring buffer shifts and scaling factors.

        :param ~.DataSpecificationGenerator spec:
        :param ~numpy.ndarray ring_buffer_shifts:
        :param float weight_scale:
        :rtype: ~numpy.ndarray
        """
        # Write the ring buffer shifts
        spec.switch_write_focus(self._synapse_params_region)

        # write the bool for deleting packets that were too late for a timer
        spec.write_value(int(self.__drop_late_spikes))

        # Write the ring buffer shifts
        spec.write_array(ring_buffer_shifts)

        # Return the weight scaling factors
        return numpy.array([
            self.__get_weight_scale(r) * weight_scale
            for r in ring_buffer_shifts])

    def _write_padding(self, spec, next_block_start_address):
        """
        :param ~.DataSpecificationGenerator spec:
        :param int next_block_start_address:
        :rtype: int
        """
        next_block_allowed_address = self.__poptable_type\
            .get_next_allowed_address(next_block_start_address)
        if next_block_allowed_address != next_block_start_address:

            # Pad out data file with the added alignment bytes:
            spec.comment("\nWriting population table required padding\n")
            spec.switch_write_focus(self._synaptic_matrix_region)
            spec.set_register_value(
                register_id=15,
                data=next_block_allowed_address - next_block_start_address)
            spec.write_repeated_value(
                data=0xDD, repeats=15, repeats_is_register=True,
                data_type=DataType.UINT8)
            return next_block_allowed_address
        return next_block_start_address

    def _write_synaptic_matrix_and_master_population_table(
            self, spec, post_slice_index, machine_vertex,
            post_vertex_slice, all_syn_block_sz, weight_scales,
            routing_info, machine_graph, machine_time_step):
        """ Simultaneously generates both the master population table and
            the synaptic matrix.

        :param ~.DataSpecificationGenerator spec:
        :param list(~pacman.model.graphs.common.Slice) post_slices:
        :param int post_slice_index:
        :param .MachineVertex machine_vertex:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param all_syn_block_sz:
        :param weight_scales:
        :param .RoutingInfo routing_info:
        :param .MachineGraph machine_graph:
        :param int machine_time_step:
        :rtype: list(GeneratorData)
        """
        spec.comment(
            "\nWriting Synaptic Matrix and Master Population Table:\n")

        # Track writes inside the synaptic matrix region:
        block_addr = 0

        # Get the edges
        in_edges = machine_graph.get_edges_ending_at_vertex(machine_vertex)

        # Set up the master population table
        self.__poptable_type.initialise_table()

        # Set up for single synapses - write the offset of the single synapses
        # initially 0
        single_synapses = list()
        spec.switch_write_focus(self._synaptic_matrix_region)
        single_addr = 0

        # Store a list of synapse info to be generated on the machine
        generate_on_machine = list()

        # For each machine edge in the vertex, create a synaptic list
        for edge in in_edges:
            if isinstance(edge.app_edge, ProjectionApplicationEdge):
                spec.comment("\nWriting matrix for edge:{}\n".format(
                    edge.label))

                pre_vertex = edge.pre_vertex
                pre_vertex_slice = pre_vertex.vertex_slice
                post_slices = edge.post_slices
                pre_slices = edge.app_edge.pre_slices

                for synapse_info in edge.app_edge.synapse_information:
                    rinfo = routing_info.get_routing_info_for_edge(edge)

                    # If connector is being built on SpiNNaker,
                    # compute matrix sizes only
                    if self.__may_generate_on_machine(
                            synapse_info, single_addr, pre_vertex_slice,
                            post_vertex_slice, edge.app_edge):
                        # We will process this a little later
                        generate_on_machine.append(_Gen(
                            synapse_info, pre_slices, pre_vertex_slice,
                            pre_vertex.index, edge.app_edge, rinfo))
                        spec.comment("Will generate on machine")
                        continue

                    block_addr, single_addr, index = self.__write_block(
                        spec, synapse_info, pre_slices, pre_vertex.index,
                        post_slices, post_slice_index, pre_vertex_slice,
                        post_vertex_slice, edge.app_edge, single_synapses,
                        weight_scales, machine_time_step, rinfo,
                        all_syn_block_sz, block_addr, single_addr,
                        machine_edge=edge)
                    self.__synapse_indices[
                        synapse_info, pre_vertex_slice.lo_atom] = index

        # Skip blocks that will be written on the machine, but add them
        # to the master population table
        generator_data = list()

        self._host_generated_block_addr = block_addr
        # numpy.random.shuffle(order)
        for gen in generate_on_machine:
            block_addr, index = self.__generate_on_chip_data(
                gen, post_slices, post_slice_index, post_vertex_slice,
                all_syn_block_sz, block_addr, machine_time_step,
                generator_data)
            self.__synapse_indices[
                gen.synapse_info, gen.pre_slice.lo_atom] = index
        self._on_chip_generated_block_addr = block_addr

        self.__poptable_type.finish_master_pop_table(
            spec, self._pop_table_region)

        # Write the size and data of single synapses to the direct region
        if single_synapses:
            single_data = numpy.concatenate(single_synapses)
            spec.reserve_memory_region(
                region=self._direct_matrix_region,
                size=(len(single_data) + 1) * BYTES_PER_WORD,
                label='DirectMatrix')
            spec.switch_write_focus(self._direct_matrix_region)
            spec.write_value(len(single_data) * BYTES_PER_WORD)
            spec.write_array(single_data)
        else:
            spec.reserve_memory_region(
                region=self._direct_matrix_region, size=BYTES_PER_WORD,
                label="DirectMatrix")
            spec.switch_write_focus(self._direct_matrix_region)
            spec.write_value(0)

        return generator_data

    def __may_generate_on_machine(
            self, synapse_info, single_addr, pre_slice, post_slice, app_edge):
        """
        :param SynapseInformation synapse_info:
        :param int single_addr:
        :param ~pacman.model.graphs.common.Slice pre_slice:
        :param ~pacman.model.graphs.common.Slice post_slice:
        :param ~.ApplicationEdge app_edge:
        :rtype: bool
        """
        connector = synapse_info.connector
        dynamics = synapse_info.synapse_dynamics
        return (
            isinstance(connector, AbstractGenerateConnectorOnMachine) and
            connector.generate_on_machine(
                synapse_info.weights, synapse_info.delays) and
            isinstance(dynamics, AbstractGenerateOnMachine) and
            dynamics.generate_on_machine and
            not isinstance(
                self.synapse_dynamics, AbstractSynapseDynamicsStructural) and
            not self.__is_direct(
                single_addr, connector, pre_slice, post_slice, app_edge,
                synapse_info))

    def __generate_on_chip_data(
            self, gen, post_slices, post_slice_index, post_vertex_slice,
            all_syn_block_sz, block_addr, machine_time_step, generator_data):
        """ Generate data for the synapse expander

        :param _Gen gen:
        :param list(.Slice) post_slices:
        :param int post_slice_index:
        :param .Slice post_vertex_slice:
        :param int all_syn_block_sz:
        :param int block_addr:
        :param int machine_time_step:
        :param list(GeneratorData) generator_data:
        :rtype: tuple(int,int)
        """

        # Get the size of the matrices that will be required
        max_row_info = self.__get_max_row_info(
            gen.synapse_info, post_vertex_slice, gen.app_edge,
            machine_time_step)

        # If delay edge exists, tell this about the data too, so it can
        # generate its own data
        if (max_row_info.delayed_max_n_synapses > 0 and
                gen.app_edge.delay_edge is not None):
            gen.app_edge.delay_edge.pre_vertex.add_generator_data(
                max_row_info.undelayed_max_n_synapses,
                max_row_info.delayed_max_n_synapses, gen.pre_slices,
                gen.pre_index, post_slices, post_slice_index, gen.pre_slice,
                post_vertex_slice, gen.synapse_info,
                gen.app_edge.n_delay_stages + 1, machine_time_step)
        elif max_row_info.delayed_max_n_synapses != 0:
            raise Exception(
                "Found delayed items but no delay machine edge for {}".format(
                    gen.app_edge.label))

        # Skip over the normal bytes but still write a master pop entry
        synaptic_matrix_offset = 0xFFFFFFFF
        index = None
        if max_row_info.undelayed_max_n_synapses:
            synaptic_matrix_offset = \
                self.__poptable_type.get_next_allowed_address(block_addr)
            index = self.__poptable_type.update_master_population_table(
                synaptic_matrix_offset, max_row_info.undelayed_max_words,
                gen.rinfo.first_key_and_mask)
            n_bytes_undelayed = (
                max_row_info.undelayed_max_bytes * gen.pre_slice.n_atoms)
            block_addr = synaptic_matrix_offset + n_bytes_undelayed

            # The synaptic matrix offset is in words for the generator
            synaptic_matrix_offset //= BYTES_PER_WORD
        elif gen.rinfo is not None:
            index = self.__poptable_type.update_master_population_table(
                0, 0, gen.rinfo.first_key_and_mask)

        if block_addr > all_syn_block_sz:
            raise Exception(
                "Too much synaptic memory has been written: {} of {} ".format(
                    block_addr, all_syn_block_sz))

        # Skip over the delayed bytes but still write a master pop entry
        delayed_synaptic_matrix_offset = 0xFFFFFFFF
        n_delay_stages = 0
        delay_rinfo = self.__delay_key_index.get(
            (gen.app_edge.pre_vertex, gen.pre_slice), None)
        d_index = None
        if max_row_info.delayed_max_n_synapses:
            n_delay_stages = gen.app_edge.n_delay_stages
            delayed_synaptic_matrix_offset = \
                self.__poptable_type.get_next_allowed_address(
                    block_addr)
            d_index = self.__poptable_type.update_master_population_table(
                delayed_synaptic_matrix_offset, max_row_info.delayed_max_words,
                delay_rinfo.first_key_and_mask)
            n_bytes_delayed = (
                max_row_info.delayed_max_bytes * gen.pre_slice.n_atoms *
                n_delay_stages)
            block_addr = delayed_synaptic_matrix_offset + n_bytes_delayed

            # The delayed synaptic matrix offset is in words for the generator
            delayed_synaptic_matrix_offset //= BYTES_PER_WORD
        elif delay_rinfo is not None:
            d_index = self.__poptable_type.update_master_population_table(
                0, 0, delay_rinfo.first_key_and_mask)

        if block_addr > all_syn_block_sz:
            raise Exception(
                "Too much synaptic memory has been written: {} of {} ".format(
                    block_addr, all_syn_block_sz))

        # Get additional data for the synapse expander
        generator_data.append(GeneratorData(
            synaptic_matrix_offset, delayed_synaptic_matrix_offset,
            max_row_info.undelayed_max_words, max_row_info.delayed_max_words,
            max_row_info.undelayed_max_n_synapses,
            max_row_info.delayed_max_n_synapses, gen.pre_slices, gen.pre_index,
            post_slices, post_slice_index, gen.pre_slice, post_vertex_slice,
            gen.synapse_info, n_delay_stages + 1, machine_time_step))
        self.__gen_on_machine[post_vertex_slice] = True

        if index is not None and d_index is not None and index != d_index:
            raise Exception(
                "Delay index {} and normal index {} do not match".format(
                    d_index, index))
        return block_addr, index

    def __write_block(
            self, spec, synapse_info, pre_slices,
            pre_slice_index, post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, app_edge, single_synapses,
            weight_scales, machine_time_step, rinfo, all_syn_block_sz,
            block_addr, single_addr, machine_edge):
        """
        :param ~.DataSpecificationGenerator spec:
        :param SynapseInformation synapse_info:
        :param list(.Slice) pre_slices:
        :param int pre_slice_index:
        :param list(.Slice) post_slices:
        :param int post_slice_index:
        :param .Slice pre_vertex_slice:
        :param .Slice post_vertex_slice:
        :param ProjectionApplicationEdge app_edge:
        :param list(~numpy.ndarray) single_synapses:
        :param dict(AbstractSynapseType,float) weight_scales:
        :param int machine_time_step:
        :param .PartitionRoutingInfo rinfo:
        :param int all_syn_block_sz:
        :param int block_addr:
        :param int single_addr:
        :param ProjectionMachineEdge machine_edge:
        :rtype: tuple(int,int,int)
        """
        (row_data, row_length, delayed_row_data, delayed_row_length,
         delayed_source_ids, delay_stages) = self.__synapse_io.get_synapses(
             synapse_info, pre_slices, pre_slice_index, post_slices,
             post_slice_index, pre_vertex_slice, post_vertex_slice,
             app_edge.n_delay_stages, self.__poptable_type,
             self.__n_synapse_types, weight_scales, machine_time_step,
             app_edge=app_edge, machine_edge=machine_edge)

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
                conn_holder.add_connections(self._read_synapses(
                    synapse_info, pre_vertex_slice, post_vertex_slice,
                    row_length, delayed_row_length, weight_scales,
                    row_data, delayed_row_data, machine_time_step))
                conn_holder.finish()

        index = None
        if row_data.size:
            block_addr, single_addr, index = self.__write_row_data(
                spec, synapse_info.connector, pre_vertex_slice,
                post_vertex_slice, row_length, row_data, rinfo,
                single_synapses, block_addr, single_addr, app_edge,
                synapse_info)
        elif rinfo is not None:
            index = self.__poptable_type.update_master_population_table(
                0, 0, rinfo.first_key_and_mask)
        del row_data

        if block_addr > all_syn_block_sz:
            raise Exception(
                "Too much synaptic memory has been written: {} of {} ".format(
                    block_addr, all_syn_block_sz))

        delay_rinfo = self.__delay_key_index.get(
            (app_edge.pre_vertex, pre_vertex_slice), None)
        d_index = None
        if delayed_row_data.size:
            block_addr, single_addr, d_index = self.__write_row_data(
                spec, synapse_info.connector, pre_vertex_slice,
                post_vertex_slice, delayed_row_length, delayed_row_data,
                delay_rinfo, single_synapses,  block_addr, single_addr,
                app_edge, synapse_info)
        elif delay_rinfo is not None:
            d_index = self.__poptable_type.update_master_population_table(
                0, 0, delay_rinfo.first_key_and_mask)
        del delayed_row_data

        if block_addr > all_syn_block_sz:
            raise Exception(
                "Too much synaptic memory has been written: {} of {} ".format(
                    block_addr, all_syn_block_sz))
        if d_index is not None and index is not None and index != d_index:
            raise Exception(
                "Delay index {} and normal index {} do not match".format(
                    d_index, index))
        return block_addr, single_addr, index

    def __is_direct(
            self, single_addr, connector, pre_vertex_slice, post_vertex_slice,
            app_edge, synapse_info):
        """ Determine if the given connection can be done with a "direct"\
            synaptic matrix - this must have an exactly 1 entry per row

        :param int single_addr:
        :param AbstractConnector connector:
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param ProjectionApplicationEdge app_edge:
        :param SynapseInformation synapse_info:
        :rtype: bool
        """
        return (
            app_edge.n_delay_stages == 0 and
            connector.use_direct_matrix(synapse_info) and
            (single_addr + (pre_vertex_slice.n_atoms * BYTES_PER_WORD) <=
                self.__one_to_one_connection_dtcm_max_bytes) and
            (pre_vertex_slice.lo_atom == post_vertex_slice.lo_atom) and
            (pre_vertex_slice.hi_atom == post_vertex_slice.hi_atom))

    def __write_row_data(
            self, spec, connector, pre_vertex_slice, post_vertex_slice,
            row_length, row_data, rinfo, single_synapses,
            block_addr, single_addr, app_edge, synapse_info):
        """
        :param ~.DataSpecificationGenerator spec:
        :param AbstractConnector connector:
        :param ~.Slice pre_vertex_slice:
        :param ~.Slice post_vertex_slice:
        :param int row_length:
        :param ~numpy.ndarray row_data:
        :param .PartitionRoutingInfo rinfo:
        :param list(~numpy.ndarray) single_synapses:
        :param int block_addr:
        :param int single_addr:
        :param ProjectionApplicationEdge app_edge:
        :param SynapseInfornation synapse_info:
        :rtype: tuple(int,int,int)
        """
        if row_length == 1 and self.__is_direct(
                single_addr, connector, pre_vertex_slice, post_vertex_slice,
                app_edge, synapse_info):
            single_rows = row_data.reshape(-1, 4)[:, 3]
            single_synapses.append(single_rows)
            index = self.__poptable_type.update_master_population_table(
                single_addr, 1, rinfo.first_key_and_mask, is_single=True)
            single_addr += len(single_rows) * BYTES_PER_WORD
        else:
            block_addr = self._write_padding(spec, block_addr)
            spec.switch_write_focus(self._synaptic_matrix_region)
            spec.write_array(row_data)
            index = self.__poptable_type.update_master_population_table(
                block_addr, row_length, rinfo.first_key_and_mask)
            block_addr += len(row_data) * BYTES_PER_WORD
        return block_addr, single_addr, index

    def _get_ring_buffer_shifts(
            self, application_vertex, application_graph, machine_time_step,
            weight_scale):
        """ Get the ring buffer shifts for this vertex

        :param .ApplicationVertex application_vertex:
        :param .ApplicationGraph application_graph:
        :param int machine_time_step:
        :param float weight_scale:
        :rtype: list(int)
        """
        if self.__ring_buffer_shifts is None:
            self.__ring_buffer_shifts = \
                self._get_ring_buffer_to_input_left_shifts(
                    application_vertex, application_graph, machine_time_step,
                    weight_scale)
        return self.__ring_buffer_shifts

    def write_data_spec(
            self, spec, application_vertex, post_vertex_slice, machine_vertex,
            placement, machine_graph, application_graph, routing_info,
            weight_scale, machine_time_step):
        """
        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param ~pacman.model.graphs.application_graph.ApplicationGraph \
        application_graph: the app graph
        :param AbstractPopulationVertex application_vertex:
            The vertex owning the synapses
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The part of the vertex we're dealing with
        :param PopulationMachineVertex machine_vertex: The machine vertex
        :param ~pacman.model.placements.Placement placement:
            Where the vertex is placed
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            The graph containing the machine vertex
        :param ~pacman.model.graphs.application.ApplicationGraph \
                application_graph:
            The graph containing the application vertex
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
            How messages are routed
        :param float weight_scale: How to scale the weights of the synapses
        :param int machine_time_step:
        """
        # reset for this machine vertex
        self._host_generated_block_addr = 0
        self._on_chip_generated_block_addr = 0

        # Create an index of delay keys into this vertex
        for m_edge in machine_graph.get_edges_ending_at_vertex(machine_vertex):
            app_edge = m_edge.app_edge
            if isinstance(app_edge.pre_vertex, DelayExtensionVertex):
                self.__delay_key_index[app_edge.pre_vertex.source_vertex,
                                       m_edge.pre_vertex.vertex_slice] = \
                    routing_info.get_routing_info_for_edge(m_edge)

        post_slice_idx = machine_vertex.index

        # Reserve the memory
        in_edges = application_graph.get_edges_ending_at_vertex(
            application_vertex)
        all_syn_block_sz = self._get_synaptic_blocks_size(
            post_vertex_slice, in_edges, machine_time_step)
        self._reserve_memory_regions(
            spec, machine_vertex, post_vertex_slice, machine_graph,
            all_syn_block_sz, application_graph, application_vertex)

        ring_buffer_shifts = self._get_ring_buffer_shifts(
            application_vertex, application_graph, machine_time_step,
            weight_scale)
        weight_scales = self._write_synapse_parameters(
            spec, ring_buffer_shifts, weight_scale)

        gen_data = self._write_synaptic_matrix_and_master_population_table(
            spec, post_slice_idx, machine_vertex,
            post_vertex_slice, all_syn_block_sz, weight_scales,
            routing_info, machine_graph, machine_time_step)

        if self.__synapse_dynamics is not None:
            self.__synapse_dynamics.write_parameters(
                spec, self._synapse_dynamics_region,
                machine_time_step, weight_scales)

            if isinstance(self.__synapse_dynamics,
                          AbstractSynapseDynamicsStructural):
                self.__synapse_dynamics.write_structural_parameters(
                    spec, self._struct_dynamics_region, machine_time_step,
                    weight_scales, application_graph, application_vertex,
                    post_vertex_slice, routing_info, self.__synapse_indices)

        self.__weight_scales[placement] = weight_scales

        self._write_on_machine_data_spec(
            spec, post_vertex_slice, weight_scales, gen_data)

    def clear_connection_cache(self):
        """ Flush the cache of connection information.
        """
        self.__retrieved_blocks = dict()

    def get_connections_from_machine(
            self, transceiver, placement, machine_edge,
            routing_infos, synapse_info, machine_time_step,
            using_extra_monitor_cores, placements=None, monitor_api=None,
            fixed_routes=None, extra_monitor=None):
        """
        :param ~spinnman.transceiver.Transceiver transceiver:
            How to talk to the machine
        :param ~pacman.model.placements.Placement placement:
            Where on the machine are we talking to?
        :param ProjectionMachineEdge machine_edge:
            What edge's connections are we talking about?
        :param ~pacman.model.routing_info.RoutingInfo routing_infos:
            Where did the edge go?
        :param SynapseInformation synapse_info:
            What do we know about the edge's synapses?
        :param int machine_time_step: How fast the clock ticks
        :param bool using_extra_monitor_cores:
            Are we to use the fast download protocol?
        :param placements: Where are all the vertices?
            Must not be ``None`` if ``using_extra_monitor_cores`` is true.
        :type placements: ~pacman.model.placements.Placements or None
        :param monitor_api:
            How do we talk the fast protocol?
            Must not be ``None`` if ``using_extra_monitor_cores`` is true.
        :type monitor_api:
            ~spinn_front_end_common.utility_models.DataSpeedUpPacketGatherMachineVertex
        :param fixed_routes:
            What is the planned configuration of the Fixed Route packet
            routing?
            Must not be ``None`` if ``using_extra_monitor_cores`` is true.
        :type fixed_routes:
            dict(tuple(int,int),~spinn_machine.FixedRouteEntry) or None
        :param extra_monitor:
        :type extra_monitor:
            ~spinn_front_end_common.utility_models.ExtraMonitorSupportMachineVertex
        :rtype: ~numpy.ndarray
        """
        app_edge = machine_edge.app_edge
        if not isinstance(app_edge, ProjectionApplicationEdge):
            return None

        # Get details for extraction
        pre_vertex_slice = machine_edge.pre_vertex.vertex_slice
        post_vertex_slice = machine_edge.post_vertex.vertex_slice

        # Get the key for the pre_vertex
        key = routing_infos.get_first_key_for_edge(machine_edge)

        # Get the key for the delayed pre_vertex
        delayed_key = None
        if app_edge.delay_edge is not None:
            delayed_key = self.__delay_key_index[
                app_edge.pre_vertex, pre_vertex_slice].first_key

        # Get the block for the connections from the pre_vertex
        index = self.__synapse_indices[synapse_info, pre_vertex_slice.lo_atom]
        master_pop_table, direct_synapses, indirect_synapses = \
            self.__compute_addresses(transceiver, placement)
        data, max_row_length = self._retrieve_synaptic_block(
            transceiver, placement, master_pop_table, indirect_synapses,
            direct_synapses, key, pre_vertex_slice.n_atoms, index,
            using_extra_monitor_cores, placements, monitor_api,
            extra_monitor, fixed_routes=fixed_routes)

        # Get the block for the connections from the delayed pre_vertex
        delayed_data = None
        delayed_max_row_len = 0
        if delayed_key is not None:
            delayed_data, delayed_max_row_len = self._retrieve_synaptic_block(
                transceiver, placement, master_pop_table, indirect_synapses,
                direct_synapses, delayed_key,
                pre_vertex_slice.n_atoms * app_edge.n_delay_stages,
                index, using_extra_monitor_cores, placements,
                monitor_api, extra_monitor, fixed_routes=fixed_routes)

        # Convert the blocks into connections
        return self._read_synapses(
            synapse_info, pre_vertex_slice, post_vertex_slice, max_row_length,
            delayed_max_row_len, self.__weight_scales[placement], data,
            delayed_data, machine_time_step)

    def __compute_addresses(self, transceiver, placement):
        """ Helper for computing the addresses of the master pop table and\
            synaptic-matrix-related bits.

        :param ~.Transceiver transceiver:
        :param ~.Placement placement:
        :rtype: tuple(int, int, int)
        """
        master_pop_table = locate_memory_region_for_placement(
            placement, self._pop_table_region, transceiver)
        synaptic_matrix = locate_memory_region_for_placement(
            placement, self._synaptic_matrix_region, transceiver)
        direct_synapses = BYTES_PER_WORD + locate_memory_region_for_placement(
            placement, self._direct_matrix_region, transceiver)
        return master_pop_table, direct_synapses, synaptic_matrix

    def _extract_synaptic_matrix_data_location(
            self, key, master_pop_table_address, txrx, placement):
        """
        :param int key:
        :param int master_pop_table_address:
        :param ~spinnman.transceiver.Transceiver txrx:
        :param ~.Placement placement:
        :rtype: list(tuple(int, int, bool))
        """
        return self.__poptable_type.extract_synaptic_matrix_data_location(
            key, master_pop_table_address, txrx, placement.x, placement.y)

    def _read_synapses(self, info, pre_slice, post_slice, max_row_length,
                       delayed_max_row_length, weight_scales,
                       data, delayed_data, timestep):
        """
        :param SynapseInformation synapse_info:
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param int max_row_length:
        :param int delayed_max_row_length:
        :param dict(AbstractSynapseType,float) weight_scales:
        :param data:
        :type data: bytes or bytearray or memoryview
        :param delayed_data:
        :type delayed_data: bytes or bytearray or memoryview
        :param int timestep:
        :return: array with ``weight`` and ``delay`` columns
        :rtype: ~numpy.ndarray
        """
        return self.__synapse_io.read_synapses(
            info, pre_slice, post_slice, max_row_length,
            delayed_max_row_length, self.__n_synapse_types, weight_scales,
            data, delayed_data, timestep)

    def _retrieve_synaptic_block(
            self, txrx, placement, master_pop_table_address,
            indirect_synapses_address, direct_synapses_address,
            key, n_rows, index, using_monitors, placements=None,
            data_receiver=None, extra_monitor=None, fixed_routes=None):
        """ Read in a synaptic block from a given processor and vertex on\
            the machine

        :param ~.Transceiver txrx:
        :param ~.Placement placement:
        :param int master_pop_table_address:
        :param int indirect_synapses_address:
        :param int direct_synapses_address:
        :param int key:
        :param int n_rows:
        :param int index:
        :param bool using_monitors:
        :param ~.Placements placements:
        :param ~.DataSpeedUpPacketGatherMachineVertex data_receiver:
        :param ~.ExtraMonitorSupportMachineVertex extra_monitor:
        :param dict(tuple(int,int),~.FixedRouteEntry) fixed_routes:
        :rtype: tuple(bytearray, int)
        """
        # See if we have already got this block
        if (placement, key, index) in self.__retrieved_blocks:
            return self.__retrieved_blocks[placement, key, index]

        items = self._extract_synaptic_matrix_data_location(
            key, master_pop_table_address, txrx, placement)
        if index >= len(items):
            return None, 0

        max_row_length, synaptic_block_offset, is_single = items[index]
        if max_row_length == 0:
            return None, 0

        block = None
        if max_row_length > 0 and synaptic_block_offset is not None:
            # read in the synaptic block
            if not is_single:
                block = self.__read_multiple_synaptic_blocks(
                    txrx, data_receiver, placement, n_rows, max_row_length,
                    indirect_synapses_address + synaptic_block_offset,
                    using_monitors, extra_monitor, fixed_routes, placements)
            else:
                block, max_row_length = self.__read_single_synaptic_block(
                    txrx, data_receiver, placement, n_rows,
                    direct_synapses_address + synaptic_block_offset,
                    using_monitors, extra_monitor, fixed_routes, placements)

        result = (block, max_row_length)
        self.__retrieved_blocks[placement, key, index] = result
        return result

    def __read_multiple_synaptic_blocks(
            self, transceiver, data_receiver, placement, n_rows,
            max_row_length, address, using_monitors, extra_monitor,
            fixed_routes, placements):
        """ Read in an array of synaptic blocks.

        :param ~.Transceiver transceiver:
        :param ~.DataSpeedUpPacketGatherMachineVertex data_receiver:
        :param ~.Placement placement:
        :param int n_rows:
        :param int max_row_length:
        :param int address:
        :param bool using_monitors:
        :param ~.ExtraMonitorSupportMachineVertex extra_monitor:
        :param dict(tuple(int,int),~.FixedRouteEntry) fixed_routes:
        :param ~.Placements placements:
        :rtype: bytearray
        """
        # calculate the synaptic block size in bytes
        synaptic_block_size = self.__synapse_io.get_block_n_bytes(
            max_row_length, n_rows)

        # read in the synaptic block
        if using_monitors:
            extra_monitor.update_transaction_id_from_machine(transceiver)
            return data_receiver.get_data(
                extra_monitor,
                placements.get_placement_of_vertex(extra_monitor),
                address, synaptic_block_size, fixed_routes)
        return transceiver.read_memory(
            placement.x, placement.y, address, synaptic_block_size)

    @staticmethod
    def __read_single_synaptic_block(
            transceiver, data_receiver, placement, n_rows, address,
            using_monitors, extra_monitor, fixed_routes, placements):
        """ Read in a single synaptic block.

        :param ~.Transceiver transceiver:
        :param ~.DataSpeedUpPacketGatherMachineVertex data_receiver:
        :param ~.Placement placement:
        :param int n_rows:
        :param int address:
        :param bool using_monitors:
        :param ~.ExtraMonitorSupportMachineVertex extra_monitor:
        :param dict(tuple(int,int),~.FixedRouteEntry) fixed_routes:
        :param ~.Placements placements:
        :rtype: tuple(bytearray, int)
        """
        # The data is one per row
        synaptic_block_size = n_rows * BYTES_PER_WORD

        # read in the synaptic row data
        if using_monitors:
            extra_monitor.update_transaction_id_from_machine(transceiver)
            single_block = data_receiver.get_data(
                extra_monitor,
                placements.get_placement_of_vertex(extra_monitor),
                address, synaptic_block_size, fixed_routes)
        else:
            single_block = transceiver.read_memory(
                placement.x, placement.y, address, synaptic_block_size)

        # Convert the block into a set of rows
        numpy_block = numpy.zeros((n_rows, BYTES_PER_WORD), dtype="uint32")
        numpy_block[:, 3] = numpy.asarray(
            single_block, dtype="uint8").view("uint32")
        numpy_block[:, 1] = 1
        return bytearray(numpy_block.tobytes()), 1

    # inherited from AbstractProvidesIncomingPartitionConstraints
    def get_incoming_partition_constraints(self):
        """ Gets the constraints due to synapses managed by this class.

        :return: a list of constraints
        :rtype: list(~pacman.model.constraints.AbstractConstraint)
        """
        return self.__poptable_type.get_edge_constraints()

    def _write_on_machine_data_spec(
            self, spec, post_vertex_slice, weight_scales, generator_data):
        """ Write the data spec for the synapse expander

        :param ~.DataSpecificationGenerator spec:
            The specification to write to
        :param ~pacman.model.common.Slice post_vertex_slice:
            The slice of the vertex being written
        :param weight_scales: scaling of weights on each synapse
        :type weight_scales: list(int or float)
        :param list(GeneratorData) generator_data:
        """
        if not generator_data:
            return

        n_bytes = (
            _SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES +
            (self.__n_synapse_types * BYTES_PER_WORD))
        for data in generator_data:
            n_bytes += data.size

        spec.reserve_memory_region(
            region=self._connector_builder_region,
            size=n_bytes, label="ConnectorBuilderRegion")
        spec.switch_write_focus(self._connector_builder_region)

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
            spec.write_value(data=min(w, dtype.max), data_type=dtype)

        for data in generator_data:
            spec.write_array(data.gen_data)

    def gen_on_machine(self, vertex_slice):
        """ True if the synapses should be generated on the machine

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: bool
        """
        return self.__gen_on_machine.get(vertex_slice, False)

    def reset_ring_buffer_shifts(self):
        self.__ring_buffer_shifts = None

    @property
    def changes_during_run(self):
        """ Whether the synapses being managed change during running.

        :rtype: bool
        """
        if self.__synapse_dynamics is None:
            return False
        return self.__synapse_dynamics.changes_during_run
