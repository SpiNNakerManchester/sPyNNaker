from spinn_utilities.overrides import overrides
from spynnaker.pyNN.utilities import utility_calls
from .abstract_connector import AbstractConnector
from spynnaker.pyNN.exceptions import SpynnakerException
from spinn_utilities.abstract_base import abstractmethod

import numpy.random
from six import raise_from

import logging
logger = logging.getLogger(__name__)


class MultapseConnector(AbstractConnector):
    """
    Create a multapse connector. The size of the source and destination\
    populations are obtained when the projection is connected. The number of\
    synapses is specified. when instantiated, the required number of synapses\
    is created by selecting at random from the source and target populations\
    with replacement. Uniform selection probability is assumed.
    """
    def __init__(self, num_synapses, allow_self_connections=True,
                 with_replacement=True, safe=True, verbose=False):
        """
        Creates a new connector.

        :param num_synapses:
            This is the total number of synapses in the connection.
        :type num_synapses: int
        :param allow_self_connections:
            Allow a neuron to connect to itself or not.
        :type allow_self_connections: bool
        :param with_replacement:
            When selecting, allow a neuron to be re-selected or not.
        :type with_replacement: bool
        """
        super(MultapseConnector, self).__init__(safe, verbose)
        self._num_synapses = num_synapses
        self._allow_self_connections = allow_self_connections
        self._with_replacement = with_replacement
        self._pre_slices = None
        self._post_slices = None
        self._synapses_per_edge = None

    @abstractmethod
    def get_rng_next(self, num_synapses, prob_connect):
        """ Get the required rngs
        """

    @overrides(AbstractConnector.set_weights_and_delays)
    def set_weights_and_delays(self, weights, delays):
        """ sets the weights and delays as needed

        :param `float` weights:
            may either be a float, a !RandomDistribution object, a list \
            1D array with at least as many items as connections to be \
            created, or a distance dependence as per a d_expression. Units nA.
        :param `float` delays:  -- as `weights`. If `None`, all synaptic \
            delays will be set to the global minimum delay.
        :raises Exception: when not a standard interface of list, scaler, \
            or random number generator
        :raises NotImplementedError: when lists are not supported and entered
        """
        if self._weights is not None:
            logger.warning(
                'Weights were already set in '+str(self)+', possibly in '
                'another projection: currently this will overwrite the values '
                'in the previous projection. For now, set up a new connector.')
        if self._delays is not None:
            logger.warning(
                'Delays were already set in '+str(self)+', possibly in '
                'another projection: currently this will overwrite the values '
                'in the previous projection. For now, set up a new connector.')
        self._weights = weights
        self._delays = delays
        self._check_parameters(weights, delays, allow_lists=True)

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self):
        return self._get_delay_maximum(self._delays, self._num_synapses)

    @overrides(AbstractConnector.get_delay_variance)
    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        self._update_synapses_per_post_vertex(pre_slices, post_slices)
        connection_slice = self._get_connection_slice(
            pre_slice_index, post_slice_index)
        return self._get_delay_variance(self._delays, [connection_slice])

    def _update_synapses_per_post_vertex(self, pre_slices, post_slices):
        if (self._synapses_per_edge is None or
                len(self._pre_slices) != len(pre_slices) or
                len(self._post_slices) != len(post_slices)):
            n_pre_atoms = sum([pre.n_atoms for pre in pre_slices])
            n_post_atoms = sum([post.n_atoms for post in post_slices])
            n_connections = n_pre_atoms * n_post_atoms
            prob_connect = [
                float(pre.n_atoms * post.n_atoms) / float(n_connections)
                for pre in pre_slices for post in post_slices]
            self._synapses_per_edge = self.get_rng_next(
                self._num_synapses, prob_connect)
            self._pre_slices = pre_slices
            self._post_slices = post_slices

    def _get_n_connections(self, pre_slice_index, post_slice_index):
        index = (len(self._post_slices) * pre_slice_index) + post_slice_index
        return self._synapses_per_edge[index]

    def _get_connection_slice(self, pre_slice_index, post_slice_index):
        index = (len(self._post_slices) * pre_slice_index) + post_slice_index
        n_connections = self._synapses_per_edge[index]
        start_connection = 0
        if index > 0:
            start_connection = numpy.sum(self._synapses_per_edge[:index])
        return slice(start_connection, start_connection + n_connections, 1)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        # pylint: disable=too-many-arguments
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

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
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

    @overrides(AbstractConnector.get_weight_mean)
    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        self._update_synapses_per_post_vertex(pre_slices, post_slices)
        n_connections = self._get_n_connections(
            pre_slice_index, post_slice_index)
        if n_connections == 0:
            return 0
        connection_slice = self._get_connection_slice(
            pre_slice_index, post_slice_index)
        return self._get_weight_mean(self._weights, [connection_slice])

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        self._update_synapses_per_post_vertex(pre_slices, post_slices)
        n_connections = self._get_n_connections(
            pre_slice_index, post_slice_index)
        if n_connections == 0:
            return 0
        connection_slice = self._get_connection_slice(
            pre_slice_index, post_slice_index)
        return self._get_weight_maximum(
            self._weights, n_connections, [connection_slice])

    @overrides(AbstractConnector.get_weight_variance)
    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        self._update_synapses_per_post_vertex(pre_slices, post_slices)
        connection_slice = self._get_connection_slice(
            pre_slice_index, post_slice_index)
        return self._get_weight_variance(self._weights, [connection_slice])

    @overrides(AbstractConnector.generate_on_machine)
    def generate_on_machine(self):
        return (
            not self._generate_lists_on_host(self._weights) and
            not self._generate_lists_on_host(self._delays))

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        # pylint: disable=too-many-arguments
        # update the synapses as required, and get the number of connections
        self._update_synapses_per_post_vertex(pre_slices, post_slices)
        n_connections = self._get_n_connections(
            pre_slice_index, post_slice_index)
        if n_connections == 0:
            return numpy.zeros(0, dtype=self.NUMPY_SYNAPSES_DTYPE)

        # get connection slice
        connection_slice = self._get_connection_slice(
            pre_slice_index, post_slice_index)

        # set up array for synaptic block
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        # Create pairs between the pre- and post-vertex slices
        pairs = numpy.mgrid[pre_vertex_slice.as_slice,
                            post_vertex_slice.as_slice].T.reshape((-1, 2))

        # Deal with case where self-connections aren't allowed
        if not self._allow_self_connections and (self._pre_population is
                                                 self._post_population):
            pairs = pairs[pairs[:, 0] != pairs[:, 1]]

        # Now do the actual random choice from the available connections
        try:
            chosen = numpy.random.choice(
                pairs.shape[0], size=n_connections,
                replace=self._with_replacement)
        except Exception as e:
            raise_from(SpynnakerException(
                "MultapseConnector: The number of connections is too large "
                "for sampling without replacement; "
                "reduce the value specified in the connector"), e)

        # Set up synaptic block
        block["source"] = pairs[chosen, 0]
        block["target"] = pairs[chosen, 1]
        block["weight"] = self._generate_weights(
            self._weights, n_connections, [connection_slice])
        block["delay"] = self._generate_delays(
            self._delays, n_connections, [connection_slice])
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "MultapseConnector({})".format(self._num_synapses)
