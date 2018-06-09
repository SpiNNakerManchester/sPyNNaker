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
        return self._get_delay_maximum(len(self._array))

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, min_delay=None, max_delay=None):
        post_neurons = self._array[1]
        mask = ((post_neurons >= post_vertex_slice.lo_atom) and
                (post_neurons <= post_vertex_slice.hi_atom))
        n_connections = numpy.max(numpy.bincount(self._array[0][mask]))
        if min_delay is None and max_delay is None:
            return n_connections

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            len(self._array), n_connections, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        return numpy.max(numpy.bincount(self._array[1]))

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self):
        return self._get_weight_maximum(len(self._array))

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        pre_neurons = self._array[0]
        post_neurons = self._array[1]
        mask = ((pre_neurons >= pre_vertex_slice.lo_atom) and
                (pre_neurons <= pre_vertex_slice.hi_atom) and
                (post_neurons >= post_vertex_slice.lo_atom) and
                (post_neurons <= post_vertex_slice.hi_atom))

        # Feed the arrays calculated above into the block structure
        source = pre_neurons[mask]
        target = post_neurons[mask]
        n_connections = len(source)

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
            self._array)
