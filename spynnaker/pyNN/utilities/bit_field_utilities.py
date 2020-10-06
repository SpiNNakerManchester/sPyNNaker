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
from pacman.utilities.algorithm_utilities. \
    partition_algorithm_utilities import determine_max_atoms_for_vertex
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex

# number of elements
ELEMENTS_USED_IN_EACH_BIT_FIELD = 3  # n words, key, pointer to bitfield

# n_filters, pointer for array
ELEMENTS_USED_IN_BIT_FIELD_HEADER = 2

# n elements in each key to n atoms map for bitfield (key, n atoms)
N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP = 2

# the regions addresses needed (
#  pop table, synaptic matrix, direct matrix, bit_field, bit field builder,
# bit_field_key, structural region)
N_REGIONS_ADDRESSES = 6

# n key to n neurons maps size in words
N_KEYS_DATA_SET_IN_WORDS = 1

# the number of bits in a word (WHY IS THIS NOT A CONSTANT SOMEWHERE!)
BIT_IN_A_WORD = 32.0


def get_estimated_sdram_for_bit_field_region(app_graph, vertex):
    """ estimates the sdram for the bit field region
    :param app_graph: the app graph
    :param vertex: machine vertex
    :return: the estimated number of bytes used by the bit field region
    """
    sdram = 0
    for incoming_edge in app_graph.get_edges_ending_at_vertex(vertex):
        if isinstance(incoming_edge, ProjectionApplicationEdge):
            edge_pre_vertex = incoming_edge.pre_vertex
            max_atoms = determine_max_atoms_for_vertex(edge_pre_vertex)
            if incoming_edge.pre_vertex.n_atoms < max_atoms:
                max_atoms = incoming_edge.pre_vertex.n_atoms

            # Get the number of likely vertices
            n_machine_vertices = int(math.ceil(
                float(incoming_edge.pre_vertex.n_atoms) /
                float(max_atoms)))
            n_atoms_per_machine_vertex = int(math.ceil(
                float(incoming_edge.pre_vertex.n_atoms) /
                n_machine_vertices))
            if isinstance(edge_pre_vertex, DelayExtensionVertex):
                n_atoms_per_machine_vertex *= \
                    edge_pre_vertex.n_delay_stages
            n_words_for_atoms = int(math.ceil(
                n_atoms_per_machine_vertex / BIT_IN_A_WORD))
            sdram += (
                (ELEMENTS_USED_IN_EACH_BIT_FIELD + (
                    n_words_for_atoms * n_machine_vertices)) *
                BYTES_PER_WORD)
    return sdram


def get_estimated_sdram_for_key_region(app_graph, vertex):
    """ gets an estimate of the bitfield builder region

    :param app_graph: the app graph
    :param vertex: machine vertex
    :return: sdram needed
    """

    # basic sdram
    sdram = N_KEYS_DATA_SET_IN_WORDS * BYTES_PER_WORD
    for in_edge in app_graph.get_edges_ending_at_vertex(vertex):

        # Get the number of likely vertices
        edge_pre_vertex = in_edge.pre_vertex
        max_atoms = determine_max_atoms_for_vertex(edge_pre_vertex)
        if in_edge.pre_vertex.n_atoms < max_atoms:
            max_atoms = in_edge.pre_vertex.n_atoms
        n_edge_vertices = int(math.ceil(
            float(in_edge.pre_vertex.n_atoms) / float(max_atoms)))
        sdram += (n_edge_vertices * N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP *
                  BYTES_PER_WORD)
    return sdram


def _exact_sdram_for_bit_field_region(
        machine_graph, vertex, n_key_map):
    """ calculates the correct sdram for the bitfield region based off \
        the machine graph and graph mapper

    :param machine_graph: machine graph
    :param vertex: the machine vertex
    :param n_key_map: n keys map
    :return: sdram in bytes
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
    """ returns the sdram requirement for the builder region
    :return: returns the sdram requirement for the builder region
    """
    return N_REGIONS_ADDRESSES * BYTES_PER_WORD


def _exact_sdram_for_bit_field_key_region(machine_graph, vertex):
    """ calcs the exact sdram for the bitfield key region

    :param machine_graph: machine graph
    :param vertex: machine vertex
    :return: bytes
    """
    return (
               N_KEYS_DATA_SET_IN_WORDS +
               len(machine_graph.get_edges_ending_at_vertex(vertex)) *
               N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP) * BYTES_PER_WORD


def reserve_bit_field_regions(
        spec, machine_graph, n_key_map, vertex, bit_field_builder_region,
        bit_filter_region, bit_field_key_region):
    """ reserves the regions for the bitfields

    :param spec: dsg file
    :param machine_graph: machine graph
    :param n_key_map: map between partitions and n keys
    :param vertex: machine vertex
    :param bit_field_builder_region: region id for the builder region
    :param bit_filter_region: region id for the bitfield region
    :param bit_field_key_region: region id for the key map
    :rtype: None
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

    :param spec: data spec writer
    :param machine_vertex: machine vertex
    :param machine_graph: machine graph
    :param routing_info: keys
    :param n_key_map: map for edge to n keys
    :param bit_field_builder_region: the region id for the bitfield builder
    :param master_pop_region_id: the region id for the master pop table
    :param synaptic_matrix_region_id: the region id for the synaptic matrix
    :param direct_matrix_region_id: the region id for the direct matrix
    :param bit_field_region_id: the region id for the bit-fields
    :param bit_field_key_map_region_id: the region id for the key map
    :param structural_dynamics_region_id:  the region id for the structural
    :param has_structural_dynamics_region: \
        bool saying if the core has a has_structural_dynamics_region or not
    :rtype: None
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
    for in_coming_edge in machine_graph.get_edges_ending_at_vertex(
            machine_vertex):
        out_going_partition = \
            machine_graph.get_outgoing_partition_for_edge(in_coming_edge)
        spec.write_value(
            routing_info.get_first_key_from_partition(out_going_partition))
        spec.write_value(
            n_key_map.n_keys_for_partition(out_going_partition))

    # ensure if nothing else that n bitfields in bitfield region set to 0
    spec.switch_write_focus(bit_field_region_id)
    spec.write_value(0)
