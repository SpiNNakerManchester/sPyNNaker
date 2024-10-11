# Copyright (c) 2019 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations
import math
from typing import Iterable, Optional, TYPE_CHECKING, Tuple

import numpy
from numpy import uint32
from numpy.typing import NDArray

from spinn_front_end_common.interface.ds import DataSpecificationBase
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

from spynnaker.pyNN.data import SpynnakerDataView

if TYPE_CHECKING:
    from spynnaker.pyNN.models.projection import Projection
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge)

#: number of elements
#  key, n atoms, atoms_per_core, pointer to bitfield
FILTER_INFO_WORDS = 4

#: n_filters, pointer for array
FILTER_HEADER_WORDS = 2

#: the number of bits in a word
# (WHY IS THIS NOT A CONSTANT SOMEWHERE!)
BIT_IN_A_WORD = 32.0


def _unique_edges(projections: Iterable[Projection]) -> Iterable[
        Tuple[ProjectionApplicationEdge, str]]:
    """
    Get the unique application edges of a collection of projections.

    :param iterable(~spynnaker.pyNN.models.projection.Projection) projections:
        The projections to examine.
    :rtype: iterable(tuple(ProjectionApplicationEdge, str))
    """
    seen_edges = set()
    for proj in projections:
        # pylint: disable=protected-access
        edge = proj._projection_edge
        synapse_info = proj._synapse_information
        # If there are no outgoing vertices, we should discount this edge
        if not edge.pre_vertex.splitter.get_out_going_vertices(
                synapse_info.partition_id):
            continue
        if (edge, synapse_info.partition_id) not in seen_edges:
            seen_edges.add((edge, synapse_info.partition_id))
            yield edge, synapse_info.partition_id


def get_sdram_for_bit_field_region(
        incoming_projections: Iterable[Projection]) -> int:
    """
    The SDRAM for the bit field filter region.

    :param incoming_projections:
        The projections that target the vertex in question
    :type incoming_projections:
        iterable(~spynnaker.pyNN.models.projection.Projection)
    :return: the estimated number of bytes used by the bit field region
    :rtype: int
    """
    sdram = FILTER_HEADER_WORDS * BYTES_PER_WORD
    for in_edge, _part_id in _unique_edges(incoming_projections):
        n_atoms = in_edge.pre_vertex.n_atoms
        n_words_for_atoms = int(math.ceil(n_atoms / BIT_IN_A_WORD))
        sdram += (FILTER_INFO_WORDS + n_words_for_atoms) * BYTES_PER_WORD
        # Also add for delay vertices if needed
        n_words_for_delays = int(math.ceil(
            n_atoms * in_edge.n_delay_stages / BIT_IN_A_WORD))
        sdram += (FILTER_INFO_WORDS + n_words_for_delays) * BYTES_PER_WORD
    return sdram


def get_sdram_for_keys(incoming_projections: Iterable[Projection]) -> int:
    """
    Gets the space needed for keys.

    :param incoming_projections:
        The projections that target the vertex in question
    :type incoming_projections:
        iterable(~spynnaker.pyNN.models.projection.Projection)
    :return: SDRAM needed
    :rtype: int
    """
    # basic sdram
    sdram = 0
    for in_edge, _part_id in _unique_edges(incoming_projections):
        sdram += BYTES_PER_WORD
        if in_edge.n_delay_stages:
            sdram += BYTES_PER_WORD
    return sdram


def get_bitfield_key_map_data(
        incoming_projections: Iterable[Projection]) -> NDArray[uint32]:
    """
    Get data for the key map region.

    :param incoming_projections:
        The projections to generate bitfields for
    :type incoming_projections:
        iterable(~spynnaker.pyNN.models.projection.Projection)
    :rtype: ~numpy.ndarray
    """
    # Gather the source vertices that target this core
    routing_infos = SpynnakerDataView.get_routing_infos()
    sources = []
    for in_edge, part_id in _unique_edges(incoming_projections):
        key = routing_infos.get_safe_first_key_from_pre_vertex(
            in_edge.pre_vertex, part_id)
        sources.append([key, in_edge.pre_vertex.n_atoms])
        if in_edge.delay_edge is not None:
            delay_key = routing_infos.get_safe_first_key_from_pre_vertex(
                in_edge.delay_edge.pre_vertex, part_id)
            n_delay_atoms = (
                in_edge.pre_vertex.n_atoms * in_edge.n_delay_stages)
            sources.append([delay_key, n_delay_atoms])

    if not sources:
        return numpy.array([], dtype=uint32)

    # Make keys and atoms, ordered by keys
    key_map = numpy.array(sources, dtype=uint32)
    key_map = key_map[numpy.argsort(key_map[:, 0])]

    # get the number of atoms per item
    return key_map[:, 1]


def write_bitfield_init_data(
        spec: DataSpecificationBase, bit_field_region: int,
        n_bit_field_bytes: int, bit_field_region_ref: Optional[int] = None):
    """
    Writes the initialisation data needed for the bitfield generator.

    :param ~data_specification.DataSpecificationGenerator spec:
        data specification writer
    :param int bit_field_region: the region ID for the bit-field filters
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
