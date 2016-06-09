from pyNN.random import RandomDistribution
from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector

import numpy
import logging

logger = logging.getLogger(__file__)


class FixedNumberPostConnector(AbstractConnector):

    def __init__(
            self, n, weights=0.0, delays=1, allow_self_connections=True,
            space=None, safe=True, verbose=False):
        AbstractConnector.__init__(self, safe, space, verbose)
        self._post_n = n
        self._weights = weights
        self._delays = delays
        self._allow_self_connections = allow_self_connections
        self._post_neurons = None

        self._check_parameters(weights, delays, allow_lists=False)
        if isinstance(n, RandomDistribution):
            raise NotImplementedError(
                "RandomDistribution is not supported for n in the"
                " implementation of FixedNumberPostConnector on this platform")

    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays, self._n_pre_neurons * self._post_n)

    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(post_vertex_slice):
            return 0.0
        return self._get_delay_variance(self._delays, None)

    def _get_post_neurons(self):
        if self._post_neurons is None:
            n = 0
            while (n < self._post_n):
                permutation = numpy.arange(self._n_post_neurons)
                for i in range(0, self._n_post_neurons - 1):
                    j = self._rng.next(
                        n=1, distribution="uniform",
                        parameters=[0, self._n_post_neurons])
                    (permutation[i], permutation[j]) = (
                        permutation[j], permutation[i])
                n += self._n_post_neurons
                if self._post_neurons is None:
                    self._post_neurons = permutation
                else:
                    self._post_neurons = numpy.append(
                        self._post_neurons, permutation)
            self._post_neurons = self._post_neurons[:self._post_n]
            self._post_neurons.sort()
        return self._post_neurons

    def _post_neurons_in_slice(self, post_vertex_slice):
        post_neurons = self._get_post_neurons()
        return post_neurons[
            (post_neurons >= post_vertex_slice.lo_atom) &
            (post_neurons <= post_vertex_slice.hi_atom)]

    def _is_connected(self, post_vertex_slice):
        return self._post_neurons_in_slice(post_vertex_slice).size > 0

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):

        if not self._is_connected(post_vertex_slice):
            return 0

        post_neurons = self._post_neurons_in_slice(post_vertex_slice)
        if min_delay is None or max_delay is None:
            return len(post_neurons)

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._delays, self._n_post * self._n_post_neurons,
            pre_vertex_slice.n_atoms * len(post_neurons), None,
            min_delay, max_delay)

    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(post_vertex_slice):
            return 0
        return pre_vertex_slice.n_atoms

    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(post_vertex_slice):
            return 0.0
        return self._get_weight_mean(self._weights, None)

    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(post_vertex_slice):
            return 0.0
        post_neurons = self._post_neurons_in_slice(post_vertex_slice)
        n_connections = pre_vertex_slice.n_atoms * len(post_neurons)
        return self._get_weight_maximum(
            self._weights, n_connections, None)

    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(post_vertex_slice):
            return 0.0
        return self._get_weight_variance(self._weights, None)

    def generate_on_machine(self):
        return (
            not self._generate_lists_on_host(self._weights) and
            not self._generate_lists_on_host(self._delays))

    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        if not self._is_connected(post_vertex_slice):
            return numpy.zeros(0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        post_neurons_in_slice = self._post_neurons_in_slice(post_vertex_slice)
        n_connections = pre_vertex_slice.n_atoms * len(post_neurons_in_slice)
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_connections -= len(post_neurons_in_slice)

        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            block["source"] = [
                pre_index for pre_index in range(
                    pre_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1)
                for post_index in post_neurons_in_slice
                if pre_index != post_index]
            block["target"] = [
                post_index for pre_index in range(
                    pre_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1)
                for post_index in post_neurons_in_slice
                if pre_index != post_index]
        else:
            block["source"] = numpy.repeat(numpy.arange(
                pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom + 1),
                len(post_neurons_in_slice))
            block["target"] = numpy.tile(
                post_neurons_in_slice, pre_vertex_slice.n_atoms)
        block["weight"] = self._generate_weights(
            self._weights, n_connections, None)
        block["delay"] = self._generate_delays(
            self._delays, n_connections, None)
        block["synapse_type"] = synapse_type
        return block
