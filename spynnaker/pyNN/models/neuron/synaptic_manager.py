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

import math
import numpy
from scipy import special  # @UnresolvedImport

from spinn_utilities.progress_bar import ProgressBar
from data_specification.enums import DataType
from spinn_utilities.config_holder import (
    get_config_float, get_config_int, get_config_bool)
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, MICRO_TO_SECOND_CONVERSION)
from spinn_front_end_common.utilities.globals_variables import (
    machine_time_step)
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.models.abstract_models import AbstractMaxSpikes
from spynnaker.pyNN.models.neuron.synapse_io import SynapseIORowBased
from spynnaker.pyNN.utilities.constants import (
    POPULATION_BASED_REGIONS, POSSION_SIGMA_SUMMATION_LIMIT)
from spynnaker.pyNN.utilities.utility_calls import (get_n_bits)
from spynnaker.pyNN.utilities.running_stats import RunningStats
from .synapse_dynamics import (
    AbstractSynapseDynamics, AbstractSynapseDynamicsStructural)
from .synaptic_matrices import SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES
from .synaptic_matrices import SynapticMatrices

TIME_STAMP_BYTES = BYTES_PER_WORD

# TODO: Make sure these values are correct (particularly CPU cycles)
_SYNAPSES_BASE_DTCM_USAGE_IN_BYTES = 7 * BYTES_PER_WORD

# 1 for drop late packets.
_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES = 1 * BYTES_PER_WORD
_SYNAPSES_BASE_N_CPU_CYCLES_PER_NEURON = 10
_SYNAPSES_BASE_N_CPU_CYCLES = 8


class SynapticManager(object):
    """ Deals with synapses
    """
    # pylint: disable=too-many-arguments, too-many-locals
    __slots__ = [
        # The number of synapse types
        "__n_synapse_types",
        # The maximum size of the direct or single synaptic matrix
        "__all_single_syn_sz",
        # The number of sigmas to use when calculating the ring buffer upper
        # bound
        "__ring_buffer_sigma",
        # The spikes-per-second to use for an incoming population that doesn't
        # specify this
        "__spikes_per_second",
        # The dynamics used by the synapses e.g. STDP, static etc.
        "__synapse_dynamics",
        # The reader and writer of synapses to and from SpiNNaker
        "__synapse_io",
        # A list of scale factors for the weights for each synapse type
        "__weight_scales",
        # A list of ring buffer shift values corresponding to the weight
        # scales; a left shift by this amount will do the multiplication by
        # the weight scale
        "__ring_buffer_shifts",
        # The actual synaptic matrix handling code, split for simplicity
        "__synaptic_matrices",
        # Determine whether spikes should be dropped if they arrive after the
        # end of a timestep
        "__drop_late_spikes",
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

    NOT_EXACT_SLICES_ERROR_MESSAGE = (
        "The splitter {} is returning estimated slices during DSG. "
        "This is deemed an error. Please fix and try again")

    TOO_MUCH_WRITTEN_SYNAPTIC_DATA = (
        "Too much synaptic memory has been written: {} of {} ")

    INDEXS_DONT_MATCH_ERROR_MESSAGE = (
        "Delay index {} and normal index {} do not match")

    NO_DELAY_EDGE_FOR_SRC_IDS_MESSAGE = (
        "Found delayed source IDs but no delay machine edge for {}")

    def __init__(self, n_synapse_types, ring_buffer_sigma, spikes_per_second,
                 drop_late_spikes):
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

        # Create the synapse IO
        self.__synapse_io = SynapseIORowBased()

        if self.__ring_buffer_sigma is None:
            self.__ring_buffer_sigma = get_config_float(
                "Simulation", "ring_buffer_sigma")

        if self.__spikes_per_second is None:
            self.__spikes_per_second = get_config_float(
                "Simulation", "spikes_per_second")

        if self.__drop_late_spikes is None:
            self.__drop_late_spikes = get_config_bool(
                "Simulation", "drop_late_spikes")

        # Prepare for dealing with STDP - there can only be one (non-static)
        # synapse dynamics per vertex at present
        self.__synapse_dynamics = None

        # Keep the details once computed to allow reading back
        self.__weight_scales = None
        self.__ring_buffer_shifts = None

        # Limit the DTCM used by one-to-one connections
        self.__all_single_syn_sz = get_config_int(
            "Simulation", "one_to_one_connection_dtcm_max_bytes")

        # Post vertex slice to synaptic matrices
        self.__synaptic_matrices = dict()

    def __get_synaptic_matrices(self, post_vertex_slice):
        """ Get the synaptic matrices for a given slice of the vertex

        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            the slice of the vertex to get the matrices for
        :rtype: SynapticMatrices
        """
        # Use the cached version if possible
        if post_vertex_slice in self.__synaptic_matrices:
            return self.__synaptic_matrices[post_vertex_slice]

        # Otherwise generate new ones
        matrices = SynapticMatrices(
            post_vertex_slice, self.__n_synapse_types,
            self.__all_single_syn_sz, self.__synapse_io,
            self._synaptic_matrix_region, self._direct_matrix_region,
            self._pop_table_region)
        self.__synaptic_matrices[post_vertex_slice] = matrices
        return matrices

    def host_written_matrix_size(self, post_vertex_slice):
        """ The size of the matrix written by the host for a given\
            machine vertex

        :param post_vertex_slice: The slice of the vertex to get the size of
        :rtype: int
        """
        matrices = self.__get_synaptic_matrices(post_vertex_slice)
        return matrices.host_generated_block_addr

    def on_chip_written_matrix_size(self, post_vertex_slice):
        """ The size of the matrix that will be written on the machine for a\
            given machine vertex

        :param post_vertex_slice: The slice of the vertex to get the size of
        :rtype: int
        """
        matrices = self.__get_synaptic_matrices(post_vertex_slice)
        return (matrices.on_chip_generated_block_addr -
                matrices.host_generated_block_addr)

    @property
    def synapse_dynamics(self):
        """ The synapse dynamics used by the synapses e.g. plastic or static.\
            Settable.

        :rtype: AbstractSynapseDynamics or None
        """
        return self.__synapse_dynamics

    @property
    def drop_late_spikes(self):
        return self.__drop_late_spikes

    @synapse_dynamics.setter
    def synapse_dynamics(self, synapse_dynamics):
        """ Set the synapse dynamics.  Note that after setting, the dynamics\
            might not be the type set as it can be combined with the existing\
            dynamics in exciting ways.
        """
        if self.__synapse_dynamics is None:
            self.__synapse_dynamics = synapse_dynamics
        else:
            self.__synapse_dynamics = self.__synapse_dynamics.merge(
                synapse_dynamics)

    @property
    def ring_buffer_sigma(self):
        """ The sigma in the estimation of the maximum summed ring buffer\
            weights.  Settable.

        :rtype: float
        """
        return self.__ring_buffer_sigma

    @ring_buffer_sigma.setter
    def ring_buffer_sigma(self, ring_buffer_sigma):
        self.__ring_buffer_sigma = ring_buffer_sigma

    @property
    def spikes_per_second(self):
        """ The assumed maximum spikes per second of an incoming population.\
            Used when calculating the ring buffer weight scaling. Settable.

        :rtype: float
        """
        return self.__spikes_per_second

    @spikes_per_second.setter
    def spikes_per_second(self, spikes_per_second):
        self.__spikes_per_second = spikes_per_second

    @property
    def vertex_executable_suffix(self):
        """ The suffix of the executable name due to the type of synapses \
            in use.

        :rtype: str
        """
        if self.__synapse_dynamics is None:
            return ""
        return self.__synapse_dynamics.get_vertex_executable_suffix()

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

    def _get_synapse_dynamics_parameter_size(
            self, n_atoms, app_graph, app_vertex):
        """ Get the size of the synapse dynamics region

        :param int n_atoms: The number of atoms on the core
        :param ~.ApplicationGraph app_graph: The application graph
        :param ~.ApplicationVertex app_vertex: The application vertex
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
                     app_graph, app_vertex, n_atoms)
        else:
            return self.__synapse_dynamics.get_parameters_sdram_usage_in_bytes(
                n_atoms, self.__n_synapse_types)

    def get_sdram_usage_in_bytes(
            self, post_vertex_slice, application_graph, app_vertex):
        """ Get the SDRAM usage of a slice of atoms of this vertex

        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The slice of atoms to get the size of
        :param ~pacman.model.graphs.application.ApplicationGraph \
                application_graph: The application graph
        :param AbstractPopulationVertex app_vertex: The application vertex
        :rtype: int
        """
        in_edges = application_graph.get_edges_ending_at_vertex(app_vertex)
        matrices = self.__get_synaptic_matrices(post_vertex_slice)
        return (
            self._get_synapse_params_size() +
            self._get_synapse_dynamics_parameter_size(
                post_vertex_slice.n_atoms, application_graph, app_vertex) +
            matrices.size(in_edges))

    def _reserve_memory_regions(
            self, spec, vertex_slice, all_syn_block_sz, machine_graph,
            machine_vertex):
        """ Reserve memory regions for a core

        :param ~.DataSpecificationGenerator spec: The data spec to reserve in
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the vertex to allocate for
        :param int all_syn_block_sz: The memory to reserve for synapses
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            The machine graph
        :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
            The machine vertex
        """
        spec.reserve_memory_region(
            region=self._synapse_params_region,
            size=self._get_synapse_params_size(),
            label='SynapseParams')

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
                    machine_graph, machine_vertex, vertex_slice.n_atoms))

            if synapse_structural_dynamics_sz != 0:
                spec.reserve_memory_region(
                    region=self._struct_dynamics_region,
                    size=synapse_structural_dynamics_sz,
                    label='synapseDynamicsStructuralParams')

    @staticmethod
    def _ring_buffer_expected_upper_bound(
            weight_mean, weight_std_dev, spikes_per_second, n_synapses_in,
            sigma):
        """ Provides expected upper bound on accumulated values in a ring\
            buffer element.

        Requires an assessment of maximum Poisson input rate.

        Assumes knowledge of mean and SD of weight distribution, fan-in
        and timestep.

        All arguments should be assumed real values except n_synapses_in
        which will be an integer.

        :param float weight_mean: Mean of weight distribution (in either nA or
            microSiemens as required)
        :param float weight_std_dev: SD of weight distribution
        :param float spikes_per_second: Maximum expected Poisson rate in Hz
        :param int n_synapses_in: No of connected synapses
        :param float sigma: How many SD above the mean to go for upper bound;
            a good starting choice is 5.0. Given length of simulation we can
            set this for approximate number of saturation events.
        :rtype: float
        """
        # E[ number of spikes ] in a timestep
        steps_per_second = (MICRO_TO_SECOND_CONVERSION /
                            machine_time_step())

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
            self, machine_vertex, machine_graph, weight_scale):
        """ Get the scaling of the ring buffer to provide as much accuracy as\
            possible without too much overflow

        :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
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
        steps_per_second = (
                MICRO_TO_SECOND_CONVERSION /
                machine_time_step())

        synapse_map = dict()
        for machine_edge in machine_graph.get_edges_ending_at_vertex(
                machine_vertex):
            if isinstance(machine_edge.app_edge, ProjectionApplicationEdge):
                for synapse_info in machine_edge.app_edge.synapse_information:
                    # Per synapse info we need any one of the edges
                    synapse_map[synapse_info] = machine_edge

        for synapse_info in synapse_map:
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
                connector, synapse_info.weights,
                synapse_info) * weight_scale_squared
            running_totals[synapse_type].add_items(
                weight_mean, weight_variance, n_connections)

            delay_variance = synapse_dynamics.get_delay_variance(
                connector, synapse_info.delays, synapse_info)
            delay_running_totals[synapse_type].add_items(
                0.0, delay_variance, n_connections)

            weight_max = (synapse_dynamics.get_weight_maximum(
                connector, synapse_info) * weight_scale)
            biggest_weight[synapse_type] = max(
                biggest_weight[synapse_type], weight_max)

            spikes_per_tick = max(
                1.0, self.__spikes_per_second / steps_per_second)
            spikes_per_second = self.__spikes_per_second
            pre_vertex = synapse_map[synapse_info].pre_vertex
            if isinstance(pre_vertex, AbstractMaxSpikes):
                rate = pre_vertex.max_spikes_per_second()
                if rate != 0:
                    spikes_per_second = rate
                spikes_per_tick = \
                    pre_vertex.max_spikes_per_ts()
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
                        stats.n_items, self.__ring_buffer_sigma),
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

    def __update_ring_buffer_shifts_and_weight_scales(
            self, machine_vertex, machine_graph, weight_scale):
        """ Update the ring buffer shifts and weight scales for this vertex

        :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
        :param float weight_scale:
        """
        if self.__ring_buffer_shifts is None:
            self.__ring_buffer_shifts = \
                self._get_ring_buffer_to_input_left_shifts(
                    machine_vertex, machine_graph, weight_scale)
            self.__weight_scales = numpy.array([
                self.__get_weight_scale(r) * weight_scale
                for r in self.__ring_buffer_shifts])

    def write_data_spec(
            self, spec, application_vertex, post_vertex_slice, machine_vertex,
            machine_graph, application_graph, routing_info, weight_scale):
        """
        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param AbstractPopulationVertex application_vertex:
            The vertex owning the synapses
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The part of the vertex we're dealing with
        :param PopulationMachineVertex machine_vertex: The machine vertex
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            The graph containing the machine vertex
        :param ~pacman.model.graphs.application.ApplicationGraph \
                application_graph:
            The graph containing the application vertex
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
            How messages are routed
        :param float weight_scale: How to scale the weights of the synapses
        """
        # Reserve the memory
        in_edges = application_graph.get_edges_ending_at_vertex(
            application_vertex)
        matrices = self.__get_synaptic_matrices(post_vertex_slice)
        all_syn_block_sz = matrices.synapses_size(in_edges)
        self._reserve_memory_regions(
            spec, post_vertex_slice, all_syn_block_sz, machine_graph,
            machine_vertex)

        self.__update_ring_buffer_shifts_and_weight_scales(
            machine_vertex, machine_graph, weight_scale)
        spec.switch_write_focus(self._synapse_params_region)
        # write the bool for deleting packets that were too late for a timer
        spec.write_value(int(self.__drop_late_spikes))
        # Write the ring buffer shifts
        spec.write_array(self.__ring_buffer_shifts)

        gen_data = matrices.write_synaptic_matrix_and_master_population_table(
            spec, machine_vertex, all_syn_block_sz, self.__weight_scales,
            routing_info, machine_graph)

        if self.__synapse_dynamics is not None:
            self.__synapse_dynamics.write_parameters(
                spec, self._synapse_dynamics_region,
                self.__weight_scales)

            if isinstance(self.__synapse_dynamics,
                          AbstractSynapseDynamicsStructural):
                self.__synapse_dynamics.write_structural_parameters(
                    spec, self._struct_dynamics_region, self.__weight_scales,
                    machine_graph, machine_vertex, routing_info, matrices)

        self._write_on_machine_data_spec(spec, post_vertex_slice, gen_data)

    def _write_on_machine_data_spec(
            self, spec, post_vertex_slice, generator_data):
        """ Write the data spec for the synapse expander

        :param ~.DataSpecificationGenerator spec:
            The specification to write to
        :param ~pacman.model.common.Slice post_vertex_slice:
            The slice of the vertex being written
        :param list(GeneratorData) generator_data:
        """
        if not generator_data:
            return

        n_bytes = (
            SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES +
            (self.__n_synapse_types * DataType.U3232.size))
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
        for w in self.__weight_scales:
            # if the weights are high enough and the population size large
            # enough, then weight_scales < 1 will result in a zero scale
            # if converted to an int, so we use U3232 here instead (as there
            # can be scales larger than U1616.max in conductance-based models)
            dtype = DataType.U3232
            spec.write_value(data=min(w, dtype.max), data_type=dtype)

        for data in generator_data:
            spec.write_array(data.gen_data)

    def get_connections_from_machine(
            self, transceiver, placements, app_edge, synapse_info):
        """ Read the connections from the machine for a given projection

        :param ~spinnman.transciever.Transceiver transceiver:
            Used to read the data from the machine
        :param ~pacman.model.placements.Placements placements:
            Where the vertices are on the machine
        :param ProjectionApplicationEdge app_edge:
            The application edge of the projection
        :param SynapseInformation synapse_info:
            The synapse information of the projection
        :return: The connections from the machine, with dtype
            AbstractSynapseDynamics.NUMPY_CONNECTORS_DTYPE
        :rtype: ~numpy.ndarray
        """

        post_vertices = app_edge.post_vertex.machine_vertices

        # Start with something in the list so that concatenate works
        connections = [numpy.zeros(
                0, dtype=AbstractSynapseDynamics.NUMPY_CONNECTORS_DTYPE)]
        progress = ProgressBar(
            len(post_vertices),
            "Getting synaptic data between {} and {}".format(
                app_edge.pre_vertex.label, app_edge.post_vertex.label))
        for post_vertex in progress.over(post_vertices):
            post_slice = post_vertex.vertex_slice
            placement = placements.get_placement_of_vertex(post_vertex)
            matrix = self.__get_synaptic_matrices(post_slice)
            connections.extend(matrix.get_connections_from_machine(
                transceiver, placement, app_edge, synapse_info))
        return numpy.concatenate(connections)

    def gen_on_machine(self, post_vertex_slice):
        """ True if the synapses should be generated on the machine

        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The slice of the vertex to determine the generation status of
        :rtype: bool
        """
        matrices = self.__get_synaptic_matrices(post_vertex_slice)
        return matrices.gen_on_machine

    def reset_ring_buffer_shifts(self):
        """ Reset the ring buffer shifts; needed if projection data changes
            between runs
        """
        self.__ring_buffer_shifts = None
        self.__weight_scales = None

    def clear_connection_cache(self):
        """ Flush the cache of connection information; needed for a second run
        """
        for matrices in self.__synaptic_matrices.values():
            matrices.clear_connection_cache()

    @property
    def changes_during_run(self):
        """ Whether the synapses being managed change during running.

        :rtype: bool
        """
        if self.__synapse_dynamics is None:
            return False
        return self.__synapse_dynamics.changes_during_run

    def read_generated_connection_holders(self, transceiver, placement):
        """ Fill in any pre-run connection holders for data which is generated
            on the machine, after it has been generated

        :param ~spinnman.transceiver.Transceiver transceiver:
            How to read the data from the machine
        :param ~pacman.model.placements.Placement placement:
            where the data is to be read from
        """
        matrices = self.__get_synaptic_matrices(placement.vertex.vertex_slice)
        matrices.read_generated_connection_holders(transceiver, placement)

    def clear_all_caches(self):
        """ Clears all cached data in the case that a reset requires remapping
            which might change things
        """
        # Clear the local caches
        self.clear_connection_cache()
        self.reset_ring_buffer_shifts()

        # We can simply reset this dict to reset everything downstream
        self.__synaptic_matrices = dict()
