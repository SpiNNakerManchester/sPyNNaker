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
import logging
import math
from typing import Optional, Sequence, TYPE_CHECKING

import numpy
from numpy.typing import NDArray

from pyNN.random import NumpyRNG

from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter

from pacman.model.graphs.common import Slice

from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.utilities.exceptions import ConfigurationException

from spynnaker.pyNN.utilities.utility_calls import (
    get_probable_maximum_selected, get_probable_minimum_selected, check_rng)
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)

logger = FormatAdapter(logging.getLogger(__name__))

N_GEN_PARAMS = 6


class FixedProbabilityConnector(AbstractGenerateConnectorOnMachine,
                                AbstractGenerateConnectorOnHost):
    """
    For each pair of pre-post cells, the connection probability is constant.
    """

    __slots__ = (
        "__allow_self_connections",
        "_p_connect",
        "__rng")

    def __init__(
            self, p_connect: float, allow_self_connections: bool = True,
            safe: bool = True, verbose: bool = False,
            rng: Optional[NumpyRNG] = None, callback: None = None):
        """
        :param p_connect:
            a value between zero and one. Each potential connection is created
            with this probability.
        :param allow_self_connections:
            if the connector is used to connect a Population to itself, this
            flag determines whether a neuron is allowed to connect to itself,
            or only to other neurons in the Population.
        :param safe:
            If ``True``, check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param rng:
            Seeded random number generator, or `None` to make one when needed
        :param callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        """
        # Support 1.0 by using maximum U032.  Warn the user because this isn't
        # *quite* the same
        if p_connect == 1.0:
            p_connect = float(DataType.U032.max)
            logger.warning(
                "Probability of 1.0 in the FixedProbabilityConnector will use "
                "{} instead.  If this is a problem, use the AllToAllConnector "
                "instead.", p_connect)
        if not 0.0 <= p_connect < 1.0:
            raise ConfigurationException(
                "The probability must be >= 0 and < 1")
        super().__init__(safe, callback, verbose)
        self._p_connect = p_connect
        self.__allow_self_connections = allow_self_connections
        self.__rng = rng

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info: SynapseInformation) -> float:
        n_connections = get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            self._p_connect)
        return self._get_delay_maximum(
            synapse_info.delays, n_connections, synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info: SynapseInformation) -> float:
        n_connections = get_probable_minimum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            self._p_connect)
        return self._get_delay_minimum(
            synapse_info.delays, n_connections, synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:
        n_connections = get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            n_post_atoms, self._p_connect, chance=1.0/10000.0)

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            n_connections, min_delay, max_delay, synapse_info)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        n_connections = get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info.n_pre_neurons, self._p_connect,
            chance=1.0/10000.0)
        return n_connections

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        n_connections = get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            self._p_connect)
        return self._get_weight_maximum(
            synapse_info.weights, n_connections, synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices: Sequence[Slice], post_vertex_slice: Slice,
            synapse_type: int, synapse_info: SynapseInformation) -> NDArray:
        rng = self.__rng or NumpyRNG()
        n_items = synapse_info.n_pre_neurons * post_vertex_slice.n_atoms
        items = rng.next(n_items)

        # If self connections are not allowed, remove possibility the self
        # connections by setting them to a value of infinity
        no_self = (
            not self.__allow_self_connections and
            synapse_info.pre_population == synapse_info.post_population)
        if no_self:
            items[0:n_items:post_vertex_slice.n_atoms + 1] = numpy.inf

        present = items < self._p_connect
        ids = numpy.where(present)[0]
        n_connections = numpy.sum(present)

        block = numpy.zeros(n_connections, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = ids // post_vertex_slice.n_atoms
        block["target"] = (
            (ids % post_vertex_slice.n_atoms) + post_vertex_slice.lo_atom)
        block["weight"] = self._generate_weights(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["delay"] = self._generate_delays(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self) -> str:
        return f"FixedProbabilityConnector({self._p_connect})"

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self) -> int:
        return ConnectorIDs.FIXED_PROBABILITY_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_params)
    def gen_connector_params(
            self, synapse_info: SynapseInformation) -> NDArray:
        allow_self = (
            self.__allow_self_connections or
            synapse_info.pre_population != synapse_info.post_population)
        return numpy.array([
            int(allow_self),
            DataType.U032.encode_as_int(self._p_connect)], dtype="uint32")

    @property
    @overrides(
        AbstractGenerateConnectorOnMachine.gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self) -> int:
        return 2 * BYTES_PER_WORD

    @property
    def p_connect(self) -> float:
        """
        Probability for each potential connection.

        A value between zero and one. (inclusive)
        """
        return self._p_connect

    @p_connect.setter
    def p_connect(self, new_value: float) -> None:
        if not 0.0 <= new_value <= 1.0:
            raise ConfigurationException(
                "The probability must be between 0 and 1 (inclusive)")
        self._p_connect = new_value

    @overrides(AbstractConnector.validate_connection)
    def validate_connection(
            self, application_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation) -> None:
        if self.generate_on_machine(synapse_info):
            check_rng(self.__rng, "FixedProbabilityConnector")
