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

import logging
import numpy
from spinn_utilities.overrides import overrides
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)

logger = logging.getLogger(__file__)


class AllToAllConnector(AbstractGenerateConnectorOnMachine):
    """ Connects all cells in the presynaptic population to all cells in \
        the postsynaptic population.
    """

    __slots__ = [
        "__allow_self_connections",
        "__random_weight_matrix"]

    def __init__(
        self, allow_self_connections=True, safe=True,
        verbose=None, random_weight_matrix=False):
        """
        :param allow_self_connections:
            if the connector is used to connect a\
            Population to itself, this flag determines whether a neuron is\
            allowed to connect to itself, or only to other neurons in the\
            Population.
        :type allow_self_connections: bool
        """
        super(AllToAllConnector, self).__init__(safe, verbose)
        self.__allow_self_connections = allow_self_connections
        self.__random_weight_matrix = random_weight_matrix

    def _connection_slices(self, pre_vertex_slice, post_vertex_slice):
        """ Get a slice of the overall set of connections.
        """
        n_post_neurons = self._n_post_neurons
        stop_atom = post_vertex_slice.hi_atom + 1
        if (not self.__allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_post_neurons -= 1
            stop_atom -= 1
        return [
            slice(n + post_vertex_slice.lo_atom, n + stop_atom)
            for n in range(
                pre_vertex_slice.lo_atom * n_post_neurons,
                (pre_vertex_slice.hi_atom + 1) * n_post_neurons,
                n_post_neurons)]

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, delays):
        return self._get_delay_maximum(
            delays, self._n_pre_neurons * self._n_post_neurons)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, delays, post_vertex_slice, min_delay=None, max_delay=None):
        # pylint: disable=too-many-arguments

        if min_delay is None or max_delay is None:
            return post_vertex_slice.n_atoms

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            delays, self._n_pre_neurons * self._n_post_neurons,
            post_vertex_slice.n_atoms, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        return self._n_pre_neurons

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, weights):
        # pylint: disable=too-many-arguments
        n_connections = self._n_pre_neurons * self._n_post_neurons
        return self._get_weight_maximum(weights, n_connections)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, weights, delays, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        # pylint: disable=too-many-arguments
        n_connections = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        if (not self.__allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_connections -= post_vertex_slice.n_atoms
        connection_slices = self._connection_slices(
            pre_vertex_slice, post_vertex_slice)
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        if (not self.__allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_atoms = pre_vertex_slice.n_atoms
            block["source"] = numpy.where(numpy.diag(
                numpy.repeat(1, n_atoms)) == 0)[0]
            block["target"] = [block["source"][
                ((n_atoms * i) + (n_atoms - 1)) - j]
                for j in range(n_atoms) for i in range(n_atoms - 1)]
            block["source"] += pre_vertex_slice.lo_atom
            block["target"] += post_vertex_slice.lo_atom
        else:
            block["source"] = numpy.repeat(numpy.arange(
                pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom + 1),
                post_vertex_slice.n_atoms)
            block["target"] = numpy.tile(numpy.arange(
                post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1),
                pre_vertex_slice.n_atoms)
        block["weight"] = self._generate_weights(
            weights, n_connections, connection_slices, pre_vertex_slice,
            post_vertex_slice)
        block["delay"] = self._generate_delays(
            delays, n_connections, connection_slices, pre_vertex_slice,
            post_vertex_slice)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "AllToAllConnector()"

    @property
    def allow_self_connections(self):
        return self.__allow_self_connections

    @allow_self_connections.setter
    def allow_self_connections(self, new_value):
        self.__allow_self_connections = new_value

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self):
        return ConnectorIDs.ALL_TO_ALL_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params)
    def gen_connector_params(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        return numpy.array([
            self.allow_self_connections],
            dtype="uint32")

    @property
    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        return 4

    @overrides(AbstractConnector.random_weight_matrix)
    def random_weight_matrix(self):
        if self.__random_weight_matrix:
            return 1
        return 0
