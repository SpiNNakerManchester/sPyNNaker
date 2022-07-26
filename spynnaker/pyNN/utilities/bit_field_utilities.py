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
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID

#: number of elements
#  key, n atoms, atoms_per_core, pointer to bitfield
ELEMENTS_USED_IN_EACH_BIT_FIELD = 4

#: n_filters, pointer for array
ELEMENTS_USED_IN_BIT_FIELD_HEADER = 2

#: n elements in each key to n atoms map for bitfield (key, n atoms,
#  core shift/n atoms per core (combined into a word))
N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP = 3

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
    sdram = ELEMENTS_USED_IN_BIT_FIELD_HEADER * BYTES_PER_WORD
    seen_app_edges = set()
    for proj in incoming_projections:
        app_edge = proj._projection_edge  # pylint: disable=protected-access
        if app_edge not in seen_app_edges:
            seen_app_edges.add(app_edge)

            n_words_for_atoms = int(math.ceil(
                app_edge.pre_vertex.n_atoms / BIT_IN_A_WORD))
            sdram += (
                (ELEMENTS_USED_IN_EACH_BIT_FIELD + n_words_for_atoms) *
                BYTES_PER_WORD)
            # Also add for delay vertices if needed
            n_words_for_delays = int(math.ceil(
                (app_edge.pre_vertex.n_atoms * app_edge.n_delay_stages) /
                BIT_IN_A_WORD))
            sdram += (
                (ELEMENTS_USED_IN_EACH_BIT_FIELD + n_words_for_delays) *
                BYTES_PER_WORD)
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
        in_edge = proj._projection_edge  # pylint: disable=protected-access
        if in_edge not in seen_app_edges:
            seen_app_edges.add(in_edge)

            sdram += N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP * BYTES_PER_WORD
            if in_edge.n_delay_stages:
                sdram += N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP * BYTES_PER_WORD

    return sdram


def exact_sdram_for_bit_field_builder_region():
    """ Gets the SDRAM requirement for the builder region

    :return: the SDRAM requirement for the builder region
    :rtype: int
    """
    return N_REGIONS_ADDRESSES * BYTES_PER_WORD


def reserve_bit_field_regions(
        spec, incoming_projections, bit_field_builder_region,
        bit_filter_region, bit_field_key_region,
        bit_field_builder_region_ref=None, bit_filter_region_ref=None,
        bit_field_key_region_ref=None):
    """ reserves the regions for the bitfields

    :param ~data_specification.DataSpecificationGenerator spec:
        dsg spec writer
    :param list(~spynnaker.pyNN.models.Projection) incoming_projections:
        The projections to generate bitfields for
    :param int bit_field_builder_region: region id for the builder region
    :param int bit_filter_region: region id for the bitfield region
    :param int bit_field_key_region: region id for the key map
    :param bit_field_builder_region_ref:
        Reference to give the region, or None if not referencable
    :type bit_field_builder_region_ref: int or None
    :param bit_filter_region_ref:
        Reference to give the region, or None if not referencable
    :type bit_filter_region_ref: int or None
    :param bit_field_key_region_ref:
        Reference to give the region, or None if not referencable
    :type bit_field_key_region_ref: int or None
    """

    # reserve the final destination for the bitfields
    spec.reserve_memory_region(
        region=bit_filter_region,
        size=get_estimated_sdram_for_bit_field_region(incoming_projections),
        label="bit_field region",
        reference=bit_filter_region_ref)

    # reserve region for the bitfield builder
    spec.reserve_memory_region(
        region=bit_field_builder_region,
        size=exact_sdram_for_bit_field_builder_region(),
        label="bit field builder region",
        reference=bit_field_builder_region_ref)

    # reserve memory region for the key region
    spec.reserve_memory_region(
        region=bit_field_key_region,
        size=get_estimated_sdram_for_key_region(incoming_projections),
        label="bit field key data",
        reference=bit_field_key_region_ref)


def write_bitfield_init_data(
        spec, incoming_projections, vertex_slice,
        bit_field_builder_region, master_pop_region_id,
        synaptic_matrix_region_id, direct_matrix_region_id,
        bit_field_region_id, bit_field_key_map_region_id,
        structural_dynamics_region_id, has_structural_dynamics_region):
    """ writes the init data needed for the bitfield generator

    :param ~data_specification.DataSpecificationGenerator spec:
        data spec writer
    :param list(~spynnaker.pyNN.models.Projection) incoming_projections:
        The projections to generate bitfields for
    :param ~pacman.model.graphs.common.slice vertex_slice:
        The slice of the target vertex
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

    # Gather the source vertices that target this core
    sources = list()
    seen_app_edges = set()
    for proj in incoming_projections:
        in_edge = proj._projection_edge  # pylint: disable=protected-access
        if in_edge not in seen_app_edges:
            seen_app_edges.add(in_edge)
            if hasattr(in_edge.post_vertex.splitter,
                       "is_direct_poisson_source"):
                # pylint: disable=protected-access
                s_info = proj._synapse_information
                if in_edge.post_vertex.splitter.is_direct_poisson_source(
                        in_edge.pre_vertex, s_info.connector,
                        s_info.synapse_dynamics):
                    continue
            n_atoms_per_core = next(iter(
                in_edge.pre_vertex.machine_vertices)).vertex_slice.n_atoms
            sources.append(
                (in_edge.pre_vertex, in_edge.pre_vertex.n_atoms,
                 n_atoms_per_core))
            delay_edge = in_edge.delay_edge
            if delay_edge is not None:
                sources.append(
                    (delay_edge.pre_vertex,
                     in_edge.pre_vertex.n_atoms * in_edge.n_delay_stages,
                     n_atoms_per_core * in_edge.n_delay_stages))

    # write n keys max atom map
    spec.write_value(len(sources))

    # load in key to max atoms map
    routing_info = SpynnakerDataView.get_routing_infos()
    for source_vertex, n_atoms, n_atoms_per_core in sources:
        r_info = routing_info.get_routing_info_from_pre_vertex(
            source_vertex, SPIKE_PARTITION_ID)
        spec.write_value(r_info.first_key)
        spec.write_value(n_atoms)
        if len(source_vertex.machine_vertices) > 1:
            spec.write_value(r_info.n_bits_atoms | (n_atoms_per_core << 5))
        else:
            spec.write_value(0)

    # ensure if nothing else that n bitfields in bitfield region set to 0
    spec.switch_write_focus(bit_field_region_id)
    spec.write_value(0)
