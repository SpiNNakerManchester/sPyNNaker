from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
import numpy


class AllToAllConnector(AbstractConnector):
    """ Connects all cells in the presynaptic population to all cells in \
        the postsynaptic population
    """
    def __init__(self, weights=0.0, delays=1, allow_self_connections=True):
        """

        :param `bool` allow_self_connections:
            if the connector is used to connect a
            Population to itself, this flag determines whether a neuron is
            allowed to connect to itself, or only to other neurons in the
            Population.
        :param `float` weights:
            may either be a float, a !RandomDistribution object, a list/
            1D array with at least as many items as connections to be
            created. Units nA.
        :param `float` delays:  -- as `weights`. If `None`, all synaptic delays
            will be set to the global minimum delay.
        :param `pyNN.Space` space:
            a Space object, needed if you wish to specify distance-
            dependent weights or delays - not implemented
    """
        AbstractConnector.__init__(self)
        self._weights = weights
        self._delays = delays
        self._allow_self_connections = allow_self_connections

    def _connection_slice(self, pre_vertex_slice, post_vertex_slice):
        """ Get a slice of the overall set of connections
        """
        return slice(
            (self._n_post_neurons * pre_vertex_slice.lo_atom) +
            post_vertex_slice.lo_atom,
            (self._n_post_neurons * pre_vertex_slice.hi_atom) +
            post_vertex_slice.hi_atom + 1,
            self._n_post_neurons - post_vertex_slice.n_atoms)

    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays, self._n_pre_neurons * self._n_post_neurons)

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        if min_delay is None or max_delay is None:
            return post_vertex_slice.n_atoms
        else:
            n_connections = (pre_vertex_slice.n_atoms *
                             post_vertex_slice.n_atoms)
            connection_slice = self._connection_slice(
                pre_vertex_slice, post_vertex_slice)

            return self._get_n_connections_from_pre_vertex_with_delay_maximum(
                self._delays, n_connections, connection_slice,
                min_delay, max_delay)

    def get_n_connections_to_post_vertex_maximum(
            self, pre_vertex_slice, post_vertex_slice):
        return pre_vertex_slice.n_atoms

    def get_weight_mean(self, pre_vertex_slice, post_vertex_slice):
        n_connections = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        connection_slice = self._connection_slice(
            pre_vertex_slice, post_vertex_slice)
        return self._get_weight_mean(
            self._weights, n_connections, connection_slice)

    def get_weight_maximum(self, pre_vertex_slice, post_vertex_slice):
        n_connections = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        connection_slice = self._connection_slice(
            pre_vertex_slice, post_vertex_slice)
        return self._get_weight_maximum(
            self._weights, n_connections, connection_slice)

    def get_weight_variance(self, pre_vertex_slice, post_vertex_slice):
        n_connections = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        connection_slice = self._connection_slice(
            pre_vertex_slice, post_vertex_slice)
        return self._get_weight_variance(
            self._weights, n_connections, connection_slice)

    def create_synaptic_block(
            self, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        n_connections = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        connection_slice = self._connection_slice(
            pre_vertex_slice, post_vertex_slice)
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        block["source"] = numpy.repeat(numpy.arange(
            pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom + 1),
            post_vertex_slice.n_atoms)
        block["target"] = numpy.tile(numpy.arange(
            post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1),
            pre_vertex_slice.n_atoms)
        block["weights"] = self._generate_values(
            self._weights, n_connections, connection_slice)
        block["delays"] = self._generate_values(
            self._delays, n_connections, connection_slice)
        block["synapse_type"] = synapse_type
