from spinn_utilities.overrides import overrides
from .abstract_connector import AbstractConnector
import logging
import numpy

logger = logging.getLogger(__name__)


class ArrayConnector(AbstractConnector):
    """ Make connections using an array of integers based on the IDs
        of the neurons in the pre- and post-populations.
    """

    __slots = [
        "_array"]

    def __init__(
            self, array,
            safe=True, callback=None, verbose=False):
        """

        :param `integer` array:
            A (numpy) array of integers that specifies the connections
            between the pre- and post-populations
        """
        super(ArrayConnector, self).__init__(safe, verbose)
        self._array = array

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self):
        n_connections_max = self._n_pre_neurons * self._n_post_neurons
        # we can probably look at the array and do better than this?
        return self._get_delay_maximum(
            self._delays, n_connections_max)

    @overrides(AbstractConnector.get_delay_variance)
    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        return self._get_delay_variance(self._delays, None)

    def _get_n_connections(self, pre_vertex_slice, post_vertex_slice):
        n_connections = pre_vertex_slice.n_atoms
        return n_connections

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        n_connections = self._get_n_connections(
            pre_vertex_slice, post_vertex_slice)

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._delays, self._n_pre_neurons * self._n_post_neurons,
            n_connections, None, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        return self._get_n_connections(
            pre_vertex_slice, post_vertex_slice)

    @overrides(AbstractConnector.get_weight_mean)
    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        return self._get_weight_mean(self._weights, None)

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        n_connections = self._get_n_connections(
            pre_vertex_slice, post_vertex_slice)
        return self._get_weight_maximum(
            self._weights, n_connections, None)

    @overrides(AbstractConnector.get_weight_variance)
    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        return self._get_weight_variance(self._weights, None)

    @overrides(AbstractConnector.generate_on_machine)
    def generate_on_machine(self):
        return False

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        n_connections = self._get_n_connections(pre_vertex_slice,
                                                post_vertex_slice)

        # The array already exists: just feed it into the block structure
        source = self._array[
            0,pre_vertex_slice.lo_atom:pre_vertex_slice.hi_atom+1]

        # This might look strange, but it's correct: the 2D array needs
        # the same set of indices on each row for this to work
        target = self._array[
            1,pre_vertex_slice.lo_atom:pre_vertex_slice.hi_atom+1]

        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        block["source"] = source
        block["target"] = target
        block["weight"] = self._generate_weights(
            self._weights, n_connections, None)
        block["delay"] = self._generate_delays(
            self._delays, n_connections, None)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "ArrayConnector({})".format(
            self._index_expression)
