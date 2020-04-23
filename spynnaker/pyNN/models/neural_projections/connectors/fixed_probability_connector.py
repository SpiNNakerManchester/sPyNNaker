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

import math
import numpy
from spinn_utilities.overrides import overrides
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.utilities import utility_calls
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)
from .abstract_connector_supports_views_on_machine import (
    AbstractConnectorSupportsViewsOnMachine)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

N_GEN_PARAMS = 6


class FixedProbabilityConnector(AbstractGenerateConnectorOnMachine,
                                AbstractConnectorSupportsViewsOnMachine):
    """ For each pair of pre-post cells, the connection probability is constant.
    """

    __slots__ = [
        "__allow_self_connections",
        "_p_connect"]

    def __init__(
            self, p_connect, allow_self_connections=True, safe=True,
            callback=None, verbose=False, rng=None):
        """
        :param p_connect:
            a float between zero and one. Each potential connection is created\
            with this probability.
        :type p_connect: float
        :param allow_self_connections:
            if the connector is used to connect a Population to itself, this\
            flag determines whether a neuron is allowed to connect to itself,\
            or only to other neurons in the Population.
        :type allow_self_connections: bool
        :param `pyNN.Space` space:
            a Space object, needed if you wish to specify distance-dependent\
            weights or delays - not implemented
        """
        super(FixedProbabilityConnector, self).__init__(
            safe, callback, verbose)
        self._p_connect = p_connect
        self.__allow_self_connections = allow_self_connections
        self._rng = rng
        if not 0 <= self._p_connect <= 1:
            raise ConfigurationException(
                "The probability must be between 0 and 1 (inclusive)")

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        n_connections = utility_calls.get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            self._p_connect)
        return self._get_delay_maximum(synapse_info.delays, n_connections)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, synapse_info, min_delay=None,
            max_delay=None):
        # pylint: disable=too-many-arguments
        n_connections = utility_calls.get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            post_vertex_slice.n_atoms, self._p_connect, chance=1.0/10000.0)

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            n_connections, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        # pylint: disable=too-many-arguments
        n_connections = utility_calls.get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info.n_pre_neurons, self._p_connect,
            chance=1.0/10000.0)
        return n_connections

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        # pylint: disable=too-many-arguments
        n_connections = utility_calls.get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            self._p_connect)
        return self._get_weight_maximum(synapse_info.weights, n_connections)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        # pylint: disable=too-many-arguments
        n_items = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        items = self._rng.next(n_items)

        # If self connections are not allowed, remove possibility the self
        # connections by setting them to a value of infinity
        if not self.__allow_self_connections:
            items[0:n_items:post_vertex_slice.n_atoms + 1] = numpy.inf

        present = items <= self._p_connect
        ids = numpy.where(present)[0]
        n_connections = numpy.sum(present)

        block = numpy.zeros(n_connections, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = (
            (ids // post_vertex_slice.n_atoms) + pre_vertex_slice.lo_atom)
        block["target"] = (
            (ids % post_vertex_slice.n_atoms) + post_vertex_slice.lo_atom)
        block["weight"] = self._generate_weights(
            n_connections, None, pre_vertex_slice, post_vertex_slice,
            synapse_info)
        block["delay"] = self._generate_delays(
            n_connections, None, pre_vertex_slice, post_vertex_slice,
            synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "FixedProbabilityConnector({})".format(self._p_connect)

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self):
        return ConnectorIDs.FIXED_PROBABILITY_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params)
    def gen_connector_params(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        params = self._basic_connector_params(synapse_info)

        params.extend([self.__allow_self_connections])

        # If prob=1.0 has been specified, take care when scaling value to
        # ensure that it doesn't wrap round to zero as an unsigned long fract
        params.extend([DataType.U032.encode_as_int(
            DataType.U032.max if self._p_connect == 1.0 else self._p_connect)])

        params.extend(self._get_connector_seed(
            pre_vertex_slice, post_vertex_slice, self._rng))
        return numpy.array(params, dtype="uint32")

    @property
    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        # view + params + seeds
        return self._view_params_bytes + (N_GEN_PARAMS * BYTES_PER_WORD)
