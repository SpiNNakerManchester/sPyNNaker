# Copyright (c) 2017-2019 The University of Manchester
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
from six import raise_from

from spinn_front_end_common.utilities.constants import \
    MICRO_TO_MILLISECOND_CONVERSION, BYTES_PER_WORD
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector)
from spynnaker.pyNN.utilities.constants import MAX_SUPPORTED_DELAY_TICS
from spynnaker.pyNN.exceptions import SynapseRowTooBigException
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractStaticSynapseDynamics, AbstractSynapseDynamicsStructural,
    AbstractSynapseDynamics)

_N_HEADER_WORDS = 3
# There are 16 slots, one per time step
_STD_DELAY_SLOTS = 16


class MaxRowInfo(object):
    """ Information about the maximums for rows in a synaptic matrix.
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
        :param int delayed_max_n_synapses:
        :param int undelayed_max_bytes:
        :param int delayed_max_bytes:
        :param int undelayed_max_words:
        :param int delayed_max_words:
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
        :rtype: int
        """
        return self.__undelayed_max_n_synapses

    @property
    def delayed_max_n_synapses(self):
        """
        :rtype: int
        """
        return self.__delayed_max_n_synapses

    @property
    def undelayed_max_bytes(self):
        """
        :rtype: int
        """
        return self.__undelayed_max_bytes

    @property
    def delayed_max_bytes(self):
        """
        :rtype: int
        """
        return self.__delayed_max_bytes

    @property
    def undelayed_max_words(self):
        """
        :rtype: int
        """
        return self.__undelayed_max_words

    @property
    def delayed_max_words(self):
        """
        :rtype: int
        """
        return self.__delayed_max_words


class SynapseIORowBased(object):
    """ A SynapseRowIO implementation that uses a row for each source neuron,\
        where each row consists of a fixed region, a plastic region, and a\
        fixed-plastic region (this is the bits of the plastic row that don't\
        actually change).  The plastic region structure is determined by the\
        synapse dynamics of the connector.
    """
    __slots__ = []

    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        """ Get the maximum delay supported by the synapse representation \
            before extensions are required, or None if any delay is supported

        :param int machine_time_step:
        :rtype: int or None
        """
        # There are 16 slots, one per time step
        return MAX_SUPPORTED_DELAY_TICS * (
            machine_time_step / MICRO_TO_MILLISECOND_CONVERSION)

    @staticmethod
    def _n_words(n_bytes):
        """
        :param int n_bytes:
        :rtype: int
        """
        return math.ceil(float(n_bytes) / BYTES_PER_WORD)

    @staticmethod
    def _get_max_row_length(
            size, dynamics, population_table, in_edge, row_length):
        """
        :param int size:
        :param AbstractSynapseDynamics dynamics:
        :param MasterPopTableAsBinarySearch population_table:
        :param in_edge:
        :type in_edge: ProjectionApplicationEdge or ProjectionMachineEdge
        :param int row_length:
        :raises SynapseRowTooBigException:
        """
        try:
            return population_table.get_allowed_row_length(size)
        except SynapseRowTooBigException as e:
            max_synapses = dynamics.get_max_synapses(e.max_size)
            raise_from(SynapseRowTooBigException(
                max_synapses,
                "The connection between {} and {} has more synapses ({}) than"
                " can currently be supported on this implementation of PyNN"
                " ({} for this connection type)."
                " Please reduce the size of the target population, or reduce"
                " the number of neurons per core.".format(
                    in_edge.pre_vertex, in_edge.post_vertex, row_length,
                    max_synapses)), e)

    def get_max_row_info(
            self, synapse_info, post_vertex_slice, n_delay_stages,
            population_table, machine_time_step, in_edge):
        """ Get the information about the maximum lengths of delayed and\
            undelayed rows in bytes (including header), words (without header)\
            and number of synapses

        :param SynapseInformation synapse_info:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param int n_delay_stages:
        :param MasterPopTableAsBinarySearch population_table:
        :param int machine_time_step:
        :param in_edge:
        :type in_edge: ProjectionApplicationEdge or ProjectionMachineEdge
        :rtype: MaxRowInfo
        :raises SynapseRowTooBigException:
        """
        max_delay_supported = self.get_maximum_delay_supported_in_ms(
            machine_time_step)
        max_delay = max_delay_supported * (n_delay_stages + 1)

        # delay point where delay extensions start
        min_delay_for_delay_extension = (
                max_delay_supported + numpy.finfo(numpy.double).tiny)

        # row length for the non-delayed synaptic matrix
        max_undelayed_n_synapses = synapse_info.connector \
            .get_n_connections_from_pre_vertex_maximum(
                post_vertex_slice, synapse_info, 0, max_delay_supported)

        # determine the max row length in the delay extension
        max_delayed_n_synapses = 0
        if n_delay_stages > 0:
            max_delayed_n_synapses = synapse_info.connector \
                .get_n_connections_from_pre_vertex_maximum(
                    post_vertex_slice, synapse_info,
                    min_delay_for_delay_extension, max_delay)

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
        undelayed_max_n_words = self._get_max_row_length(
            undelayed_n_words, dynamics, population_table, in_edge,
            max_undelayed_n_synapses)
        delayed_max_n_words = self._get_max_row_length(
            delayed_n_words, dynamics, population_table, in_edge,
            max_delayed_n_synapses)

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

    @staticmethod
    def _get_max_row_length_and_row_data(
            connections, row_indices, n_rows, post_vertex_slice,
            n_synapse_types, population_table, synapse_dynamics):
        """
        :param ~numpy.ndarray connections:
        :param ~numpy.ndarray row_indices:
        :param int n_rows:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param int n_synapse_types:
        :param MasterPopTableAsBinarySearch population_table:
        :param AbstractSynapseDynamics synapse_dynamics:
        :rtype: tuple(int, ~numpy.ndarray)
        """
        # pylint: disable=too-many-arguments, too-many-locals
        row_ids = range(n_rows)
        ff_data, ff_size = None, None
        fp_data, pp_data, fp_size, pp_size = None, None, None, None
        if isinstance(synapse_dynamics, AbstractStaticSynapseDynamics):

            # Get the static data
            ff_data, ff_size = synapse_dynamics.get_static_synaptic_data(
                connections, row_indices, n_rows, post_vertex_slice,
                n_synapse_types)

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
                    n_synapse_types)

        # Add some padding
        row_lengths = [
            _N_HEADER_WORDS + pp_data[i].size + fp_data[i].size +
            ff_data[i].size for i in row_ids]
        max_length = max(row_lengths) - _N_HEADER_WORDS
        max_row_length = population_table.get_allowed_row_length(max_length)
        padding = [
            numpy.zeros(
                max_row_length - (row_length - _N_HEADER_WORDS),
                dtype="uint32")
            for row_length in row_lengths]

        # Join the bits into rows
        items_to_join = [
            pp_size, pp_data, ff_size, fp_size, ff_data, fp_data, padding]
        rows = [numpy.concatenate(items) for items in zip(*items_to_join)]
        row_data = numpy.concatenate(rows)

        # Return the data
        return max_row_length, row_data

    def get_synapses(
            self, synapse_info, pre_slices, pre_slice_index,
            post_slices, post_slice_index, pre_vertex_slice,
            post_vertex_slice, n_delay_stages, population_table,
            n_synapse_types, weight_scales, machine_time_step,
            app_edge, machine_edge):
        """ Get the synapses as an array of words for non-delayed synapses and\
            an array of words for delayed synapses. This is used to prepare\
            information for *deployment to SpiNNaker*.

        :param SynapseInformation synapse_info:
        :param list(~pacman.model.graphs.common.Slice) pre_slices:
        :param int pre_slice_index:
        :param list(~pacman.model.graphs.common.Slice) post_slices:
        :param int post_slice_index:
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param int n_delay_stages:
        :param MasterPopTableAsBinarySearch population_table:
        :param int n_synapse_types:
        :param dict(AbstractSynapseType,float) weight_scales:
        :param int machine_time_step:
        :param ProjectionApplicationEdge app_edge:
        :param ProjectionMachineEdge machine_edge:
        :return: (row_data, max_row_length, delayed_row_data,
            max_delayed_row_length, delayed_source_ids, stages)
        :rtype:
            tuple(~numpy.ndarray, int, ~numpy.ndarray, int, ~numpy.ndarray,\
            ~numpy.ndarray)
        """
        # pylint: disable=too-many-arguments, too-many-locals
        # pylint: disable=assignment-from-no-return
        # Get delays in timesteps
        max_delay = self.get_maximum_delay_supported_in_ms(machine_time_step)
        if max_delay is not None:
            max_delay *= (MICRO_TO_MILLISECOND_CONVERSION / machine_time_step)

        # Get the actual connections
        connections = synapse_info.connector.create_synaptic_block(
            pre_slices, pre_slice_index, post_slices, post_slice_index,
            pre_vertex_slice, post_vertex_slice, synapse_info.synapse_type,
            synapse_info)

        # Convert delays to timesteps
        connections["delay"] = numpy.rint(
            connections["delay"] * (
                MICRO_TO_MILLISECOND_CONVERSION / machine_time_step))

        # Scale weights
        connections["weight"] = (connections["weight"] * weight_scales[
            synapse_info.synapse_type])

        # Set connections for structural plasticity
        if isinstance(synapse_info.synapse_dynamics,
                      AbstractSynapseDynamicsStructural):
            synapse_info.synapse_dynamics.set_connections(
                connections, post_vertex_slice, app_edge, synapse_info,
                machine_edge)

        # Split the connections up based on the delays
        if max_delay is not None:
            plastic_delay_mask = (connections["delay"] <= max_delay)
            undelayed_connections = connections[
                numpy.where(plastic_delay_mask)]
            delayed_connections = connections[
                numpy.where(~plastic_delay_mask)]
        else:
            undelayed_connections = connections
            delayed_connections = numpy.zeros(
                0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        del connections

        # Get the data for the connections
        row_data = numpy.zeros(0, dtype="uint32")
        max_row_length = 0
        if undelayed_connections.size or \
                isinstance(synapse_info.synapse_dynamics,
                           AbstractSynapseDynamicsStructural):
            # Get which row each connection will go into
            undelayed_row_indices = (
                    undelayed_connections["source"] - pre_vertex_slice.lo_atom)
            max_row_length, row_data = self._get_max_row_length_and_row_data(
                undelayed_connections, undelayed_row_indices,
                pre_vertex_slice.n_atoms, post_vertex_slice, n_synapse_types,
                population_table, synapse_info.synapse_dynamics)

            del undelayed_row_indices
        del undelayed_connections

        # Get the data for the delayed connections
        delayed_row_data = numpy.zeros(0, dtype="uint32")
        max_delayed_row_length = 0
        stages = numpy.zeros(0, dtype="uint32")
        delayed_source_ids = numpy.zeros(0, dtype="uint32")
        if delayed_connections.size:
            # Get the delay stages and which row each delayed connection will
            # go into
            stages = numpy.floor((numpy.round(
                delayed_connections["delay"] - 1.0)) / max_delay).astype(
                "uint32")
            delayed_row_indices = (
                    (delayed_connections[
                         "source"] - pre_vertex_slice.lo_atom) +
                    ((stages - 1) * pre_vertex_slice.n_atoms))
            delayed_connections["delay"] -= max_delay * stages
            delayed_source_ids = (
                    delayed_connections["source"] - pre_vertex_slice.lo_atom)

            # Get the data
            max_delayed_row_length, delayed_row_data = \
                self._get_max_row_length_and_row_data(
                    delayed_connections, delayed_row_indices,
                    pre_vertex_slice.n_atoms * n_delay_stages,
                    post_vertex_slice, n_synapse_types, population_table,
                    synapse_info.synapse_dynamics)
            del delayed_row_indices
        del delayed_connections

        return (row_data, max_row_length, delayed_row_data,
                max_delayed_row_length, delayed_source_ids, stages)

    def read_synapses(
            self, synapse_info, pre_vertex_slice, post_vertex_slice,
            max_row_length, delayed_max_row_length, n_synapse_types,
            weight_scales, data, delayed_data, machine_time_step):
        """ Read the synapses for a given projection synapse information\
            object out of the given data. This is used to parse information\
            *read from SpiNNaker*.

        :param SynapseInformation synapse_info:
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param int max_row_length:
        :param int delayed_max_row_length:
        :param int n_synapse_types:
        :param dict(AbstractSynapseType,float) weight_scales:
        :param bytearray data:
        :param bytearray delayed_data:
        :param int machine_time_step:
        :return: array with ``weight`` and ``delay`` columns
        :rtype: ~numpy.ndarray
        """
        # pylint: disable=too-many-arguments, too-many-locals

        # Translate the data into rows
        row_data = None
        delayed_row_data = None
        if data is not None and len(data):
            row_data = numpy.frombuffer(data, dtype="<u4").reshape(
                -1, (max_row_length + _N_HEADER_WORDS))
        if delayed_data is not None and len(delayed_data):
            delayed_row_data = numpy.frombuffer(
                delayed_data, dtype="<u4").reshape(
                -1, (delayed_max_row_length + _N_HEADER_WORDS))

        dynamics = synapse_info.synapse_dynamics
        if isinstance(dynamics, AbstractStaticSynapseDynamics):
            # Read static data
            connections = self._read_static_data(
                dynamics, pre_vertex_slice, post_vertex_slice, n_synapse_types,
                row_data, delayed_row_data)
        else:
            # Read plastic data
            connections = self._read_plastic_data(
                dynamics, pre_vertex_slice, post_vertex_slice, n_synapse_types,
                row_data, delayed_row_data)

        if not connections:
            return numpy.zeros(
                0, dtype=AbstractSynapseDynamics.NUMPY_CONNECTORS_DTYPE)

        # Join the connections into a single list
        connections = numpy.concatenate(connections)

        # Return the delays values to milliseconds
        connections["delay"] /= (
                MICRO_TO_MILLISECOND_CONVERSION / machine_time_step)

        # Undo the weight scaling
        connections["weight"] /= weight_scales[synapse_info.synapse_type]

        # Return the connections
        return connections

    @staticmethod
    def _parse_static_data(row_data, dynamics):
        """
        :param ~numpy.ndarray row_data:
        :param AbstractStaticSynapseDynamics dynamics:
        :rtype: tuple(int, list(~numpy.ndarray))
        """
        n_rows = row_data.shape[0]
        ff_size = row_data[:, 1]
        ff_words = dynamics.get_n_static_words_per_row(ff_size)
        ff_start = _N_HEADER_WORDS
        ff_end = ff_start + ff_words
        return (
            ff_size,
            [row_data[row, ff_start:ff_end[row]] for row in range(n_rows)])

    def __convert_delayed_data(
            self, n_synapses, pre_vertex_slice, delayed_connections):
        """ Take the delayed_connections and convert the source ids and delay\
            values
        """
        synapse_ids = range(len(n_synapses))
        row_stage = numpy.array([
            i // pre_vertex_slice.n_atoms
            for i in synapse_ids], dtype="uint32")
        row_min_delay = (row_stage + 1) * 16
        connection_min_delay = numpy.concatenate([
            numpy.repeat(row_min_delay[i], n_synapses[i])
            for i in synapse_ids])
        connection_source_extra = numpy.concatenate([
            numpy.repeat(
                row_stage[i] * numpy.uint32(pre_vertex_slice.n_atoms),
                n_synapses[i])
            for i in synapse_ids])
        delayed_connections["source"] -= connection_source_extra
        delayed_connections["source"] += pre_vertex_slice.lo_atom
        delayed_connections["delay"] += connection_min_delay
        return delayed_connections

    def _read_static_data(self, dynamics, pre_vertex_slice, post_vertex_slice,
                          n_synapse_types, row_data, delayed_row_data):
        """ Read static data.

        :param AbstractStaticSynapseDynamics dynamics:
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param int n_synapse_types:
        :param ~numpy.ndarray row_data:
        :param ~numpy.ndarray delayed_row_data:
        :rtype: list(~numpy.ndarray)
        """
        # pylint: disable=too-many-arguments, too-many-locals
        connections = []

        if row_data is not None and row_data.size:
            ff_size, ff_data = self._parse_static_data(row_data, dynamics)
            undelayed_connections = dynamics.read_static_synaptic_data(
                post_vertex_slice, n_synapse_types, ff_size, ff_data)
            undelayed_connections["source"] += pre_vertex_slice.lo_atom
            connections.append(undelayed_connections)

        if delayed_row_data is not None and delayed_row_data.size:
            ff_size, ff_data = self._parse_static_data(
                delayed_row_data, dynamics)
            delayed_connections = dynamics.read_static_synaptic_data(
                post_vertex_slice, n_synapse_types, ff_size, ff_data)

            # Use the row index to work out the actual delay and source
            n_synapses = dynamics.get_n_synapses_in_rows(ff_size)
            delayed_connections = self.__convert_delayed_data(
                n_synapses, pre_vertex_slice, delayed_connections)
            connections.append(delayed_connections)

        return connections

    @staticmethod
    def _parse_plastic_data(row_data, dynamics):
        """
        :param ~numpy.ndarray row_data:
        :param AbstractPlasticSynapseDynamics dynamics:
        :rtype: tuple(int, list(~numpy.ndarray))
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
            self, dynamics, pre_vertex_slice, post_vertex_slice,
            n_synapse_types, row_data, delayed_row_data):
        """ Read plastic data.

        :param AbstractPlasticSynapseDynamics dynamics:
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param int n_synapse_types:
        :param ~numpy.ndarray row_data:
        :param ~numpy.ndarray delayed_row_data:
        :rtype: list(~numpy.ndarray)
        """
        # pylint: disable=too-many-arguments, too-many-locals
        connections = []

        if row_data is not None:
            pp_size, pp_data, fp_size, fp_data = self._parse_plastic_data(
                row_data, dynamics)
            undelayed_connections = dynamics.read_plastic_synaptic_data(
                post_vertex_slice, n_synapse_types, pp_size, pp_data,
                fp_size, fp_data)
            undelayed_connections["source"] += pre_vertex_slice.lo_atom
            connections.append(undelayed_connections)

        if delayed_row_data is not None:
            pp_size, pp_data, fp_size, fp_data = self._parse_plastic_data(
                delayed_row_data, dynamics)
            delayed_connections = dynamics.read_plastic_synaptic_data(
                post_vertex_slice, n_synapse_types, pp_size, pp_data,
                fp_size, fp_data)

            # Use the row index to work out the actual delay and source
            n_synapses = dynamics.get_n_synapses_in_rows(pp_size, fp_size)
            delayed_connections = self.__convert_delayed_data(
                n_synapses, pre_vertex_slice, delayed_connections)
            connections.append(delayed_connections)

        return connections

    def get_block_n_bytes(self, max_row_length, n_rows):
        """ Get the number of bytes in a block given the max row length and\
            number of rows

        :param int max_row_length:
        :param int n_rows:
        :rtype: int
        """
        return (_N_HEADER_WORDS + max_row_length) * BYTES_PER_WORD * n_rows
