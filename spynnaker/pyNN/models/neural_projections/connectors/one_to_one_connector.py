import numpy
from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector


class OneToOneConnector(AbstractConnector):
    """
    Where the pre- and postsynaptic populations have the same size, connect
    cell i in the presynaptic pynn_population.py to cell i in the postsynaptic
    pynn_population.py for all i.
    """

    def __init__(self, weights=0.0, delays=1):
        """
        :param weights:
            may either be a float, a !RandomDistribution object, a list/
            1D array with at least as many items as connections to be
            created. Units nA.
        :param delays:
            as `weights`. If `None`, all synaptic delays will be set
            to the global minimum delay.

        """
        self._weights = weights
        self._delays = delays

    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays, max((self._n_pre_neurons, self._n_post_neurons)))

    def get_n_connections_from_pre_vertex_maximum(
            self, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        return 1

    def get_n_connections_to_post_vertex_maximum(
            self, pre_vertex_slice, post_vertex_slice):
        return 1

    def get_weight_mean(self, pre_vertex_slice, post_vertex_slice):
        max_lo_atom = max(
            (pre_vertex_slice.lo_atom, post_vertex_slice.lo_atom))
        min_hi_atom = min(
            (pre_vertex_slice.hi_atom, post_vertex_slice.hi_atom))
        n_connections = (min_hi_atom - max_lo_atom) + 1
        connection_slice = slice(max_lo_atom, min_hi_atom + 1)
        return self._get_weight_mean(
            self._weights, n_connections, connection_slice)

    def get_weight_maximum(self, pre_vertex_slice, post_vertex_slice):
        max_lo_atom = max(
            (pre_vertex_slice.lo_atom, post_vertex_slice.lo_atom))
        min_hi_atom = min(
            (pre_vertex_slice.hi_atom, post_vertex_slice.hi_atom))
        n_connections = (min_hi_atom - max_lo_atom) + 1
        connection_slice = slice(max_lo_atom, min_hi_atom + 1)
        return self._get_weight_maximum(
            self._weights, n_connections, connection_slice)

    def get_weight_variance(self, pre_vertex_slice, post_vertex_slice):
        max_lo_atom = max(
            (pre_vertex_slice.lo_atom, post_vertex_slice.lo_atom))
        min_hi_atom = min(
            (pre_vertex_slice.hi_atom, post_vertex_slice.hi_atom))
        connection_slice = slice(max_lo_atom, min_hi_atom + 1)
        return self._get_weight_variance(self._weights, connection_slice)

    def create_synaptic_block(
            self, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type, connector_index):
        max_lo_atom = max(
            (pre_vertex_slice.lo_atom, post_vertex_slice.lo_atom))
        min_hi_atom = min(
            (pre_vertex_slice.hi_atom, post_vertex_slice.hi_atom))
        n_connections = max((0, (min_hi_atom - max_lo_atom) + 1))
        connection_slice = slice(max_lo_atom, min_hi_atom + 1)
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        block["source"] = numpy.arange(max_lo_atom, min_hi_atom + 1)
        block["target"] = numpy.arange(max_lo_atom, min_hi_atom + 1)
        block["weight"] = self._generate_values(
            self._weights, n_connections, connection_slice)
        block["delay"] = self._generate_values(
            self._delays, n_connections, connection_slice)
        block["synapse_type"] = synapse_type
        block["connector_index"] = connector_index
        return block
