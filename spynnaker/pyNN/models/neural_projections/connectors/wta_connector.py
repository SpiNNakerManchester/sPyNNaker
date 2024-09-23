# Copyright (c) 2024 The University of Manchester
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
from typing import Sequence, Optional, TYPE_CHECKING

import numpy
from numpy import uint32
from numpy.typing import NDArray

from spinn_utilities.overrides import overrides

from pacman.model.graphs.common import Slice

from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.interface.ds import DataType
from spynnaker.pyNN.types import Weight_Types

from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import SynapseInformation
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge)


class WTAConnector(AbstractGenerateConnectorOnMachine,
                   AbstractGenerateConnectorOnHost):
    """
    Normally used to connect a population to itself, the assumption is that
    the population can represent multiple potential winner-takes-all groups,
    where each is independent.  The connector will connect each pre-neuron in a
    group to each post-neuron in the same group, except the one with the same
    index.

    Can be used for two distinct populations BUT
    they must have the same number of neurons
    and neuron X of the source will not connect to neuron X of the target.
    """

    __slots__ = ("__n_neurons_per_group", "__weights")

    def __init__(self, n_neurons_per_group: Optional[int] = None,
                 weights: Optional[NDArray[numpy.float64]] = None,
                 safe: bool = True, verbose: Optional[bool] = None,
                 callback: None = None):
        """
        :param n_neurons_per_group:
            The number of neurons in each winner-takes-all group.
            Must be a positive integer divisor of source.size
        :param weights:
            The weights for one group of neurons
            Single Value, RandomDistribution and string values not supported.
        :param safe:
            If ``True``, check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        """
        super().__init__(safe, callback, verbose)
        self.__n_neurons_per_group = n_neurons_per_group
        self.__weights = weights
        self.__check_weights(weights, n_neurons_per_group)

    def __check_weights(self, weights: Optional[NDArray[numpy.float64]],
                        n_neurons_per_group: Optional[int]):
        if weights is not None and n_neurons_per_group is not None:
            n_weights = n_neurons_per_group * (n_neurons_per_group - 1)
            if len(weights) != n_weights:
                raise ValueError(
                    "The number of weights must be equal to the number of "
                    f"connections in a group "
                    f"({n_neurons_per_group} x ({n_neurons_per_group} - 1) = "
                    f"{n_weights})")

    def __n_connections(self, synapse_info: SynapseInformation):
        # If not specified, use the smallest of the two populations
        if self.__n_neurons_per_group is None:
            n_values = min(synapse_info.n_pre_neurons,
                           synapse_info.n_post_neurons)
            return n_values * (n_values - 1)

        # Find out how many groups there are at most
        n_groups_pre = synapse_info.n_pre_neurons // self.__n_neurons_per_group
        n_groups_post = (synapse_info.n_post_neurons //
                         self.__n_neurons_per_group)
        n_groups = min(n_groups_pre, n_groups_post)
        return (n_groups * self.__n_neurons_per_group *
                (self.__n_neurons_per_group - 1))

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info: SynapseInformation) -> float:
        return self._get_delay_maximum(
            synapse_info.delays, self.__n_connections(synapse_info),
            synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info: SynapseInformation) -> float:
        return self._get_delay_minimum(
            synapse_info.delays, self.__n_connections(synapse_info),
            synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:

        # At most, a pre-neuron will target all post-neurons in the group,
        # except the one with the same index.  For a given subset of post
        # atoms, there might be fewer to target...
        n_targets = n_post_atoms
        if self.__n_neurons_per_group is not None:
            n_targets = min(self.__n_neurons_per_group - 1, n_post_atoms)
        if min_delay is None or max_delay is None:
            return n_targets

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays, self.__n_connections(synapse_info),
            n_targets, min_delay, max_delay, synapse_info)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        # At most, each post-neuron will be targeted by all pre-neurons in a
        # group, except the one with the same index.
        if self.__n_neurons_per_group is None:
            return min(synapse_info.n_pre_neurons,
                       synapse_info.n_post_neurons) - 1
        return self.__n_neurons_per_group - 1

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        if self.__weights is not None:
            return numpy.amax(self.__weights)
        return self._get_weight_maximum(
            synapse_info.weights, self.__n_connections(synapse_info),
            synapse_info)

    @overrides(AbstractConnector.get_weight_mean)
    def get_weight_mean(self, weights: Weight_Types,
                        synapse_info: SynapseInformation) -> float:
        if self.__weights is None:
            return AbstractConnector.get_weight_mean(
                self, weights, synapse_info)
        else:
            return float(numpy.mean(numpy.abs(self.__weights)))

    @overrides(AbstractConnector.get_weight_variance)
    def get_weight_variance(self, weights: Weight_Types,
                            synapse_info: SynapseInformation) -> float:
        if self.__weights is None:
            return AbstractConnector.get_weight_variance(
                self, weights, synapse_info)
        else:
            return float(numpy.var(numpy.abs(self.__weights)))

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices: Sequence[Slice], post_vertex_slice: Slice,
            synapse_type: int, synapse_info: SynapseInformation) -> NDArray:
        group_size = self.__n_neurons_per_group
        if group_size is None:
            group_size = min(synapse_info.n_pre_neurons,
                             synapse_info.n_post_neurons)
        # pylint: disable=protected-access
        post_lo, post_hi = synapse_info.pre_population._view_range
        pre_lo, pre_hi = synapse_info.pre_population._view_range
        post_start = max(post_vertex_slice.lo_atom, post_lo)
        post_end = min(post_vertex_slice.hi_atom + 1, post_hi + 1)
        post_group, post_value = divmod(post_start, group_size)

        pre_start = pre_lo + (post_group * group_size)
        pre_end = min(pre_start + group_size, pre_hi + 1)
        n_values = pre_end - pre_start

        pres = list()
        posts = list()
        for post in range(post_start, post_end):
            for value in range(n_values):
                if value != post_value:
                    pres.append(pre_start + value)
                    posts.append(post)

            post_value += 1
            if post_value == group_size:
                post_value = 0
                pre_start += group_size
                pre_end = min(pre_start + group_size, pre_hi + 1)
                if pre_start >= pre_hi:
                    break
                n_values = pre_end - pre_start
        block = numpy.zeros(len(pres), dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = pres
        block["target"] = posts
        block["weight"] = self._generate_weights(
            block["source"], block["target"], len(pres), post_vertex_slice,
            synapse_info)
        block["delay"] = self._generate_delays(
            block["source"], block["target"], len(pres), post_vertex_slice,
            synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return f"WTAConnector(n_neuron_per_group={self.__n_neurons_per_group})"

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self) -> int:
        return ConnectorIDs.WTA_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_params)
    def gen_connector_params(
            self, synapse_info: SynapseInformation) -> NDArray[uint32]:
        n_values = self.__n_neurons_per_group
        if n_values is None:
            n_values = min(synapse_info.n_pre_neurons,
                           synapse_info.n_post_neurons)
        has_weights = int(self.__weights is not None)
        params = numpy.array([n_values, has_weights], dtype=uint32)
        if self.__weights is None:
            weights = numpy.zeros(0, dtype=uint32)
        else:
            weights = DataType.S1615.encode_as_numpy_int_array(self.__weights)
        return numpy.concatenate((params, weights))

    @property
    @overrides(
        AbstractGenerateConnectorOnMachine.gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self) -> int:
        size = BYTES_PER_WORD * 2
        if self.__weights is not None:
            size += len(self.__weights) * BYTES_PER_WORD
        return size

    @overrides(AbstractConnector.validate_connection)
    def validate_connection(
            self, application_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation):
        if (synapse_info.pre_population.size !=
                synapse_info.post_population.size):
            raise ValueError(
                "WTAConnector can only be used with populations that are "
                "the same size as each other")
        if self.__n_neurons_per_group is not None:
            if self.__n_neurons_per_group > synapse_info.pre_population.size:
                raise ValueError(
                    "WTAConnector cannot be used with a group size larger "
                    "than the population size")
            if ((synapse_info.post_population.size /
                 self.__n_neurons_per_group) !=
                    (synapse_info.post_population.size //
                     self.__n_neurons_per_group)):
                raise ValueError(
                    "The number of neurons in each population must be "
                    "divisible by the number of neurons per group")
        n_neurons_per_group = self.__n_neurons_per_group
        if n_neurons_per_group is None:
            n_neurons_per_group = min(synapse_info.pre_population.size,
                                      synapse_info.post_population.size)
        self.__check_weights(self.__weights, n_neurons_per_group)
