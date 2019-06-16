import logging
import numpy
from spinn_utilities.overrides import overrides
from .abstract_connector import AbstractConnector

logger = logging.getLogger(__name__)


class ArrayConnector(AbstractConnector):
    """ Make connections using an array of integers based on the IDs\
        of the neurons in the pre- and post-populations.
    """

    __slots = [
        "__array", "__array_dims", "__n_total_connections"]

    def __init__(
            self, array,
            safe=True, callback=None, verbose=False):
        """
        :param array:
            An explicit boolean matrix that specifies the connections\
            between the pre- and post-populations\
            (see PyNN documentation)
        """
        super(ArrayConnector, self).__init__(safe, verbose)
        self.__array = array
        # we can get the total number of connections straight away
        # from the boolean matrix
        n_total_connections = 0
        # array shape
        dims = array.shape
        for i in range(dims[0]):
            for j in range(dims[1]):
                if array[i, j] == 1:
                    n_total_connections += 1

        self.__n_total_connections = n_total_connections
        self.__array_dims = dims

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, delays):
        return self._get_delay_maximum(delays, len(self.__array))

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, delays, post_vertex_slice, min_delay=None, max_delay=None):
        n_connections = 0
        post_lo = post_vertex_slice.lo_atom
        post_hi = post_vertex_slice.hi_atom
        for i in range(self.__array_dims[0]):
            for j in range(post_lo, post_hi+1):
                if self.__array[i, j] == 1:
                    n_connections += 1

        if min_delay is None and max_delay is None:
            return n_connections

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            delays, self.__n_total_connections, n_connections, min_delay,
            max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        return self.__n_total_connections

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, weights):
        return self._get_weight_maximum(weights, self.__n_total_connections)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, weights, delays, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        pre_neurons = []
        post_neurons = []
        n_connections = 0
        pre_lo = pre_vertex_slice.lo_atom
        pre_hi = pre_vertex_slice.hi_atom
        post_lo = post_vertex_slice.lo_atom
        post_hi = post_vertex_slice.hi_atom
        for i in range(pre_lo, pre_hi+1):
            for j in range(post_lo, post_hi+1):
                if self.__array[i, j] == 1:
                    pre_neurons.append(i)
                    post_neurons.append(j)
                    n_connections += 1

        # Feed the arrays calculated above into the block structure
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        block["source"] = pre_neurons
        block["target"] = post_neurons
        block["weight"] = self._generate_weights(
            weights, n_connections, None)
        block["delay"] = self._generate_delays(
            delays, n_connections, None)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "ArrayConnector({})".format(
            self.__array)
