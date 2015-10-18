from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from pyNN.random import RandomDistribution
from spynnaker.pyNN.utilities import utility_calls
import numpy


@add_metaclass(ABCMeta)
class AbstractConnector(object):
    """ Abstract class which PyNN Connectors extend
    """

    NUMPY_SYNAPSES_DTYPE = [("source", "uint32"), ("target", "uint16"),
                            ("weight", "float64"), ("delay", "float64"),
                            ("synapse_type", "uint8"), ("index", "uint8")]

    def __init__(self):
        self._n_pre_neurons = None
        self._n_post_neurons = None

    def set_population_information(
            self, n_pre_neurons, n_post_neurons):
        self._n_pre_neurons = n_pre_neurons
        self._n_post_neurons = n_post_neurons

    @staticmethod
    def _get_delay_maximum(delays, n_connections):
        """ Get the maximum delay given a float, RandomDistribution or list of\
            delays
        """
        if isinstance(delays, RandomDistribution):
            if delays.boundaries is not None:
                return max(delays.boundaries)

            return utility_calls.get_maximum_probable_value(
                delays, n_connections)
        elif not hasattr(delays, '__iter__'):
            return delays
        else:
            return max(delays)

    @abstractmethod
    def get_delay_maximum(self):
        """ Get the maximum delay specified by the user in ms, or None if\
            unbounded
        """

    @staticmethod
    def _get_n_connections_from_pre_vertex_with_delay_maximum(
            delays, n_connections, connection_slice, min_delay, max_delay):
        """ Gets the expected number of delays that will fall within min_delay\
            and max_delay given given a float, RandomDistribution or list of\
            delays
        """
        if isinstance(delays, RandomDistribution):
            return utility_calls.get_probability_within_range(
                delays, min_delay, max_delay) * n_connections * 1.1
        elif not hasattr(delays, '__iter__'):
            if delays >= min_delay and delays <= max_delay:
                return n_connections
            return 0
        else:
            return len([
                delay for delay in delays[connection_slice]
                if delay >= min_delay and delay <= max_delay])

    @abstractmethod
    def get_n_connections_from_pre_vertex_maximum(
            self, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        """ Get the maximum number of connections between those from each of\
            the neurons in the pre_vertex_slice (or all in the pre vertex if\
            pre_vertex_slice is None) to neurons in the post_vertex_slice,\
            for connections with a delay between min_delay and max_delay\
            (inclusive) if specified (otherwise all connections)
        """

    @abstractmethod
    def get_n_connections_to_post_vertex_maximum(
            self, pre_vertex_slice, post_vertex_slice):
        """ Get the maximum number of connections between those to each of the\
            neurons in the post_vertex_slice from neurons in the\
            pre_vertex_slice
        """

    @staticmethod
    def _get_weight_mean(weights, n_connections, connection_slice):
        """ Get the mean of the weights
        """
        if isinstance(weights, RandomDistribution):
            return utility_calls.get_mean(weights)
        elif not hasattr(weights, '__iter__'):
            return weights
        else:
            return numpy.mean(weights[connection_slice])[0]

    @abstractmethod
    def get_weight_mean(self, pre_vertex_slice, post_vertex_slice):
        """ Get the mean of the weights for this connection
        """

    @staticmethod
    def _get_weight_maximum(weights, n_connections, connection_slice):
        """ Get the maximum of the weights
        """
        if isinstance(weights, RandomDistribution):
            if weights.boundaries is not None:
                return max(weights.boundaries)

            return utility_calls.get_maximum_probable_value(
                weights, n_connections)
        elif not hasattr(weights, '__iter__'):
            return weights
        else:
            return max(weights[connection_slice])

    @abstractmethod
    def get_weight_maximum(self, pre_vertex_slice, post_vertex_slice):
        """ Get the maximum of the weights for this connection
        """

    @staticmethod
    def _get_weight_variance(weights, connection_slice):
        """ Get the variance of the weights
        """
        if isinstance(weights, RandomDistribution):
            return utility_calls.get_variance(weights)
        elif not hasattr(weights, '__iter__'):
            return 0.0
        else:
            return numpy.var(weights[connection_slice])[0]

    @abstractmethod
    def get_weight_variance(self, pre_vertex_slice, post_vertex_slice):
        """ Get the variance of the weights for this connection
        """

    def _generate_values(self, values, n_connections, connection_slice):
        if isinstance(values, RandomDistribution):
            return values.next(n_connections)
        elif not hasattr(values, '__iter__'):
            return numpy.repeat([values], n_connections)
        else:
            return values[connection_slice]

    @abstractmethod
    def create_synaptic_block(
            self, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        """ Create a synaptic block from the data
        """
