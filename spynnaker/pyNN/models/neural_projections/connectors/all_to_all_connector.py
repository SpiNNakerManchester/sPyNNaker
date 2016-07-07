from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector

import numpy
import logging

logger = logging.getLogger(__file__)


class AllToAllConnector(AbstractConnector):
    """ Connects all cells in the presynaptic population to all cells in \
        the postsynaptic population
    """

    def __init__(
            self, weights=0.0, delays=1, allow_self_connections=True,
            space=None, safe=True, verbose=None):
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
    """
        AbstractConnector.__init__(self, safe, space, verbose)
        self._weights = weights
        self._delays = delays
        self._allow_self_connections = allow_self_connections

        self._check_parameters(weights, delays)

    def _connection_slices(self, pre_vertex_slice, post_vertex_slice):
        """ Get a slice of the overall set of connections
        """
        n_post_neurons = self._n_post_neurons
        stop_atom = post_vertex_slice.hi_atom + 1
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_post_neurons -= 1
            stop_atom -= 1
        return [
            slice(n + post_vertex_slice.lo_atom, n + stop_atom)
            for n in range(
                pre_vertex_slice.lo_atom * n_post_neurons,
                (pre_vertex_slice.hi_atom + 1 * n_post_neurons),
                n_post_neurons)]

    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays, self._n_pre_neurons * self._n_post_neurons)

    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        connection_slices = self._connection_slices(
            pre_vertex_slice, post_vertex_slice)
        return self._get_delay_variance(self._delays, connection_slices)

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):

        total_n_connections_per_pre_neuron = self._n_post_neurons
        n_connections_per_pre_neuron = post_vertex_slice.n_atoms
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_connections_per_pre_neuron -= 1
            total_n_connections_per_pre_neuron -= 1

        if min_delay is None or max_delay is None:
            return n_connections_per_pre_neuron

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._delays,
            self._n_pre_neurons * total_n_connections_per_pre_neuron,
            n_connections_per_pre_neuron,
            self._connection_slices(pre_vertex_slice, post_vertex_slice),
            min_delay, max_delay)

    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            return pre_vertex_slice.n_atoms - 1
        return pre_vertex_slice.n_atoms

    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        n_connections = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_connections -= post_vertex_slice.n_atoms
        connection_slices = self._connection_slices(
            pre_vertex_slice, post_vertex_slice)
        return self._get_weight_mean(self._weights, connection_slices)

    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        n_connections = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_connections -= post_vertex_slice.n_atoms
        connection_slices = self._connection_slices(
            pre_vertex_slice, post_vertex_slice)
        return self._get_weight_maximum(
            self._weights, n_connections, connection_slices)

    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        connection_slices = self._connection_slices(
            pre_vertex_slice, post_vertex_slice)
        return self._get_weight_variance(self._weights, connection_slices)

    def generate_on_machine(self):
        return (
            not self._generate_lists_on_host(self._weights) and
            not self._generate_lists_on_host(self._delays))

    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        n_connections = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_connections -= post_vertex_slice.n_atoms
        connection_slices = self._connection_slices(
            pre_vertex_slice, post_vertex_slice)
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        if (not self._allow_self_connections and
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
            self._weights, n_connections, connection_slices)
        block["delay"] = self._generate_delays(
            self._delays, n_connections, connection_slices)
        block["synapse_type"] = synapse_type
        return block
