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

import numpy
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import InvalidParameterType
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID

# Indices of the source and target in the connection list array
_SOURCE = 0
_TARGET = 1
_FIRST_PARAM = 2


class FromListConnector(AbstractConnector, AbstractGenerateConnectorOnHost):
    """
    Make connections according to a list.
    """
    __slots__ = [
        "__conn_list",
        "__column_names",
        "__sources",
        "__targets",
        "__weights",
        "__delays",
        "__extra_parameters",
        "__extra_parameter_names",
        "__split_conn_list",
        "__split_post_slices"]

    def __init__(self, conn_list, safe=True, verbose=False, column_names=None,
                 callback=None):
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
        self.__split_conn_list = {}
        self.__split_post_slices = None

        # Call the conn_list setter, as this sets the internal values
        self.conn_list = conn_list

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        if self.__delays is None:
            if hasattr(synapse_info.delays, "__len__"):
                return numpy.max(synapse_info.delays)
            return self._get_delay_maximum(
                synapse_info.delays, len(self.__targets), synapse_info)
        else:
            return numpy.max(self.__delays)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info):
        if self.__delays is None:
            if hasattr(synapse_info.delays, "__len__"):
                return numpy.min(synapse_info.delays)
            return self._get_delay_minimum(
                synapse_info.delays, len(self.__targets), synapse_info)
        else:
            return numpy.min(self.__delays)

    @overrides(AbstractConnector.get_delay_variance)
    def get_delay_variance(self, delays, synapse_info):
        if self.__delays is None:
            if hasattr(synapse_info.delays, "__len__"):
                return numpy.var(synapse_info.delays)
            return AbstractConnector.get_delay_variance(
                self, delays, synapse_info)
        else:
            return numpy.var(self.__delays)

    def __id_to_m_vertex_index(self, n_atoms, slices):
        """ Produce an array that maps from a vertex atom id to the
            machine vertex index of the target
        """
        mapping = numpy.zeros(n_atoms, dtype="uint32")
        for i, s in enumerate(slices):
            mapping[s.get_raster_ids()] = i
        return mapping

    def _split_connections(self, n_atoms, post_slices):
        """
        :param list(~pacman.model.graphs.common.Slice) post_slices:
        """
        # If nothing has changed, use the cache
        if self.__split_post_slices == post_slices:
            return False

        # If there are no connections, return
        if not len(self.__conn_list):
            self.__split_conn_list = {}
            return True

        self.__split_post_slices = list(post_slices)
        m_vertex_mapping = self.__id_to_m_vertex_index(n_atoms, post_slices)

        # Get which index of the fromlist is on which vertex
        target_vertices = m_vertex_mapping[self.__targets]

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
        return True

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms, synapse_info, min_delay=None,
            max_delay=None):

        mask = None
        delays_handled = False
        if (min_delay is not None and max_delay is not None and
                (self.__delays is not None or
                 hasattr(synapse_info.delays, "__len__"))):
            delays = self.__delays
            if delays is None:
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

    def __numpy_group(self, conns, column):
        # Sort by the column to group by
        s = conns[conns[:, column].argsort()]

        # Find split points by getting the first indices of the unique items
        # and then removing the first (as that will be 0 and we don't want to
        # split at 0)
        split_points = numpy.unique(s[:, column], return_index=True)[1][1:]

        # Perform the split
        return numpy.array_split(conns, split_points)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        if not len(self.__targets):
            return 0
        # pylint: disable=too-many-arguments
        return numpy.max(numpy.bincount(
            self.__targets.astype('int64', copy=False)))

    @overrides(AbstractConnector.get_weight_mean)
    def get_weight_mean(self, weights, synapse_info):
        if self.__weights is None:
            if hasattr(synapse_info.weights, "__len__"):
                return numpy.mean(synapse_info.weights)
            return AbstractConnector.get_weight_mean(
                self, weights, synapse_info)
        else:
            return numpy.mean(numpy.abs(self.__weights))

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        # pylint: disable=too-many-arguments
        if self.__weights is None:
            if hasattr(synapse_info.weights, "__len__"):
                return numpy.amax(synapse_info.weights)
            return self._get_weight_maximum(
                synapse_info.weights, len(self.__targets), synapse_info)
        else:
            return numpy.amax(numpy.abs(self.__weights))

    @overrides(AbstractConnector.get_weight_variance)
    def get_weight_variance(self, weights, synapse_info):
        # pylint: disable=too-many-arguments
        if self.__weights is None:
            if hasattr(synapse_info.weights, "__len__"):
                return numpy.var(synapse_info.weights)
            return AbstractConnector.get_weight_variance(
                self, weights, synapse_info)
        else:
            return numpy.var(numpy.abs(self.__weights))

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices, post_vertex_slice, synapse_type, synapse_info):
        # pylint: disable=too-many-arguments
        self._split_connections(synapse_info.n_post_neurons, post_slices)
        post_lo = post_vertex_slice.lo_atom
        if post_lo not in self.__split_conn_list:
            return numpy.zeros(0, dtype=self.NUMPY_SYNAPSES_DTYPE)
        else:
            indices = self.__split_conn_list[post_lo]
        # pylint: disable=protected-access
        pre_raster_to_core = self._get_raster_to_core(
            self._get_pre_slices(synapse_info.pre_population._vertex))
        post_raster_to_core = self._get_raster_to_core(post_slices)

        block = numpy.zeros(len(indices), dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = pre_raster_to_core[self.__sources[indices]]
        block["target"] = post_raster_to_core[self.__targets[indices]]
        # check that conn_list has weights, if not then use the value passed in
        if self.__weights is None:
            if hasattr(synapse_info.weights, "__len__"):
                block["weight"] = numpy.array(synapse_info.weights)[indices]
            else:
                block["weight"] = self._generate_weights(
                    block["source"], block["target"], len(indices),
                    post_vertex_slice, synapse_info)
        else:
            block["weight"] = self.__weights[indices]
        # check that conn_list has delays, if not then use the value passed in
        if self.__delays is None:
            if hasattr(synapse_info.delays, "__len__"):
                block["delay"] = numpy.array(synapse_info.delays)[indices]
            else:
                block["delay"] = self._generate_delays(
                    block["source"], block["target"], len(indices),
                    post_vertex_slice, synapse_info)
        else:
            block["delay"] = self._clip_delays(self.__delays[indices])
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return f"FromListConnector(n_connections={len(self.__sources)})"

    @property
    def conn_list(self):
        """
        The connection list.

        :rtype: ~numpy.ndarray
        """
        return self.__conn_list

    @conn_list.setter
    def conn_list(self, conn_list):
        if conn_list is None or not len(conn_list):
            self.__conn_list = numpy.zeros((0, 2), dtype="uint32")
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
        column_names = self.__column_names
        if self.__column_names is None:
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
        self.__weights = None
        try:
            weight_column = column_names.index('weight') + _FIRST_PARAM
            self.__weights = self.__conn_list[:, weight_column]
        except ValueError:
            pass

        # Find any delays
        self.__delays = None
        try:
            delay_column = column_names.index('delay') + _FIRST_PARAM
            self.__delays = (numpy.rint(
                numpy.array(self.__conn_list[:, delay_column]) *
                SpynnakerDataView.get_simulation_time_step_per_ms()) *
                SpynnakerDataView.get_simulation_time_step_ms())
        except ValueError:
            pass

        # Find extra columns
        extra_columns = list()
        for i, name in enumerate(column_names):
            if name not in ('weight', 'delay'):
                extra_columns.append(i + _FIRST_PARAM)

        # Check any additional parameters have single values over the whole
        # set of connections (as other things aren't currently supported
        for i in extra_columns:
            # numpy.ptp gives the difference between the maximum and
            # minimum values of an array, so if 0, all values are equal
            if numpy.ptp(self.__conn_list[:, i]):
                raise ValueError(
                    f"All values in column {i} "
                    f"({column_names[i - _FIRST_PARAM]}) of a "
                    "FromListConnector must have the same value")

        # Store the extra data
        self.__extra_parameters = None
        self.__extra_parameter_names = None
        if extra_columns:
            self.__extra_parameters = self.__conn_list[:, extra_columns]
            self.__extra_parameter_names = [
                column_names[i - _FIRST_PARAM] for i in extra_columns]

    @property
    def column_names(self):
        """
        The names of the columns in the array after the first two.
        Of particular interest is whether ``weight`` and ``delay`` columns
        are present.

        :rtype: list(str)
        """
        return self.__column_names

    @column_names.setter
    def column_names(self, column_names):
        self.__column_names = column_names

    def get_extra_parameters(self):
        """
        Getter for the extra parameters. Excludes ``weight`` and
        ``delay`` columns.

        :return: The extra parameters
        :rtype: ~numpy.ndarray
        """
        return self.__extra_parameters

    def get_extra_parameter_names(self):
        """
        Get the names of the extra parameters.

        :rtype: list(str)
        """
        return self.__extra_parameter_names

    @overrides(AbstractConnector.get_connected_vertices)
    def get_connected_vertices(self, s_info, source_vertex, target_vertex):
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

        target_vertices = post_mapping[self.__targets]
        source_vertices = pre_mapping[self.__sources]

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

    def _apply_parameters_to_synapse_type(self, synapse_type):
        """
        :param AbstractStaticSynapseDynamics synapse_type:
        """
        if self.__extra_parameter_names:
            for i, name in enumerate(self.__extra_parameter_names):
                synapse_type.set_value(name, self.__extra_parameters[:, i])
