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
import numpy
from pacman.utilities.constants import FULL_MASK
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_utilities.ordered_set import OrderedSet
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID

#: number of elements
FILTER_INFO_WORDS = 3  # n words, key, pointer to bitfield

#: n_filters, pointer for array
FILTER_HEADER_WORDS = 2

#: n elements in each key to n atoms map for bitfield (key, n atoms)
KEY_N_ATOM_MAP_WORDS = 2

#: the regions addresses needed (
#: pop table, synaptic matrix, direct matrix, bit_field, bit field builder,
#: bit_field_key, structural region)
N_REGIONS_ADDRESSES = 6

#: n key to n neurons maps size in words
N_KEYS_DATA_SET_IN_WORDS = 1

#: the number of bits in a word
# (WHY IS THIS NOT A CONSTANT SOMEWHERE!)
BIT_IN_A_WORD = 32.0


def get_estimated_sdram_for_bit_field_region(incoming_projections):
    """ estimates the SDRAM for the bit field region

    :param iterable(~spynnaker.pyNN.models.Projection) incoming_projections:
        The projections that target the vertex in question
    :return: the estimated number of bytes used by the bit field region
    :rtype: int
    """
    sdram = FILTER_HEADER_WORDS * BYTES_PER_WORD
    seen_app_edges = set()
    for proj in incoming_projections:
        app_edge = proj._projection_edge
        if app_edge not in seen_app_edges:
            seen_app_edges.add(app_edge)
            n_atoms = app_edge.pre_vertex.n_atoms
            n_words_for_atoms = int(math.ceil(n_atoms / BIT_IN_A_WORD))
            sdram += (FILTER_INFO_WORDS + n_words_for_atoms) * BYTES_PER_WORD
            # Also add for delay vertices if needed
            n_words_for_delays = int(math.ceil(
                n_atoms * app_edge.n_delay_stages / BIT_IN_A_WORD))
            sdram += (FILTER_INFO_WORDS + n_words_for_delays) * BYTES_PER_WORD
    return sdram


def get_estimated_sdram_for_key_region(incoming_projections):
    """ gets an estimate of the bitfield builder region

    :param iterable(~spynnaker.pyNN.models.Projection) incoming_projections:
        The projections that target the vertex in question
    :return: SDRAM needed
    :rtype: int
    """

    # basic sdram
    sdram = N_KEYS_DATA_SET_IN_WORDS * BYTES_PER_WORD
    seen_app_edges = set()
    for proj in incoming_projections:
        in_edge = proj._projection_edge
        if in_edge not in seen_app_edges:
            seen_app_edges.add(in_edge)
            sdram += KEY_N_ATOM_MAP_WORDS * BYTES_PER_WORD
            if in_edge.n_delay_stages:
                sdram += KEY_N_ATOM_MAP_WORDS * BYTES_PER_WORD

    return sdram


def exact_sdram_for_bit_field_builder_region():
    """ Gets the SDRAM requirement for the builder region

    :return: the SDRAM requirement for the builder region
    :rtype: int
    """
    return N_REGIONS_ADDRESSES * BYTES_PER_WORD


def get_bitfield_builder_data(
        master_pop_region_id, synaptic_matrix_region_id,
        direct_matrix_region_id, bit_field_region_id,
        bit_field_key_map_region_id, structural_dynamics_region_id,
        has_structural_dynamics_region):

    """ Get data for bit field region

    :param int master_pop_region_id: the region id for the master pop table
    :param int synaptic_matrix_region_id: the region id for the synaptic matrix
    :param int direct_matrix_region_id: the region id for the direct matrix
    :param int bit_field_region_id: the region id for the bit-fields
    :param int bit_field_key_map_region_id: the region id for the key map
    :param int structural_dynamics_region_id: the region id for the structural
    :param bool has_structural_dynamics_region:
        whether the core has a structural_dynamics region
    :rtype: ~numpy.ndarray
    """
    # save 4 bytes by making a key flag of full mask to avoid when not got
    # a structural
    if not has_structural_dynamics_region:
        struct_region = FULL_MASK
    else:
        struct_region = structural_dynamics_region_id

    return numpy.array([
        master_pop_region_id, synaptic_matrix_region_id,
        direct_matrix_region_id, bit_field_region_id,
        bit_field_key_map_region_id, struct_region], dtype="uint32")


def get_bitfield_key_map_data(incoming_projections, routing_info):
    """ Get data for the key map region

    :param list(~spynnaker.pyNN.models.Projection) incoming_projections:
        The projections to generate bitfields for
    :param ~pacman.model.routing_info.RoutingInfo routing_info: keys
    :rtype: ~numpy.ndarray
    """
    # Gather the source vertices that target this core
    sources = OrderedSet()
    for proj in incoming_projections:
        in_edge = proj._projection_edge
        if in_edge not in sources:
            key = routing_info.get_first_key_from_pre_vertex(
                in_edge.pre_vertex, SPIKE_PARTITION_ID)
            if key is not None:
                sources.add((key, in_edge.pre_vertex.n_atoms))

    key_map = numpy.array(
        [[key, n_atoms] for key, n_atoms in sources], dtype="uint32")

    # write n keys max atom map
    return numpy.concatenate(([len(sources)], numpy.ravel(key_map)))


def write_bitfield_init_data(
        spec, bit_field_builder_region, builder_data,
        bit_field_key_map_region, key_map_data, bit_field_region,
        n_bit_field_bytes, bit_field_builder_region_ref=None,
        bit_field_key_region_ref=None, bit_field_region_ref=None):
    """ writes the init data needed for the bitfield generator

    :param ~data_specification.DataSpecificationGenerator spec:
        data spec writer
    :param int bit_field_builder_region: the region id for the bitfield builder
    :param ~numpy.ndarray builder_data: Data for the builder region
    :param int bit_field_region_id: the region id for the bit-fields
    :param int bit_field_key_map_region_id: the region id for the key map
    """
    # reserve region for the bitfield builder
    spec.reserve_memory_region(
        region=bit_field_builder_region,
        size=len(builder_data) * BYTES_PER_WORD,
        label="bit field builder region",
        reference=bit_field_builder_region_ref)
    spec.switch_write_focus(bit_field_builder_region)
    spec.write_array(builder_data)

    # reserve memory region for the key region
    spec.reserve_memory_region(
        region=bit_field_key_map_region,
        size=len(key_map_data) * BYTES_PER_WORD,
        label="bit field key data",
        reference=bit_field_key_region_ref)
    spec.switch_write_focus(bit_field_key_map_region)
    spec.write_array(key_map_data)

    # reserve the final destination for the bitfields
    spec.reserve_memory_region(
        region=bit_field_region,
        size=n_bit_field_bytes,
        label="bit_field region",
        reference=bit_field_region_ref)
    # Ensure a 0 is written at least to indicate no bit fields
    spec.switch_write_focus(bit_field_region)
    spec.write_value(0)
