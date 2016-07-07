from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector

import numpy.random


class MultapseConnector(AbstractConnector):
    """
    Create a multapse connector. The size of the source and destination
    populations are obtained when the projection is connected. The number of
    synapses is specified. when instantiated, the required number of synapses
    is created by selecting at random from the source and target populations
    with replacement. Uniform selection probability is assumed.

    :param num_synapses:
        Integer. This is the total number of synapses in the connection.
    :param weights:
        may either be a float, a !RandomDistribution object, a list/
        1D array with at least as many items as connections to be
        created. Units nA.
    :param delays:
        as `weights`. If `None`, all synaptic delays will be set
        to the global minimum delay.

    """
    def __init__(
            self, num_synapses, weights=0.0, delays=1,
            safe=True, verbose=False):
        """
        Creates a new connector.
        """
        AbstractConnector.__init__(self, safe, None, verbose)
        self._num_synapses = num_synapses
        self._weights = weights
        self._delays = delays
        self._pre_slices = None
        self._post_slices = None
        self._synapses_per_subedge = None

        self._check_parameters(weights, delays)

    def get_delay_maximum(self):
        return self._get_delay_maximum(self._delays, self._num_synapses)

    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        self._update_synapses_per_post_vertex(pre_slices, post_slices)
        connection_slice = self._get_connection_slice(
            pre_slice_index, post_slice_index)
        return self._get_delay_variance(self._delays, [connection_slice])

    def _update_synapses_per_post_vertex(self, pre_slices, post_slices):
        if (self._synapses_per_subedge is None or
                len(self._pre_slices) != len(pre_slices) or
                len(self._post_slices) != len(post_slices)):
            n_pre_atoms = sum([pre.n_atoms for pre in pre_slices])
            n_post_atoms = sum([post.n_atoms for post in post_slices])
            n_connections = n_pre_atoms * n_post_atoms
            prob_connect = [
                float(pre.n_atoms * post.n_atoms) / float(n_connections)
                for pre in pre_slices for post in post_slices]
            self._synapses_per_subedge = self._rng.next(
                1, distribution="multinomial", parameters=[
                    self._num_synapses, prob_connect])
            self._pre_slices = pre_slices
            self._post_slices = post_slices

    def _get_n_connections(self, pre_slice_index, post_slice_index):
        index = (len(self._post_slices) * pre_slice_index) + post_slice_index
        return self._synapses_per_subedge[index]

    def _get_connection_slice(self, pre_slice_index, post_slice_index):
        index = (len(self._post_slices) * pre_slice_index) + post_slice_index
        n_connections = self._synapses_per_subedge[index]
        start_connection = 0
        if index > 0:
            start_connection = numpy.sum(self._synapses_per_subedge[:index])
        return slice(start_connection, start_connection + n_connections, 1)

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):

        self._update_synapses_per_post_vertex(pre_slices, post_slices)

        n_total_connections = self._get_n_connections(
            pre_slice_index, post_slice_index)
        if n_total_connections == 0:
            return 0
        prob_per_atom = (
            float(n_total_connections) /
            float(pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms))
        full_connections = 0
        while prob_per_atom > 1.0:
            full_connections += 1
            prob_per_atom -= 1.0
        n_connections_per_pre_atom = \
            utility_calls.get_probable_maximum_selected(
                self._n_pre_neurons * self._n_post_neurons,
                post_vertex_slice.n_atoms, prob_per_atom)
        n_connections_per_pre_atom += (
            full_connections * post_vertex_slice.n_atoms)

        if min_delay is None or max_delay is None:
            return n_connections_per_pre_atom

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._delays, self._n_pre_neurons * self._n_post_neurons,
            n_connections_per_pre_atom,
            [self._get_connection_slice(pre_slice_index, post_slice_index)],
            min_delay, max_delay)

    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        self._update_synapses_per_post_vertex(pre_slices, post_slices)
        n_total_connections = self._get_n_connections(
            pre_slice_index, post_slice_index)
        if n_total_connections == 0:
            return 0
        prob_per_atom = (
            float(n_total_connections) /
            float(pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms))
        full_connections = 0
        while prob_per_atom > 1.0:
            full_connections += 1
            prob_per_atom -= 1.0
        return (utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_post_neurons,
            pre_vertex_slice.n_atoms, prob_per_atom) +
            (full_connections * pre_vertex_slice.n_atoms))

    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        self._update_synapses_per_post_vertex(pre_slices, post_slices)
        n_connections = self._get_n_connections(
            pre_slice_index, post_slice_index)
        if n_connections == 0:
            return 0
        connection_slice = self._get_connection_slice(
            pre_slice_index, post_slice_index)
        return self._get_weight_mean(self._weights, [connection_slice])

    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        self._update_synapses_per_post_vertex(pre_slices, post_slices)
        n_connections = self._get_n_connections(
            pre_slice_index, post_slice_index)
        if n_connections == 0:
            return 0
        connection_slice = self._get_connection_slice(
            pre_slice_index, post_slice_index)
        return self._get_weight_maximum(
            self._weights, n_connections, [connection_slice])

    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        self._update_synapses_per_post_vertex(pre_slices, post_slices)
        connection_slice = self._get_connection_slice(
            pre_slice_index, post_slice_index)
        return self._get_weight_variance(self._weights, [connection_slice])

    def generate_on_machine(self):
        return (
            not self._generate_lists_on_host(self._weights) and
            not self._generate_lists_on_host(self._delays))

    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        self._update_synapses_per_post_vertex(pre_slices, post_slices)
        n_connections = self._get_n_connections(
            pre_slice_index, post_slice_index)
        if n_connections == 0:
            return numpy.zeros(
                0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        connection_slice = self._get_connection_slice(
            pre_slice_index, post_slice_index)
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        block["source"] = numpy.random.choice(
            numpy.arange(
                pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom + 1),
            size=n_connections, replace=True)
        block["source"].sort()
        block["target"] = numpy.random.choice(
            numpy.arange(
                post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1),
            size=n_connections, replace=True)
        block["weight"] = self._generate_weights(
            self._weights, n_connections, [connection_slice])
        block["delay"] = self._generate_delays(
            self._delays, n_connections, [connection_slice])
        block["synapse_type"] = synapse_type
        return block
