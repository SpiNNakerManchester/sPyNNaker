# Copyright (c) 2014 The University of Manchester
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
import logging
from typing import (
    Dict, List, Optional, Sequence, Tuple, Union, cast, TYPE_CHECKING)

import numpy
from numpy import floating, integer, int64, uint32
from numpy.typing import NDArray
from typing_extensions import TypeGuard

from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter

from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.common import Slice

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.types import Delay_Types, Weight_Delay_Types, Weight_Types
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID

from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)
    from spynnaker.pyNN.models.neuron.synapse_dynamics import (
        AbstractSynapseDynamics)

logger = FormatAdapter(logging.getLogger(__name__))

# Indices of the source and target in the connection list array
_SOURCE = 0
_TARGET = 1
_FIRST_PARAM = 2


def _is_sequential(value: Weight_Delay_Types
                   ) -> TypeGuard[NDArray[numpy.float64]]:
    return isinstance(value, numpy.ndarray)


@dataclass(frozen=True)
class _ExtraParams:
    """
    Information about extra parameters.
    """
    data: NDArray
    names: Sequence[str]


class FromListConnector(AbstractConnector, AbstractGenerateConnectorOnHost):
    """
    Make connections according to a list.
    """
    __slots__ = (
        "__conn_list",
        "__column_names",
        "__sources",
        "__targets",
        "__weights",
        "__delays",
        "__extra_params",
        "__split_conn_list",
        "__split_post_slices")

    def __init__(self, conn_list: Union[None, NDArray, List[Tuple[int, ...]]],
                 column_names: Optional[Sequence[str]] = None, *,
                 safe=True, verbose=False, callback=None):
        """
        :param conn_list:
            A numpy array or a list of tuples, one tuple for each connection.
            Each tuple should contain::

                (pre_idx, post_idx, p1, p2, ..., pn)

            where ``pre_idx`` is the index (i.e. order in the Population,
            not the ID) of the presynaptic neuron, ``post_idx`` is
            the index of the postsynaptic neuron, and
            ``p1``, ``p2``, etc. are the synaptic parameters (e.g.,
            weight, delay, plasticity parameters).
            All tuples/rows must have the same number of items.
        :type conn_list: ~numpy.ndarray or list(tuple(int,int,...))
        :param bool safe:
            if ``True``, check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param column_names: the names of the parameters ``p1``, ``p2``, etc.
            If not provided, it is assumed the parameters are ``weight, delay``
            (for backwards compatibility).
        :type column_names: None or tuple(str) or list(str)
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        """
        super().__init__(safe, callback, verbose)

        self.__column_names = column_names
        self.__split_conn_list: Dict[int, NDArray[integer]] = {}
        self.__split_post_slices: Optional[List[Slice]] = None

        # These are set by the conn_list setter
        self.__conn_list: NDArray
        self.__sources: NDArray[uint32]
        self.__targets: NDArray[uint32]
        self.__delays: Optional[NDArray[floating]]
        self.__weights: Optional[NDArray[floating]]
        self.__extra_params: Optional[_ExtraParams]

        # Call the conn_list setter, as this sets the internal values
        self.conn_list = cast(NDArray, conn_list)  # Bug: python/mypy#3004

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info: SynapseInformation) -> float:
        if self.__delays is None:
            if _is_sequential(synapse_info.delays):
                return float(numpy.max(synapse_info.delays))
            return self._get_delay_maximum(
                synapse_info.delays, len(self.__targets), synapse_info)
        else:
            return numpy.max(self.__delays)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info: SynapseInformation) -> float:
        if self.__delays is None:
            if _is_sequential(synapse_info.delays):
                return float(numpy.min(synapse_info.delays))
            return self._get_delay_minimum(
                synapse_info.delays, len(self.__targets), synapse_info)
        else:
            return numpy.min(self.__delays)

    @overrides(AbstractConnector.get_delay_variance)
    def get_delay_variance(self, delays: Delay_Types,
                           synapse_info: SynapseInformation) -> float:
        if self.__delays is None:
            if _is_sequential(synapse_info.delays):
                return float(numpy.var(synapse_info.delays))
            return AbstractConnector.get_delay_variance(
                self, delays, synapse_info)
        else:
            return numpy.var(self.__delays)

    def __id_to_m_vertex_index(self, n_atoms: int, slices: Sequence[Slice]):
        """ Produce an array that maps from a vertex atom id to the
            machine vertex index of the target
        """
        mapping = numpy.zeros(n_atoms, dtype="uint32")
        for i, s in enumerate(slices):
            mapping[s.get_raster_ids()] = i
        return mapping

    def _split_connections(
            self, n_pre_atoms: int, n_post_atoms: int,
            post_slices: Sequence[Slice]):
        """
        :param list(~pacman.model.graphs.common.Slice) post_slices:
        """
        input_filter = numpy.logical_and(
            self.__targets < n_post_atoms, self.__sources < n_pre_atoms)
        targets = self.__targets[input_filter]
        sources = self.__sources[input_filter]
        weights = (None if self.__weights is None else
                   self.__weights[input_filter])
        delays = (None if self.__delays is None else
                  self.__delays[input_filter])

        # If nothing has changed, use the cache
        if self.__split_post_slices == post_slices:
            return sources, targets, weights, delays

        # If there are no connections, return
        if not len(self.__conn_list):
            self.__split_conn_list = {}
            return sources, targets, weights, delays

        self.__split_post_slices = list(post_slices)
        m_vertex_mapping = self.__id_to_m_vertex_index(
            n_post_atoms, post_slices)

        # Get which index of the from list is on which vertex
        target_vertices = m_vertex_mapping[self.__targets[input_filter]]

        # Get how many on each vertex there are
        index_count = numpy.bincount(
            target_vertices, minlength=len(post_slices))[:len(post_slices)]

        # Get the sort order to put connections on each vertex
        sort_indices = numpy.argsort(target_vertices)

        # Split the sort order in to groups of connection indices
        split_indices = numpy.array(numpy.split(
            sort_indices, numpy.cumsum(index_count)), dtype=object)[:-1]

        # Get the results indexed by hi_atom in the slices
        self.__split_conn_list = {
            post_slices[i].lo_atom: indices
            for i, indices in enumerate(split_indices)
            if len(indices) > 0
        }
        return sources, targets, weights, delays

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:
        mask = None
        delays_handled = False
        if (min_delay is not None and max_delay is not None):
            if self.__delays is not None:
                mask = ((self.__delays >= min_delay) &
                        (self.__delays <= max_delay))
                delays_handled = True
            elif _is_sequential(synapse_info.delays):
                delays = synapse_info.delays
                mask = ((delays >= min_delay) & (delays <= max_delay))
                delays_handled = True
        if mask is None:
            conns = self.__conn_list.copy()
        else:
            conns = self.__conn_list[mask].copy()
        if conns.size == 0:
            return 0

        # Make targets be core indices
        conns[:, _TARGET] //= n_post_atoms

        # Split into sources
        source_split_conns = self.__numpy_group(conns, _SOURCE)

        # Split into groups by post_n_atoms
        target_split_conns = [
            self.__numpy_group(s, _TARGET) for s in source_split_conns]

        # Find the biggest group
        max_targets = max([len(t) for s in target_split_conns for t in s])

        # If no delays just return max targets as this is for all delays
        # If there are delays in the list, this was also handled above
        if min_delay is None or max_delay is None or delays_handled:
            return max_targets

        # If here, there must be no delays in the list, so use the passed in
        # ones
        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            max_targets, min_delay, max_delay, synapse_info)

    @staticmethod
    def __numpy_group(conns: NDArray, column: int) -> List[NDArray]:
        # Sort by the column to group by
        s = conns[conns[:, column].argsort()]

        # Find split points by getting the first indices of the unique items
        # and then removing the first (as that will be 0 and we don't want to
        # split at 0)
        split_points = numpy.unique(s[:, column], return_index=True)[1][1:]

        # Perform the split
        return numpy.array_split(conns, split_points)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        if not len(self.__targets):
            return 0
        return int(numpy.max(numpy.bincount(
            self.__targets.astype(int64, copy=False))))

    @overrides(AbstractConnector.get_weight_mean)
    def get_weight_mean(self, weights: Weight_Types,
                        synapse_info: SynapseInformation) -> float:
        if self.__weights is None:
            if _is_sequential(synapse_info.weights):
                return float(numpy.mean(synapse_info.weights))
            return AbstractConnector.get_weight_mean(
                self, weights, synapse_info)
        else:
            return float(numpy.mean(numpy.abs(self.__weights)))

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        if self.__weights is None:
            if _is_sequential(synapse_info.weights):
                return float(numpy.amax(synapse_info.weights))
            return self._get_weight_maximum(
                synapse_info.weights, len(self.__targets), synapse_info)
        else:
            return float(numpy.amax(numpy.abs(self.__weights)))

    @overrides(AbstractConnector.get_weight_variance)
    def get_weight_variance(self, weights: Weight_Types,
                            synapse_info: SynapseInformation) -> float:
        if self.__weights is None:
            if _is_sequential(synapse_info.weights):
                return float(numpy.var(synapse_info.weights))
            return AbstractConnector.get_weight_variance(
                self, weights, synapse_info)
        else:
            return float(numpy.var(numpy.abs(self.__weights)))

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices: Sequence[Slice], post_vertex_slice: Slice,
            synapse_type: int, synapse_info: SynapseInformation) -> NDArray:
        sources, targets, weights, delays = self._split_connections(
            synapse_info.n_pre_neurons, synapse_info.n_post_neurons,
            post_slices)
        post_lo = post_vertex_slice.lo_atom
        if post_lo not in self.__split_conn_list:
            return numpy.zeros(0, dtype=self.NUMPY_SYNAPSES_DTYPE)
        else:
            indices = self.__split_conn_list[post_lo]

        block = numpy.zeros(len(indices), dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = synapse_info.pre_vertex.get_key_ordered_indices(
            sources[indices])
        block["target"] = post_vertex_slice.get_relative_indices(
            targets[indices])
        # check that conn_list has weights, if not then use the value passed in
        if weights is None:
            if _is_sequential(synapse_info.weights):
                block["weight"] = numpy.array(synapse_info.weights)[indices]
            else:
                block["weight"] = self._generate_weights(
                    block["source"], block["target"], len(indices),
                    post_vertex_slice, synapse_info)
        else:
            block["weight"] = weights[indices]
        # check that conn_list has delays, if not then use the value passed in
        if delays is None:
            if _is_sequential(synapse_info.delays):
                block["delay"] = numpy.array(synapse_info.delays)[indices]
            else:
                block["delay"] = self._generate_delays(
                    block["source"], block["target"], len(indices),
                    post_vertex_slice, synapse_info)
        else:
            block["delay"] = self._clip_delays(delays[indices])
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return f"FromListConnector(n_connections={len(self.__sources)})"

    @property
    def conn_list(self) -> NDArray:
        """
        The connection list.

        :rtype: ~numpy.ndarray
        """
        return self.__conn_list

    @conn_list.setter
    def conn_list(self, conn_list: Union[
            None, NDArray, List[Tuple[int, ...]]]):
        if conn_list is None or not len(conn_list):
            self.__conn_list = numpy.zeros((0, 2), dtype=uint32)
        else:
            self.__conn_list = numpy.array(conn_list)

        # If the shape of the conn_list is 2D, numpy has been able to create
        # a 2D array which means every entry has the same number of values.
        # If this was not possible, raise an exception!
        if len(self.__conn_list.shape) != 2:
            raise InvalidParameterType(
                "Each tuple in the connection list for the"
                " FromListConnector must have the same number of elements")

        # This tells us how many columns are in the list
        n_columns = self.__conn_list.shape[1]
        if n_columns < 2:
            raise InvalidParameterType(
                "Each tuple in the connection list for the"
                " FromListConnector must have at least 2 elements")
        if (self.__column_names is not None and
                n_columns != len(self.__column_names) + _FIRST_PARAM):
            raise InvalidParameterType(
                "The number of column names must match the number of"
                " additional elements in each tuple in the connection list,"
                " not including the pre_idx or post_idx")

        # Get the column names if not specified
        if self.__column_names is not None:
            column_names = self.__column_names
        else:
            if n_columns == 4:
                column_names = ('weight', 'delay')
            elif n_columns == 2:
                column_names = ()
            else:
                raise TypeError(
                    f"Need to set 'column_names' for n_columns={n_columns}")

        # Set the source and targets
        self.__sources = self.__conn_list[:, _SOURCE].astype(numpy.uint32)
        self.__targets = self.__conn_list[:, _TARGET].astype(numpy.uint32)

        # Find any weights
        try:
            weight_column = column_names.index('weight') + _FIRST_PARAM
            self.__weights = self.__conn_list[:, weight_column]
        except ValueError:
            self.__weights = None

        # Find any delays
        try:
            delay_column = column_names.index('delay') + _FIRST_PARAM
            self.__delays = (numpy.rint(
                numpy.array(self.__conn_list[:, delay_column]) *
                SpynnakerDataView.get_simulation_time_step_per_ms()) *
                SpynnakerDataView.get_simulation_time_step_ms())
        except ValueError:
            self.__delays = None

        # Find extra columns
        extra_columns = [
            i + _FIRST_PARAM
            for i, name in enumerate(column_names)
            if name not in ('weight', 'delay')]

        # Check any additional parameters have single values over the whole
        # set of connections (as other things aren't currently supported)
        for i in extra_columns:
            # pylint: disable=wrong-spelling-in-comment
            # numpy.ptp gives the difference between the maximum and
            # minimum values of an array, so if 0, all values are equal
            if numpy.ptp(self.__conn_list[:, i]):
                raise ValueError(
                    f"All values in column {i} "
                    f"({column_names[i - _FIRST_PARAM]}) of a "
                    "FromListConnector must have the same value")

        # Store the extra data
        if extra_columns:
            self.__extra_params = _ExtraParams(
                self.__conn_list[:, extra_columns],
                tuple(
                    column_names[i - _FIRST_PARAM] for i in extra_columns))
        else:
            self.__extra_params = None

    @property
    def column_names(self) -> Optional[Sequence[str]]:
        """
        The names of the columns in the array after the first two.
        Of particular interest is whether ``weight`` and ``delay`` columns
        are present.

        :rtype: list(str)
        """
        return self.__column_names

    @column_names.setter
    def column_names(self, column_names: Optional[Sequence[str]]):
        self.__column_names = column_names

    def get_extra_parameters(self) -> Optional[NDArray]:
        """
        Getter for the extra parameters. Excludes ``weight`` and
        ``delay`` columns.

        :return: The extra parameters
        :rtype: ~numpy.ndarray
        """
        return self.__extra_params.data if self.__extra_params else None

    def get_extra_parameter_names(self) -> Optional[Sequence[str]]:
        """
        Get the names of the extra parameters.

        :rtype: list(str)
        """
        return self.__extra_params.names if self.__extra_params else None

    @overrides(AbstractConnector.get_connected_vertices)
    def get_connected_vertices(
            self, s_info: SynapseInformation,
            source_vertex: ApplicationVertex,
            target_vertex: ApplicationVertex) -> Sequence[
                Tuple[MachineVertex, Sequence[AbstractVertex]]]:
        # Divide the targets into bins based on post slices
        post_slices = [m.vertex_slice
                       for m in target_vertex.splitter.get_in_coming_vertices(
                           SPIKE_PARTITION_ID)]
        pre_vertices = source_vertex.splitter.get_out_going_vertices(
            SPIKE_PARTITION_ID)
        pre_slices = [m.vertex_slice for m in pre_vertices]

        post_mapping = self.__id_to_m_vertex_index(
            s_info.n_post_neurons, post_slices)
        pre_mapping = self.__id_to_m_vertex_index(
            s_info.n_pre_neurons, pre_slices)

        input_filter = numpy.logical_and(
            self.__targets < target_vertex.n_atoms,
            self.__sources < source_vertex.n_atoms)

        target_vertices = post_mapping[self.__targets[input_filter]]
        source_vertices = pre_mapping[self.__sources[input_filter]]

        # Join the groups from both axes
        n_bins = (len(pre_slices), len(post_slices))
        joined_indices = numpy.ravel_multi_index(
            (source_vertices, target_vertices), n_bins, mode="clip")

        # Get a count of the indices in each bin
        index_count = numpy.bincount(
            joined_indices, minlength=numpy.prod(n_bins))

        pre_post_lo = [(pre.lo_atom, post.lo_atom) for pre in pre_slices
                       for post in post_slices]

        # Put the counts into a dict by hi-atom
        split_counts = {
            pre_post: count
            for pre_post, count in zip(pre_post_lo, index_count)
            if count > 0
        }

        return [
            (m_vert, [s_vert for s_vert in pre_vertices
                      if (s_vert.vertex_slice.lo_atom,
                          m_vert.vertex_slice.lo_atom) in split_counts])
            for m_vert in target_vertex.splitter.get_in_coming_vertices(
                SPIKE_PARTITION_ID)
        ]

    def _apply_parameters_to_synapse_type(
            self, synapse_type: AbstractSynapseDynamics):
        """
        :param AbstractStaticSynapseDynamics synapse_type:
        """
        if self.__extra_params:
            for i, name in enumerate(self.__extra_params.names):
                synapse_type.set_value(name, self.__extra_params.data[:, i])

    @overrides(AbstractConnector.validate_connection)
    def validate_connection(
            self, application_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation):
        out_of_range_targets = self.__targets >= synapse_info.n_post_neurons
        if any(out_of_range_targets):
            logger.warning(
                "Some targets are out of range: {}",
                self.__conn_list[out_of_range_targets])
        out_of_range_sources = self.__sources >= synapse_info.n_pre_neurons
        if any(out_of_range_sources):
            logger.warning(
                "Some sources are out of range: {}",
                self.__conn_list[out_of_range_sources])
