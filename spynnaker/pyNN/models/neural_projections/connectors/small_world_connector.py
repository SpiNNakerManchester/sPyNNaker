# Copyright (c) 2016 The University of Manchester
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
from typing import Optional, Sequence, TYPE_CHECKING

import numpy
from numpy.typing import NDArray

from pyNN.random import NumpyRNG

from spinn_utilities.overrides import overrides

from pacman.model.graphs.common import Slice

from spinn_front_end_common.utilities.exceptions import ConfigurationException

from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import SynapseInformation


class SmallWorldConnector(AbstractConnector, AbstractGenerateConnectorOnHost):
    """
    A connector that uses connection statistics based on the Small World
    network connectivity model.

    .. note::
        This is typically used from a population to itself.
    """
    __slots__ = (
        "__degree",
        "__mask",
        "__n_connections",
        "__rewiring",
        "__rng")

    def __init__(
            self, degree: float, rewiring: float,
            allow_self_connections: bool = True,
            n_connections: Optional[int] = None,
            rng: Optional[NumpyRNG] = None,
            safe: bool = True, callback: None = None, verbose: bool = False):
        """
        :param degree:
            the region length where nodes will be connected locally
        :param rewiring: the probability of rewiring each edge
        :param allow_self_connections:
            if the connector is used to connect a Population to itself, this
            flag determines whether a neuron is allowed to connect to itself,
            or only to other neurons in the Population.
            False is currently unsupported!
        :param n_connections:
            if specified, the number of efferent synaptic connections per
            neuron
        :param rng:
            Seeded random number generator, or ``None`` to make one when
            needed.
        :param safe:
            If ``True``, check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        :param verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        """
        super().__init__(safe, callback, verbose)
        self.__rewiring = rewiring
        self.__degree = degree
        if not allow_self_connections:
            raise NotImplementedError(
                "disabling self connections currently not supported")
        self.__mask: Optional[NDArray] = None
        self.__n_connections = 0
        self.__rng = rng or NumpyRNG()

        if n_connections is not None:
            raise NotImplementedError(
                "n_connections is not implemented for"
                " SmallWorldConnector on this platform")

    @overrides(AbstractConnector.set_projection_information)
    def set_projection_information(
            self, synapse_info: SynapseInformation) -> None:
        super().set_projection_information(synapse_info)
        self._set_n_connections(synapse_info)

    def _set_n_connections(self, synapse_info: SynapseInformation) -> None:
        if self.space is None:
            raise ConfigurationException("a metric space is required")
        # Get the probabilities up-front for now
        # TODO: Work out how this can be done statistically
        # space.distances(...) expects N,3 array in PyNN0.7, but 3,N in PyNN0.8
        pre_positions = synapse_info.pre_population.positions
        post_positions = synapse_info.post_population.positions

        distances = self.space.distances(
            pre_positions, post_positions, False)

        # PyNN 0.8 returns a flattened (C-style) array from space.distances,
        # so the easiest thing to do here is to reshape back to the "expected"
        # PyNN 0.7 shape; otherwise later code gets confusing and difficult
        if len(distances.shape) == 1:
            d = numpy.reshape(distances, (pre_positions.shape[0],
                                          post_positions.shape[0]))
        else:
            d = distances

        self.__mask = (d < self.__degree).astype(numpy.float64)
        self.__n_connections = int(math.ceil(numpy.sum(self.__mask)))

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info: SynapseInformation) -> float:
        return self._get_delay_maximum(
            synapse_info.delays, self.__n_connections, synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info: SynapseInformation) -> float:
        return self._get_delay_minimum(
            synapse_info.delays, self.__n_connections, synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:
        assert self.__mask is not None
        # Break the array into n_post_atoms units
        split_positions = numpy.arange(
            0, synapse_info.n_post_neurons, n_post_atoms)
        split_array = numpy.array_split(self.__mask, split_positions)

        # Sum the 1s in each split row
        sum_rows = [numpy.sum(s, axis=1) for s in split_array]

        # Find the maximum of the rows
        n_connections = max([x for y in sum_rows for x in y])

        if min_delay is None or max_delay is None:
            return n_connections

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays, self.__n_connections, n_connections,
            min_delay, max_delay, synapse_info)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        assert self.__mask is not None
        return numpy.amax([
            numpy.sum(self.__mask[:, i]) for i in range(
                synapse_info.n_post_neurons)])

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        return self._get_weight_maximum(
            synapse_info.weights, self.__n_connections, synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices: Sequence[Slice], post_vertex_slice: Slice,
            synapse_type: int, synapse_info: SynapseInformation) -> NDArray:
        if self.__mask is None:
            return numpy.zeros(0, dtype=self.NUMPY_SYNAPSES_DTYPE)
        raster_ids = post_vertex_slice.get_raster_ids()
        ids = numpy.where(self.__mask[:, raster_ids])
        n_connections = len(ids[0])

        block = numpy.zeros(n_connections, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = synapse_info.pre_vertex.get_key_ordered_indices(
            ids[0] % synapse_info.n_pre_neurons)
        block["target"] = post_vertex_slice.get_relative_indices(
            raster_ids[ids[1]])
        block["weight"] = self._generate_weights(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["delay"] = self._generate_delays(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["synapse_type"] = synapse_type

        # Re-wire some connections
        rewired = numpy.where(
            self.__rng.next(n_connections) < self.__rewiring)[0]
        block["target"][rewired] = (
            (self.__rng.next(rewired.size) * (post_vertex_slice.n_atoms - 1)) +
            post_vertex_slice.lo_atom)

        return block

    def __repr__(self) -> str:
        return ("SmallWorldConnector"
                f"(degree={self.__degree}, rewiring={self.__rewiring})")
