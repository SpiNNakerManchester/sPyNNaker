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

import numpy
from spinn_utilities.overrides import overrides
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)


class ArrayConnector(AbstractConnector, AbstractGenerateConnectorOnHost):
    """ Make connections using an array of integers based on the IDs\
        of the neurons in the pre- and post-populations.
    """

    __slots__ = [
        "__array", "__array_dims", "__n_total_connections"]

    def __init__(self, array, safe=True, callback=None, verbose=False):
        """
        :param array:
            An explicit boolean matrix that specifies the connections
            between the pre- and post-populations
            (see PyNN documentation). Must be 2D in practice.
        :type array: ~numpy.ndarray(2, ~numpy.uint8)
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If False, this check is skipped.
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        """
        super().__init__(safe, callback, verbose)
        self.__array = array
        # we can get the total number of connections straight away
        # from the boolean matrix
        n_total_connections = 0
        # array shape
        dims = array.shape
        for i in range(dims[0]):
            for j in range(dims[1]):
                if array[i, j] == 1:
                    n_total_connections += 1

        self.__n_total_connections = n_total_connections
        self.__array_dims = dims

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        return self._get_delay_maximum(
            synapse_info.delays, len(self.__array), synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info):
        return self._get_delay_minimum(
            synapse_info.delays, len(self.__array), synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, synapse_info, min_delay=None,
            max_delay=None):
        n_connections = 0
        post_lo = post_vertex_slice.lo_atom
        post_hi = post_vertex_slice.hi_atom
        for i in range(self.__array_dims[0]):
            for j in range(post_lo, post_hi+1):
                if self.__array[i, j] == 1:
                    n_connections += 1

        if min_delay is None and max_delay is None:
            return n_connections

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays, self.__n_total_connections, n_connections,
            min_delay, max_delay, synapse_info)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        return self.__n_total_connections

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        return self._get_weight_maximum(
            synapse_info.weights, self.__n_total_connections, synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, post_slices, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        pre_neurons = []
        post_neurons = []
        n_connections = 0
        pre_lo = pre_vertex_slice.lo_atom
        pre_hi = pre_vertex_slice.hi_atom
        post_lo = post_vertex_slice.lo_atom
        post_hi = post_vertex_slice.hi_atom
        for i in range(pre_lo, pre_hi+1):
            for j in range(post_lo, post_hi+1):
                if self.__array[i, j] == 1:
                    pre_neurons.append(i)
                    post_neurons.append(j)
                    n_connections += 1

        # Feed the arrays calculated above into the block structure
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        block["source"] = pre_neurons
        block["target"] = post_neurons
        block["weight"] = self._generate_weights(
            block["source"], block["target"], n_connections, None,
            pre_vertex_slice, post_vertex_slice, synapse_info)
        block["delay"] = self._generate_delays(
            block["source"], block["target"], n_connections, None,
            pre_vertex_slice, post_vertex_slice, synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "ArrayConnector({})".format(self.__array)
