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
from .abstract_connector import AbstractConnector


class SmallWorldConnector(AbstractConnector):
    """ A connector that uses connection statistics based on the Small World\
        network connectivity model.

    .. note::
        This is typically used from a population to itself.
    """
    __slots__ = [
        "__allow_self_connections",  # TODO: currently ignored
        "__degree",
        "__mask",
        "__n_connections",
        "__rewiring"]

    def __init__(
            self, degree, rewiring, allow_self_connections=True,
            n_connections=None, rng=None, safe=True, callback=None,
            verbose=False):
        """
        :param float degree:
            the region length where nodes will be connected locally
        :param float rewiring: the probability of rewiring each edge
        :param bool allow_self_connections:
            if the connector is used to connect a Population to itself, this
            flag determines whether a neuron is allowed to connect to itself,
            or only to other neurons in the Population.
        :param n_connections:
            if specified, the number of efferent synaptic connections per
            neuron
        :type n_connections: int or None
        :param rng:
            Seeded random number generator, or ``None`` to make one when
            needed.
        :type rng: ~pyNN.random.NumpyRNG or None
        :param bool safe:
            If ``True``, check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        """
        # pylint: disable=too-many-arguments
        super().__init__(safe, callback, verbose, rng)
        self.__rewiring = rewiring
        self.__degree = degree
        # pylint:disable=unused-private-member
        self.__allow_self_connections = allow_self_connections
        self.__mask = None
        self.__n_connections = None

        if n_connections is not None:
            raise NotImplementedError(
                "n_connections is not implemented for"
                " SmallWorldConnector on this platform")

    @overrides(AbstractConnector.set_projection_information)
    def set_projection_information(self, synapse_info):
        super().set_projection_information(synapse_info)
        self._set_n_connections(synapse_info)

    def _set_n_connections(self, synapse_info):
        """
        :param SynapseInformation synapse_info:
        """
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

        self.__mask = (d < self.__degree).astype(float)

        self.__n_connections = int(math.ceil(numpy.sum(self.__mask)))

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        return self._get_delay_maximum(
            synapse_info.delays, self.__n_connections, synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info):
        return self._get_delay_minimum(
            synapse_info.delays, self.__n_connections, synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms, synapse_info, min_delay=None,
            max_delay=None):

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
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        # pylint: disable=too-many-arguments
        return numpy.amax([
            numpy.sum(self.__mask[:, i]) for i in range(
                synapse_info.n_post_neurons)])

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        # pylint: disable=too-many-arguments
        return self._get_weight_maximum(
            synapse_info.weights, self.__n_connections, synapse_info)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, post_slices, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        # pylint: disable=too-many-arguments
        ids = numpy.where(self.__mask[
            pre_vertex_slice.as_slice, post_vertex_slice.as_slice])
        n_connections = len(ids[0])

        block = numpy.zeros(n_connections, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = (
            (ids[0] % pre_vertex_slice.n_atoms) + pre_vertex_slice.lo_atom)
        block["target"] = (
            (ids[1] % post_vertex_slice.n_atoms) + post_vertex_slice.lo_atom)
        block["weight"] = self._generate_weights(
            block["source"], block["target"], n_connections, None,
            pre_vertex_slice, post_vertex_slice, synapse_info)
        block["delay"] = self._generate_delays(
            block["source"], block["target"], n_connections, None,
            pre_vertex_slice, post_vertex_slice, synapse_info)
        block["synapse_type"] = synapse_type

        # Re-wire some connections
        rewired = numpy.where(
            self._rng.next(n_connections) < self.__rewiring)[0]
        block["target"][rewired] = (
            (self._rng.next(rewired.size) * (post_vertex_slice.n_atoms - 1)) +
            post_vertex_slice.lo_atom)

        return block

    def __repr__(self):
        return "SmallWorldConnector(degree={}, rewiring={})".format(
            self.__degree, self.__rewiring)
