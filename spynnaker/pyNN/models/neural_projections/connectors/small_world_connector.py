from .abstract_connector import AbstractConnector
from spinn_utilities.overrides import overrides
import numpy


class SmallWorldConnector(AbstractConnector):
    __slots__ = [
        "_degree",
        "_mask",
        "_n_connections",
        "_rewiring"]

    def __init__(
            self, degree, rewiring, allow_self_connections=True, safe=True,
            verbose=False, n_connections=None):
        # pylint: disable=too-many-arguments
        super(SmallWorldConnector, self).__init__(safe, verbose)
        self._rewiring = rewiring
        self._degree = degree

        if n_connections is not None:
            raise NotImplementedError(
                "n_connections is not implemented for"
                " SmallWorldConnector on this platform")

    @overrides(AbstractConnector.set_projection_information)
    def set_projection_information(
            self, pre_population, post_population, rng, machine_time_step):
        AbstractConnector.set_projection_information(
            self, pre_population, post_population, rng, machine_time_step)
        self._set_n_connections()

    def _set_n_connections(self):
        # Get the probabilities up-front for now
        # TODO: Work out how this can be done statistically
        # space.distances(...) expects N,3 array in PyNN0.7, but 3,N in PyNN0.8
        pre_positions = self._pre_population.positions
        post_positions = self._post_population.positions

        distances = self._space.distances(
            pre_positions, post_positions, False)

        # PyNN 0.8 returns a flattened (C-style) array from space.distances,
        # so the easiest thing to do here is to reshape back to the "expected"
        # PyNN 0.7 shape; otherwise later code gets confusing and difficult
        if (len(distances.shape) == 1):
            d = numpy.reshape(distances, (pre_positions.shape[0],
                                          post_positions.shape[0]))
        else:
            d = distances

        self._mask = (d < self._degree).astype(float)

        self._n_connections = numpy.sum(self._mask)

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self):
        return self._get_delay_maximum(self._n_connections)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, min_delay=None, max_delay=None):
        # pylint: disable=too-many-arguments
        n_connections = numpy.amax([
            numpy.sum(self._mask[i, post_vertex_slice.as_slice])
            for i in range(self._n_pre_neurons)])

        if min_delay is None or max_delay is None:
            return n_connections

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._n_connections, n_connections, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        # pylint: disable=too-many-arguments
        return numpy.amax([
            numpy.sum(self._mask[:, i]) for i in range(self._n_post_neurons)])

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self):
        # pylint: disable=too-many-arguments
        return self._get_weight_maximum(self._n_connections)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        # pylint: disable=too-many-arguments
        ids = numpy.where(self._mask[
            pre_vertex_slice.as_slice, post_vertex_slice.as_slice])
        n_connections = len(ids[0])

        block = numpy.zeros(n_connections, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = ids[0]
        block["target"] = ids[1]
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

    def __repr__(self):
        return "SmallWorldConnector(degree={}, rewiring={})".format(
            self._degree, self._rewiring)
