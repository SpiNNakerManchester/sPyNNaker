# Copyright (c) 2019-2020 The University of Manchester
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
from pacman.utilities.constants import FULL_MASK
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.models.abstract_models import AbstractHasDelayStages

#: number of elements
ELEMENTS_USED_IN_EACH_BIT_FIELD = 3  # n words, key, pointer to bitfield

#: n_filters, pointer for array
ELEMENTS_USED_IN_BIT_FIELD_HEADER = 2

#: n elements in each key to n atoms map for bitfield (key, n atoms)
N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP = 2

#: the regions addresses needed (
#: pop table, synaptic matrix, direct matrix, bit_field, bit field builder,
#: bit_field_key, structural region)
N_REGIONS_ADDRESSES = 6

#: n key to n neurons maps size in words
N_KEYS_DATA_SET_IN_WORDS = 1

#: the number of bits in a word
# (WHY IS THIS NOT A CONSTANT SOMEWHERE!)
BIT_IN_A_WORD = 32.0


def get_estimated_sdram_for_bit_field_region(app_graph, vertex):
    """ estimates the SDRAM for the bit field region

    :param ~pacman.model.graphs.application.ApplicationGraph app_graph:
        the app graph
    :param ~pacman.model.graphs.application.ApplicationVertex vertex:
        app vertex
    :return: the estimated number of bytes used by the bit field region
    :rtype: int
    """
    sdram = 0
    for incoming_edge in app_graph.get_edges_ending_at_vertex(vertex):
        if isinstance(incoming_edge, ProjectionApplicationEdge):
            slices, _ = (
                incoming_edge.pre_vertex.splitter.get_out_going_slices())
            n_machine_vertices = len(slices)

            slice_atoms = list()
            for vertex_slice in slices:
                slice_atoms.append(vertex_slice.n_atoms)
            n_atoms_per_machine_vertex = max(slice_atoms)

            if isinstance(incoming_edge.pre_vertex, AbstractHasDelayStages):
                n_atoms_per_machine_vertex *= \
                    incoming_edge.pre_vertex.n_delay_stages
            n_words_for_atoms = int(math.ceil(
                n_atoms_per_machine_vertex / BIT_IN_A_WORD))
            sdram += (
                (ELEMENTS_USED_IN_EACH_BIT_FIELD + (
                    n_words_for_atoms * n_machine_vertices)) *
                BYTES_PER_WORD)
    return sdram


def get_estimated_sdram_for_key_region(app_graph, vertex):
    """ gets an estimate of the bitfield builder region

    :param ~pacman.model.graphs.application.ApplicationGraph app_graph:
        the app graph
    :param ~pacman.model.graphs.application.ApplicationVertex vertex:
        app vertex
    :return: SDRAM needed
    :rtype: int
    """

    # basic sdram
    sdram = N_KEYS_DATA_SET_IN_WORDS * BYTES_PER_WORD
    for in_edge in app_graph.get_edges_ending_at_vertex(vertex):

        # Get the number of likely vertices
        slices, _ = in_edge.pre_vertex.splitter.get_out_going_slices()
        sdram += (
            len(slices) * N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP * BYTES_PER_WORD)
    return sdram


def _exact_sdram_for_bit_field_region(
        machine_graph, vertex, n_key_map):
    """ calculates the correct SDRAM for the bitfield region based off \
        the machine graph

    :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
        machine graph
    :param ~pacman.model.graphs.machine.MachineVertex vertex:
        the machine vertex
    :param ~pacman.model.routing_info.AbstractMachinePartitionNKeysMap \
            n_key_map:
        n keys map
    :return: SDRAM in bytes
    :rtype: int
    """
    sdram = ELEMENTS_USED_IN_BIT_FIELD_HEADER * BYTES_PER_WORD
    for incoming_edge in machine_graph.get_edges_ending_at_vertex(vertex):
        n_keys = n_key_map.n_keys_for_partition(
            machine_graph.get_outgoing_partition_for_edge(incoming_edge))
        n_words_for_atoms = int(math.ceil(n_keys / BIT_IN_A_WORD))

        sdram += (
            (ELEMENTS_USED_IN_EACH_BIT_FIELD + n_words_for_atoms) *
            BYTES_PER_WORD)
    return sdram


def exact_sdram_for_bit_field_builder_region():
    """ Gets the SDRAM requirement for the builder region

    :return: the SDRAM requirement for the builder region
    :rtype: int
    """
    return N_REGIONS_ADDRESSES * BYTES_PER_WORD


def _exact_sdram_for_bit_field_key_region(machine_graph, vertex):
    """ Calculates the exact SDRAM for the bitfield key region

    :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
        machine graph
    :param ~pacman.model.graphs.machine.MachineVertex vertex: machine vertex
    :return: bytes
    :rtype: int
    """
    return (
        N_KEYS_DATA_SET_IN_WORDS +
        len(machine_graph.get_edges_ending_at_vertex(vertex)) *
        N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP) * BYTES_PER_WORD


def reserve_bit_field_regions(
        spec, machine_graph, n_key_map, vertex, bit_field_builder_region,
        bit_filter_region, bit_field_key_region):
    """ reserves the regions for the bitfields

    :param ~data_specification.DataSpecificationGenerator spec:
        dsg spec writer
    :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
        machine graph
    :param ~pacman.model.routing_info.AbstractMachinePartitionNKeysMap \
            n_key_map:
        map between partitions and n keys
    :param ~pacman.model.graphs.machine.MachineVertex vertex: machine vertex
    :param int bit_field_builder_region: region id for the builder region
    :param int bit_filter_region: region id for the bitfield region
    :param int bit_field_key_region: region id for the key map
    """

    # reserve the final destination for the bitfields
    spec.reserve_memory_region(
        region=bit_filter_region,
        size=_exact_sdram_for_bit_field_region(
            machine_graph, vertex, n_key_map),
        label="bit_field region")

    # reserve region for the bitfield builder
    spec.reserve_memory_region(
        region=bit_field_builder_region,
        size=exact_sdram_for_bit_field_builder_region(),
        label="bit field builder region")

    # reserve memory region for the key region
    spec.reserve_memory_region(
        region=bit_field_key_region,
        size=_exact_sdram_for_bit_field_key_region(machine_graph, vertex),
        label="bit field key data")


def write_bitfield_init_data(
        spec, machine_vertex, machine_graph, routing_info, n_key_map,
        bit_field_builder_region, master_pop_region_id,
        synaptic_matrix_region_id, direct_matrix_region_id,
        bit_field_region_id, bit_field_key_map_region_id,
        structural_dynamics_region_id, has_structural_dynamics_region):
    """ writes the init data needed for the bitfield generator

    :param ~data_specification.DataSpecificationGenerator spec:
        data spec writer
    :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
        machine vertex
    :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
        machine graph
    :param ~pacman.model.routing_info.RoutingInfo routing_info: keys
    :param ~pacman.model.routing_info.AbstractMachinePartitionNKeysMap \
            n_key_map:
        map for edge to n keys
    :param int bit_field_builder_region: the region id for the bitfield builder
    :param int master_pop_region_id: the region id for the master pop table
    :param int synaptic_matrix_region_id: the region id for the synaptic matrix
    :param int direct_matrix_region_id: the region id for the direct matrix
    :param int bit_field_region_id: the region id for the bit-fields
    :param int bit_field_key_map_region_id: the region id for the key map
    :param int structural_dynamics_region_id: the region id for the structural
    :param bool has_structural_dynamics_region:
        whether the core has a structural_dynamics region
    """
    spec.switch_write_focus(bit_field_builder_region)

    spec.write_value(master_pop_region_id)
    spec.write_value(synaptic_matrix_region_id)
    spec.write_value(direct_matrix_region_id)
    spec.write_value(bit_field_region_id)
    spec.write_value(bit_field_key_map_region_id)

    # save 4 bytes by making a key flag of full mask to avoid when not got
    # a structural
    if not has_structural_dynamics_region:
        spec.write_value(FULL_MASK)
    else:
        spec.write_value(structural_dynamics_region_id)

    spec.switch_write_focus(bit_field_key_map_region_id)

    # write n keys max atom map
    spec.write_value(
        len(machine_graph.get_edges_ending_at_vertex(machine_vertex)))

    # load in key to max atoms map
    for out_going_partition in machine_graph.\
            get_multicast_edge_partitions_ending_at_vertex(machine_vertex):
        spec.write_value(
            routing_info.get_first_key_from_partition(out_going_partition))
        spec.write_value(
            n_key_map.n_keys_for_partition(out_going_partition))

    # ensure if nothing else that n bitfields in bitfield region set to 0
    spec.switch_write_focus(bit_field_region_id)
    spec.write_value(0)
