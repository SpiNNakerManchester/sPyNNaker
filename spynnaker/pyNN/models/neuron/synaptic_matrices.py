# Copyright (c) 2017-2020 The University of Manchester
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

import numpy
from collections import namedtuple

from pacman.model.routing_info import BaseKeyAndMask
from data_specification.enums.data_type import DataType

from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron.master_pop_table import (
    MasterPopTableAsBinarySearch)
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from .synaptic_matrix_app import SynapticMatrixApp
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.utilities.bit_field_utilities import (
    get_sdram_for_bit_field_region, get_bitfield_key_map_data,
    write_bitfield_init_data)

# 1 for synaptic matrix region
# 1 for master pop region
# 1 for bitfield filter region
# 1 for structural region
# 1 for n_edges
# 1 for post_vertex_slice.lo_atom
# 1 for post_vertex_slice.n_atoms
# 1 for post index
# 1 for n_synapse_types
# 1 for timestep per delay
# 1 for padding
# 4 for Population RNG seed
# 4 for core RNG seed
SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES = (
    1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 4 + 4) * BYTES_PER_WORD

DIRECT_MATRIX_HEADER_COST_BYTES = 1 * BYTES_PER_WORD

# Value to use when there is no region
INVALID_REGION_ID = 0xFFFFFFFF

# Identifiers for synapse regions
SYNAPSE_FIELDS = [
    "synapse_params", "pop_table", "synaptic_matrix", "synapse_dynamics",
    "structural_dynamics", "bitfield_filter", "connection_builder"]
SynapseRegions = namedtuple(
    "SynapseRegions", SYNAPSE_FIELDS)


class SynapticMatrices(object):
    """ Handler of synaptic matrices for a core of a population vertex
    """

    __slots__ = [
        # The number of synapse types received
        "__n_synapse_types",
        # The region identifiers
        "__regions",
        # The sub-matrices for each incoming edge
        "__matrices",
        # The address within the synaptic matrix region after the last matrix
        # was written
        "__host_generated_block_addr",
        # The address within the synaptic matrix region after the last
        # generated matrix will be written
        "__on_chip_generated_block_addr",
        # Determine if any of the matrices can be generated on the machine
        "__gen_on_machine",
        # Number of bits to use for neuron IDs
        "__max_atoms_per_core",
        # The stored master population table data
        "__master_pop_data",
        # The stored generated data
        "__generated_data",
        # The size needed for generated data
        "__generated_data_size",
        # The number of generated matrices
        "__n_generated_matrices",
        # The matrices that need to be generated on host
        "__on_host_matrices",
        # The application vertex
        "__app_vertex",
        # The weight scales
        "__weight_scales",
        # The size of all synaptic blocks added together
        "__all_syn_block_sz",
        # Whether data generation has already happened
        "__data_generated",
        # The size of the bit field data to be allocated
        "__bit_field_size",
        # The bit field key map generated
        "__bit_field_key_map",
        # The maximum generated data, for calculating timeouts
        "__max_gen_data"
    ]

    def __init__(
            self, app_vertex, regions, max_atoms_per_core, weight_scales,
            all_syn_block_sz):
        """
        :param SynapseRegions regions: The synapse regions to use
        """
        self.__app_vertex = app_vertex
        self.__regions = regions
        self.__n_synapse_types = app_vertex.neuron_impl.get_n_synapse_types()
        self.__max_atoms_per_core = max_atoms_per_core
        self.__weight_scales = weight_scales
        self.__all_syn_block_sz = all_syn_block_sz

        # Map of (app_edge, synapse_info) to SynapticMatrixApp
        self.__matrices = dict()

        # Store locations of synaptic data and generated data
        self.__host_generated_block_addr = 0
        self.__on_chip_generated_block_addr = 0

        # Determine whether to generate on machine
        self.__gen_on_machine = False
        self.__data_generated = False
        self.__max_gen_data = 0
        self.__on_host_matrices = None
        self.__generated_data = None
        self.__generated_data_size = 0
        self.__n_generated_matrices = 0
        self.__master_pop_data = None
        self.__bit_field_size = 0
        self.__bit_field_key_map = None

    @property
    def max_gen_data(self):
        """  The maximum amount of data to be generated for the synapses.

        :rtype: int
        """
        return self.__max_gen_data

    @property
    def bit_field_size(self):
        """ The size of the bit field data

        :rtype: int
        """
        return self.__bit_field_size

    @property
    def host_generated_block_addr(self):
        """ The address within the synaptic region after the last block
            written by the on-host synaptic generation i.e. the start of
            the space that can be overwritten provided the synapse expander
            is run again

        :rtype: int
        """
        return self.__host_generated_block_addr

    @property
    def on_chip_generated_matrix_size(self):
        """ The size of the space used by the generated matrix i.e. the
            space that can be overwritten provided the synapse expander
            is run again

        :rtype: int
        """
        return (self.__on_chip_generated_block_addr -
                self.__host_generated_block_addr)

    def generate_data(self):
        # If the data has already been generated, stop
        if self.__data_generated:
            return
        self.__data_generated = True

        # If there are no synapses, there is nothing to do!
        if self.__all_syn_block_sz == 0:
            return

        # Track writes inside the synaptic matrix region:
        block_addr = 0

        # Set up the master population table
        poptable = MasterPopTableAsBinarySearch()
        poptable.initialise_table()

        # Set up other lists
        self.__on_host_matrices = list()
        generated_data = list()

        # Keep on-machine generated blocks together at the end
        generate_on_machine = list()
        self.__generated_data_size = (
            SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES +
            (self.__n_synapse_types * DataType.U3232.size))

        # For each incoming machine vertex, reserve pop table space
        for proj in self.__app_vertex.incoming_projections:
            # pylint: disable=protected-access
            app_edge = proj._projection_edge
            synapse_info = proj._synapse_information
            app_key_info = self.__app_key_and_mask(app_edge)
            if app_key_info is None:
                continue
            d_app_key_info = self.__delay_app_key_and_mask(app_edge)
            app_matrix = SynapticMatrixApp(
                synapse_info, app_edge, self.__n_synapse_types,
                self.__regions.synaptic_matrix, self.__max_atoms_per_core,
                self.__all_syn_block_sz, app_key_info, d_app_key_info,
                self.__weight_scales)
            self.__matrices[app_edge, synapse_info] = app_matrix

            # If we can generate on machine, store until end
            if synapse_info.may_generate_on_machine():
                generate_on_machine.append(app_matrix)
            else:
                block_addr = app_matrix.reserve_matrices(block_addr, poptable)
                self.__on_host_matrices.append(app_matrix)

        self.__host_generated_block_addr = block_addr

        # Now add the blocks on machine to keep these all together
        self.__max_gen_data = 0
        for app_matrix in generate_on_machine:
            block_addr = app_matrix.reserve_matrices(block_addr, poptable)
            gen_data = app_matrix.get_generator_data()
            self.__generated_data_size += gen_data.size
            generated_data.extend(gen_data.gen_data)
            self.__max_gen_data += app_matrix.gen_size
        if generated_data:
            self.__gen_on_machine = True
            self.__n_generated_matrices = len(generate_on_machine)
            self.__generated_data = numpy.concatenate(generated_data)
        else:
            self.__gen_on_machine = True
            self.__n_generated_matrices = 0
            self.__generated_data = numpy.zeros(0, dtype="uint32")

        self.__on_chip_generated_block_addr = block_addr

        # Store the master pop table
        self.__master_pop_data = poptable.get_pop_table_data()

        # Store bit field data
        self.__bit_field_size = get_sdram_for_bit_field_region(
            self.__app_vertex.incoming_projections)
        self.__bit_field_key_map = get_bitfield_key_map_data(
            self.__app_vertex.incoming_projections)
        self.__generated_data_size += (
            len(self.__bit_field_key_map) * BYTES_PER_WORD)

    def __write_pop_table(self, spec, poptable_ref=None):
        master_pop_table_sz = len(self.__master_pop_data) * BYTES_PER_WORD
        spec.reserve_memory_region(
            region=self.__regions.pop_table, size=master_pop_table_sz,
            label='PopTable', reference=poptable_ref)
        spec.switch_write_focus(region=self.__regions.pop_table)
        spec.write_array(self.__master_pop_data)

    def write_synaptic_data(
            self, spec, post_vertex_slice, references):
        """ Write the synaptic data for all incoming projections

        :param ~data_specification.DataSpecificationGenerator spec:
            The spec to write to
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The slice of the post-vertex the matrix is for
        :param SynapseRegions references:
            Regions which are referenced; each region which is not referenced
            can be None.
        """

        # Reserve the region
        spec.comment(
            "\nWriting Synaptic Matrix and Master Population Table:\n")

        self.__write_pop_table(spec, references.pop_table)

        spec.reserve_memory_region(
            region=self.__regions.synaptic_matrix,
            size=self.__all_syn_block_sz, label='SynBlocks',
            reference=references.synaptic_matrix)

        # Write data for each matrix
        spec.switch_write_focus(self.__regions.synaptic_matrix)
        for matrix in self.__on_host_matrices:
            matrix.write_matrix(spec, post_vertex_slice)

        self.__write_synapse_expander_data_spec(
            spec, post_vertex_slice, references.connection_builder)

        write_bitfield_init_data(
            spec, self.__regions.bitfield_filter, self.__bit_field_size,
            references.bitfield_filter)

    def __write_synapse_expander_data_spec(
            self, spec, post_vertex_slice, connection_builder_ref=None):
        """ Write the data spec for the synapse expander

        :param ~.DataSpecificationGenerator spec:
            The specification to write to
        :param list(GeneratorData) generator_data: The data to be written
        :param weight_scales: scaling of weights on each synapse
        :type weight_scales: list(int or float)
        """
        if self.__generated_data is None:
            if connection_builder_ref is not None:
                # If there is a reference, we still need a region to create
                spec.reserve_memory_region(
                    region=self.__regions.connection_builder,
                    size=4, label="ConnectorBuilderRegion",
                    reference=connection_builder_ref)
            return

        spec.reserve_memory_region(
            region=self.__regions.connection_builder,
            size=self.__generated_data_size, label="ConnectorBuilderRegion",
            reference=connection_builder_ref)
        spec.switch_write_focus(self.__regions.connection_builder)
        spec.write_value(self.__regions.synaptic_matrix)
        spec.write_value(self.__regions.pop_table)
        spec.write_value(self.__regions.bitfield_filter)
        if isinstance(self.__app_vertex.synapse_dynamics,
                      AbstractSynapseDynamicsStructural):
            spec.write_value(self.__regions.structural_dynamics)
        else:
            spec.write_value(INVALID_REGION_ID)
        spec.write_value(self.__n_generated_matrices)
        spec.write_value(post_vertex_slice.lo_atom)
        spec.write_value(post_vertex_slice.n_atoms)
        spec.write_value(0)  # TODO: The index if needed
        spec.write_value(self.__n_synapse_types)
        spec.write_value(DataType.S1615.encode_as_int(
            SpynnakerDataView.get_simulation_time_step_per_ms()))
        # Per-Population RNG
        spec.write_array(self.__app_vertex.pop_seed)
        # Per-Core RNG
        spec.write_array(self.__app_vertex.core_seed)
        for w in self.__weight_scales:
            # if the weights are high enough and the population size large
            # enough, then weight_scales < 1 will result in a zero scale
            # if converted to an int, so we use U3232 here instead (as there
            # can be scales larger than U1616.max in conductance-based models)
            dtype = DataType.U3232
            spec.write_value(data=min(w, dtype.max), data_type=dtype)

        spec.write_array(self.__generated_data)
        spec.write_array(self.__bit_field_key_map)

    def __get_app_key_and_mask(self, r_info, n_stages, max_atoms_per_core):
        """ Get a key and mask for an incoming application vertex as a whole

        :param list(tuple(int, Slice)) keys:
            The key and slice of each relevant machine vertex in the incoming
            application vertex
        :param int mask: The mask that covers all keys
        :param n_stages: The number of delay stages
        :rtype: None or _AppKeyInfo
        """

        # Find the bit that is just for the core
        mask_size = r_info.n_bits_atoms
        core_mask = (r_info.machine_mask - r_info.mask) >> mask_size
        pre = r_info.vertex
        n_atoms = min(max_atoms_per_core, pre.n_atoms)

        return _AppKeyInfo(r_info.key, r_info.mask, core_mask,
                           mask_size, n_atoms * n_stages)

    def __app_key_and_mask(self, app_edge):
        """ Get a key and mask for an incoming application vertex as a whole

        :param PopulationApplicationEdge app_edge:
            The application edge to get the key and mask of
        :param RoutingInfo routing_info: The routing information of all edges
        """
        routing_info = SpynnakerDataView.get_routing_infos()
        r_info = routing_info.get_routing_info_from_pre_vertex(
            app_edge.pre_vertex, SPIKE_PARTITION_ID)
        if r_info is None:
            return None
        return self.__get_app_key_and_mask(
            r_info, 1, app_edge.pre_vertex.get_max_atoms_per_core())

    def __delay_app_key_and_mask(self, app_edge):
        """ Get a key and mask for a whole incoming delayed application\
            vertex, or return None if no delay edge exists

        :param PopulationApplicationEdge app_edge:
            The application edge to get the key and mask of
        :param RoutingInfo routing_info: The routing information of all edges
        """
        delay_edge = app_edge.delay_edge
        if delay_edge is None:
            return None
        routing_info = SpynnakerDataView.get_routing_infos()
        r_info = routing_info.get_routing_info_from_pre_vertex(
            delay_edge.pre_vertex, SPIKE_PARTITION_ID)

        # We use the app_edge pre-vertex max atoms here as the delay vertex
        # is split according to this
        return self.__get_app_key_and_mask(
            r_info, app_edge.n_delay_stages,
            app_edge.pre_vertex.get_max_atoms_per_core())

    def get_connections_from_machine(self, placement, app_edge, synapse_info):
        """ Get the synaptic connections from the machine

        :param ~pacman.model.placements.Placement placement:
            Where the vertices are on the machine
        :param ProjectionApplicationEdge app_edge:
            The application edge of the projection
        :param SynapseInformation synapse_info:
            The synapse information of the projection
        :return: A list of arrays of connections, each with dtype
            AbstractSynapseDynamics.NUMPY_CONNECTORS_DTYPE
        :rtype: ~numpy.ndarray
        """
        matrix = self.__matrices[app_edge, synapse_info]
        return matrix.get_connections(placement)

    def read_generated_connection_holders(self, placement):
        """ Fill in any pre-run connection holders for data which is generated
            on the machine, after it has been generated

        :param ~pacman.model.placements.Placement placement:
            where the data is to be read from
        """
        for matrix in self.__matrices.values():
            matrix.read_generated_connection_holders(placement)

    @property
    def gen_on_machine(self):
        """ Whether any matrices need to be generated on the machine

        :rtype: bool
        """
        return self.__gen_on_machine

    def get_index(self, app_edge, synapse_info):
        """ Get the index of an incoming projection in the population table

        :param ProjectionApplicationEdge app_edge:
            The application edge of the projection
        :param SynapseInformation synapse_info:
            The synapse information of the projection
        """
        matrix = self.__matrices[app_edge, synapse_info]
        return matrix.get_index()


class _AppKeyInfo(object):
    """ An object which holds an application key and mask along with the other
        details
    """

    __slots__ = ["app_key", "app_mask", "core_mask", "core_shift", "n_neurons"]

    def __init__(self, app_key, app_mask, core_mask, core_shift, n_neurons):
        """

        :param int app_key: The application-level key
        :param int app_mask: The application-level mask
        :param int core_mask: The mask to get the core from the key
        :param int core_shift: The shift to get the core from the key
        :param int n_neurons:
            The neurons in each core (except possibly the last)
        """
        self.app_key = app_key
        self.app_mask = app_mask
        self.core_mask = core_mask
        self.core_shift = core_shift
        self.n_neurons = n_neurons

    @property
    def key_and_mask(self):
        """ Convenience method to get the key and mask as an object

        :rtype: BaseKeyAndMask
        """
        return BaseKeyAndMask(self.app_key, self.app_mask)
