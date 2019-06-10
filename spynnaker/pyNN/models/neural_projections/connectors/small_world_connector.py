import numpy
from spinn_utilities.overrides import overrides
from .abstract_connector import AbstractConnector


class SmallWorldConnector(AbstractConnector):
    __slots__ = [
        "__allow_self_connections",  # TODO: currently ignored
        "__degree",
        "__mask",
        "__n_connections",
        "__rewiring"]

    def __init__(
            self, degree, rewiring, allow_self_connections=True, safe=True,
            verbose=False, n_connections=None):
        # pylint: disable=too-many-arguments
        super(SmallWorldConnector, self).__init__(safe, verbose)
        self.__rewiring = rewiring
        self.__degree = degree
        self.__allow_self_connections = allow_self_connections

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
        pre_positions = self.pre_population.positions
        post_positions = self.post_population.positions

        distances = self.space.distances(
            pre_positions, post_positions, False)

        # PyNN 0.8 returns a flattened (C-style) array from space.distances,
        # so the easiest thing to do here is to reshape back to the "expected"
        # PyNN 0.7 shape; otherwise later code gets confusing and difficult
        if (len(distances.shape) == 1):
            d = numpy.reshape(distances, (pre_positions.shape[0],
                                          post_positions.shape[0]))
        else:
            d = distances

        self.__mask = (d < self.__degree).astype(float)

        self.__n_connections = numpy.sum(self.__mask)

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, delays):
        return self._get_delay_maximum(delays, self.__n_connections)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, delays, post_vertex_slice, min_delay=None, max_delay=None):
        # pylint: disable=too-many-arguments
        n_connections = numpy.amax([
            numpy.sum(self.__mask[i, post_vertex_slice.as_slice])
            for i in range(self._n_pre_neurons)])

        if min_delay is None or max_delay is None:
            return n_connections

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            delays, self.__n_connections, n_connections, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        # pylint: disable=too-many-arguments
        return numpy.amax([
            numpy.sum(self.__mask[:, i]) for i in range(self._n_post_neurons)])

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, weights):
        # pylint: disable=too-many-arguments
        return self._get_weight_maximum(weights, self.__n_connections)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, weights, delays, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
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
            weights, n_connections, None)
        block["delay"] = self._generate_delays(
            delays, n_connections, None)
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
