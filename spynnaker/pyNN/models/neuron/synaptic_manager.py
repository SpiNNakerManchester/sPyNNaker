from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neuron import master_pop_table_generators
from spynnaker.pyNN.utilities.running_stats import RunningStats
from spynnaker.pyNN.models.neural_projections.connectors.one_to_one_connector \
    import OneToOneConnector
from spynnaker.pyNN.models.spike_source.spike_source_poisson \
    import SpikeSourcePoisson
from spynnaker.pyNN.models.utility_models.delay_extension_vertex \
    import DelayExtensionVertex
from spynnaker.pyNN.models.neuron.synapse_io.synapse_io_row_based \
    import SynapseIORowBased
from spynnaker.pyNN.models.neural_projections.projection_partitionable_edge \
    import ProjectionPartitionableEdge
from spynnaker.pyNN.models.neuron.synapse_dynamics.synapse_dynamics_static \
    import SynapseDynamicsStatic

from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from pacman.model.graph_mapper.slice import Slice

from data_specification.enums.data_type import DataType

from spinn_front_end_common.utilities import helpful_functions

from scipy import special
import scipy.stats
from collections import defaultdict
from pyNN.random import RandomDistribution
import math
import sys
import numpy
import struct

# TODO: Make sure these values are correct (particularly CPU cycles)
_SYNAPSES_BASE_DTCM_USAGE_IN_BYTES = 28
_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES = 0
_SYNAPSES_BASE_N_CPU_CYCLES_PER_NEURON = 10
_SYNAPSES_BASE_N_CPU_CYCLES = 8


class SynapticManager(object):
    """ Deals with synapses
    """

    def __init__(self, synapse_type, machine_time_step, ring_buffer_sigma,
                 spikes_per_second, population_table_type=None,
                 synapse_io=None):

        self._synapse_type = synapse_type
        self._ring_buffer_sigma = ring_buffer_sigma
        self._spikes_per_second = spikes_per_second
        self._machine_time_step = machine_time_step

        # Get the type of population table
        self._population_table_type = population_table_type
        if population_table_type is None:
            population_table_type = ("MasterPopTableAs" + conf.config.get(
                "MasterPopTable", "generator"))
            algorithms = helpful_functions.get_valid_components(
                master_pop_table_generators, "master_pop_table_as")
            self._population_table_type = algorithms[population_table_type]()

        # Get the synapse IO
        self._synapse_io = synapse_io
        if synapse_io is None:
            self._synapse_io = SynapseIORowBased(machine_time_step)

        if self._ring_buffer_sigma is None:
            self._ring_buffer_sigma = conf.config.getfloat(
                "Simulation", "ring_buffer_sigma")

        if self._spikes_per_second is None:
            self._spikes_per_second = conf.config.getfloat(
                "Simulation", "spikes_per_second")
        self._spikes_per_tick = max(
            1.0,
            self._spikes_per_second /
            (1000000.0 / float(self._machine_time_step)))

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
            raise exceptions.SynapticConfigurationException(
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

    @property
    def maximum_delay_supported_in_ms(self):
        return self._synapse_io.get_maximum_delay_supported_in_ms()

    @property
    def vertex_executable_suffix(self):
        return self._synapse_dynamics.get_vertex_executable_suffix()

    def add_pre_run_connection_holder(
            self, connection_holder, edge, synapse_info):
        self._pre_run_connection_holders[(edge, synapse_info)].append(
            connection_holder)

    def get_n_cpu_cycles(self, vertex_slice, graph):

        # TODO: Calculate this correctly
        return 0

    def get_dtcm_usage_in_bytes(self, vertex_slice, graph):

        # TODO: Calculate this correctly
        return 0

    def _get_synapse_params_size(self, vertex_slice):
        per_neuron_usage = (
            self._synapse_type.get_sdram_usage_per_neuron_in_bytes())
        return (_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES +
                (per_neuron_usage * vertex_slice.n_atoms) +
                (4 * self._synapse_type.get_n_synapse_types()))

    def _get_static_synaptic_matrix_sdram_requirements(self):
        return 8 # 4 for address of direct addresses, and
        # 4 for the size of the direct addresses matrix in bytes

    def _get_exact_synaptic_blocks_size(
            self, post_slices, post_slice_index, post_vertex_slice,
            graph_mapper, subvertex_in_edges):
        """ Get the exact size all of the synaptic blocks
        """

        memory_size = self._get_static_synaptic_matrix_sdram_requirements()

        # Go through the subedges and add up the memory
        for subedge in subvertex_in_edges:

            edge = graph_mapper.get_partitionable_edge_from_partitioned_edge(
                subedge)
            if isinstance(edge, ProjectionPartitionableEdge):

                # Add on the size of the tables to be generated
                pre_vertex_slice = graph_mapper.get_subvertex_slice(
                    subedge.pre_subvertex)
                pre_slices = graph_mapper.get_subvertex_slices(edge.pre_vertex)
                pre_slice_index = graph_mapper.get_subvertex_index(
                    subedge.pre_subvertex)

                memory_size += self._get_size_of_synapse_information(
                    edge.synapse_information, pre_slices, pre_slice_index,
                    post_slices, post_slice_index, pre_vertex_slice,
                    post_vertex_slice, edge.n_delay_stages)

        return memory_size

    def _get_estimate_synaptic_blocks_size(self, post_vertex_slice, in_edges):
        """ Get an estimate of the synaptic blocks memory size
        """

        memory_size = self._get_static_synaptic_matrix_sdram_requirements()

        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionPartitionableEdge):

                # Get an estimate of the number of post sub-vertices by
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

                # Get an estimate of the number of pre-sub-vertices - clearly
                # this will not be correct if the SDRAM usage is high!
                # TODO: Can be removed once we move to population-based keys
                n_atoms_per_subvertex = sys.maxint
                if isinstance(in_edge.pre_vertex, AbstractPartitionableVertex):
                    n_atoms_per_subvertex = \
                        in_edge.pre_vertex.get_max_atoms_per_core()
                if in_edge.pre_vertex.n_atoms < n_atoms_per_subvertex:
                    n_atoms_per_subvertex = in_edge.pre_vertex.n_atoms
                pre_slices = [Slice(
                    lo_atom, min(
                        in_edge.pre_vertex.n_atoms,
                        lo_atom + n_atoms_per_subvertex - 1))
                    for lo_atom in range(
                        0, in_edge.pre_vertex.n_atoms, n_atoms_per_subvertex)]

                pre_slice_index = 0
                for pre_vertex_slice in pre_slices:
                    memory_size += self._get_size_of_synapse_information(
                        in_edge.synapse_information, pre_slices,
                        pre_slice_index, post_slices, post_slice_index,
                        pre_vertex_slice, post_vertex_slice,
                        in_edge.n_delay_stages)
                    pre_slice_index += 1

        return memory_size

    def _get_size_of_synapse_information(
            self, synapse_information, pre_slices, pre_slice_index,
            post_slices, post_slice_index, pre_vertex_slice, post_vertex_slice,
            n_delay_stages):

        memory_size = 0
        for synapse_info in synapse_information:
            undelayed_size, delayed_size = \
                self._synapse_io.get_sdram_usage_in_bytes(
                    synapse_info, pre_slices,
                    pre_slice_index, post_slices, post_slice_index,
                    pre_vertex_slice, post_vertex_slice,
                    n_delay_stages, self._population_table_type)

            memory_size = self._population_table_type\
                .get_next_allowed_address(memory_size)
            memory_size += undelayed_size
            memory_size = self._population_table_type\
                .get_next_allowed_address(memory_size)
            memory_size += delayed_size
        return memory_size

    def _get_synapse_dynamics_parameter_size(self, vertex_slice, in_edges):
        """ Get the size of the synapse dynamics region
        """
        return self._synapse_dynamics.get_parameters_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self._synapse_type.get_n_synapse_types())

    def get_sdram_usage_in_bytes(self, vertex_slice, in_edges):
        return (
            self._get_synapse_params_size(vertex_slice) +
            self._get_synapse_dynamics_parameter_size(vertex_slice, in_edges) +
            self._get_estimate_synaptic_blocks_size(vertex_slice, in_edges) +
            self._population_table_type.get_master_population_table_size(
                vertex_slice, in_edges))

    def _reserve_memory_regions(
            self, spec, vertex, subvertex, vertex_slice, graph, sub_graph,
            all_syn_block_sz, graph_mapper):

        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value,
            size=self._get_synapse_params_size(vertex_slice),
            label='SynapseParams')

        in_edges = graph.incoming_edges_to_vertex(vertex)
        master_pop_table_sz = \
            self._population_table_type.get_exact_master_population_table_size(
                subvertex, sub_graph, graph_mapper)
        if master_pop_table_sz > 0:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.POPULATION_TABLE
                                                         .value,
                size=master_pop_table_sz, label='PopTable')
        if all_syn_block_sz > 0:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX
                                                         .value,
                size=all_syn_block_sz, label='SynBlocks')

        synapse_dynamics_sz = self._get_synapse_dynamics_parameter_size(
            vertex_slice, in_edges)
        if synapse_dynamics_sz != 0:
            spec.reserve_memory_region(
                region=constants.POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS
                                                         .value,
                size=synapse_dynamics_sz, label='synapseDynamicsParams')

    def get_number_of_mallocs_used_by_dsg(self):
        return 4

    @staticmethod
    def _ring_buffer_expected_upper_bound(
            weight_mean, weight_std_dev, spikes_per_second,
            machine_timestep, n_synapses_in, sigma):
        """
        Provides expected upper bound on accumulated values in a ring buffer
        element.

        Requires an assessment of maximum Poisson input rate.

        Assumes knowledge of mean and SD of weight distribution, fan-in
        & timestep.

        All arguments should be assumed real values except n_synapses_in
        which will be an integer.

        weight_mean - Mean of weight distribution (in either nA or
                      microSiemens as required)
        weight_std_dev - SD of weight distribution
        spikes_per_second - Maximum expected Poisson rate in Hz
        machine_timestep - in us
        n_synapses_in - No of connected synapses
        sigma - How many SD above the mean to go for upper bound;
                a good starting choice is 5.0.  Given length of simulation we
                can set this for approximate number of saturation events

        """

        # E[ number of spikes ] in a timestep
        # x /1000000.0 = conversion between microsecond to second
        average_spikes_per_timestep = (
            float(n_synapses_in * spikes_per_second) *
            (float(machine_timestep) / 1000000.0))

        # Exact variance contribution from inherent Poisson variation
        poisson_variance = average_spikes_per_timestep * (weight_mean ** 2)

        # Upper end of range for Poisson summation required below
        # upper_bound needs to be an integer
        upper_bound = int(round(average_spikes_per_timestep +
                                constants.POSSION_SIGMA_SUMMATION_LIMIT *
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

            gammai = special.gammaincc(1 + upper_bound,
                                       average_spikes_per_timestep)

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
            self, subvertex, sub_graph, graph_mapper, post_slices,
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

        for subedge in sub_graph.incoming_subedges_from_subvertex(subvertex):
            pre_vertex_slice = graph_mapper.get_subvertex_slice(
                subedge.pre_subvertex)
            edge = graph_mapper.get_partitionable_edge_from_partitioned_edge(
                subedge)
            pre_slices = [
                graph_mapper.get_subvertex_slice(subv)
                for subv in graph_mapper.get_subvertices_from_vertex(
                    edge.pre_vertex)]
            pre_slice_index = pre_slices.index(pre_vertex_slice)
            if isinstance(edge, ProjectionPartitionableEdge):
                for synapse_info in edge.synapse_information:
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

                    spikes_per_tick = self._spikes_per_tick
                    spikes_per_second = self._spikes_per_second
                    if isinstance(edge.pre_vertex, SpikeSourcePoisson):
                        spikes_per_second = edge.pre_vertex.rate
                        if hasattr(spikes_per_second, "__getitem__"):
                            spikes_per_second = max(spikes_per_second)
                        elif isinstance(spikes_per_second, RandomDistribution):
                            spikes_per_second = \
                                utility_calls.get_maximum_probable_value(
                                    spikes_per_second,
                                    pre_vertex_slice.n_atoms)
                        prob = 1.0 - ((1.0 / 100.0) / pre_vertex_slice.n_atoms)
                        spikes_per_tick = (
                            spikes_per_second /
                            (1000000.0 / float(self._machine_time_step)))
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
                max_weights[synapse_type] = total_weights[synapse_type]
            else:
                max_weights[synapse_type] = min(
                    self._ring_buffer_expected_upper_bound(
                        stats.mean, stats.standard_deviation,
                        rates.mean, machine_timestep, stats.n_items,
                        self._ring_buffer_sigma),
                    total_weights[synapse_type])
                max_weights[synapse_type] = max(
                    max_weights[synapse_type], biggest_weight[synapse_type])

        # Convert these to powers
        max_weight_powers = [0 if w <= 0
                             else int(math.ceil(max(0, math.log(w, 2))))
                             for w in max_weights]

        # If 2^max_weight_power equals the max weight, we have to add another
        # power, as range is 0 - (just under 2^max_weight_power)!
        max_weight_powers = [w + 1 if (2 ** w) <= a else w
                             for w, a in zip(max_weight_powers, max_weights)]

        # If we have synapse dynamics that uses signed weights,
        # Add another bit of shift to prevent overflows
        if weights_signed:
            max_weight_powers = [m + 1 for m in max_weight_powers]

        return max_weight_powers

    @staticmethod
    def _get_weight_scale(ring_buffer_to_input_left_shift):
        """ Return the amount to scale the weights by to convert them from \
            floating point values to 16-bit fixed point numbers which can be \
            shifted left by ring_buffer_to_input_left_shift to produce an\
            s1615 fixed point number
        """
        return float(math.pow(2, 16 - (ring_buffer_to_input_left_shift + 1)))

    def _write_synapse_parameters(
            self, spec, subvertex, subgraph, graph_mapper, post_slices,
            post_slice_index, post_vertex_slice, input_type):

        # Get the ring buffer shifts and scaling factors
        weight_scale = input_type.get_global_weight_scale()
        ring_buffer_shifts = self._get_ring_buffer_to_input_left_shifts(
            subvertex, subgraph, graph_mapper, post_slices, post_slice_index,
            post_vertex_slice, self._machine_time_step, weight_scale)

        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value)
        utility_calls.write_parameters_per_neuron(
            spec, post_vertex_slice,
            self._synapse_type.get_synapse_type_parameters())

        spec.write_array(ring_buffer_shifts)

        weight_scales = numpy.array([
            self._get_weight_scale(r) * weight_scale
            for r in ring_buffer_shifts])
        return weight_scales

    def _write_padding(
            self, spec, synaptic_matrix_region, next_block_start_address):
        next_block_allowed_address = self._population_table_type\
            .get_next_allowed_address(next_block_start_address)
        if next_block_allowed_address != next_block_start_address:

            # Pad out data file with the added alignment bytes:
            spec.comment("\nWriting population table required"
                         " padding\n")
            spec.switch_write_focus(synaptic_matrix_region)
            spec.set_register_value(
                register_id=15,
                data=next_block_allowed_address - next_block_start_address)
            spec.write_value(
                data=0xDD, repeats=15, repeats_is_register=True,
                data_type=DataType.UINT8)
            return next_block_allowed_address
        return next_block_start_address

    def _write_synaptic_matrix_and_master_population_table(
            self, spec, post_slices, post_slice_index, subvertex,
            post_vertex_slice, all_syn_block_sz, weight_scales,
            master_pop_table_region, synaptic_matrix_region, routing_info,
            graph_mapper, partitioned_graph):
        """ Simultaneously generates both the master population table and
            the synaptic matrix.
        """
        spec.comment(
            "\nWriting Synaptic Matrix and Master Population Table:\n")

        # Track writes inside the synaptic matrix region:
        next_block_start_address = 0
        n_synapse_types = self._synapse_type.get_n_synapse_types()

        # Get the edges
        in_subedges = \
            partitioned_graph.incoming_subedges_from_subvertex(subvertex)

        # Set up the master population table
        self._population_table_type.initialise_table(
            spec, master_pop_table_region)

        # Set up for single synapses - write the offset of the single synapses
        # initially 0
        single_synapses = list()
        spec.switch_write_focus(synaptic_matrix_region)
        spec.write_value(0)
        next_single_start_position = 0

        # For each subedge into the subvertex, create a synaptic list
        for subedge in in_subedges:

            edge = graph_mapper.get_partitionable_edge_from_partitioned_edge(
                subedge)
            if isinstance(edge, ProjectionPartitionableEdge):

                spec.comment("\nWriting matrix for subedge:{}\n".format(
                    subedge.label))

                pre_vertex_slice = graph_mapper.get_subvertex_slice(
                    subedge.pre_subvertex)
                pre_slices = graph_mapper.get_subvertex_slices(edge.pre_vertex)
                pre_slice_index = graph_mapper.get_subvertex_index(
                    subedge.pre_subvertex)

                for synapse_info in edge.synapse_information:

                    (row_data, row_length, delayed_row_data,
                     delayed_row_length, delayed_source_ids, delay_stages) = \
                        self._synapse_io.get_synapses(
                            synapse_info, pre_slices, pre_slice_index,
                            post_slices, post_slice_index, pre_vertex_slice,
                            post_vertex_slice, edge.n_delay_stages,
                            self._population_table_type, n_synapse_types,
                            weight_scales)

                    if edge.delay_edge is not None:
                        edge.delay_edge.pre_vertex.add_delays(
                            pre_vertex_slice, delayed_source_ids, delay_stages)
                    elif delayed_source_ids.size != 0:
                        raise Exception("Found delayed source ids but no delay"
                                        " edge for edge {}".format(edge.label))

                    if ((edge, synapse_info) in
                            self._pre_run_connection_holders):
                        holders = self._pre_run_connection_holders[
                            edge, synapse_info]
                        for connection_holder in holders:
                            connections = self._synapse_io.read_synapses(
                                synapse_info, pre_vertex_slice,
                                post_vertex_slice, row_length,
                                delayed_row_length, n_synapse_types,
                                weight_scales, row_data, delayed_row_data,
                                edge.n_delay_stages)
                            connection_holder.add_connections(connections)
                            connection_holder.finish()

                    if len(row_data) > 0:
                        partition = partitioned_graph.get_partition_of_subedge(
                            subedge)
                        keys_and_masks = \
                            routing_info.get_keys_and_masks_from_partition(
                                partition)

                        if (row_length == 1 and isinstance(
                                synapse_info.connector, OneToOneConnector)):
                            single_rows = row_data.reshape(-1, 4)[:, 3]
                            single_synapses.append(single_rows)
                            self._population_table_type\
                                .update_master_population_table(
                                    spec, next_single_start_position, 1,
                                    keys_and_masks, master_pop_table_region,
                                    is_single=True)
                            next_single_start_position += len(single_rows)
                        else:
                            next_block_start_address = self._write_padding(
                                spec, synaptic_matrix_region,
                                next_block_start_address)
                            spec.switch_write_focus(synaptic_matrix_region)
                            spec.write_array(row_data)
                            self._population_table_type\
                                .update_master_population_table(
                                    spec, next_block_start_address, row_length,
                                    keys_and_masks, master_pop_table_region)
                            next_block_start_address += len(row_data) * 4
                    del row_data

                    if next_block_start_address > all_syn_block_sz:
                        raise Exception(
                            "Too much synaptic memory has been written:"
                            " {} of {} ".format(
                                next_block_start_address, all_syn_block_sz))

                    if len(delayed_row_data) > 0:
                        keys_and_masks = self._delay_key_index[
                            (edge.pre_vertex, pre_vertex_slice.lo_atom,
                             pre_vertex_slice.hi_atom)]

                        if (delayed_row_length == 1 and isinstance(
                                synapse_info.connector, OneToOneConnector)):
                            single_rows = delayed_row_data.reshape(-1, 4)[:, 3]
                            single_synapses.append(single_rows)
                            self._population_table_type\
                                .update_master_population_table(
                                    spec, next_single_start_position, 1,
                                    keys_and_masks, master_pop_table_region,
                                    is_single=True)
                            next_single_start_position += len(single_rows)
                        else:
                            next_block_start_address = self._write_padding(
                                spec, synaptic_matrix_region,
                                next_block_start_address)
                            spec.switch_write_focus(synaptic_matrix_region)
                            spec.write_array(delayed_row_data)
                            self._population_table_type\
                                .update_master_population_table(
                                    spec, next_block_start_address,
                                    delayed_row_length, keys_and_masks,
                                    master_pop_table_region)
                            next_block_start_address += len(
                                delayed_row_data) * 4
                    del delayed_row_data

                    if next_block_start_address > all_syn_block_sz:
                        raise Exception(
                            "Too much synaptic memory has been written:"
                            " {} of {} ".format(
                                next_block_start_address, all_syn_block_sz))

        self._population_table_type.finish_master_pop_table(
            spec, master_pop_table_region)

        # Write the size and data of single synapses to the end of the region
        spec.switch_write_focus(synaptic_matrix_region)
        if len(single_synapses) > 0:
            single_data = numpy.concatenate(single_synapses)
            spec.write_value(len(single_data) * 4)
            spec.write_array(single_data)
        else:
            spec.write_value(0)

        # Write the position of the single synapses
        spec.set_write_pointer(0)
        spec.write_value(next_block_start_address)


    def write_data_spec(
            self, spec, vertex, post_vertex_slice, subvertex, placement,
            partitioned_graph, graph, routing_info, graph_mapper, input_type):

        # Create an index of delay keys into this subvertex
        for subedge in partitioned_graph.incoming_subedges_from_subvertex(
                subvertex):
            edge = graph_mapper.get_partitionable_edge_from_partitioned_edge(
                subedge)
            if isinstance(edge.pre_vertex, DelayExtensionVertex):
                pre_vertex_slice = graph_mapper.get_subvertex_slice(
                    subedge.pre_subvertex)
                partition = partitioned_graph.get_partition_of_subedge(subedge)
                self._delay_key_index[
                    (edge.pre_vertex.source_vertex, pre_vertex_slice.lo_atom,
                     pre_vertex_slice.hi_atom)] = \
                    routing_info.get_keys_and_masks_from_partition(partition)

        post_slices = graph_mapper.get_subvertex_slices(vertex)
        post_slice_index = graph_mapper.get_subvertex_index(subvertex)

        # Reserve the memory
        subvert_in_edges = partitioned_graph.incoming_subedges_from_subvertex(
            subvertex)
        all_syn_block_sz = self._get_exact_synaptic_blocks_size(
            post_slices, post_slice_index, post_vertex_slice, graph_mapper,
            subvert_in_edges)
        self._reserve_memory_regions(
            spec, vertex, subvertex, post_vertex_slice, graph,
            partitioned_graph, all_syn_block_sz, graph_mapper)

        weight_scales = self._write_synapse_parameters(
            spec, subvertex, partitioned_graph, graph_mapper, post_slices,
            post_slice_index, post_vertex_slice, input_type)

        self._write_synaptic_matrix_and_master_population_table(
            spec, post_slices, post_slice_index, subvertex, post_vertex_slice,
            all_syn_block_sz, weight_scales,
            constants.POPULATION_BASED_REGIONS.POPULATION_TABLE.value,
            constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
            routing_info, graph_mapper, partitioned_graph)

        self._synapse_dynamics.write_parameters(
            spec, constants.POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value,
            self._machine_time_step, weight_scales)

        self._weight_scales[placement] = weight_scales

    def get_connections_from_machine(
            self, transceiver, placement, subedge, graph_mapper,
            routing_infos, synapse_info, partitioned_graph):

        edge = graph_mapper.get_partitionable_edge_from_partitioned_edge(
            subedge)
        if not isinstance(edge, ProjectionPartitionableEdge):
            return None

        # Get details for extraction
        pre_vertex_slice = graph_mapper.get_subvertex_slice(
            subedge.pre_subvertex)
        post_vertex_slice = graph_mapper.get_subvertex_slice(
            subedge.post_subvertex)
        n_synapse_types = self._synapse_type.get_n_synapse_types()

        # Get the key for the pre_subvertex
        partition = partitioned_graph.get_partition_of_subedge(subedge)
        key = routing_infos.get_keys_and_masks_from_partition(
            partition)[0].key

        # Get the key for the delayed pre_subvertex
        delayed_key = None
        if edge.delay_edge is not None:
            delayed_key = self._delay_key_index[
                (edge.pre_vertex, pre_vertex_slice.lo_atom,
                 pre_vertex_slice.hi_atom)][0].key

        # Get the block for the connections from the pre_subvertex
        master_pop_table_address = \
            helpful_functions.locate_memory_region_for_placement(
                placement,
                constants.POPULATION_BASED_REGIONS.POPULATION_TABLE.value,
                transceiver)
        synaptic_matrix_address = \
            helpful_functions.locate_memory_region_for_placement(
                placement,
                constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
                transceiver)
        direct_synapses_address = (
            self._get_static_synaptic_matrix_sdram_requirements() +
            synaptic_matrix_address + struct.unpack_from(
                "<I", transceiver.read_memory(
                    placement.x, placement.y, synaptic_matrix_address, 4))[0])
        indirect_synapses_address = synaptic_matrix_address + 4
        data, max_row_length = self._retrieve_synaptic_block(
            transceiver, placement, master_pop_table_address,
            indirect_synapses_address, direct_synapses_address,
            key, pre_vertex_slice.n_atoms, synapse_info.index)

        # Get the block for the connections from the delayed pre_subvertex
        delayed_data = None
        delayed_max_row_length = 0
        if delayed_key is not None:
            delayed_data, delayed_max_row_length = \
                self._retrieve_synaptic_block(
                    transceiver, placement, master_pop_table_address,
                    indirect_synapses_address, direct_synapses_address,
                    delayed_key,
                    pre_vertex_slice.n_atoms * edge.n_delay_stages,
                    synapse_info.index)

        # Convert the blocks into connections
        return self._synapse_io.read_synapses(
            synapse_info, pre_vertex_slice, post_vertex_slice,
            max_row_length, delayed_max_row_length, n_synapse_types,
            self._weight_scales[placement], data, delayed_data,
            edge.n_delay_stages)

    def _retrieve_synaptic_block(
            self, transceiver, placement, master_pop_table_address,
            indirect_synapses_address, direct_synapses_address,
            key, n_rows, index):
        """ Read in a synaptic block from a given processor and subvertex on\
            the machine
        """

        # See if we have already got this block
        if (placement, key, index) in self._retrieved_blocks:
            return self._retrieved_blocks[(placement, key, index)]

        items = \
            self._population_table_type.extract_synaptic_matrix_data_location(
                key, master_pop_table_address, transceiver,
                placement.x, placement.y)
        if index >= len(items):
            return None, None

        max_row_length, synaptic_block_offset, is_single = items[index]

        block = None
        if max_row_length > 0 and synaptic_block_offset is not None:

            if not is_single:

                # calculate the synaptic block size in bytes
                synaptic_block_size = self._synapse_io.get_block_n_bytes(
                    max_row_length, n_rows)

                # read in the synaptic block
                block = transceiver.read_memory(
                    placement.x, placement.y,
                    indirect_synapses_address + synaptic_block_offset,
                    synaptic_block_size)

            else:
                # The data is one per row
                synaptic_block_size = n_rows * 4

                # read in the synaptic row data
                single_block = numpy.asarray(transceiver.read_memory(
                    placement.x, placement.y,
                    direct_synapses_address + (synaptic_block_offset * 4),
                    synaptic_block_size), dtype="uint8").view("uint32")

                # Convert the block into a set of rows
                numpy_block = numpy.zeros((n_rows, 4), dtype="uint32")
                numpy_block[:, 3] = single_block
                numpy_block[:, 1] = 1
                block = bytearray(numpy_block.tobytes())
                max_row_length = 1

        self._retrieved_blocks[(placement, key, index)] = (
            block, max_row_length)
        return block, max_row_length

    # inherited from AbstractProvidesIncomingPartitionConstraints
    def get_incoming_partition_constraints(self):
        return self._population_table_type.get_edge_constraints()
