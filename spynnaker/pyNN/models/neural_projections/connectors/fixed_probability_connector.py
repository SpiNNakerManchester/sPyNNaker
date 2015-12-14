from pyNN.random import RandomDistribution
from spynnaker.pyNN.utilities import utility_calls
import math
from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
from spinn_front_end_common.utilities import exceptions
import numpy


class FixedProbabilityConnector(AbstractConnector):
    """
    For each pair of pre-post cells, the connection probability is constant.

    :param `float` p_connect:
        a float between zero and one. Each potential connection
        is created with this probability.
    :param `bool` allow_self_connections:
        if the connector is used to connect a
        Population to itself, this flag determines whether a neuron is
        allowed to connect to itself, or only to other neurons in the
        Population.
    :param weights:
        may either be a float or a !RandomDistribution object. Units nA.
    :param delays:
        If `None`, all synaptic delays will be set
        to the global minimum delay.
    :param `pyNN.Space` space:
        a Space object, needed if you wish to specify distance-
        dependent weights or delays - not implemented
    """
    def __init__(self, p_connect, weights=0.0, delays=1,
                 allow_self_connections=True):
        """
        Creates a new FixedProbabilityConnector.
        """
        self._p_connect = p_connect
        self._weights = weights
        self._delays = delays
        self._allow_self_connections = allow_self_connections

        if hasattr(self._weights, "__iter__"):
            raise NotImplementedError(
                "Lists of weights are not supported for the"
                " FixedProbabilityConnector")
        if hasattr(self._delays, "__iter__"):
            raise NotImplementedError(
                "Lists of delays are not supported for the"
                " FixedProbabilityConnector")

        if not 0 <= self._p_connect <= 1:
            raise exceptions.ConfigurationException(
                "The probability should be between 0 and 1 (inclusive)")

    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays,
            self._n_pre_neurons * self._n_post_neurons * self._p_connect * 2.0)

    def get_n_connections_from_pre_vertex_maximum(
            self, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        if min_delay is None or max_delay is None:
            return int(math.ceil(
                post_vertex_slice.n_atoms * self._p_connect * 2.0))

        if isinstance(self._delays, RandomDistribution):
            return int(math.ceil(utility_calls.get_probability_within_range(
                self._delays, min_delay, max_delay) *
                post_vertex_slice.n_atoms * self._p_connect * 2.0))
        elif not hasattr(self._delays, '__iter__'):
            if self._delays >= min_delay and self._delays <= max_delay:
                return int(math.ceil(
                    post_vertex_slice.n_atoms * self._p_connect * 2.0))
            return 0

        raise Exception("Unknown input type for delays")

    def get_n_connections_to_post_vertex_maximum(
            self, pre_vertex_slice, post_vertex_slice):
        return int(math.ceil(pre_vertex_slice.n_atoms * self._p_connect * 2.0))

    def get_weight_mean(self, pre_vertex_slice, post_vertex_slice):
        n_connections = int(math.ceil(
            pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms *
            self._p_connect * 1.1))
        return self._get_weight_mean(
            self._weights, n_connections, None)

    def get_weight_maximum(self, pre_vertex_slice, post_vertex_slice):
        n_connections = int(math.ceil(
            pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms *
            self._p_connect * 1.1))
        return self._get_weight_maximum(
            self._weights, n_connections, None)

    def get_weight_variance(self, pre_vertex_slice, post_vertex_slice):
        return self._get_weight_variance(self._weights, None)

    def create_synaptic_block(
            self, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type, connector_index):

        present = (numpy.random.rand(
            post_vertex_slice.n_atoms * pre_vertex_slice.n_atoms) <=
            self._p_connect)
        ids = numpy.where(present)[0]
        n_connections = numpy.sum(present)

        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        block["source"] = (
            (ids / post_vertex_slice.n_atoms) + pre_vertex_slice.lo_atom)
        block["target"] = (
            (ids % post_vertex_slice.n_atoms) + post_vertex_slice.lo_atom)
        block["weight"] = self._generate_values(
            self._weights, n_connections, None)
        block["delay"] = self._generate_values(
            self._delays, n_connections, None)
        block["synapse_type"] = synapse_type
        block["connector_index"] = connector_index
        return block
