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

import math
import numpy
from collections import defaultdict

from spinn_utilities.ordered_set import OrderedSet
from pacman.model.routing_info import BaseKeyAndMask
from data_specification.enums.data_type import DataType

from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron.master_pop_table import (
    MasterPopTableAsBinarySearch)
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from .key_space_tracker import KeySpaceTracker
from .synaptic_matrix_app import SynapticMatrixApp

# 1 for synaptic matrix region
# 1 for n_edges
# 2 for post_vertex_slice.lo_atom, post_vertex_slice.n_atoms
# 1 for n_synapse_types
# 1 for n_synapse_type_bits
# 1 for n_synapse_index_bits
SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES = (
    1 + 1 + 2 + 1 + 1 + 1) * BYTES_PER_WORD

DIRECT_MATRIX_HEADER_COST_BYTES = 1 * BYTES_PER_WORD


class SynapticMatrices(object):
    """ Handler of synaptic matrices for a core of a population vertex
    """

    __slots__ = [
        # The slice of the post-vertex that these matrices are for
        "__post_vertex_slice",
        # The number of synapse types received
        "__n_synapse_types",
        # The maximum summed size of the "direct" or "single" matrices
        "__all_single_syn_sz",
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
        # The maximum generated data, for calculating timeouts
        "__max_gen_data"
    ]

    def __init__(
            self, post_vertex_slice, n_synapse_types, all_single_syn_sz,
            synaptic_matrix_region, direct_matrix_region, poptable_region,
            connection_builder_region, synaptic_matrix_ref=None,
            direct_matrix_ref=None, poptable_ref=None,
            connection_builder_ref=None):
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
        self.__all_single_syn_sz = all_single_syn_sz
        self.__synaptic_matrix_region = synaptic_matrix_region
        self.__direct_matrix_region = direct_matrix_region
        self.__poptable_region = poptable_region
        self.__connection_builder_region = connection_builder_region
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
        self.__max_gen_data = 0

    @property
    def max_gen_data(self):
        """  The maximum amount of data to be generated for the synapses.

        :rtype: int
        """
        return self.__max_gen_data

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
            self.__poptable, synapse_info, app_edge,
            self.__n_synapse_types, self.__all_single_syn_sz,
            self.__post_vertex_slice, self.__synaptic_matrix_region,
            self.__direct_matrix_region)
        self.__matrices[key] = matrix
        return matrix

    def write_synaptic_data(
            self, spec, incoming_projections, all_syn_block_sz, weight_scales):
        """ Write the synaptic data for all incoming projections

        :param ~data_specification.DataSpecificationGenerator spec:
            The spec to write to
        :param list(~spynnaker8.models.Projection) incoming_projection:
            The projections to generate data for
        :param int all_syn_block_sz:
            The size in bytes of the space reserved for synapses
        :param list(float) weight_scales: The weight scale of each synapse
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

        # Convert the data for convenience
        incoming_by_app_edge, delayed_by_app_edge, key_space_tracker = \
            self.__incoming_by_app_edge(incoming_projections)

        # Set up for single synapses
        # The list is seeded with an empty array so we can just concatenate
        # later (as numpy doesn't let you concatenate nothing)
        single_synapses = [numpy.array([], dtype="uint32")]
        single_addr = 0

        # Lets write some synapses
        spec.switch_write_focus(self.__synaptic_matrix_region)

        # Store a list of synapse info to be generated on the machine
        generate_on_machine = list()

        # For each incoming machine vertex, create a synaptic list
        for app_edge, m_vertices in incoming_by_app_edge.items():
            delayed_m_vertices = delayed_by_app_edge.get(app_edge, [])

            spec.comment("\nWriting matrix for edge:{}\n".format(
                app_edge.label))
            app_key_info = self.__app_key_and_mask(
                m_vertices, app_edge, key_space_tracker)
            d_app_key_info = self.__delay_app_key_and_mask(
                delayed_m_vertices, app_edge, key_space_tracker)

            for synapse_info in app_edge.synapse_information:
                app_matrix = self.__app_matrix(app_edge, synapse_info)
                delay_pre_vertex = None
                if app_edge.delay_edge is not None:
                    delay_pre_vertex = app_edge.delay_edge.pre_vertex
                app_matrix.set_info(
                    all_syn_block_sz, app_key_info, d_app_key_info,
                    weight_scales, m_vertices, delay_pre_vertex)

                # If we can generate the connector on the machine, do so
                if app_matrix.can_generate_on_machine(single_addr):
                    generate_on_machine.append(app_matrix)
                else:
                    block_addr, single_addr = app_matrix.write_matrix(
                        spec, block_addr, single_addr, single_synapses)

        self.__host_generated_block_addr = block_addr

        # Skip blocks that will be written on the machine, but add them
        # to the master population table
        generator_data = list()
        self.__max_gen_data = 0
        for app_matrix in generate_on_machine:
            block_addr = app_matrix.write_on_chip_matrix_data(
                generator_data, block_addr)
            self.__max_gen_data += app_matrix.gen_size
            self.__gen_on_machine = True

        self.__on_chip_generated_block_addr = block_addr

        # Finish the master population table
        self.__poptable.finish_master_pop_table(
            spec, self.__poptable_region, self.__poptable_ref)

        # Write the size and data of single synapses to the direct region
        single_data = numpy.concatenate(single_synapses)
        single_data_words = len(single_data)
        spec.reserve_memory_region(
            region=self.__direct_matrix_region,
            size=(
                single_data_words * BYTES_PER_WORD +
                DIRECT_MATRIX_HEADER_COST_BYTES),
            label='DirectMatrix',
            reference=self.__direct_matrix_ref)
        spec.switch_write_focus(self.__direct_matrix_region)
        spec.write_value(single_data_words * BYTES_PER_WORD)
        if single_data_words:
            spec.write_array(single_data)

        self.__write_synapse_expander_data_spec(
            spec, generator_data, weight_scales)

    def __write_synapse_expander_data_spec(
            self, spec, generator_data, weight_scales):
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
        spec.write_value(self.__n_synapse_types)
        spec.write_value(get_n_bits(self.__n_synapse_types))
        n_neuron_id_bits = get_n_bits(self.__post_vertex_slice.n_atoms)
        spec.write_value(n_neuron_id_bits)
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

    def __incoming_by_app_edge(self, incoming_projections):
        """ Convert a list of incoming projections to a dict of
            application edge -> list of pre vertices, and a key tracker

        :param list(~spynnaker.pyNN.models.Projection) incoming_projections:
            The incoming projections
        :rtype: tuple(dict, KeySpaceTracker)
        """
        incoming_by_app_edge = defaultdict(OrderedSet)
        delayed_by_app_edge = defaultdict(OrderedSet)
        key_space_tracker = KeySpaceTracker()
        pre_vertices = set()

        for proj in incoming_projections:
            # pylint: disable=protected-access
            app_edge = proj._projection_edge

            # Skip if already done
            if app_edge in incoming_by_app_edge:
                continue

            # Add all incoming machine vertices
            out_verts = app_edge.pre_vertex.splitter.get_out_going_vertices(
                SPIKE_PARTITION_ID)
            for machine_vertex in out_verts:
                if machine_vertex in pre_vertices:
                    continue

                pre_vertices.add(machine_vertex)
                routing_info = SpynnakerDataView.get_routing_infos()
                rinfo = routing_info.get_routing_info_from_pre_vertex(
                    machine_vertex, SPIKE_PARTITION_ID)
                key_space_tracker.allocate_keys(rinfo)

                incoming_by_app_edge[app_edge].add(machine_vertex)

            # Add all incoming delayed vertices
            delay_edge = app_edge.delay_edge
            if delay_edge is not None:
                verts = delay_edge.pre_vertex.splitter.get_out_going_vertices(
                    SPIKE_PARTITION_ID)
                for machine_vertex in verts:
                    if machine_vertex in pre_vertices:
                        continue

                    pre_vertices.add(machine_vertex)
                    routing_info = SpynnakerDataView.get_routing_infos()
                    rinfo = routing_info.get_routing_info_from_pre_vertex(
                        machine_vertex, SPIKE_PARTITION_ID)
                    key_space_tracker.allocate_keys(rinfo)
                    delayed_by_app_edge[app_edge].add(machine_vertex)

        return incoming_by_app_edge, delayed_by_app_edge, key_space_tracker

    @staticmethod
    def __check_keys_adjacent(keys, mask_size):
        """ Check that a given list of keys and slices have no gaps between
            them

        :param list(tuple(int, Slice)) keys: A list of keys and slices to check
        :param mask_size: The number of 0s in the mask
        :rtype: bool
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

        :param list(tuple(int, Slice)) keys:
            The key and slice of each relevant machine vertex in the incoming
            application vertex
        :param int mask: The mask that covers all keys
        :param n_stages: The number of delay stages
        :param key_space_tracker:
            A key space tracker that has been filled in with all keys this
            vertex will receive
        :rtype: None or _AppKeyInfo
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

    def __check_key_slices(self, n_atoms, slices, delay_stages=1):
        """ Check if a list of slices cover all n_atoms without any gaps

        :param int n_atoms: The total number of atoms expected
        :param list(Slice) slices: The list of slices to check
        :rtype: bool
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
            if n_atoms_per_core is None:
                n_atoms_per_core = s.n_atoms

        # If the number of atoms per core is too big, this can't be done
        if ((n_atoms_per_core * delay_stages) >
                self.__poptable.max_n_neurons_per_core):
            return False
        return True

    def __app_key_and_mask(self, m_vertices, app_edge, key_space_tracker):
        """ Get a key and mask for an incoming application vertex as a whole,\
            or say it isn't possible (return None)

        :param list(MachineVertex) m_vertices:
            The relevant incoming machine vertices
        :param PopulationApplicationEdge app_edge:
            The application edge to get the key and mask of
        :param KeySpaceTracker key_space_tracker:
            A tracker pre-filled with the keys of all incoming edges
        """
        # If there are too many pre-cores, give up now
        if len(m_vertices) > self.__poptable.max_core_mask:
            return None

        # Work out if the keys allow the machine vertices to be merged
        mask = None
        keys = list()

        # Can be merged only if all the masks are the same
        pre_slices = list()
        for m_vertex in m_vertices:
            routing_info = SpynnakerDataView.get_routing_infos()
            rinfo = routing_info.get_routing_info_from_pre_vertex(
                m_vertex, SPIKE_PARTITION_ID)
            pre_slices.append(m_vertex.vertex_slice)
            # No routing info at all? Must have been filtered, so doesn't work
            if rinfo is None:
                return None
            # Mask is not the same as the last mask?  Doesn't work
            if mask is not None and rinfo.first_mask != mask:
                return None
            mask = rinfo.first_mask
            keys.append((rinfo.first_key, m_vertex.vertex_slice))

        if mask is None:
            return None

        if not self.__check_key_slices(
                app_edge.pre_vertex.n_atoms, pre_slices):
            return None

        return self.__get_app_key_and_mask(keys, mask, 1, key_space_tracker)

    def __delay_app_key_and_mask(
            self, m_vertices, app_edge, key_space_tracker):
        """ Get a key and mask for a whole incoming delayed application\
            vertex, or say it isn't possible (return None)

        :param list(MachineVertex) m_vertices:
            The relevant incoming machine vertices from delays
        :param PopulationApplicationEdge app_edge:
            The application edge to get the key and mask of
        :param KeySpaceTracker key_space_tracker:
            A tracker pre-filled with the keys of all incoming edges
        """
        # If there are no delay vertices, stop
        if not m_vertices:
            return None

        # If there are too many pre-cores, give up now
        if len(m_vertices) > self.__poptable.max_core_mask:
            return None

        # Work out if the keys allow the machine vertices to be
        # merged
        mask = None
        keys = list()

        # Can be merged only if all the masks are the same
        pre_slices = list()
        for m_vertex in m_vertices:
            routing_info = SpynnakerDataView.get_routing_infos()
            rinfo = routing_info.get_routing_info_from_pre_vertex(
                m_vertex, SPIKE_PARTITION_ID)
            pre_slices.append(m_vertex.vertex_slice)
            # No routing info at all? Must have been filtered, so doesn't work
            if rinfo is None:
                return None
            # Mask is not the same as the last mask?  Doesn't work
            if mask is not None and rinfo.first_mask != mask:
                return None
            mask = rinfo.first_mask
            keys.append((rinfo.first_key, m_vertex.vertex_slice))

        if not self.__check_key_slices(
                app_edge.pre_vertex.n_atoms, pre_slices,
                app_edge.n_delay_stages):
            return None

        return self.__get_app_key_and_mask(
            keys, mask, app_edge.n_delay_stages, key_space_tracker)

    def get_connections_from_machine(
            self, placement, app_edge, synapse_info):
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
        return matrix.get_connections(placement)

    def read_generated_connection_holders(self, placement):
        """ Fill in any pre-run connection holders for data which is generated
            on the machine, after it has been generated

        :param ~pacman.model.placements.Placement placement:
            where the data is to be read from
        """
        for matrix in self.__matrices.values():
            matrix.read_generated_connection_holders(placement)

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

    def get_index(self, app_edge, synapse_info, m_vertex):
        """ Get the index of an incoming projection in the population table

        :param ProjectionApplicationEdge app_edge:
            The application edge of the projection
        :param SynapseInformation synapse_info:
            The synapse information of the projection
        :param ~pacman.model.graphs.machine.MachineVertex m_vertex:
            The source machine vertex
        """
        matrix = self.__app_matrix(app_edge, synapse_info)
        return matrix.get_index(m_vertex)


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
