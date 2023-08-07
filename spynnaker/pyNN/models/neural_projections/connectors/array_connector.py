# Copyright (c) 2017 The University of Manchester
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
import numpy
from numpy import uint8
from numpy.typing import NDArray
from typing import Sequence, Optional, TYPE_CHECKING
from spinn_utilities.overrides import overrides
from pacman.model.graphs.common import Slice
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import SynapseInformation


class ArrayConnector(AbstractConnector, AbstractGenerateConnectorOnHost):
    """
    Make connections using an array of integers based on the IDs
    of the neurons in the pre- and post-populations.
    """

    __slots__ = (
        "__array",
        "__array_dims",
        "__n_total_connections")

    def __init__(self, array: NDArray[uint8],
                 safe=True, callback=None, verbose=False):
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
    def get_delay_maximum(self, synapse_info: SynapseInformation):
        return self._get_delay_maximum(
            synapse_info.delays, len(self.__array), synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info: SynapseInformation):
        return self._get_delay_minimum(
            synapse_info.delays, len(self.__array), synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:
        # Break the array into n_post_atoms units
        split_positions = numpy.arange(
            0, synapse_info.n_post_neurons, n_post_atoms)
        split_array = numpy.array_split(self.__array, split_positions)

        # Sum the 1s in each split row
        sum_rows = [numpy.sum(s, axis=1) for s in split_array]

        # Find the maximum of the rows
        max_connections_row = max([x for y in sum_rows for x in y])

        if min_delay is None or max_delay is None:
            return max_connections_row

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays, self.__n_total_connections,
            max_connections_row, min_delay, max_delay, synapse_info)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        # Max number per column is required
        max_connections_col = 0
        for j in range(self.__array_dims[1]):
            n_connections_col = 0
            for i in range(self.__array_dims[0]):
                if self.__array[i, j] == 1:
                    n_connections_col = 0

            if n_connections_col > max_connections_col:
                max_connections_col = n_connections_col

        return max_connections_col

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        return self._get_weight_maximum(
            synapse_info.weights, self.__n_total_connections, synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices: Sequence[Slice], post_vertex_slice: Slice,
            synapse_type: int, synapse_info: SynapseInformation) -> NDArray:
        pre_neurons = []
        post_neurons = []
        n_connections = 0
        pre_lo = 0
        pre_hi = synapse_info.n_pre_neurons - 1
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
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["delay"] = self._generate_delays(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return f"ArrayConnector({self.__array})"
