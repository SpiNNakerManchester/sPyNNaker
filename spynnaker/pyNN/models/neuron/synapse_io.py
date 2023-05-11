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

import numpy

from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector)
from spynnaker.pyNN.exceptions import SynapseRowTooBigException
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractStaticSynapseDynamics, AbstractSDRAMSynapseDynamics)
from .master_pop_table import MasterPopTableAsBinarySearch

_N_HEADER_WORDS = 3
# There are 16 slots, one per time step
_STD_DELAY_SLOTS = 16


class MaxRowInfo(object):
    """
    Information about the maximums for rows in a synaptic matrix.
    """

    __slots__ = [
        "__undelayed_max_n_synapses",
        "__delayed_max_n_synapses",
        "__undelayed_max_bytes",
        "__delayed_max_bytes",
        "__undelayed_max_words",
        "__delayed_max_words",
    ]

    def __init__(
            self, undelayed_max_n_synapses, delayed_max_n_synapses,
            undelayed_max_bytes, delayed_max_bytes,
            undelayed_max_words, delayed_max_words):
        """
        :param int undelayed_max_n_synapses:
            Maximum number of synapses in a row of the undelayed matrix
        :param int delayed_max_n_synapses:
            Maximum number of synapses in a row of the delayed matrix
        :param int undelayed_max_bytes:
            Maximum number of bytes, including headers, in a row of the
            undelayed matrix, or 0 if no synapses
        :param int delayed_max_bytes:
            Maximum number of bytes, including headers, in a row of the
            delayed matrix, or 0 if no synapses
        :param int undelayed_max_words:
            Maximum number of words, excluding headers, in a row of the
            undelayed matrix
        :param int delayed_max_words:
            Maximum number of words, excluding headers, in a row of the
            delayed matrix
        """
        self.__undelayed_max_n_synapses = undelayed_max_n_synapses
        self.__delayed_max_n_synapses = delayed_max_n_synapses
        self.__undelayed_max_bytes = undelayed_max_bytes
        self.__delayed_max_bytes = delayed_max_bytes
        self.__undelayed_max_words = undelayed_max_words
        self.__delayed_max_words = delayed_max_words

    @property
    def undelayed_max_n_synapses(self):
        """
        Maximum number of synapses in a row of the undelayed matrix.

        :rtype: int
        """
        return self.__undelayed_max_n_synapses

    @property
    def delayed_max_n_synapses(self):
        """
        Maximum number of synapses in a row of the delayed matrix.

        :rtype: int
        """
        return self.__delayed_max_n_synapses

    @property
    def undelayed_max_bytes(self):
        """
        Maximum number of bytes, including headers, in a row of the
        undelayed matrix.

        :rtype: int
        """
        return self.__undelayed_max_bytes

    @property
    def delayed_max_bytes(self):
        """
        Maximum number of bytes, including headers, in a row of the
        delayed matrix.

        :rtype: int
        """
        return self.__delayed_max_bytes

    @property
    def undelayed_max_words(self):
        """
        Maximum number of words, excluding headers, in a row of the
        undelayed matrix.

        :rtype: int
        """
        return self.__undelayed_max_words

    @property
    def delayed_max_words(self):
        """
        Maximum number of words, excluding headers, in a row of the
        undelayed matrix.

        :rtype: int
        """
        return self.__delayed_max_words


def get_maximum_delay_supported_in_ms(post_vertex_max_delay_ticks):
    """
    Get the maximum delay supported by the synapse representation
    before extensions are required, or `None` if any delay is supported.

    :param int post_vertex_max_delay_ticks: post vertex max delay
    :rtype: int
    """
    return (post_vertex_max_delay_ticks *
            SpynnakerDataView.get_simulation_time_step_ms())


def get_max_row_info(
        synapse_info, n_post_atoms, n_delay_stages, in_edge):
    """
    Get the information about the maximum lengths of delayed and
    undelayed rows in bytes (including header), words (without header)
    and number of synapses.

    :param SynapseInformation synapse_info:
        The synapse information to get the row data for
    :param int n_post_atoms:
        The number of post atoms to get the maximum for
    :param int n_delay_stages:
        The number of delay stages on the edge
    :param ProjectionApplicationEdge in_edge:
        The incoming edge on which the synapse information is held
    :rtype: MaxRowInfo
    :raises SynapseRowTooBigException:
        If the synapse information can't be represented
    """
    max_delay_supported = get_maximum_delay_supported_in_ms(
        in_edge.post_vertex.splitter.max_support_delay())
    max_delay = max_delay_supported * (n_delay_stages + 1)
    pad_to_length = None
    if isinstance(synapse_info.synapse_dynamics, AbstractSDRAMSynapseDynamics):
        pad_to_length = synapse_info.synapse_dynamics.pad_to_length

    # delay point where delay extensions start
    min_delay_for_delay_extension = (
        max_delay_supported + numpy.finfo(numpy.double).tiny)

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
    else:
        undelayed_n_words = dynamics.get_n_words_for_plastic_connections(
            max_undelayed_n_synapses)
        delayed_n_words = dynamics.get_n_words_for_plastic_connections(
            max_delayed_n_synapses)

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


def _get_allowed_row_length(n_words, dynamics, in_edge, n_synapses):
    """
    Get the allowed row length in words in the population table for a
    desired row length in words.

    :param int n_words: The number of words in the row
    :param AbstractSynapseDynamics dynamics: The synapse dynamics used
    :param ProjectionApplicationEdge in_edge: The incoming edge
    :param int n_synapses: The number of synapses for the number of words
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
        max_synapses = dynamics.get_max_synapses(e.max_size)
        raise SynapseRowTooBigException(
            max_synapses,
            f"The connection between {in_edge.pre_vertex} and "
            f"{in_edge.post_vertex} has more synapses ({n_synapses}) than "
            "can currently be supported on this implementation of PyNN "
            f"({max_synapses} for this connection type). "
            "Please reduce the size of the target population, or reduce "
            "the number of neurons per core.") from e


def get_synapses(
        connections, synapse_info, n_delay_stages, n_synapse_types,
        weight_scales, app_edge, post_vertex_slice, max_row_info,
        gen_undelayed, gen_delayed, max_atoms_per_core):
    """
    Get the synapses as an array of words for non-delayed synapses and
    an array of words for delayed synapses. This is used to prepare
    information for *deployment to SpiNNaker*.

    :param ~numpy.ndarray connections:
        The connections to get the synapses from
    :param SynapseInformation synapse_info:
        The synapse information to convert to synapses
    :param int n_delay_stages:
        The number of delay stages in total to be represented
    :param int n_synapse_types:
        The number of synapse types in total to be represented
    :param list(float) weight_scales:
        The scaling of the weights for each synapse type
    :param ~pacman.model.graphs.application.ApplicationEdge app_edge:
        The incoming machine edge that the synapses are on
    :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        The slice of the post-vertex to get the synapses for
    :param MaxRowInfo max_row_info:
        The maximum row information for the synapses
    :param bool gen_undelayed:
        Whether to generate undelayed data
    :param bool gen_delayed:
        Whether to generate delayed data
    :param int max_atoms_per_core:
        The maximum number of atoms on a core
    :return:
        (``row_data``, ``delayed_row_data``) where:

        * ``row_data`` is the undelayed connectivity data arranged into a
            row per source, each row the same length
        * ``delayed_row_data`` is the delayed connectivity data arranged
            into a row per source per delay stage, each row the same length
    :rtype:
        tuple(~numpy.ndarray, ~numpy.ndarray)
    """
    # pylint: disable=too-many-arguments
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
    row_data = numpy.zeros(0, dtype="uint32")
    if gen_undelayed and max_row_info.undelayed_max_n_synapses:
        # Get which row each connection will go into
        undelayed_row_indices = undelayed_connections["source"]
        row_data = _get_row_data(
            undelayed_connections, undelayed_row_indices,
            app_edge.pre_vertex.n_atoms, post_vertex_slice, n_synapse_types,
            synapse_info.synapse_dynamics,
            max_row_info.undelayed_max_n_synapses,
            max_row_info.undelayed_max_words, max_atoms_per_core)
        del undelayed_row_indices
    del undelayed_connections

    # Get the data for the delayed connections
    delayed_row_data = numpy.zeros(0, dtype="uint32")
    if gen_delayed and max_row_info.delayed_max_n_synapses:
        # Get the delay stages and which row each delayed connection will
        # go into
        stages = numpy.floor((numpy.round(
            delayed_connections["delay"] - 1.0)) / max_delay).astype("uint32")
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
            app_edge.pre_vertex.n_atoms * n_delay_stages, post_vertex_slice,
            n_synapse_types, synapse_info.synapse_dynamics,
            max_row_info.delayed_max_n_synapses,
            max_row_info.delayed_max_words, max_atoms_per_core)
        del delayed_row_indices
    del delayed_connections

    return row_data, delayed_row_data


def _get_row_data(
        connections, row_indices, n_rows, post_vertex_slice,
        n_synapse_types, synapse_dynamics, max_row_n_synapses,
        max_row_n_words, max_atoms_per_core):
    """
    :param ~numpy.ndarray connections:
        The connections to convert; the dtype is
        AbstractConnector.NUMPY_SYNAPSES_DTYPE
    :param ~numpy.ndarray row_indices:
        The row into which each connection should go; same length as
        connections
    :param int n_rows: The total number of rows
    :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        The slice of the post vertex to get the data for
    :param int n_synapse_types: The number of synapse types allowed
    :param AbstractSynapseDynamics synapse_dynamics:
        The synapse dynamics of the synapses
    :param int max_row_n_synapses: The maximum number of synapses in a row
    :param int max_row_n_words: The maximum number of words in a row
    :param int max_atoms_per_core: The maximum number of atoms per core
    :rtype: tuple(int, ~numpy.ndarray)
    """
    # pylint: disable=too-many-arguments
    row_ids = range(n_rows)
    ff_data, ff_size = None, None
    fp_data, pp_data, fp_size, pp_size = None, None, None, None
    if isinstance(synapse_dynamics, AbstractStaticSynapseDynamics):

        # Get the static data
        ff_data, ff_size = synapse_dynamics.get_static_synaptic_data(
            connections, row_indices, n_rows, post_vertex_slice,
            n_synapse_types, max_row_n_synapses, max_atoms_per_core)

        # Blank the plastic data
        fp_data = [numpy.zeros(0, dtype="uint32") for _ in range(n_rows)]
        pp_data = [numpy.zeros(0, dtype="uint32") for _ in range(n_rows)]
        fp_size = [numpy.zeros(1, dtype="uint32") for _ in range(n_rows)]
        pp_size = [numpy.zeros(1, dtype="uint32") for _ in range(n_rows)]
    else:

        # Blank the static data
        ff_data = [numpy.zeros(0, dtype="uint32") for _ in row_ids]
        ff_size = [numpy.zeros(1, dtype="uint32") for _ in row_ids]

        # Get the plastic data
        fp_data, pp_data, fp_size, pp_size = \
            synapse_dynamics.get_plastic_synaptic_data(
                connections, row_indices, n_rows, post_vertex_slice,
                n_synapse_types, max_row_n_synapses, max_atoms_per_core)

    # Add some padding
    row_lengths = [
        pp_data[i].size + fp_data[i].size + ff_data[i].size
        for i in row_ids]
    padding = [
        numpy.zeros(max_row_n_words - row_length, dtype="uint32")
        for row_length in row_lengths]

    # Join the bits into rows
    items_to_join = [
        pp_size, pp_data, ff_size, fp_size, ff_data, fp_data, padding]
    rows = [numpy.concatenate(items) for items in zip(*items_to_join)]
    row_data = numpy.concatenate(rows)

    # Return the data
    return row_data


def convert_to_connections(
        synapse_info, post_vertex_slice, n_pre_atoms,
        max_row_length, n_synapse_types, weight_scales, data,
        delayed, post_vertex_max_delay_ticks, max_atoms_per_core):
    """
    Read the synapses for a given projection synapse information
    object out of the given data and convert to connection data

    :param SynapseInformation synapse_info:
        The synapse information of the synapses
    :param int n_pre_atoms: The number of atoms in the pre-vertex
    :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        The slice of the target neurons of the synapses in the data
    :param int max_row_length:
        The length of each row in the data
    :param int n_synapse_types:
        The number of synapse types in total
    :param list(float) weight_scales:
        The weight scaling of each synapse type
    :param bytearray data:
        The raw data containing the synapses
    :param bool delayed:
        True if the data should be considered delayed
    :param int post_vertex_max_delay_ticks:
        The maximum delayed ticks supported from post vertex
    :param int max_atoms_per_core:
        The maximum number of atoms on a core
    :return: The connections read from the data; the dtype is
        :py:attr:`~.AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE`
    :rtype: ~numpy.ndarray
    """
    # If there is no data, return nothing
    if data is None or not len(data):
        return numpy.zeros(
            0, dtype=AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE)

    # Translate the data into rows
    row_data = numpy.frombuffer(data, dtype="<u4").reshape(
        -1, (max_row_length + _N_HEADER_WORDS))

    dynamics = synapse_info.synapse_dynamics
    if isinstance(dynamics, AbstractStaticSynapseDynamics):
        # Read static data
        connections = _read_static_data(
            dynamics, post_vertex_slice, n_pre_atoms, n_synapse_types,
            row_data, delayed, post_vertex_max_delay_ticks, max_atoms_per_core)
    else:
        # Read plastic data
        connections = _read_plastic_data(
            dynamics, post_vertex_slice, n_pre_atoms, n_synapse_types,
            row_data, delayed, post_vertex_max_delay_ticks, max_atoms_per_core)

    # There might still be no connections if the row was all padding
    if not connections.size:
        return numpy.zeros(
            0, dtype=AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE)

    # Convert 0 delays to max delays
    connections["delay"][connections["delay"] == 0] = (
        post_vertex_max_delay_ticks)

    # Return the connections after appropriate scaling
    return _rescale_connections(connections, weight_scales, synapse_info)


def read_all_synapses(
        data, delayed_data, synapse_info, n_synapse_types,
        weight_scales, post_vertex_slice, n_pre_atoms,
        post_vertex_max_delay_ticks, max_row_info, max_atoms_per_core):
    """
    Read the synapses for a given projection synapse information
    object out of the given delayed and undelayed data.

    :param bytearray data:
        The raw data containing the undelayed synapses
    :param bytearray delayed_data:
        The raw data containing the delayed synapses
    :param SynapseInformation synapse_info:
        The synapse info that generated the synapses
    :param int n_synapse_types:
        The total number of synapse types available
    :param list(float) weight_scales:
        A weight scale for each synapse type
    :param int n_pre_atoms: The number of atoms in the pre-vertex
    :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        The slice of the post-vertex to read the synapses for
    :param int post_vertex_max_delay_ticks:
            max delayed ticks supported from post vertex
    :param MaxRowInfo max_row_info:
        The maximum information for each of the rows
    :param int max_atoms_per_core:
        The maximum number of atoms on a core
    :return: The connections read from the data; the dtype is
        :py:attr:`~.AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE`
    :rtype: ~numpy.ndarray
    """
    connections = []
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


def _parse_static_data(row_data, dynamics):
    """
    Parse static synaptic data.

    :param ~numpy.ndarray row_data: The raw row data
    :param AbstractStaticSynapseDynamics dynamics:
        The synapse dynamics that can decode the rows
    :return: A tuple of the recorded length of each row and the row data
        organised into rows
    :rtype: tuple(~numpy.ndarray, list(~numpy.ndarray))
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
        dynamics, post_vertex_slice, n_pre_atoms,
        n_synapse_types, row_data, delayed, post_vertex_max_delay_ticks,
        max_atoms_per_core):
    """
    Read static data from row data.

    :param AbstractStaticSynapseDynamics dynamics:
        The synapse dynamics that generated the data
    :param int n_pre_atoms: The number of atoms on the pre-vertex
    :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        The slice of neurons that are the targets of the synapses
    :param int n_synapse_types:
        The number of synapse types available
    :param ~numpy.ndarray row_data:
        The raw row data to read
    :param bool delayed: True if data should be considered delayed
    :param int post_vertex_max_delay_ticks: post vertex delay maximum
    :param int max_atoms_per_core: The maximum number of atoms on a core
    :return: the connections read with dtype
        :py:attr:`~.AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE`
    :rtype: list(~numpy.ndarray)
    """
    if row_data is None or not row_data.size:
        return numpy.zeros(
            0, dtype=AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE)
    ff_size, ff_data = _parse_static_data(row_data, dynamics)
    connections = dynamics.read_static_synaptic_data(
        post_vertex_slice, n_synapse_types, ff_size, ff_data,
        max_atoms_per_core)
    if delayed:
        n_synapses = dynamics.get_n_synapses_in_rows(ff_size)
        connections = _convert_delayed_data(
            n_synapses, n_pre_atoms, connections,
            post_vertex_max_delay_ticks)
    return connections


def _parse_plastic_data(row_data, dynamics):
    """
    Parse plastic synapses from raw row data.

    :param ~numpy.ndarray row_data: The raw data to parse
    :param AbstractPlasticSynapseDynamics dynamics:
        The dynamics that generated the data
    :return: A tuple of the recorded length of the plastic-plastic data in
        each row; the plastic-plastic data organised into rows; the
        recorded length of the static-plastic data in each row; and the
        static-plastic data organised into rows
    :rtype: tuple(~numpy.ndarray, list(~numpy.ndarray), ~numpy.ndarray,
        list(~numpy.ndarray))
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
        dynamics, post_vertex_slice, n_pre_atoms,
        n_synapse_types, row_data, delayed, post_vertex_max_delay_ticks,
        max_atoms_per_core):
    """
    Read plastic data from raw data.

    :param AbstractStaticSynapseDynamics dynamics:
        The synapse dynamics that generated the data
    :param int n_pre_atoms: The number of atoms in the pre-vertex
    :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        The slice of neurons that are the targets of the synapses
    :param int n_synapse_types:
        The number of synapse types available
    :param ~numpy.ndarray row_data:
        The raw row data to read
    :param bool delayed: True if data should be considered delayed
    :param int post_vertex_max_delay_ticks: post vertex delay maximum
    :param int max_atoms_per_core: The maximum number of atoms on a core
    :return: the connections read with dtype
        :py:attr:`~.AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE`
    :rtype: list(~numpy.ndarray)
    """
    if row_data is None or not row_data.size:
        return numpy.zeros(
            0, dtype=AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE)
    pp_size, pp_data, fp_size, fp_data = _parse_plastic_data(
        row_data, dynamics)
    connections = dynamics.read_plastic_synaptic_data(
        post_vertex_slice, n_synapse_types, pp_size, pp_data,
        fp_size, fp_data, max_atoms_per_core)

    if delayed:
        n_synapses = dynamics.get_n_synapses_in_rows(pp_size, fp_size)
        connections = _convert_delayed_data(
            n_synapses, n_pre_atoms, connections,
            post_vertex_max_delay_ticks)
    return connections


def _rescale_connections(connections, weight_scales, synapse_info):
    """
    Scale the connection data into machine values.

    :param ~numpy.ndarray connections: The connections to be rescaled
    :param list(float) weight_scales: The weight scale of each synapse type
    :param SynapseInformation synapse_info:
        The synapse information of the connections
    """
    # Return the delays values to milliseconds
    connections["delay"] /= SpynnakerDataView.get_simulation_time_step_per_ms()
    # Undo the weight scaling
    connections["weight"] /= weight_scales[synapse_info.synapse_type]
    return connections


def _convert_delayed_data(
        n_synapses, n_pre_atoms, delayed_connections,
        post_vertex_max_delay_ticks):
    """
    Take the delayed_connections and convert the source ids and delay
    values back to global values.

    :param ~numpy.ndarray n_synapses: The number of synapses in each row
    :param int n_pre_atoms: number of atoms in the pre-vertex
    :param ~numpy.ndarray delayed_connections:
        The connections to convert of dtype
        :py:attr:`~.AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE`
    :param int post_vertex_max_delay_ticks: post vertex delay maximum
    :return: The converted connection with the same dtype
    :rtype: ~numpy.ndarray
    """
    # Work out the delay stage of each row; rows are the all the rows
    # from the first delay stage, then all from the second stage and so on
    synapse_ids = range(len(n_synapses))
    row_stage = numpy.array([
        i // n_pre_atoms
        for i in synapse_ids], dtype="uint32")
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
            row_stage[i] * numpy.uint32(n_pre_atoms),
            n_synapses[i])
        for i in synapse_ids])
    # Do the conversions
    delayed_connections["source"] -= connection_source_extra
    delayed_connections["delay"] += connection_min_delay
    return delayed_connections
