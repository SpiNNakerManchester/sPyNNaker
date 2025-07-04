# Copyright (c) 2015 The University of Manchester
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
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union, TYPE_CHECKING

import numpy
from numpy import integer, uint32
from numpy.typing import NDArray

from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.common import Slice

from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector)
from spynnaker.pyNN.exceptions import SynapseRowTooBigException
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractStaticSynapseDynamics, AbstractSDRAMSynapseDynamics,
    AbstractPlasticSynapseDynamics)
from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
    NUMPY_CONNECTORS_DTYPE, ConnectionsArray)
from spynnaker.pyNN.types import WeightScales

from .master_pop_table import MasterPopTableAsBinarySearch

if TYPE_CHECKING:
    from typing_extensions import TypeAlias
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)
    from spynnaker.pyNN.models.neuron.synapse_dynamics import (
        AbstractSynapseDynamics)
    _RowData: TypeAlias = numpy.ndarray  # 2D

_N_HEADER_WORDS = 3
# There are 16 slots, one per time step
_STD_DELAY_SLOTS = 16


@dataclass(frozen=True)
class MaxRowInfo(object):
    """
    Information about the maximums for rows in a synaptic matrix.
    """

    #: Maximum number of synapses in a row of the undelayed matrix.
    undelayed_max_n_synapses: int

    #: Maximum number of synapses in a row of the delayed matrix
    delayed_max_n_synapses: int

    #: Maximum number of bytes, including headers, in a row of the
    #: undelayed matrix, or 0 if no synapses.
    undelayed_max_bytes: int

    #: Maximum number of bytes, including headers, in a row of the
    #: delayed matrix, or 0 if no synapses.
    delayed_max_bytes: int

    #: Maximum number of words, excluding headers, in a row of the
    #: undelayed matrix.
    undelayed_max_words: int

    #: Maximum number of words, excluding headers, in a row of the
    #: delayed matrix.
    delayed_max_words: int


def get_maximum_delay_supported_in_ms(
        post_vertex_max_delay_ticks: int) -> float:
    """
    Get the maximum delay supported by the synapse representation
    before extensions are required.

    :param post_vertex_max_delay_ticks: post vertex max delay
    :return: Maximum delay, in milliseconds.
    """
    return (post_vertex_max_delay_ticks *
            SpynnakerDataView.get_simulation_time_step_ms())


def get_max_row_info(
        synapse_info: SynapseInformation, n_post_atoms: int,
        n_delay_stages: int, in_edge: ProjectionApplicationEdge) -> MaxRowInfo:
    """
    Get the information about the maximum lengths of delayed and
    undelayed rows in bytes (including header), words (without header)
    and number of synapses.

    :param synapse_info:
        The synapse information to get the row data for
    :param n_post_atoms:
        The number of post atoms to get the maximum for
    :param n_delay_stages:
        The number of delay stages on the edge
    :param in_edge:
        The incoming edge on which the synapse information is held
    :raises SynapseRowTooBigException:
        If the synapse information can't be represented
    """
    max_delay_supported = get_maximum_delay_supported_in_ms(
        in_edge.post_vertex.splitter.max_support_delay())
    max_delay = max_delay_supported * (n_delay_stages + 1)
    pad_to_length: Optional[int] = None
    if isinstance(synapse_info.synapse_dynamics, AbstractSDRAMSynapseDynamics):
        pad_to_length = synapse_info.synapse_dynamics.pad_to_length

    # delay point where delay extensions start
    min_delay_for_delay_extension = (
        max_delay_supported + numpy.finfo(numpy.double).tiny).item()

    # row length for the non-delayed synaptic matrix
    max_undelayed_n_synapses = synapse_info.connector \
        .get_n_connections_from_pre_vertex_maximum(
            n_post_atoms, synapse_info, 0, max_delay_supported)
    if pad_to_length is not None:
        max_undelayed_n_synapses = max(
            pad_to_length, max_undelayed_n_synapses)

    # determine the max row length in the delay extension
    max_delayed_n_synapses = 0
    if n_delay_stages > 0:
        max_delayed_n_synapses = synapse_info.connector \
            .get_n_connections_from_pre_vertex_maximum(
                n_post_atoms, synapse_info,
                min_delay_for_delay_extension, max_delay)
        if pad_to_length is not None:
            max_delayed_n_synapses = max(
                pad_to_length, max_delayed_n_synapses)

    # Get the row sizes
    dynamics = synapse_info.synapse_dynamics
    if isinstance(dynamics, AbstractStaticSynapseDynamics):
        undelayed_n_words = dynamics.get_n_words_for_static_connections(
            max_undelayed_n_synapses)
        delayed_n_words = dynamics.get_n_words_for_static_connections(
            max_delayed_n_synapses)
    elif isinstance(dynamics, AbstractPlasticSynapseDynamics):
        undelayed_n_words = dynamics.get_n_words_for_plastic_connections(
            max_undelayed_n_synapses)
        delayed_n_words = dynamics.get_n_words_for_plastic_connections(
            max_delayed_n_synapses)
    else:
        raise TypeError(f"{dynamics=} has an unexpected type {type(dynamics)}")

    # Adjust for the allowed row lengths from the population table
    undelayed_max_n_words = _get_allowed_row_length(
        undelayed_n_words, dynamics, in_edge,  max_undelayed_n_synapses)
    delayed_max_n_words = _get_allowed_row_length(
        delayed_n_words, dynamics, in_edge, max_delayed_n_synapses)

    undelayed_max_bytes = 0
    if undelayed_max_n_words > 0:
        undelayed_max_bytes = (
            undelayed_max_n_words + _N_HEADER_WORDS) * BYTES_PER_WORD
    delayed_max_bytes = 0
    if delayed_max_n_words > 0:
        delayed_max_bytes = (
            delayed_max_n_words + _N_HEADER_WORDS) * BYTES_PER_WORD

    return MaxRowInfo(
        max_undelayed_n_synapses, max_delayed_n_synapses,
        undelayed_max_bytes, delayed_max_bytes,
        undelayed_max_n_words, delayed_max_n_words)


def _get_allowed_row_length(
        n_words: int, dynamics: AbstractSynapseDynamics,
        in_edge: ProjectionApplicationEdge, n_synapses: int) -> int:
    """
    Get the allowed row length in words in the population table for a
    desired row length in words.

    :param n_words: The number of words in the row
    :param dynamics: The synapse dynamics used
    :param in_edge: The incoming edge
    :param n_synapses: The number of synapses for the number of words
    :raises SynapseRowTooBigException:
        If the given row is too big; the exception will detail the maximum
        number of synapses that are supported.
    """
    if n_words == 0:
        return 0
    try:
        return MasterPopTableAsBinarySearch.get_allowed_row_length(n_words)
    except SynapseRowTooBigException as e:
        # Find the number of synapses available for the maximum population
        # table size, as extracted from the exception
        if isinstance(dynamics, AbstractSDRAMSynapseDynamics):
            max_synapses = dynamics.get_max_synapses(e.max_size)
            raise SynapseRowTooBigException(
                max_synapses,
                f"The connection between {in_edge.pre_vertex} and "
                f"{in_edge.post_vertex} has more synapses ({n_synapses}) than "
                "can currently be supported on this implementation of PyNN "
                f"({max_synapses} for this connection type). "
                "Please reduce the size of the target population, or reduce "
                "the number of neurons per core.") from e
        # Ugh!
        raise


def get_synapses(
        connections: ConnectionsArray, synapse_info: SynapseInformation,
        n_delay_stages: int, n_synapse_types: int,
        weight_scales: WeightScales, app_edge: ProjectionApplicationEdge,
        max_row_info: MaxRowInfo, gen_undelayed: bool, gen_delayed: bool,
        max_atoms_per_core: int) -> Tuple[_RowData, _RowData]:
    """
    Get the synapses as an array of words for non-delayed synapses and
    an array of words for delayed synapses. This is used to prepare
    information for *deployment to SpiNNaker*.

    :param connections:
        The connections to get the synapses from
    :param synapse_info:
        The synapse information to convert to synapses
    :param n_delay_stages:
        The number of delay stages in total to be represented
    :param n_synapse_types:
        The number of synapse types in total to be represented
    :param weight_scales: The scaling of the weights for each synapse type
    :param app_edge:
        The incoming machine edge that the synapses are on
    :param max_row_info:
        The maximum row information for the synapses
    :param gen_undelayed:
        Whether to generate undelayed data
    :param gen_delayed:
        Whether to generate delayed data
    :param max_atoms_per_core:
        The maximum number of atoms on a core
    :return:
        (``row_data``, ``delayed_row_data``) where:

        * ``row_data`` is the undelayed connectivity data arranged into a
            row per source, each row the same length
        * ``delayed_row_data`` is the delayed connectivity data arranged
            into a row per source per delay stage, each row the same length
    """
    # Get delays in timesteps
    max_delay = app_edge.post_vertex.splitter.max_support_delay()

    # Convert delays to timesteps
    connections["delay"] = numpy.rint(
        connections["delay"] *
        SpynnakerDataView.get_simulation_time_step_per_ms())

    # Scale weights
    if not synapse_info.synapse_type_from_dynamics:
        connections["weight"] = (connections["weight"] * weight_scales[
            synapse_info.synapse_type])

    # Split the connections up based on the delays
    if max_delay is not None:
        plastic_delay_mask = (connections["delay"] <= max_delay)
        undelayed_connections = connections[numpy.where(plastic_delay_mask)]
        delayed_connections = connections[numpy.where(~plastic_delay_mask)]
    else:
        undelayed_connections = connections
        delayed_connections = numpy.zeros(
            0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

    # Get the data for the connections
    row_data = numpy.zeros(0, dtype=uint32)
    if gen_undelayed and max_row_info.undelayed_max_n_synapses:
        # Get which row each connection will go into
        undelayed_row_indices = undelayed_connections["source"]
        row_data = _get_row_data(
            undelayed_connections, undelayed_row_indices,
            app_edge.pre_vertex.n_atoms, n_synapse_types,
            synapse_info.synapse_dynamics,
            max_row_info.undelayed_max_n_synapses,
            max_row_info.undelayed_max_words, max_atoms_per_core)
        del undelayed_row_indices
    del undelayed_connections

    # Get the data for the delayed connections
    delayed_row_data = numpy.zeros(0, dtype=uint32)
    if gen_delayed and max_row_info.delayed_max_n_synapses:
        # Get the delay stages and which row each delayed connection will
        # go into
        stages = numpy.floor((numpy.round(
            delayed_connections["delay"] - 1.0)) / max_delay).astype(uint32)
        delayed_cores = delayed_connections["source"] // max_atoms_per_core
        local_sources = delayed_connections["source"] - (
            delayed_cores * max_atoms_per_core)
        delay_atoms_per_core = max_atoms_per_core * n_delay_stages
        delayed_pre_cores = delayed_cores * delay_atoms_per_core
        local_index = ((stages - 1) * max_atoms_per_core) + local_sources
        delayed_row_indices = delayed_pre_cores + local_index
        delayed_connections["delay"] -= max_delay * stages

        # Get the data
        delayed_row_data = _get_row_data(
            delayed_connections, delayed_row_indices,
            app_edge.pre_vertex.n_atoms * n_delay_stages,
            n_synapse_types, synapse_info.synapse_dynamics,
            max_row_info.delayed_max_n_synapses,
            max_row_info.delayed_max_words, max_atoms_per_core)
        del delayed_row_indices
    del delayed_connections

    return row_data, delayed_row_data


def _get_row_data(
        connections: ConnectionsArray, row_indices: NDArray[numpy.integer],
        n_rows: int, n_synapse_types: int,
        synapse_dynamics: AbstractSynapseDynamics, max_row_n_synapses: int,
        max_row_n_words: int, max_atoms_per_core: int) -> _RowData:
    """
    :param connections:
        The connections to convert; the dtype is
        AbstractConnector.NUMPY_SYNAPSES_DTYPE
    :param row_indices:
        The row into which each connection should go; same length as
        connections
    :param n_rows: The total number of rows
    :param n_synapse_types: The number of synapse types allowed
    :param synapse_dynamics:
        The synapse dynamics of the synapses
    :param max_row_n_synapses: The maximum number of synapses in a row
    :param max_row_n_words: The maximum number of words in a row
    :param max_atoms_per_core: The maximum number of atoms per core
    """
    fp_data: Union[NDArray[uint32], List[NDArray[uint32]]]
    pp_data: Union[NDArray[uint32], List[NDArray[uint32]]]
    if isinstance(synapse_dynamics, AbstractStaticSynapseDynamics):
        # Get the static data
        ff_data, ff_size = synapse_dynamics.get_static_synaptic_data(
            connections, row_indices, n_rows, n_synapse_types,
            max_row_n_synapses, max_atoms_per_core)

        # Blank the plastic data
        fp_data = numpy.zeros((n_rows, 0), dtype=uint32)
        pp_data = numpy.zeros((n_rows, 0), dtype=uint32)
        fp_size:  NDArray[uint32]
        fp_size = numpy.zeros((n_rows, 1), dtype=uint32)
        pp_size:  NDArray[uint32]
        pp_size = numpy.zeros((n_rows, 1), dtype=uint32)
    else:
        assert isinstance(synapse_dynamics, AbstractPlasticSynapseDynamics)
        # Blank the static data
        ff_data = [numpy.zeros(0, dtype=uint32) for _ in range(n_rows)]
        ff_size = numpy.zeros((n_rows, 1), dtype=uint32)

        # Get the plastic data
        fp_data, pp_data, fp_size, pp_size = \
            synapse_dynamics.get_plastic_synaptic_data(
                connections, row_indices, n_rows, n_synapse_types,
                max_row_n_synapses, max_atoms_per_core)

    # Add some padding
    row_lengths = [
        pp_data[i].size + fp_data[i].size + ff_data[i].size
        for i in range(n_rows)]
    padding = [
        numpy.zeros(max_row_n_words - row_length, dtype=uint32)
        for row_length in row_lengths]

    # Join the bits into rows
    rows = [numpy.concatenate(items) for items in zip(
        pp_size, pp_data, ff_size, fp_size, ff_data, fp_data, padding)]
    row_data = numpy.concatenate(rows)

    # Return the data
    return row_data


def convert_to_connections(
        synapse_info: SynapseInformation, post_vertex_slice: Slice,
        n_pre_atoms: int, max_row_length: int, n_synapse_types: int,
        weight_scales: WeightScales, data: Union[bytes, NDArray, None],
        delayed: bool, post_vertex_max_delay_ticks: int,
        max_atoms_per_core: int) -> ConnectionsArray:
    """
    Read the synapses for a given projection synapse information
    object out of the given data and convert to connection data

    :param synapse_info:
        The synapse information of the synapses
    :param n_pre_atoms: The number of atoms in the pre-vertex
    :param post_vertex_slice:
        The slice of the target neurons of the synapses in the data
    :param max_row_length:
        The length of each row in the data
    :param n_synapse_types:
        The number of synapse types in total
    :param weight_scales:
        The weight scaling of each synapse type
    :param data:
        The raw data containing the synapses
    :param delayed:
        True if the data should be considered delayed
    :param post_vertex_max_delay_ticks:
        The maximum delayed ticks supported from post vertex
    :param max_atoms_per_core:
        The maximum number of atoms on a core
    :return: The connections read from the data; the dtype is
        :py:const:`~.NUMPY_CONNECTORS_DTYPE`
    """
    # If there is no data, return nothing
    if data is None or len(data) == 0:
        return numpy.zeros(0, dtype=NUMPY_CONNECTORS_DTYPE)

    # Translate the data into rows
    row_data = numpy.frombuffer(data, dtype="<u4").reshape(
        -1, (max_row_length + _N_HEADER_WORDS))

    dynamics = synapse_info.synapse_dynamics
    if isinstance(dynamics, AbstractStaticSynapseDynamics):
        # Read static data
        connections = _read_static_data(
            dynamics, n_pre_atoms, n_synapse_types, row_data, delayed,
            post_vertex_max_delay_ticks, max_atoms_per_core)
    elif isinstance(dynamics, AbstractPlasticSynapseDynamics):
        # Read plastic data
        connections = _read_plastic_data(
            dynamics, n_pre_atoms, n_synapse_types, row_data, delayed,
            post_vertex_max_delay_ticks, max_atoms_per_core)
    else:
        raise TypeError(f"{dynamics=} has unexpected type {type(dynamics)}")

    # There might still be no connections if the row was all padding
    if not connections.size:
        return numpy.zeros(0, dtype=NUMPY_CONNECTORS_DTYPE)

    # Convert 0 delays to max delays
    connections["delay"][connections["delay"] == 0] = (
        post_vertex_max_delay_ticks)

    connections = __convert_sources_and_targets(
        connections, synapse_info.pre_vertex, post_vertex_slice)

    # Return the connections after appropriate scaling
    return _rescale_connections(connections, weight_scales, synapse_info)


def read_all_synapses(
        data: NDArray[uint32], delayed_data: NDArray[uint32],
        synapse_info: SynapseInformation, n_synapse_types: int,
        weight_scales: WeightScales, post_vertex_slice: Slice,
        n_pre_atoms: int, post_vertex_max_delay_ticks: int,
        max_row_info: MaxRowInfo, max_atoms_per_core: int
        ) -> ConnectionsArray:
    """
    Read the synapses for a given projection synapse information
    object out of the given delayed and undelayed data.

    :param data:
        The raw data containing the undelayed synapses
    :param delayed_data:
        The raw data containing the delayed synapses
    :param synapse_info:
        The synapse info that generated the synapses
    :param n_synapse_types:
        The total number of synapse types available
    :param weight_scales:
        A weight scale for each synapse type
    :param n_pre_atoms: The number of atoms in the pre-vertex
    :param post_vertex_slice:
        The slice of the post-vertex to read the synapses for
    :param post_vertex_max_delay_ticks:
            max delayed ticks supported from post vertex
    :param max_row_info:
        The maximum information for each of the rows
    :param max_atoms_per_core:
        The maximum number of atoms on a core
    :return: The connections read from the data; the dtype is
        :py:const:`~.NUMPY_CONNECTORS_DTYPE`
    """
    connections: List[ConnectionsArray] = []
    max_row_length = max_row_info.undelayed_max_words
    delayed_max_row_length = max_row_info.delayed_max_words
    connections.append(convert_to_connections(
        synapse_info, post_vertex_slice, n_pre_atoms, max_row_length,
        n_synapse_types, weight_scales, data, False,
        post_vertex_max_delay_ticks, max_atoms_per_core))
    connections.append(convert_to_connections(
        synapse_info, post_vertex_slice, n_pre_atoms,
        delayed_max_row_length, n_synapse_types, weight_scales, delayed_data,
        True, post_vertex_max_delay_ticks, max_atoms_per_core))

    # Join the connections into a single list and return it
    return numpy.concatenate(connections)


def _parse_static_data(
        row_data: _RowData,
        dynamics: AbstractStaticSynapseDynamics) -> Tuple[
            NDArray[numpy.integer], List[_RowData]]:
    """
    Parse static synaptic data.

    :param row_data: The raw row data
    :param dynamics:
        The synapse dynamics that can decode the rows
    :return: A tuple of the recorded length of each row and the row data
        organised into rows
    """
    n_rows = row_data.shape[0]
    ff_size = row_data[:, 1]
    ff_words = dynamics.get_n_static_words_per_row(ff_size)
    ff_start = _N_HEADER_WORDS
    ff_end = ff_start + ff_words
    return (
        ff_size,
        [row_data[row, ff_start:ff_end[row]] for row in range(n_rows)])


def _read_static_data(
        dynamics: AbstractStaticSynapseDynamics, n_pre_atoms: int,
        n_synapse_types: int, row_data: _RowData, delayed: bool,
        post_vertex_max_delay_ticks: int,
        max_atoms_per_core: int) -> ConnectionsArray:
    """
    Read static data from row data.

    :param dynamics:
        The synapse dynamics that generated the data
    :param n_pre_atoms: The number of atoms on the pre-vertex
    :param n_synapse_types:
        The number of synapse types available
    :param row_data:
        The raw row data to read
    :param delayed: True if data should be considered delayed
    :param post_vertex_max_delay_ticks: post vertex delay maximum
    :param max_atoms_per_core: The maximum number of atoms on a core
    :return: the connections read with dtype
        :py:const:`~.NUMPY_CONNECTORS_DTYPE`
    """
    if row_data is None or not row_data.size:
        return numpy.zeros(0, dtype=NUMPY_CONNECTORS_DTYPE)
    ff_size, ff_data = _parse_static_data(row_data, dynamics)
    connections = dynamics.read_static_synaptic_data(
        n_synapse_types, ff_size, ff_data, max_atoms_per_core)
    if delayed:
        n_synapses = dynamics.get_n_synapses_in_rows(ff_size)
        connections = _convert_delayed_data(
            n_synapses, n_pre_atoms, connections,
            post_vertex_max_delay_ticks)
    return connections


def _parse_plastic_data(
        row_data: _RowData,
        dynamics: AbstractPlasticSynapseDynamics) -> Tuple[
            NDArray[uint32], List[_RowData], NDArray[uint32], List[_RowData]]:
    """
    Parse plastic synapses from raw row data.

    :param row_data: The raw data to parse
    :param dynamics:
        The dynamics that generated the data
    :return: A tuple of the recorded length of the plastic-plastic data in
        each row; the plastic-plastic data organised into rows; the
        recorded length of the static-plastic data in each row; and the
        static-plastic data organised into rows
    """
    n_rows = row_data.shape[0]
    pp_size = row_data[:, 0]
    pp_words = dynamics.get_n_plastic_plastic_words_per_row(pp_size)
    fp_size = row_data[numpy.arange(n_rows), pp_words + 2]
    fp_words = dynamics.get_n_fixed_plastic_words_per_row(fp_size)
    fp_start = pp_size + _N_HEADER_WORDS
    fp_end = fp_start + fp_words
    row_ids = range(n_rows)
    return (
        pp_size,
        [row_data[row, 1:pp_words[row] + 1] for row in row_ids],
        fp_size,
        [row_data[row, fp_start[row]:fp_end[row]] for row in row_ids])


def _read_plastic_data(
        dynamics: AbstractPlasticSynapseDynamics, n_pre_atoms: int,
        n_synapse_types: int, row_data: Optional[_RowData], delayed: bool,
        post_vertex_max_delay_ticks: int,
        max_atoms_per_core: int) -> ConnectionsArray:
    """
    Read plastic data from raw data.

    :param dynamics:
        The synapse dynamics that generated the data
    :param n_pre_atoms: The number of atoms in the pre-vertex
    :param n_synapse_types:
        The number of synapse types available
    :param row_data:
        The raw row data to read
    :param delayed: True if data should be considered delayed
    :param post_vertex_max_delay_ticks: post vertex delay maximum
    :param max_atoms_per_core: The maximum number of atoms on a core
    :return: the connections read with dtype
        :py:const:`~.NUMPY_CONNECTORS_DTYPE`
    """
    if row_data is None or not row_data.size:
        return numpy.zeros(0, dtype=NUMPY_CONNECTORS_DTYPE)
    pp_size, pp_data, fp_size, fp_data = _parse_plastic_data(
        row_data, dynamics)
    connections = dynamics.read_plastic_synaptic_data(
        n_synapse_types, pp_size, pp_data, fp_size, fp_data,
        max_atoms_per_core)

    if delayed:
        n_synapses = dynamics.get_n_synapses_in_rows(pp_size, fp_size)
        connections = _convert_delayed_data(
            n_synapses, n_pre_atoms, connections,
            post_vertex_max_delay_ticks)
    return connections


def _rescale_connections(
        connections: ConnectionsArray, weight_scales: WeightScales,
        synapse_info: SynapseInformation) -> ConnectionsArray:
    """
    Scale the connection data into machine values.

    :param connections: The connections to be rescaled
    :param weight_scales: The weight scale of each synapse type
    :param synapse_info: The synapse information of the connections
    """
    # Return the delays values to milliseconds
    connections["delay"] /= SpynnakerDataView.get_simulation_time_step_per_ms()
    # Undo the weight scaling
    connections["weight"] /= weight_scales[synapse_info.synapse_type]
    return connections


def _convert_delayed_data(
        n_synapses: NDArray[integer], n_pre_atoms: int,
        delayed_connections: ConnectionsArray,
        post_vertex_max_delay_ticks: int) -> ConnectionsArray:
    """
    Take the delayed_connections and convert the source ids and delay
    values back to global values.

    :param n_synapses: The number of synapses in each row
    :param n_pre_atoms: number of atoms in the pre-vertex
    :param delayed_connections:
        The connections to convert of dtype
        :py:const:`~.NUMPY_CONNECTORS_DTYPE`
    :param post_vertex_max_delay_ticks: post vertex delay maximum
    :return: The converted connection with the same dtype
    """
    # Work out the delay stage of each row; rows are the all the rows
    # from the first delay stage, then all from the second stage and so on
    synapse_ids = range(len(n_synapses))
    row_stage = numpy.array([
        i // n_pre_atoms
        for i in synapse_ids], dtype=uint32)
    # Work out the delay for each stage
    row_min_delay = (row_stage + 1) * post_vertex_max_delay_ticks
    # Repeat the delay for all connections in the same row
    connection_min_delay = numpy.concatenate([
        numpy.repeat(row_min_delay[i], n_synapses[i])
        for i in synapse_ids])
    # Repeat the "extra" source id for all connections in the same row;
    # this converts the row id back to a source neuron id
    connection_source_extra = numpy.concatenate([
        numpy.repeat(
            row_stage[i] * uint32(n_pre_atoms),
            n_synapses[i])
        for i in synapse_ids])
    # Do the conversions
    delayed_connections["source"] -= connection_source_extra
    delayed_connections["delay"] += connection_min_delay
    return delayed_connections


def __convert_sources_and_targets(
        connections: ConnectionsArray, pre_vertex: ApplicationVertex,
        post_vertex_slice: Slice) -> ConnectionsArray:
    connections["source"] = pre_vertex.get_raster_ordered_indices(
        connections["source"])
    connections["target"] = post_vertex_slice.get_raster_indices(
        connections["target"])
    return connections
