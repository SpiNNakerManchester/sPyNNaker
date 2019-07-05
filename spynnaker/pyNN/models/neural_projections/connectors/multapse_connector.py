import logging
import math
import numpy.random
from six import raise_from
from spinn_utilities.abstract_base import abstractmethod
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.exceptions import SpynnakerException
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)

logger = logging.getLogger(__name__)


class MultapseConnector(AbstractGenerateConnectorOnMachine):
    """ Create a multapse connector. The size of the source and destination\
        populations are obtained when the projection is connected. The number\
        of synapses is specified. when instantiated, the required number of\
        synapses is created by selecting at random from the source and target\
        populations with replacement. Uniform selection probability is assumed.
    """
    __slots__ = [
        "__allow_self_connections",
        "__num_synapses",
        "__post_slices",
        "__pre_slices",
        "__synapses_per_edge",
        "__with_replacement"]

    def __init__(self, num_synapses, allow_self_connections=True,
                 with_replacement=True, safe=True, verbose=False,
                 rng=None):
        """
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
        self.__num_synapses = num_synapses
        self.__allow_self_connections = allow_self_connections
        self.__with_replacement = with_replacement
        self.__pre_slices = None
        self.__post_slices = None
        self.__synapses_per_edge = None
        self._rng = rng

    @abstractmethod
    def get_rng_next(self, num_synapses, prob_connect):
        """ Get the required RNGs
        """

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, delays):
        return self._get_delay_maximum(delays, self.__num_synapses)

    def _update_synapses_per_post_vertex(self, pre_slices, post_slices):
        if (self.__synapses_per_edge is None or
                len(self.__pre_slices) != len(pre_slices) or
                len(self.__post_slices) != len(post_slices)):
            n_pre_atoms = sum([pre.n_atoms for pre in pre_slices])
            n_post_atoms = sum([post.n_atoms for post in post_slices])
            n_connections = n_pre_atoms * n_post_atoms
            if (not self.__with_replacement and
                    n_connections < self.__num_synapses):
                raise SpynnakerException(
                    "FixedNumberTotalConnector will not work correctly when "
                    "with_replacement=False & num_synapses > n_pre * n_post")
            prob_connect = [
                float(pre.n_atoms * post.n_atoms) / float(n_connections)
                for pre in pre_slices for post in post_slices]
            self.__synapses_per_edge = self.get_rng_next(
                self.__num_synapses, prob_connect)
            if sum(self.__synapses_per_edge) != self.__num_synapses:
                raise Exception("{} of {} synapses generated".format(
                    sum(self.__synapses_per_edge), self.__num_synapses))
            self.__pre_slices = pre_slices
            self.__post_slices = post_slices

    def _get_n_connections(self, pre_slice_index, post_slice_index):
        index = (len(self.__post_slices) * pre_slice_index) + post_slice_index
        return self.__synapses_per_edge[index]

    def _get_connection_slice(self, pre_slice_index, post_slice_index):
        index = (len(self.__post_slices) * pre_slice_index) + post_slice_index
        n_connections = self.__synapses_per_edge[index]
        start_connection = 0
        if index > 0:
            start_connection = numpy.sum(self.__synapses_per_edge[:index])
        return slice(start_connection, start_connection + n_connections, 1)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, delays, post_vertex_slice, min_delay=None, max_delay=None):
        prob_in_slice = (
            float(post_vertex_slice.n_atoms) / float(self._n_post_neurons))
        max_in_slice = utility_calls.get_probable_maximum_selected(
            self.__num_synapses, self.__num_synapses, prob_in_slice)
        prob_in_row = 1.0 / float(self._n_pre_neurons)
        n_connections = utility_calls.get_probable_maximum_selected(
            self.__num_synapses, max_in_slice, prob_in_row)

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            delays, self._n_pre_neurons * self._n_post_neurons,
            n_connections, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        prob_of_choosing_post_atom = 1.0 / float(self._n_post_neurons)
        return utility_calls.get_probable_maximum_selected(
            self.__num_synapses, self.__num_synapses,
            prob_of_choosing_post_atom)

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, weights):
        return self._get_weight_maximum(weights, self.__num_synapses)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, weights, delays, pre_slices, pre_slice_index, post_slices,
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
        if (not self.__allow_self_connections and
                self.pre_population is self.post_population):
            pairs = pairs[pairs[:, 0] != pairs[:, 1]]

        # Now do the actual random choice from the available connections
        try:
            chosen = numpy.random.choice(
                pairs.shape[0], size=n_connections,
                replace=self.__with_replacement)
        except Exception as e:
            raise_from(SpynnakerException(
                "MultapseConnector: The number of connections is too large "
                "for sampling without replacement; "
                "reduce the value specified in the connector"), e)

        # Set up synaptic block
        block["source"] = pairs[chosen, 0]
        block["target"] = pairs[chosen, 1]
        block["weight"] = self._generate_weights(
            weights, n_connections, [connection_slice])
        block["delay"] = self._generate_delays(
            delays, n_connections, [connection_slice])
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "MultapseConnector({})".format(self.__num_synapses)

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self):
        return ConnectorIDs.FIXED_TOTAL_NUMBER_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params)
    def gen_connector_params(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        self._update_synapses_per_post_vertex(pre_slices, post_slices)
        n_connections = self._get_n_connections(
            pre_slice_index, post_slice_index)
        params = [
            self.__allow_self_connections,
            self.__with_replacement,
            n_connections,
            pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms]
        params.extend(self._get_connector_seed(
            pre_vertex_slice, post_vertex_slice, self._rng))
        return numpy.array(params, dtype="uint32")

    @property
    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        return 16 + 16
