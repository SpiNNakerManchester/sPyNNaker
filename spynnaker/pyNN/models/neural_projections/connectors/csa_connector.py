from spinn_utilities.overrides import overrides
from .abstract_connector import AbstractConnector
import logging
import numpy
import csa

logger = logging.getLogger(__name__)


class CSAConnector(AbstractConnector):
    """ Make connections using a Connection Set Algebra (Djurfeldt 2012)
        description between the neurons in the pre- and post-populations.
    """

    __slots = [
        "_cset"]

    def __init__(
            self, cset,
            safe=True, callback=None, verbose=False):
        """

        :param `string` cset:
            A string describing the connection set between populations
        """
        super(CSAConnector, self).__init__(safe, verbose)
        self._cset = cset
        # think this is probably needed here
        self._arrays_set = False

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
        # do the work from self._cset in here
#        if not self._arrays_set:
        # get the values for this slice
        pre_lo = pre_vertex_slice.lo_atom
        pre_hi = pre_vertex_slice.hi_atom
        post_lo = post_vertex_slice.lo_atom
        post_hi = post_vertex_slice.hi_atom

        # use CSA to cross the range of this vertex's neurons with the cset
        pair_list = csa.cross(range(pre_lo, pre_hi),
                              range(post_lo, post_hi)) * self._cset

        print 'pair_list: ', pair_list
        print 'tabulate: ', csa.tabulate(pair_list)

        self._pre_neurons = [x[0] for x in pair_list]
        self._post_neurons = [x[1] for x in pair_list]

        print 'pre_neurons: ', self._pre_neurons
        print 'post_neurons: ', self._post_neurons

            #self._arrays_set = True

        n_connections = len(self._pre_neurons) # size of the array created
        print 'n_connections: ', n_connections
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

        # Use whatever has been set up in _get_n_connections here
        # to send into the block structure

        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        block["source"] = self._pre_neurons
        block["target"] = self._post_neurons
        block["weight"] = self._generate_weights(
            self._weights, n_connections, None)
        block["delay"] = self._generate_delays(
            self._delays, n_connections, None)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "CSAConnector({})".format(
            self._cset)
