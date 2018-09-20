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

        :param '?' cset:
            A description of the connection set between populations
        """
        super(CSAConnector, self).__init__(safe, verbose)
        self._cset = cset
        self._verbose = verbose

        # Storage for full connection sets
        self._full_connection_set = None
        self._full_cset = None

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self):
        n_connections_max = self._n_pre_neurons * self._n_post_neurons
        # we can probably look at the array and do better than this?
        return self._get_delay_maximum(
            self._delays, n_connections_max)

    @overrides(AbstractConnector.get_delay_variance)
    def get_delay_variance(self):
        return self._get_delay_variance(self._delays, None)

    def _get_n_connections(self, pre_vertex_slice, post_vertex_slice):
        # do the work from self._cset in here
        # get the values for this slice
        pre_lo = pre_vertex_slice.lo_atom
        pre_hi = pre_vertex_slice.hi_atom
        post_lo = post_vertex_slice.lo_atom
        post_hi = post_vertex_slice.hi_atom

        # this is where the magic needs to happen somehow
        if self._full_cset is None:
            self._full_cset = [x for x in csa.cross(
                range(self._n_pre_neurons),
                range(self._n_post_neurons)) * self._cset]

        # use CSA to cross the range of this vertex's neurons with the cset
        pair_list = csa.cross(
            range(pre_lo, pre_hi+1),
            range(post_lo, post_hi+1)) * self._full_cset

        if self._verbose:
            print('full cset: ', self._full_cset)
            print('this vertex pair_list: ', pair_list)
            print('this vertex pre_neurons: ',
                  [x[0] for x in pair_list])
            print('this vertex post_neurons: ',
                  [x[1] for x in pair_list])

        n_connections = len(pair_list)  # size of the array created
        return n_connections, pair_list

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        n_connections, pair_list = self._get_n_connections(
            pre_vertex_slice, post_vertex_slice)

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._delays, self._n_pre_neurons * self._n_post_neurons,
            n_connections, None, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        n_connections, pair_list = self._get_n_connections(
            pre_vertex_slice, post_vertex_slice)
        return n_connections

    @overrides(AbstractConnector.get_weight_mean)
    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        return self._get_weight_mean(self._weights, None)

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        n_connections, pair_list = self._get_n_connections(
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
        n_connections, pair_list = self._get_n_connections(
            pre_vertex_slice, post_vertex_slice)

        # Use whatever has been set up in _get_n_connections here
        # to send into the block structure

        # Use the CSA implementation to show the connection structure?
        if self._full_connection_set is None:
            self._full_connection_set = [x for x in pair_list]
        else:
            self._full_connection_set += [x for x in pair_list]

        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        # source and target are the pre_neurons and post_neurons in pair_list
        block["source"] = [x[0] for x in pair_list]
        block["target"] = [x[1] for x in pair_list]
        block["weight"] = self._generate_weights(
            self._weights, n_connections, None)
        block["delay"] = self._generate_delays(
            self._delays, n_connections, None)
        block["synapse_type"] = synapse_type
        return block

    def show_connection_set(self):
        csa.show(self._full_connection_set,
                 self._n_pre_neurons, self._n_post_neurons)

    def __repr__(self):
        return "CSAConnector({})".format(
            self._full_cset)
