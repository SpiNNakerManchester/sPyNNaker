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

from pacman.model.routing_info import BaseKeyAndMask
from data_specification.enums.data_type import DataType

from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.utilities.globals_variables import (
    machine_time_step_per_ms)
from spynnaker.pyNN.models.neuron.master_pop_table import (
    MasterPopTableAsBinarySearch)
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from .synaptic_matrix_app import SynapticMatrixApp

# 1 for synaptic matrix region
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
    1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 4 + 4) * BYTES_PER_WORD

DIRECT_MATRIX_HEADER_COST_BYTES = 1 * BYTES_PER_WORD


class SynapticMatrices(object):
    """ Handler of synaptic matrices for a core of a population vertex
    """

    __slots__ = [
        # The slice of the post-vertex that these matrices are for
        "__post_vertex_slice",
        # The number of synapse types received
        "__n_synapse_types",
        # The ID of the synaptic matrix region
        "__synaptic_matrix_region",
        # The ID of the "direct" or "single" matrix region
        "__direct_matrix_region",
        # The ID of the master population table region
        "__poptable_region",
        # The ID of the connection builder region
        "__connection_builder_region",
        # The master population table data structure
        "__poptable",
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
        # Reference to give the synaptic matrix
        "__synaptic_matrix_ref",
        # Reference to give the direct matrix
        "__direct_matrix_ref",
        # Reference to give the master population table
        "__poptable_ref",
        # Reference to give the connection builder
        "__connection_builder_ref",
        # Number of bits to use for neuron IDs
        "__max_atoms_per_core"
    ]

    def __init__(
            self, post_vertex_slice, n_synapse_types,
            synaptic_matrix_region, direct_matrix_region, poptable_region,
            connection_builder_region, max_atoms_per_core,
            synaptic_matrix_ref=None, direct_matrix_ref=None,
            poptable_ref=None, connection_builder_ref=None):
        """
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The slice of the post vertex that these matrices are for
        :param int n_synapse_types: The number of synapse types available
        :param int all_single_syn_sz:
            The space available for "direct" or "single" synapses
        :param int synaptic_matrix_region:
            The region where synaptic matrices are stored
        :param int direct_matrix_region:
            The region where "direct" or "single" synapses are stored
        :param int poptable_region:
            The region where the population table is stored
        :param int connection_builder_region:
            The region where the synapse generator information is stored
        :param synaptic_matrix_ref:
            The reference to the synaptic matrix region, or None if not
            referenceable
        :type synaptic_matrix_ref: int or None
        :param direct_matrix_ref:
            The reference to the direct matrix region, or None if not
            referenceable
        :type direct_matrix_ref: int or None
        :param poptable_ref:
            The reference to the pop table region, or None if not
            referenceable
        :type poptable_ref: int or None
        :param connection_builder_ref:
            The reference to the connection builder region, or None if not
            referenceable
        :type connection_builder_ref: int or None
        """
        self.__post_vertex_slice = post_vertex_slice
        self.__n_synapse_types = n_synapse_types
        self.__synaptic_matrix_region = synaptic_matrix_region
        self.__direct_matrix_region = direct_matrix_region
        self.__poptable_region = poptable_region
        self.__connection_builder_region = connection_builder_region
        self.__max_atoms_per_core = max_atoms_per_core
        self.__synaptic_matrix_ref = synaptic_matrix_ref
        self.__direct_matrix_ref = direct_matrix_ref
        self.__poptable_ref = poptable_ref
        self.__connection_builder_ref = connection_builder_ref

        # Set up the master population table
        self.__poptable = MasterPopTableAsBinarySearch()

        # Map of (app_edge, synapse_info) to SynapticMatrixApp
        self.__matrices = dict()

        # Store locations of synaptic data and generated data
        self.__host_generated_block_addr = 0
        self.__on_chip_generated_block_addr = 0

        # Determine whether to generate on machine
        self.__gen_on_machine = False

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

    def __app_matrix(self, app_edge, synapse_info):
        """ Get or create an application synaptic matrix object

        :param ProjectionApplicationEdge app_edge:
            The application edge to get the object for
        :param SynapseInformation synapse_info:
            The synapse information to get the object for
        :rtype: SynapticMatrixApp
        """
        key = (app_edge, synapse_info)
        if key in self.__matrices:
            return self.__matrices[key]

        matrix = SynapticMatrixApp(
            self.__poptable, synapse_info, app_edge, self.__n_synapse_types,
            self.__post_vertex_slice, self.__synaptic_matrix_region,
            self.__max_atoms_per_core)
        self.__matrices[key] = matrix
        return matrix

    def write_synaptic_data(
            self, spec, incoming_projections, all_syn_block_sz, weight_scales,
            routing_info, app_vertex):
        """ Write the synaptic data for all incoming projections

        :param ~data_specification.DataSpecificationGenerator spec:
            The spec to write to
        :param list(~spynnaker8.models.Projection) incoming_projection:
            The projections to generate data for
        :param int all_syn_block_sz:
            The size in bytes of the space reserved for synapses
        :param list(float) weight_scales: The weight scale of each synapse
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
            The routing information for all edges
        """
        # If there are no synapses, there is nothing to do!
        if all_syn_block_sz == 0:
            return

        # Reserve the region
        spec.comment(
            "\nWriting Synaptic Matrix and Master Population Table:\n")
        spec.reserve_memory_region(
            region=self.__synaptic_matrix_region,
            size=all_syn_block_sz, label='SynBlocks',
            reference=self.__synaptic_matrix_ref)

        # Track writes inside the synaptic matrix region:
        block_addr = 0
        self.__poptable.initialise_table()

        # Lets write some synapses
        spec.switch_write_focus(self.__synaptic_matrix_region)

        # Store a list of synapse info to be generated on the machine
        generate_on_machine = list()

        # For each incoming machine vertex, create a synaptic list
        for proj in incoming_projections:
            app_edge = proj._projection_edge
            synapse_info = proj._synapse_information
            spec.comment("\nWriting matrix for edge:{}\n".format(
                app_edge.label))
            app_key_info = self.__app_key_and_mask(app_edge, routing_info)
            if app_key_info is None:
                continue
            d_app_key_info = self.__delay_app_key_and_mask(
                app_edge, routing_info)
            app_matrix = self.__app_matrix(app_edge, synapse_info)
            app_matrix.set_info(
                all_syn_block_sz, app_key_info, d_app_key_info, weight_scales)

            # If we can generate the connector on the machine, do so
            if synapse_info.may_generate_on_machine():
                generate_on_machine.append(app_matrix)
            else:
                block_addr = app_matrix.write_matrix(spec, block_addr)

        self.__host_generated_block_addr = block_addr

        # Skip blocks that will be written on the machine, but add them
        # to the master population table
        generator_data = list()
        for app_matrix in generate_on_machine:
            block_addr = app_matrix.write_on_chip_matrix_data(
                generator_data, block_addr)
            self.__gen_on_machine = True

        self.__on_chip_generated_block_addr = block_addr

        # Finish the master population table
        self.__poptable.finish_master_pop_table(
            spec, self.__poptable_region, self.__poptable_ref)

        # Write the size and data of single synapses to the direct region
        # This is currently disabled
        single_data_words = 0
        spec.reserve_memory_region(
            region=self.__direct_matrix_region,
            size=(
                single_data_words * BYTES_PER_WORD +
                DIRECT_MATRIX_HEADER_COST_BYTES),
            label='DirectMatrix',
            reference=self.__direct_matrix_ref)
        spec.switch_write_focus(self.__direct_matrix_region)
        spec.write_value(single_data_words * BYTES_PER_WORD)

        self.__write_synapse_expander_data_spec(
            spec, generator_data, weight_scales, app_vertex)

    def __write_synapse_expander_data_spec(
            self, spec, generator_data, weight_scales, app_vertex):
        """ Write the data spec for the synapse expander

        :param ~.DataSpecificationGenerator spec:
            The specification to write to
        :param list(GeneratorData) generator_data: The data to be written
        :param weight_scales: scaling of weights on each synapse
        :type weight_scales: list(int or float)
        """
        if not generator_data:
            if self.__connection_builder_ref is not None:
                # If there is a reference, we still need a region to create
                spec.reserve_memory_region(
                    region=self.__connection_builder_region,
                    size=4, label="ConnectorBuilderRegion",
                    reference=self.__connection_builder_ref)
            return

        n_bytes = (
            SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES +
            (self.__n_synapse_types * DataType.U3232.size))
        for data in generator_data:
            n_bytes += data.size

        spec.reserve_memory_region(
            region=self.__connection_builder_region,
            size=n_bytes, label="ConnectorBuilderRegion",
            reference=self.__connection_builder_ref)
        spec.switch_write_focus(self.__connection_builder_region)

        spec.write_value(self.__synaptic_matrix_region)
        spec.write_value(len(generator_data))
        spec.write_value(self.__post_vertex_slice.lo_atom)
        spec.write_value(self.__post_vertex_slice.n_atoms)
        spec.write_value(0)  # TODO: The index if needed
        spec.write_value(self.__n_synapse_types)
        spec.write_value(
            DataType.S1615.encode_as_int(machine_time_step_per_ms()))
        # Padding to ensure 8-byte alignment for weight scales
        spec.write_value(0)
        # Per-Population RNG
        spec.write_array(app_vertex.pop_seed)
        # Per-Core RNG
        spec.write_array(app_vertex.core_seed)
        for w in weight_scales:
            # if the weights are high enough and the population size large
            # enough, then weight_scales < 1 will result in a zero scale
            # if converted to an int, so we use U3232 here instead (as there
            # can be scales larger than U1616.max in conductance-based models)
            dtype = DataType.U3232
            spec.write_value(data=min(w, dtype.max), data_type=dtype)

        items = list()
        for data in generator_data:
            items.extend(data.gen_data)
        spec.write_array(numpy.concatenate(items))

    def __get_app_key_and_mask(self, r_info, n_stages):
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
        core_mask = (r_info.machine_mask - r_info.first_mask) >> mask_size
        pre = r_info.vertex
        n_atoms = min(pre.splitter.max_atoms_per_core, pre.n_atoms)

        return _AppKeyInfo(r_info.first_key, r_info.first_mask, core_mask,
                           mask_size, n_atoms * n_stages)

    def __app_key_and_mask(self, app_edge, routing_info):
        """ Get a key and mask for an incoming application vertex as a whole

        :param PopulationApplicationEdge app_edge:
            The application edge to get the key and mask of
        :param RoutingInfo routing_info: The routing information of all edges
        """
        r_info = routing_info.get_routing_info_from_pre_vertex(
            app_edge.pre_vertex, SPIKE_PARTITION_ID)
        if r_info is None:
            return None
        return self.__get_app_key_and_mask(r_info, 1)

    def __delay_app_key_and_mask(self, app_edge, routing_info):
        """ Get a key and mask for a whole incoming delayed application\
            vertex, or return None if no delay edge exists

        :param PopulationApplicationEdge app_edge:
            The application edge to get the key and mask of
        :param RoutingInfo routing_info: The routing information of all edges
        """
        delay_edge = app_edge.delay_edge
        if delay_edge is None:
            return None
        r_info = routing_info.get_routing_info_from_pre_vertex(
            delay_edge.pre_vertex, SPIKE_PARTITION_ID)

        return self.__get_app_key_and_mask(r_info, app_edge.n_delay_stages)

    def get_connections_from_machine(
            self, transceiver, placement, app_edge, synapse_info):
        """ Get the synaptic connections from the machine

        :param ~spinnman.transceiver.Transceiver transceiver:
            Used to read the data from the machine
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
        matrix = self.__app_matrix(app_edge, synapse_info)
        return matrix.get_connections(transceiver, placement)

    def read_generated_connection_holders(self, transceiver, placement):
        """ Fill in any pre-run connection holders for data which is generated
            on the machine, after it has been generated

        :param ~spinnman.transceiver.Transceiver transceiver:
            How to read the data from the machine
        :param ~pacman.model.placements.Placement placement:
            where the data is to be read from
        """
        for matrix in self.__matrices.values():
            matrix.read_generated_connection_holders(transceiver, placement)

    def clear_connection_cache(self):
        """ Clear any values read from the machine
        """
        for matrix in self.__matrices.values():
            matrix.clear_connection_cache()

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
        matrix = self.__app_matrix(app_edge, synapse_info)
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
