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
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_utilities.ordered_set import OrderedSet
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.data import SpynnakerDataView

#: number of elements
#  key, n atoms, atoms_per_core, pointer to bitfield
FILTER_INFO_WORDS = 4

#: n_filters, pointer for array
FILTER_HEADER_WORDS = 2

#: the number of bits in a word
# (WHY IS THIS NOT A CONSTANT SOMEWHERE!)
BIT_IN_A_WORD = 32.0


def get_sdram_for_bit_field_region(incoming_projections):
    """ the SDRAM for the bit field filter region

    :param iterable(~spynnaker.pyNN.models.Projection) incoming_projections:
        The projections that target the vertex in question
    :return: the estimated number of bytes used by the bit field region
    :rtype: int
    """
    sdram = FILTER_HEADER_WORDS * BYTES_PER_WORD
    seen_app_edges = set()
    for proj in incoming_projections:
        app_edge = proj._projection_edge  # pylint: disable=protected-access
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


def get_sdram_for_keys(incoming_projections):
    """ gets the space needed for keys

    :param iterable(~spynnaker.pyNN.models.Projection) incoming_projections:
        The projections that target the vertex in question
    :return: SDRAM needed
    :rtype: int
    """

    # basic sdram
    sdram = 0
    seen_app_edges = set()
    for proj in incoming_projections:
        in_edge = proj._projection_edge  # pylint: disable=protected-access
        if in_edge not in seen_app_edges:
            seen_app_edges.add(in_edge)
            sdram += BYTES_PER_WORD
            if in_edge.n_delay_stages:
                sdram += BYTES_PER_WORD

    return sdram


def get_bitfield_key_map_data(incoming_projections):
    """ Get data for the key map region

    :param list(~spynnaker.pyNN.models.Projection) incoming_projections:
        The projections to generate bitfields for
    :rtype: ~numpy.ndarray
    """
    # Gather the source vertices that target this core
    routing_infos = SpynnakerDataView.get_routing_infos()
    sources = OrderedSet()
    for proj in incoming_projections:
        in_edge = proj._projection_edge
        if in_edge not in sources:
            key = routing_infos.get_first_key_from_pre_vertex(
                in_edge.pre_vertex, SPIKE_PARTITION_ID)
            if key is not None:
                sources.add((key, in_edge.pre_vertex.n_atoms))

    if not sources:
        return numpy.array([], dtype="uint32")

    # Make keys and atoms, ordered by keys
    key_map = numpy.array(
        [[key, n_atoms] for key, n_atoms in sources], dtype="uint32")
    key_map = key_map[numpy.argsort(key_map[:, 0])]

    # get the number of atoms per item
    return key_map[:, 1]


def write_bitfield_init_data(
        spec, bit_field_region, n_bit_field_bytes, bit_field_region_ref=None):
    """ writes the init data needed for the bitfield generator

    :param ~data_specification.DataSpecificationGenerator spec:
        data spec writer
    :param int bit_field_region: the region id for the bit-field filters
    :param int n_bit_field_bytes: the size of the region
    :param int bit_field_region_ref: The reference to the region
    """
    # reserve the final destination for the bitfields
    spec.reserve_memory_region(
        region=bit_field_region, size=n_bit_field_bytes,
        label="bit_field region", reference=bit_field_region_ref)

    # Ensure a 0 is written at least to indicate no bit fields if not expanded
    spec.switch_write_focus(bit_field_region)
    spec.write_value(0)
