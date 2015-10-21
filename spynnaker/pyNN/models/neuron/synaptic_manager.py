from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neuron import master_pop_table_generators
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.utilities.running_stats import RunningStats
from pacman.model.graph_mapper.slice import Slice
from data_specification.enums.data_type import DataType
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

from spinn_front_end_common.utilities import helpful_functions

import data_specification.utility_calls as dsg_utilities

from scipy import special
import math
import sys
import numpy

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

        # Prepare for dealing with STDP - there can only be one (non-static)
        # synapse dynamics per vertex at present
        self._synapse_dynamics = None

    @property
    def synapse_dynamics(self):
        return self._synapse_dynamics

    @synapse_dynamics.setter
    def synapse_dynamics(self, synapse_dynamics):

        # We can always override static dynamics or None
        if self._synapse_dynamics is None or isinstance(
                synapse_dynamics, SynapseDynamicsStatic):
            self._synapse_dynamics = synapse_dynamics

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

    def _get_exact_synaptic_blocks_size(
            self, n_post_slices, post_slice_index, post_vertex_slice,
            graph_mapper, subvertex, subvertex_in_edges):
        """ Get the exact size all of the synaptic blocks
        """
        memory_size = 0

        # Go through the subedges and add up the memory
        for subedge in subvertex_in_edges:

            edge = graph_mapper.get_partitionable_edge_from_partitioned_edge(
                subedge)
            if isinstance(edge, ProjectionPartitionableEdge):

                # Add on the size of the tables to be generated
                pre_vertex_slice = graph_mapper.get_subvertex_slice(
                    subedge.pre_subvertex)
                pre_slices = list(graph_mapper.get_subvertices_from_vertex(
                    edge.pre_vertex))
                n_pre_slices = len(pre_slices)
                pre_slice_index = pre_slices.index(subedge.pre_subvertex)

                undelayed_size, delayed_size = \
                    self._synapse_io.get_sdram_usage_in_bytes(
                        edge.synapse_information, n_pre_slices,
                        pre_slice_index, n_post_slices, post_slice_index,
                        pre_vertex_slice, post_vertex_slice,
                        edge.n_delay_stages)

                # Add population table required padding between blocks and
                # add the block sizes
                memory_size = self._population_table_type\
                    .get_next_allowed_address(memory_size)
                memory_size += undelayed_size
                memory_size = self._population_table_type\
                    .get_next_allowed_address(memory_size)
                memory_size += delayed_size

        return memory_size

    def _get_estimate_synaptic_blocks_size(self, post_vertex_slice, in_edges):
        """ Get an estimate of the synaptic blocks memory size
        """
        memory_size = 0

        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionPartitionableEdge):

                # Get an estimate of the number of post sub-vertices by
                # assuming that all of them are the same size as this one
                n_post_slices = int(math.ceil(
                    float(in_edge.pre_vertex.n_atoms) /
                    float(post_vertex_slice.n_atoms)))
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
                n_pre_slices = int(math.ceil(
                    float(in_edge.pre_vertex.n_atoms) / n_atoms_per_subvertex))

                pre_slice_index = 0
                for lo_atom in range(
                        0, in_edge.pre_vertex.n_atoms, n_atoms_per_subvertex):
                    pre_vertex_slice = Slice(
                        lo_atom, lo_atom + n_atoms_per_subvertex - 1)
                    undelayed_size, delayed_size = \
                        self._synapse_io.get_sdram_usage_in_bytes(
                            in_edge.synapse_information, n_pre_slices,
                            pre_slice_index, n_post_slices, post_slice_index,
                            pre_vertex_slice, post_vertex_slice,
                            in_edge.n_delay_stages)

                    memory_size = self._population_table_type\
                        .get_next_allowed_address(memory_size)
                    memory_size += undelayed_size
                    memory_size = self._population_table_type\
                        .get_next_allowed_address(memory_size)
                    memory_size += delayed_size
                    pre_slice_index += 1

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
            self, spec, vertex, vertex_slice, graph, all_syn_block_sz):

        spec.reserve_memory_region(
            region=constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value,
            size=self._get_synapse_params_size(vertex_slice),
            label='SynapseParams')

        in_edges = graph.incoming_edges_to_vertex(vertex)
        master_pop_table_sz = \
            self._population_table_type.get_master_population_table_size(
                vertex_slice, in_edges)
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
            self, subvertex, sub_graph, graph_mapper, post_vertex_slice,
            machine_timestep):
        """ Get the scaling of the ring buffer to provide as much accuracy as\
            possible without too much overflow
        """
        n_synapse_types = self._synapse_type.get_n_synapse_types()
        running_totals = [RunningStats()] * n_synapse_types
        total_weights = numpy.zeros(n_synapse_types)
        biggest_weight = numpy.zeros(n_synapse_types)
        weights_signed = False

        for subedge in sub_graph.incoming_subedges_from_subvertex(subvertex):
            pre_vertex_slice = graph_mapper.get_subvertex_slice(
                subedge.pre_subvertex)
            edge = graph_mapper.get_partitionable_edge_from_partitioned_edge(
                subedge)
            for synapse_info in edge.synapse_information:
                synapse_type = synapse_info.synapse_type
                synapse_dynamics = synapse_info.synapse_dynamics
                connector = synapse_info.connector
                weight_mean = synapse_dynamics.get_weight_mean(
                    connector, pre_vertex_slice, post_vertex_slice)
                n_connections = \
                    connector.get_n_connections_to_post_vertex_maximum(
                        pre_vertex_slice, post_vertex_slice)
                weight_variance = synapse_dynamics.get_weight_variance(
                    connector, pre_vertex_slice, post_vertex_slice)
                running_totals[synapse_type].add_items(
                    weight_mean, weight_variance, n_connections)

                weight_max = synapse_dynamics.get_weight_maximum(
                    connector, pre_vertex_slice, post_vertex_slice)
                biggest_weight[synapse_type] = max(
                    biggest_weight[synapse_type], weight_max)
                total_weights[synapse_type] += (
                    weight_max * n_connections)

                if synapse_dynamics.are_weights_signed():
                    weights_signed = True

        max_weights = numpy.zeros(n_synapse_types)
        for synapse_type in range(n_synapse_types):
            stats = running_totals[synapse_type]
            max_weights[synapse_type] = min(
                self._ring_buffer_expected_upper_bound(
                    stats.mean, stats.standard_deviation,
                    self._spikes_per_second, machine_timestep, stats.n_items,
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
        max_weight_powers = [w + 1 if (2 ** w) >= a else w
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
            self, spec, subvertex, subgraph, graph_mapper, vertex_slice):

        # Get the ring buffer shifts and scaling factors
        ring_buffer_shifts = self._get_ring_buffer_to_input_left_shifts(
            subvertex, subgraph, graph_mapper, vertex_slice,
            self._machine_time_step)

        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value)
        utility_calls.write_parameters_per_neuron(
            spec, vertex_slice,
            self._synapse_type.get_synapse_type_parameters())

        spec.write_array(ring_buffer_shifts)

        return ring_buffer_shifts

    def _write_padding(
            self, spec, synaptic_matrix_region, next_block_start_addr):
        next_block_allowed_addr = self._population_table_type\
            .get_next_allowed_address(next_block_start_addr)
        if next_block_allowed_addr != next_block_start_addr:

            # Pad out data file with the added alignment bytes:
            spec.comment("\nWriting population table required"
                         " padding\n")
            spec.switch_write_focus(synaptic_matrix_region)
            spec.set_register_value(
                register_id=15,
                data=next_block_allowed_addr - next_block_start_addr)
            spec.write_value(
                data=0xDD, repeats_register=15, data_type=DataType.UINT8)
            return next_block_allowed_addr
        return next_block_start_addr

    def _write_synaptic_matrix_and_master_population_table(
            self, spec, n_post_slices, post_slice_index, subvertex,
            post_vertex_slice, all_syn_block_sz, weight_scales,
            master_pop_table_region, synaptic_matrix_region, routing_info,
            graph_mapper, subgraph, delay_key_index):
        """ Simultaneously generates both the master population table and
            the synatic matrix.
        """
        spec.comment(
            "\nWriting Synaptic Matrix and Master Population Table:\n")

        # Track writes inside the synaptic matrix region:
        next_block_start_addr = 0
        n_synapse_types = self._synapse_type.get_n_synapse_types()

        # Get the edges
        in_subedges = subgraph.incoming_subedges_from_subvertex(subvertex)

        # Set up the master population table
        self._population_table_type.initialise_table(
            spec, master_pop_table_region)

        # For each subedge into the subvertex, create a synaptic list
        for subedge in in_subedges:

            edge = graph_mapper.get_partitionable_edge_from_partitioned_edge(
                subedge)
            if isinstance(edge, ProjectionPartitionableEdge):

                spec.comment("\nWriting matrix for subedge:{}\n".format(
                    subedge.label))

                pre_vertex_slice = graph_mapper.get_subvertex_slice(
                    subedge.pre_subvertex)
                pre_vertex_slices = list(
                    graph_mapper.get_subvertices_from_vertex(edge.pre_vertex))
                n_pre_slices = len(pre_vertex_slices)
                pre_slice_index = pre_vertex_slices.index(
                    subedge.pre_subvertex)

                row_data, row_length, delayed_row_data, delayed_row_length =\
                    self._synapse_io.get_synapses(
                        edge.synapse_information, n_pre_slices,
                        pre_slice_index, n_post_slices, post_slice_index,
                        pre_vertex_slice, post_vertex_slice,
                        edge.n_delay_stages, self._population_table_type,
                        n_synapse_types, weight_scales)

                if len(row_data) > 0:
                    next_block_start_addr = self._write_padding(
                        spec, synaptic_matrix_region, next_block_start_addr)
                    spec.switch_write_focus(synaptic_matrix_region)
                    self.spec.write_array(row_data)
                    keys_and_masks = \
                        routing_info.get_keys_and_masks_from_subedge(subedge)
                    self._population_table_type.update_master_population_table(
                        spec, next_block_start_addr, row_length,
                        keys_and_masks, master_pop_table_region)
                    next_block_start_addr += len(row_data)
                del row_data

                if len(delayed_row_data) > 0:
                    next_block_start_addr = self._write_padding(
                        spec, synaptic_matrix_region, next_block_start_addr)
                    spec.switch_write_focus(synaptic_matrix_region)
                    self.spec.write_array(delayed_row_data)
                    keys_and_masks = delay_key_index[
                        (subedge.pre_subvertex, pre_vertex_slice)]
                    self._population_table_type.update_master_population_table(
                        spec, next_block_start_addr, delayed_row_length,
                        keys_and_masks, master_pop_table_region)
                    next_block_start_addr += len(delayed_row_data)
                del delayed_row_data

        self._population_table_type.finish_master_pop_table(
            spec, master_pop_table_region)

    def write_data_spec(
            self, spec, vertex, vertex_slice, subvertex, placement, subgraph,
            graph, routing_info, hostname, graph_mapper):

        # Create an index of delay keys into this subvertex
        delay_key_index = dict()
        for subedge in subgraph.incoming_subedges_from_subvertex(subvertex):
            edge = graph_mapper.get_partitionable_edge_from_partitioned_edge(
                subedge)
            if isinstance(edge.pre_vertex, DelayExtensionVertex):
                pre_slice = graph_mapper.get_subvertex_slice(
                    subedge.pre_subvertex)
                delay_key_index[(subedge.pre_subvertex, pre_slice)] =\
                    routing_info.get_keys_and_masks_from_subedge(subedge)

        subvertices = list(graph_mapper.get_subvertices_from_vertex(vertex))
        n_slices = len(subvertices)
        slice_index = subvertices.index(subvertex)

        # Reserve the memory
        subvert_in_edges = subgraph.incoming_subedges_from_subvertex(subvertex)
        all_syn_block_sz = self._get_exact_synaptic_blocks_size(
            n_slices, slice_index, vertex_slice, graph_mapper, subvertex,
            subvert_in_edges)
        self._reserve_memory_regions(
            spec, vertex, vertex_slice, graph, all_syn_block_sz)

        ring_buffer_shifts = self._write_synapse_parameters(
            spec, subvertex, subgraph, graph_mapper, vertex_slice)
        weight_scales = [self._get_weight_scale(r) for r in ring_buffer_shifts]

        self._write_synaptic_matrix_and_master_population_table(
            spec, n_slices, slice_index, subvertex, vertex_slice,
            all_syn_block_sz, weight_scales,
            constants.POPULATION_BASED_REGIONS.POPULATION_TABLE.value,
            constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
            routing_info, graph_mapper, subgraph, delay_key_index)

        self._synapse_dynamics.write_parameters(
            spec, constants.POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value,
            self._machine_time_step, weight_scales)

    def get_synaptic_list_from_machine(
            self, placements, transceiver, pre_subvertex, pre_n_atoms,
            post_subvertex, synapse_io, subgraph, routing_infos,
            weight_scales):
        """

        :param placements:
        :param transceiver:
        :param pre_subvertex:
        :param pre_n_atoms:
        :param post_subvertex:
        :param synapse_io:
        :param subgraph:
        :param routing_infos:
        :param weight_scales:
        :return:
        """

        synaptic_block, max_row_length = self._retrieve_synaptic_block(
            placements, transceiver, pre_subvertex, pre_n_atoms,
            post_subvertex, routing_infos, subgraph)

        # translate the synaptic block into a sublist of synapse_row_infos
        synapse_list = None
        if max_row_length > 0:
            synapse_list = self._translate_synaptic_block_from_memory(
                synaptic_block, pre_n_atoms, max_row_length, synapse_io,
                weight_scales)
        else:
            synapse_list = SynapticList([])
        return synapse_list

    def _translate_synaptic_block_from_memory(
            self, synaptic_block, n_atoms, max_row_length, synapse_io,
            weight_scales):
        """
        translates a collection of memory into synaptic rows
        """
        synaptic_list = list()
        numpy_block = numpy.frombuffer(dtype='uint8',
                                       buffer=synaptic_block).view(dtype='<u4')
        position_in_block = 0
        for atom in range(n_atoms):

            # extract the 3 elements of a row (PP, FF, FP)
            p_p_entries, f_f_entries, f_p_entries = \
                self._extract_row_data_from_memory_block(numpy_block,
                                                         position_in_block)

            # new position in synpaptic block
            position_in_block = ((atom + 1) *
                                 (max_row_length +
                                  constants.SYNAPTIC_ROW_HEADER_WORDS))

            bits_reserved_for_type = \
                self._synapse_type.get_n_synapse_type_bits()
            synaptic_row = synapse_io.create_row_info_from_elements(
                p_p_entries, f_f_entries, f_p_entries, bits_reserved_for_type,
                weight_scales)

            synaptic_list.append(synaptic_row)
        return SynapticList(synaptic_list)

    @staticmethod
    def _extract_row_data_from_memory_block(synaptic_block, position_in_block):

        """
        extracts the 6 elements from a data block which is ordered
        no PP, pp, No ff, NO fp, FF fp
        """

        # read in number of plastic plastic entries
        no_plastic_plastic_entries = synaptic_block[position_in_block]
        position_in_block += 1

        # read inall the plastic entries
        end_point = position_in_block + no_plastic_plastic_entries
        plastic_plastic_entries = synaptic_block[position_in_block:end_point]

        # update position in block
        position_in_block = end_point

        # read in number of both fixed fixed and fixed plastic
        no_fixed_fixed = synaptic_block[position_in_block]
        position_in_block += 1
        no_fixed_plastic = synaptic_block[position_in_block]
        position_in_block += 1

        # read in fixed fixed
        end_point = position_in_block + no_fixed_fixed
        fixed_fixed_entries = synaptic_block[position_in_block:end_point]
        position_in_block = end_point

        # read in fixed plastic (fixed plastic are in 16 bits, so each int is
        # 2 entries)
        end_point = position_in_block + math.ceil(no_fixed_plastic / 2.0)
        fixed_plastic_entries = \
            synaptic_block[position_in_block:end_point].view(dtype='<u2')
        if no_fixed_plastic % 2.0 == 1:  # remove last entry if required
            fixed_plastic_entries = \
                fixed_plastic_entries[0:len(fixed_plastic_entries) - 1]

        # return the different entries
        return plastic_plastic_entries, fixed_fixed_entries, \
            fixed_plastic_entries

    def _retrieve_synaptic_block(
            self, placements, transceiver, pre_subvertex, pre_n_atoms,
            post_subvertex, routing_infos, subgraph):
        """
        reads in a synaptic block from a given processor and subvertex on the
        machine.
        """
        post_placement = placements.get_placement_of_subvertex(post_subvertex)
        post_x, post_y, post_p = \
            post_placement.x, post_placement.y, post_placement.p

        # either read in the master pop table or retrieve it from storage
        master_pop_base_mem_address, app_data_base_address = \
            self._population_table_type.locate_master_pop_table_base_address(
                post_x, post_y, post_p, transceiver,
                constants.POPULATION_BASED_REGIONS.POPULATION_TABLE.value)

        incoming_edges = subgraph.incoming_subedges_from_subvertex(
            post_subvertex)
        incoming_key_combo = None
        for subedge in incoming_edges:
            if subedge.pre_subvertex == pre_subvertex:
                routing_info = \
                    routing_infos.get_subedge_information_from_subedge(subedge)
                keys_and_masks = routing_info.keys_and_masks
                incoming_key_combo = keys_and_masks[0].key
                break

        maxed_row_length, synaptic_block_base_address_offset = \
            self._population_table_type.extract_synaptic_matrix_data_location(
                incoming_key_combo, master_pop_base_mem_address,
                transceiver, post_x, post_y)

        block = None
        if maxed_row_length > 0:

            # calculate the synaptic block size in words
            synaptic_block_size = (pre_n_atoms * 4 *
                                   (constants.SYNAPTIC_ROW_HEADER_WORDS +
                                    maxed_row_length))

            # read in the base address of the synaptic matrix in the app region
            # table
            synapse_region_base_address_location = \
                dsg_utilities.get_region_base_address_offset(
                    app_data_base_address,
                    constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value)

            # read in the memory address of the synaptic_region base address
            synapse_region_base_address = helpful_functions.read_data(
                post_x, post_y, synapse_region_base_address_location, 4,
                "<I", transceiver)

            # the base address of the synaptic block in absolute terms is the
            # app base, plus the synaptic matrix base plus the offset
            synaptic_block_base_address = (app_data_base_address +
                                           synapse_region_base_address +
                                           synaptic_block_base_address_offset)

            # read in and return the synaptic block
            block = transceiver.read_memory(
                post_x, post_y, synaptic_block_base_address,
                synaptic_block_size)

            if len(block) != synaptic_block_size:
                raise exceptions.SynapticBlockReadException(
                    "Not enough data has been read"
                    " (aka, something funkky happened)")
        return block, maxed_row_length

    # inhirrted from AbstractProvidesIncomingEdgeConstraints
    def get_incoming_edge_constraints(self):
        """

        :param partitioned_edge:
        :param graph_mapper:
        :return:
        """
        return self._population_table_type.get_edge_constraints()
