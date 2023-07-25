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
from numpy import uint32
from numpy.typing import NDArray
from typing import Sequence, Optional
from spinn_utilities.overrides import overrides
from pacman.model.graphs.common import Slice
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)
from spynnaker.pyNN.models.neural_projections import SynapseInformation


class AllToAllConnector(AbstractGenerateConnectorOnMachine,
                        AbstractGenerateConnectorOnHost):
    """
    Connects all cells in the presynaptic population to all cells in
    the postsynaptic population.
    """

    __slots__ = ("__allow_self_connections", )

    def __init__(self, allow_self_connections=True, safe=True,
                 verbose=None, callback=None):
        """
        :param bool allow_self_connections:
            if the connector is used to connect a Population to itself, this
            flag determines whether a neuron is allowed to connect to itself,
            or only to other neurons in the Population.
        :param bool safe:
            If ``True``, check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        """
        super().__init__(safe, callback, verbose)
        self.__allow_self_connections = allow_self_connections

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info: SynapseInformation) -> float:
        return self._get_delay_maximum(
            synapse_info.delays,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info: SynapseInformation) -> float:
        return self._get_delay_minimum(
            synapse_info.delays,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:
        if min_delay is None or max_delay is None:
            return n_post_atoms

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            n_post_atoms, min_delay, max_delay, synapse_info)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        return synapse_info.n_pre_neurons

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        n_conns = synapse_info.n_pre_neurons * synapse_info.n_post_neurons
        return self._get_weight_maximum(
            synapse_info.weights, n_conns, synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices: Sequence[Slice], post_vertex_slice: Slice,
            synapse_type: int, synapse_info: SynapseInformation) -> NDArray:
        n_connections = synapse_info.n_pre_neurons * post_vertex_slice.n_atoms
        if not self.__allow_self_connections:
            n_connections -= post_vertex_slice.n_atoms
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        if not self.__allow_self_connections:
            n_atoms = synapse_info.n_pre_neurons
            block["source"] = numpy.where(numpy.diag(
                numpy.repeat(1, n_atoms)) == 0)[0]
            block["target"] = [block["source"][
                ((n_atoms * i) + (n_atoms - 1)) - j]
                for j in range(n_atoms) for i in range(n_atoms - 1)]
            block["target"] += post_vertex_slice.lo_atom
        else:
            block["source"] = numpy.repeat(numpy.arange(
                0, synapse_info.n_pre_neurons), post_vertex_slice.n_atoms)
            block["target"] = numpy.tile(numpy.arange(
                post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1),
                synapse_info.n_pre_neurons)
        block["weight"] = self._generate_weights(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["delay"] = self._generate_delays(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "AllToAllConnector()"

    @property
    def allow_self_connections(self) -> bool:
        """
        :rtype: bool
        """
        return self.__allow_self_connections

    @allow_self_connections.setter
    def allow_self_connections(self, new_value: bool):
        self.__allow_self_connections = new_value

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self) -> int:
        return ConnectorIDs.ALL_TO_ALL_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_params)
    def gen_connector_params(self) -> NDArray[uint32]:
        return numpy.array([
            int(self.__allow_self_connections)], dtype=uint32)

    @property
    @overrides(
        AbstractGenerateConnectorOnMachine.gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self) -> int:
        return BYTES_PER_WORD
