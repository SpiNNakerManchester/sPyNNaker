from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector

import numpy


class SmallWorldConnector(AbstractConnector):

    def __init__(
            self, degree, rewiring, allow_self_connections=True, weights=0.0,
            delays=1, space=None, safe=True, verbose=False,
            n_connections=None):
        AbstractConnector.__init__(self, safe, space, verbose)
        self._rewiring = rewiring

        self._check_parameters(weights, delays, allow_lists=False)
        if n_connections is not None:
            raise NotImplementedError(
                "n_connections is not implemented for"
                " SmallWorldConnector on this platform")

        # Get the probabilities up-front for now
        # TODO: Work out how this can be done statistically
        pre_positions = self._pre_population.positions
        post_positions = self._post_population.positions
        distances = self._space.distances(
            pre_positions, post_positions, False)
        self._mask = (distances < degree).as_type(float)
        self._n_connections = numpy.sum(self._mask)

    def get_delay_maximum(self):
        return self._get_delay_maximum(self._delays, self._n_connections)

    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        return self._get_delay_variance(self._delays, None)

    def _get_n_connections(self, pre_vertex_slice, post_vertex_slice):
        return numpy.sum(
            self._mask[pre_vertex_slice.as_slice, post_vertex_slice.as_slice])

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):

        n_connections = numpy.amax([
            numpy.sum(self._mask[i, post_vertex_slice.as_slice])
            for i in range(
                pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom + 1)])

        if min_delay is None or max_delay is None:
            return n_connections

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._delays, self._n_connections,
            n_connections, None, min_delay, max_delay)

    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        n_connections = numpy.amax([
            numpy.sum(self._mask[pre_vertex_slice.as_slice, i])
            for i in range(
                post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1)])

        return n_connections

    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        return self._get_weight_mean(self._weights, None)

    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        n_connections = self._get_n_connections(
            pre_vertex_slice, post_vertex_slice)
        return self._get_weight_maximum(
            self._weights, n_connections, None)

    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        return self._get_weight_variance(self._weights, None)

    def generate_on_machine(self):
        return False

    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):

        ids = numpy.where(self._mask[
            pre_vertex_slice.as_slice, post_vertex_slice.as_slice])[0]
        n_connections = numpy.sum(ids)

        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        block["source"] = (
            (ids / post_vertex_slice.n_atoms) + pre_vertex_slice.lo_atom)
        block["target"] = (
            (ids % post_vertex_slice.n_atoms) + post_vertex_slice.lo_atom)
        block["weight"] = self._generate_weights(
            self._weights, n_connections, None)
        block["delay"] = self._generate_delays(
            self._delays, n_connections, None)
        block["synapse_type"] = synapse_type

        # Re-wire some connections
        rewired = numpy.where(
            self._rng.next(n_connections) < self._rewiring)[0]
        block["target"][rewired] = (
            (self._rng.next(rewired.size) * (post_vertex_slice.n_atoms - 1)) +
            post_vertex_slice.lo_atom)

        return block
