from pyNN.random import RandomDistribution
from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
import numpy
import logging

logger = logging.getLogger(__file__)


class FixedNumberPreConnector(AbstractConnector):
    """ Connects a fixed number of pre-synaptic neurons selected at random,
        to all post-synaptic neurons
    """
    def __init__(
            self, n, weights=0.0, delays=1, allow_self_connections=True,
            space=None, safe=True, verbose=False):
        """

        :param `int` n:
            number of random pre-synaptic neurons connected to output
        :param `bool` allow_self_connections:
            if the connector is used to connect a
            Population to itself, this flag determines whether a neuron is
            allowed to connect to itself, or only to other neurons in the
            Population.
        :param weights:
            may either be a float, a !RandomDistribution object, a list/
            1D array with at least as many items as connections to be
            created. Units nA.
        :param delays:
            If `None`, all synaptic delays will be set
            to the global minimum delay.
        :param `pyNN.Space` space:
            a Space object, needed if you wish to specify distance-
            dependent weights or delays - not implemented
        """
        AbstractConnector.__init__(self, safe, space, verbose)
        self._n_pre = n
        self._weights = weights
        self._delays = delays
        self._allow_self_connections = allow_self_connections
        self._pre_neurons = None

        self._check_parameters(weights, delays, allow_lists=False)
        if isinstance(n, RandomDistribution):
            raise NotImplementedError(
                "RandomDistribution is not supported for n in the"
                " implementation of FixedNumberPreConnector on this platform")

    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays, self._n_pre * self._n_post_neurons)

    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(pre_vertex_slice):
            return 0.0
        return self._get_delay_variance(self._delays, None)

    def _get_pre_neurons(self):
        if self._pre_neurons is None:
            self._pre_neurons = numpy.random.choice(
                self._n_pre_neurons, self._n_pre, False)
            self._pre_neurons.sort()
        return self._pre_neurons

    def _pre_neurons_in_slice(self, pre_vertex_slice):
        pre_neurons = self._get_pre_neurons()
        return pre_neurons[
            (pre_neurons >= pre_vertex_slice.lo_atom) &
            (pre_neurons <= pre_vertex_slice.hi_atom)]

    def _is_connected(self, pre_vertex_slice):
        return self._pre_neurons_in_slice(pre_vertex_slice).size > 0

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):

        if not self._is_connected(pre_vertex_slice):
            return 0

        if min_delay is None or max_delay is None:
            return post_vertex_slice.n_atoms

        pre_neurons = self._pre_neurons_in_slice(pre_vertex_slice)
        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._delays, self._n_pre * self._n_post_neurons,
            len(pre_neurons) * post_vertex_slice.n_atoms, None,
            min_delay, max_delay)

    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(pre_vertex_slice):
            return 0
        return self._n_pre

    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(pre_vertex_slice):
            return 0.0
        return self._get_weight_mean(self._weights, None)

    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(pre_vertex_slice):
            return 0.0
        pre_neurons = self._pre_neurons_in_slice(pre_vertex_slice)
        n_connections = len(pre_neurons) * post_vertex_slice.n_atoms
        return self._get_weight_maximum(
            self._weights, n_connections, None)

    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(pre_vertex_slice):
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
        if not self._is_connected(pre_vertex_slice):
            return numpy.zeros(0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        pre_neurons_in_slice = self._pre_neurons_in_slice(pre_vertex_slice)

        n_connections = len(pre_neurons_in_slice) * post_vertex_slice.n_atoms
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_connections -= len(pre_neurons_in_slice)
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            block["source"] = [
                pre_index for pre_index in pre_neurons_in_slice
                for post_index in range(
                    post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1)
                if pre_index != post_index]
            block["target"] = [
                post_index for pre_index in pre_neurons_in_slice
                for post_index in range(
                    post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1)
                if pre_index != post_index]
        else:
            block["source"] = numpy.repeat(
                pre_neurons_in_slice, post_vertex_slice.n_atoms)
            block["target"] = numpy.tile(numpy.arange(
                post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1),
                len(pre_neurons_in_slice))
        block["weight"] = self._generate_weights(
            self._weights, n_connections, None)
        block["delay"] = self._generate_delays(
            self._delays, n_connections, None)
        block["synapse_type"] = synapse_type
        return block
