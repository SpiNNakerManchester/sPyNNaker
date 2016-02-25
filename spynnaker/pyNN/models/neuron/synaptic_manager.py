from scipy import special
import math
import sys
import numpy

from spynnaker.pyNN.utilities import constants, conf
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neural_properties import master_pop_table_generators
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_projections.projection_partitioned_edge \
    import ProjectionPartitionedEdge
from spynnaker.pyNN.models.neural_projections.projection_partitionable_edge \
    import ProjectionPartitionableEdge
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from spinn_front_end_common.utilities import helpful_functions
from data_specification.enums.data_type import DataType
import data_specification.utility_calls as dsg_utilities


# TODO: Make sure these values are correct (particularly CPU cycles)
_SYNAPSES_BASE_DTCM_USAGE_IN_BYTES = 28
_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES = 0
_SYNAPSES_BASE_N_CPU_CYCLES_PER_NEURON = 10
_SYNAPSES_BASE_N_CPU_CYCLES = 8


class SynapticManager(object):
    """ Deals with synapses
    """

    def __init__(self, synapse_type, machine_time_step, ring_buffer_sigma,
                 spikes_per_second, population_table_type=None):

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

        if self._ring_buffer_sigma is None:
            self._ring_buffer_sigma = conf.config.getfloat(
                "Simulation", "ring_buffer_sigma")

        if self._spikes_per_second is None:
            self._spikes_per_second = conf.config.getfloat(
                "Simulation", "spikes_per_second")

        # Prepare for dealing with STDP
        self._stdp_checked = False
        self._stdp_mechanism = None

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
    def vertex_executable_suffix(self):
        if self._stdp_mechanism is None:
            return ""
        return "_" + self._stdp_mechanism.get_vertex_executable_suffix()

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

    def _check_synapse_dynamics(self, in_edges):
        """ Checks the synapse dynamics for all edges is the same
        """
        if self._stdp_checked:
            return True
        self._stdp_checked = True
        for in_edge in in_edges:
            if (isinstance(in_edge, ProjectionPartitionableEdge) and
                    in_edge.synapse_dynamics is not None):
                if in_edge.synapse_dynamics.fast is not None:
                    raise exceptions.SynapticConfigurationException(
                        "Fast synapse dynamics are not supported")
                elif in_edge.synapse_dynamics.slow is not None:
                    if self._stdp_mechanism is None:
                        self._stdp_mechanism = in_edge.synapse_dynamics.slow
                    else:
                        if not (self._stdp_mechanism ==
                                in_edge.synapse_dynamics.slow):
                            raise exceptions.SynapticConfigurationException(
                                "Different STDP mechanisms on the same"
                                " vertex are not supported")

    def _get_synaptic_block_size(self, synaptic_sub_list, max_n_words):
        """ Get the size of a single block
        """
        # Gets smallest possible (i.e. supported by row length
        # Table structure) that can contain max_row_length
        row_length = self._population_table_type.get_allowed_row_length(
            max_n_words)
        num_rows = synaptic_sub_list.get_n_rows()
        syn_row_sz = 4 * (constants.SYNAPTIC_ROW_HEADER_WORDS + row_length)
        return syn_row_sz * num_rows

    def _get_exact_synaptic_blocks_size(
            self, graph_mapper, subvertex_in_edges):
        """ Get the exact size all of the synaptic blocks
        """
        memory_size = 0

        # Go through the subedges and add up the memory
        for subedge in subvertex_in_edges:

            # pad the memory size to meet 1 k offsets
            if (memory_size & 0x3FF) != 0:
                memory_size = (memory_size & 0xFFFFFC00) + 0x400

            sublist = subedge.get_synapse_sublist(graph_mapper)
            max_n_words = max([
                graph_mapper.get_partitionable_edge_from_partitioned_edge(
                    subedge).get_synapse_row_io().get_n_words(synapse_row)
                for synapse_row in sublist.get_rows()])

            all_syn_block_sz = self._get_synaptic_block_size(
                sublist, max_n_words)
            memory_size += all_syn_block_sz
        return memory_size

    def _get_estimate_synaptic_blocks_size(self, vertex_slice, in_edges):
        """ Get an estimate of the synaptic blocks memory size
        """
        self._check_synapse_dynamics(in_edges)
        memory_size = 0

        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionPartitionableEdge):

                # Get maximum row length in this edge
                max_n_words = in_edge.get_max_n_words(vertex_slice)
                all_syn_block_sz = self._get_synaptic_block_size(
                    in_edge, max_n_words)

                # TODO: Fix this to be more accurate!
                # May require modification to the master population table
                n_atoms = sys.maxint
                edge_pre_vertex = in_edge.pre_vertex
                if isinstance(edge_pre_vertex, AbstractPartitionableVertex):
                    n_atoms = in_edge.pre_vertex.get_max_atoms_per_core()
                if in_edge.pre_vertex.n_atoms < n_atoms:
                    n_atoms = in_edge.pre_vertex.n_atoms

                num_rows = in_edge.get_n_rows()
                extra_mem = math.ceil(float(num_rows) / float(n_atoms)) * 1024
                if extra_mem == 0:
                    extra_mem = 1024
                all_syn_block_sz += extra_mem
                memory_size += all_syn_block_sz

        return memory_size

    def _get_synapse_dynamics_parameter_size(self, in_edges):
        """ Get the size of the synapse dynamics region
        """
        self._check_synapse_dynamics(in_edges)
        if self._stdp_mechanism is not None:
            return self._stdp_mechanism.get_params_size(
                len(self._synapse_type.get_synapse_targets()))
        return 0

    def get_sdram_usage_in_bytes(self, vertex_slice, in_edges):
        return (
            self._get_synapse_params_size(vertex_slice) +
            self._get_synapse_dynamics_parameter_size(in_edges) +
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
            in_edges)
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

    def _get_ring_buffer_totals(self, subvertex, sub_graph, graph_mapper):
        in_sub_edges = sub_graph.incoming_subedges_from_subvertex(subvertex)
        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
        n_synapse_types = len(self._synapse_type.get_synapse_targets())
        absolute_max_weights = numpy.zeros(n_synapse_types)

        # If we have an STDP mechanism, get the maximum plastic weight
        stdp_max_weight = None
        if self._stdp_mechanism is not None:
            stdp_max_weight = self._stdp_mechanism.get_max_weight()
            absolute_max_weights.fill(stdp_max_weight)

        total_weights = numpy.zeros((n_synapse_types, vertex_slice.n_atoms))
        total_square_weights = numpy.zeros(
            (n_synapse_types, vertex_slice.n_atoms))
        total_items = numpy.zeros((n_synapse_types, vertex_slice.n_atoms))
        for subedge in in_sub_edges:
            sublist = subedge.get_synapse_sublist(graph_mapper)
            sublist.sum_n_connections(total_items)
            edge = graph_mapper.get_partitionable_edge_from_partitioned_edge(
                subedge)

            if edge.synapse_dynamics is None:

                # If there's no STDP maximum weight, sum the initial weights
                sublist.max_weights(absolute_max_weights)
                sublist.sum_weights(total_weights)
                sublist.sum_square_weights(total_square_weights)

            else:

                # Otherwise, sum the pathological case of all columns being
                # at stdp_max_weight
                sublist.sum_fixed_weight(total_weights, stdp_max_weight)
                sublist.sum_fixed_weight(total_square_weights,
                                         stdp_max_weight * stdp_max_weight)

        return (total_weights, total_square_weights, total_items,
                absolute_max_weights)

    def _get_ring_buffer_to_input_left_shifts(
            self, subvertex, sub_graph, graph_mapper, machine_timestep):
        """ Get the scaling of the ring buffer to provide as much accuracy as\
            possible without too much overflow
        """

        total_weights, total_square_weights, total_items, abs_max_weights =\
            self._get_ring_buffer_totals(subvertex, sub_graph, graph_mapper)

        # Get maximum weight that can go into each post-synaptic neuron per
        # synapse-type
        max_weights = [max(t) for t in total_weights]

        # Clip the total items to avoid problems finding the mean of nothing(!)
        total_items = numpy.clip(total_items, a_min=1,
                                 a_max=numpy.iinfo(int).max)
        weight_means = total_weights / total_items

        # Calculate the standard deviation, clipping to avoid numerical errors
        weight_std_devs = numpy.sqrt(
            numpy.clip(numpy.divide(
                total_square_weights -
                numpy.divide(numpy.power(total_weights, 2),
                             total_items),
                total_items), a_min=0.0, a_max=numpy.finfo(float).max))

        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
        n_synapse_types = len(self._synapse_type.get_synapse_targets())
        expected_weights = numpy.fromfunction(
            numpy.vectorize(
                lambda i, j: self._ring_buffer_expected_upper_bound(
                    weight_means[i][j], weight_std_devs[i][j],
                    self._spikes_per_second, machine_timestep,
                    total_items[i][j], self._ring_buffer_sigma)),
            (n_synapse_types, vertex_slice.n_atoms))
        expected_max_weights = [max(t) for t in expected_weights]
        max_weights = [min((w, e))
                       for w, e in zip(max_weights, expected_max_weights)]
        max_weights = [max((w, a))
                       for w, a in zip(max_weights, abs_max_weights)]

        # Convert these to powers
        max_weight_powers = [0 if w <= 0
                             else int(math.ceil(max(0, math.log(w, 2))))
                             for w in max_weights]

        # If 2^max_weight_power equals the max weight, we have to add another
        # power, as range is 0 - (just under 2^max_weight_power)!
        max_weight_powers = [w + 1 if (2 ** w) >= a else w
                             for w, a in zip(max_weight_powers, max_weights)]

        # If we have an STDP mechanism that uses signed weights,
        # Add another bit of shift to prevent overflows
        if self._stdp_mechanism is not None\
                and self._stdp_mechanism.are_weights_signed():
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
            subvertex, subgraph, graph_mapper, self._machine_time_step)
        weight_scales = [self._get_weight_scale(r) for r in ring_buffer_shifts]

        # update projections for future use
        in_partitioned_edges = subgraph.incoming_subedges_from_subvertex(
            subvertex)
        for partitioned_edge in in_partitioned_edges:
            partitioned_edge.weight_scales_setter(weight_scales)

        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value)
        utility_calls.write_parameters_per_neuron(
            spec, vertex_slice,
            self._synapse_type.get_synapse_type_parameters())

        spec.write_array(ring_buffer_shifts)

        return weight_scales

    @staticmethod
    def _write_synapse_row_info(
            sublist, row_io, spec, current_write_ptr, fixed_row_length, region,
            weight_scales, n_synapse_type_bits):
        """ Write this synaptic block to the designated synaptic matrix region\
            at its current write pointer.
        """

        # Switch focus to the synaptic matrix memory region:
        spec.switch_write_focus(region)

        # Align the write pointer to the next 1Kbyte boundary using padding:
        write_ptr = current_write_ptr

        # Remember this aligned address, it's where this block will start:
        block_start_addr = write_ptr

        # Write the synaptic block, tracking the word count:
        synaptic_rows = sublist.get_rows()
        data = numpy.zeros(
            (fixed_row_length +
             constants.SYNAPTIC_ROW_HEADER_WORDS) *
            sublist.get_n_rows(), dtype="uint32")
        data.fill(0xBBCCDDEE)

        for row_no, row in enumerate(synaptic_rows):
            data_pos = ((fixed_row_length +
                         constants.SYNAPTIC_ROW_HEADER_WORDS) *
                        row_no)

            plastic_region = row_io.get_packed_plastic_region(
                row, weight_scales, n_synapse_type_bits)

            # Write the size of the plastic region
            data[data_pos] = plastic_region.size
            data_pos += 1

            # Write the plastic region
            data[data_pos:(data_pos + plastic_region.size)] = plastic_region
            data_pos += plastic_region.size

            fixed_fixed_region = row_io.get_packed_fixed_fixed_region(
                row, weight_scales, n_synapse_type_bits)
            fixed_plastic_region = row_io.get_packed_fixed_plastic_region(
                row, weight_scales, n_synapse_type_bits)

            # Write the size of the fixed parts
            data[data_pos] = fixed_fixed_region.size
            data[data_pos + 1] = fixed_plastic_region.size
            data_pos += 2

            # Write the fixed fixed region
            data[data_pos:(data_pos + fixed_fixed_region.size)] = \
                fixed_fixed_region
            data_pos += fixed_fixed_region.size

            # As everything needs to be word aligned, add extra zero to
            # fixed_plastic Region if it has an odd number of entries and build
            # uint32 view of it
            if (fixed_plastic_region.size % 2) != 0:
                fixed_plastic_region = numpy.asarray(numpy.append(
                    fixed_plastic_region, 0), dtype='uint16')
            # does indeed return something (due to c fancy stuff in numpy) ABS

            # noinspection PyNoneFunctionAssignment
            fixed_plastic_region_words = fixed_plastic_region.view(
                dtype="uint32")
            data[data_pos:(data_pos + fixed_plastic_region_words.size)] = \
                fixed_plastic_region_words

        spec.write_array(data)
        write_ptr += data.size * 4

        # The current write pointer is where the next block could start:
        next_block_start_addr = write_ptr
        return block_start_addr, next_block_start_addr

    def _write_synaptic_matrix_and_master_population_table(
            self, spec, subvertex, all_syn_block_sz, weight_scales,
            master_pop_table_region, synaptic_matrix_region, routing_info,
            graph_mapper, partitioned_graph):
        """ Simultaneously generates both the master population table and
            the synaptic matrix.
        """
        spec.comment(
            "\nWriting Synaptic Matrix and Master Population Table:\n")

        # Track writes inside the synaptic matrix region:
        next_block_start_addr = 0
        n_synapse_type_bits = self._synapse_type.get_n_synapse_type_bits()

        # Filtering incoming subedges
        in_subedges = \
            partitioned_graph.incoming_subedges_from_subvertex(subvertex)
        in_proj_subedges = [e for e in in_subedges
                            if isinstance(e, ProjectionPartitionedEdge)]

        # Set up the master population table
        self._population_table_type.initialise_table(
            spec, master_pop_table_region)

        # For each entry in subedge into the subvertex, create a
        # sub-synaptic list
        for subedge in in_proj_subedges:
            partition = partitioned_graph.get_partition_of_subedge(subedge)
            keys_and_masks = routing_info.get_keys_and_masks_from_partition(
                partition)
            spec.comment(
                "\nWriting matrix for subedge:{}\n".format(subedge.label))
            sublist = subedge.get_synapse_sublist(graph_mapper)
            associated_edge = \
                graph_mapper.get_partitionable_edge_from_partitioned_edge(
                    subedge)
            row_io = associated_edge.get_synapse_row_io()

            # Get the maximum row length in words, excluding headers
            max_row_length = max([row_io.get_n_words(row)
                                 for row in sublist.get_rows()])

            # Get an entry in the row length table for this length
            row_length = self._population_table_type.get_allowed_row_length(
                max_row_length)
            block_start_addr = 0
            if max_row_length > 0:

                # Determine where the next block will actually start
                # and generate any required padding
                next_block_allowed_addr = \
                    self._population_table_type.get_next_allowed_address(
                        next_block_start_addr)
                if next_block_allowed_addr != next_block_start_addr:

                    # Pad out data file with the added alignment bytes:
                    spec.switch_write_focus(synaptic_matrix_region)
                    spec.set_register_value(
                        register_id=15,
                        data=next_block_allowed_addr - next_block_start_addr)
                    spec.write_value(data=0xDD, repeats_register=15,
                                     data_type=DataType.UINT8)

                # Write the synaptic block for the sublist
                (block_start_addr, next_block_start_addr) = \
                    self._write_synapse_row_info(
                        sublist, row_io, spec, next_block_allowed_addr,
                        row_length, synaptic_matrix_region, weight_scales,
                        n_synapse_type_bits)

            self._population_table_type.update_master_population_table(
                spec, block_start_addr, row_length, keys_and_masks,
                master_pop_table_region)

        self._population_table_type.finish_master_pop_table(
            spec, master_pop_table_region)

    def write_data_spec(
            self, spec, vertex, vertex_slice, subvertex, placement, subgraph,
            graph, routing_info, hostname, graph_mapper):

        # Reserve the memory
        subvert_in_edges = subgraph.incoming_subedges_from_subvertex(subvertex)
        all_syn_block_sz = self._get_exact_synaptic_blocks_size(
            graph_mapper, subvert_in_edges)
        self._reserve_memory_regions(
            spec, vertex, vertex_slice, graph, all_syn_block_sz)

        weight_scales = self._write_synapse_parameters(
            spec, subvertex, subgraph, graph_mapper, vertex_slice)

        self._write_synaptic_matrix_and_master_population_table(
            spec, subvertex, all_syn_block_sz, weight_scales,
            constants.POPULATION_BASED_REGIONS.POPULATION_TABLE.value,
            constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
            routing_info, graph_mapper, subgraph)

        if self._stdp_mechanism is not None:
            self._stdp_mechanism.write_plastic_params(
                spec,
                constants.POPULATION_BASED_REGIONS.SYNAPSE_DYNAMICS.value,
                self._machine_time_step, weight_scales)

        # Free any additional memory
        for subedge in subvert_in_edges:
            subedge.free_sublist()

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
        """ Translates a collection of memory into synaptic rows
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

            # new position in synaptic block
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

        """ extracts the 6 elements from a data block which is ordered\
            no PP, PP, No FF, NO FP, FF, FP
        """

        # read in number of plastic plastic entries
        no_plastic_plastic_entries = synaptic_block[position_in_block]
        position_in_block += 1

        # read in all the plastic entries
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
        master_pop_base_mem_address = \
            self._population_table_type.locate_master_pop_table_base_address(
                post_placement, transceiver,
                constants.POPULATION_BASED_REGIONS.POPULATION_TABLE.value)

        incoming_edges = subgraph.incoming_subedges_from_subvertex(
            post_subvertex)
        incoming_key_combo = None
        for subedge in incoming_edges:
            if subedge.pre_subvertex == pre_subvertex:
                partition = subgraph.get_partition_of_subedge(subedge)
                keys_and_masks = \
                    routing_infos.get_keys_and_masks_from_partition(partition)
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

            # read in the memory address of the synaptic_region base address
            synapse_region_base_address = helpful_functions.\
                locate_memory_region_for_placement(
                    post_placement,
                    constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
                    transceiver)

            # the base address of the synaptic block in absolute terms is the
            # app base, plus the synaptic matrix base plus the offset
            synaptic_block_base_address = (synapse_region_base_address +
                                           synaptic_block_base_address_offset)

            # read in and return the synaptic block
            block = transceiver.read_memory(
                post_x, post_y, synaptic_block_base_address,
                synaptic_block_size)

            if len(block) != synaptic_block_size:
                raise exceptions.SynapticBlockReadException(
                    "Not enough data has been read")
        return block, maxed_row_length

    # inherited from AbstractProvidesIncomingPartitionConstraints
    def get_incoming_edge_constraints(self):
        """
        :return:
        """
        return self._population_table_type.get_edge_constraints()
