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

from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import SynapseInformation
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge)


class OneToOneOffsetConnector(
        AbstractGenerateConnectorOnMachine,
        AbstractGenerateConnectorOnHost):
    """
    A Connector that connects each pre-neuron to a post-neuron offset by a
    specific amount, positive or negative.  If this goes beyond the start or
    end of the post neurons, it can optionally wrap around.  Additional options
    include a group size, where the offset and wrap is applied repeatedly to
    subsets of neurons.

    In the current implementation it is assumed that the pre- and
    post-populations have the same number of neurons, and that the number of
    neurons is divisible by the group size if specified.  The offset must also
    be smaller than the group size or the number of neurons.
    """

    __slots__ = ("__n_neurons_per_group", "__offset", "__wrap")

    def __init__(self, offset: int, wrap: bool,
                 n_neurons_per_group: Optional[int] = None,
                 safe: bool = True, verbose: bool = False,
                 callback: None = None):
        """
        :param offset:
            The offset to apply to the pre-neuron index to get the post neuron
            index.  This can be positive or negative.
        :param wrap:
            Whether to wrap around the start or end of the post neurons if the
            post neuron id is out of range.
        :param n_neurons_per_group:
            The number of neurons in each group.
            Must be a positive integer divisor of source.size
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
        self.__offset = offset
        self.__wrap = wrap

    def __n_connections(self, synapse_info: SynapseInformation):
        if self.__wrap:
            # If there is a wrap, there will always be a next connection
            return synapse_info.n_pre_neurons

        n_groups = 1
        if self.__n_neurons_per_group is not None:
            n_groups = synapse_info.n_pre_neurons // self.__n_neurons_per_group

        # If there isn't a wrap, there are always offset less per group
        return synapse_info.n_pre_neurons - (n_groups * abs(self.__offset))

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

        # At most each pre-neuron will one post neuron
        return 1

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        # At most each post neuron will be targeted by one pre-neuron
        return 1

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        return self._get_weight_maximum(
            synapse_info.weights, self.__n_connections(synapse_info),
            synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices: Sequence[Slice], post_vertex_slice: Slice,
            synapse_type: int, synapse_info: SynapseInformation) -> NDArray:
        group_size = self.__n_neurons_per_group
        if group_size is None:
            group_size = synapse_info.n_pre_neurons

        # pylint: disable=protected-access
        post_lo, post_hi = synapse_info.pre_population._view_range
        pre_lo, pre_hi = synapse_info.pre_population._view_range
        post_start = max(post_vertex_slice.lo_atom, post_lo)
        post_end = min(post_vertex_slice.hi_atom + 1, post_hi + 1)
        post_group, post_value = divmod(post_start, group_size)

        pre_start = pre_lo + (post_group * group_size)
        pre_end = min(pre_start + group_size, pre_hi)

        pres = list()
        posts = list()
        for post in range(post_start, post_end):
            pre = post - self.__offset
            if pre < pre_start:
                if self.__wrap:
                    pre += group_size
                else:
                    continue
            if pre > pre_end:
                if self.__wrap:
                    pre -= group_size
                else:
                    continue
            pres.append(pre)
            posts.append(post)

            post_value += 1
            if post_value == group_size:
                post_value = 0
                pre_start += group_size
                pre_end = min(pre_start + group_size, pre_hi)
                if pre_start >= pre_hi:
                    break

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
        return (f"offsetConnector(offset={self.__offset}, wrap={self.__wrap}, "
                f"n_neurons_per_group={self.__n_neurons_per_group})")

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self) -> int:
        return ConnectorIDs.ONE_TO_ONE_OFFSET_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_params)
    def gen_connector_params(
            self, synapse_info: SynapseInformation) -> NDArray[uint32]:
        n_values = self.__n_neurons_per_group
        if n_values is None:
            n_values = synapse_info.n_pre_neurons
        return numpy.array([self.__offset, int(self.__wrap), n_values],
                           dtype=uint32)

    @property
    @overrides(
        AbstractGenerateConnectorOnMachine.gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self) -> int:
        return BYTES_PER_WORD * 3

    @overrides(AbstractConnector.validate_connection)
    def validate_connection(
            self, application_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation):
        if (synapse_info.pre_population.size !=
                synapse_info.post_population.size):
            raise NotImplementedError(
                "OneToOneOffsetConnector is only designed to be used with "
                "populations that are the same size as each other")
        if self.__n_neurons_per_group is not None:
            if self.__n_neurons_per_group > synapse_info.pre_population.size:
                raise ValueError(
                    "OneToOneOffsetConnector cannot be used with a group size "
                    "larger than the population size")
            if ((synapse_info.post_population.size /
                 self.__n_neurons_per_group) !=
                    (synapse_info.post_population.size //
                     self.__n_neurons_per_group)):
                raise NotImplementedError(
                    "The number of neurons in each population must be "
                    "divisible by the number of neurons per group")

        n_values = self.__n_neurons_per_group
        if n_values is None:
            n_values = synapse_info.n_pre_neurons
        if n_values < abs(self.__offset):
            raise ValueError(
                "The offset must be smaller than the number of neurons")
