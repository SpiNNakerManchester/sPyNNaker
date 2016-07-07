from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
import logging
import numpy

logger = logging.getLogger(__name__)


class FromListConnector(AbstractConnector):
    """ Make connections according to a list.

    :param: conn_list:
        a list of tuples, one tuple for each connection. Each
        tuple should contain::

         (pre_idx, post_idx, weight, delay)

        where pre_idx is the index (i.e. order in the Population,
        not the ID) of the presynaptic neuron, and post_idx is
        the index of the postsynaptic neuron.
    """

    CONN_LIST_DTYPE = [
        ("source", "uint32"), ("target", "uint32"),
        ("weight", "float64"), ("delay", "float64")]

    def __init__(self, conn_list, safe=True, verbose=False):
        """
        Creates a new FromListConnector.
        """
        AbstractConnector.__init__(self, safe, None, verbose)
        if conn_list is None or len(conn_list) == 0:
            self._conn_list = numpy.zeros(0, dtype=self.CONN_LIST_DTYPE)
        else:
            temp_conn_list = conn_list
            if not isinstance(conn_list[0], tuple):
                temp_conn_list = [tuple(items) for items in conn_list]
            self._conn_list = numpy.array(
                temp_conn_list, dtype=self.CONN_LIST_DTYPE)

    def get_delay_maximum(self):
        return numpy.max(self._conn_list["delay"])

    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        delays = self._conn_list["delay"][mask]
        if delays.size == 0:
            return 0
        return numpy.var(delays)

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):

        mask = None
        if min_delay is None or max_delay is None:
            mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                    (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                    (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                    (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        else:
            mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                    (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                    (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                    (self._conn_list["target"] <= post_vertex_slice.hi_atom) &
                    (self._conn_list["delay"] >= min_delay) &
                    (self._conn_list["delay"] <= max_delay))
        sources = self._conn_list["source"][mask]
        if sources.size == 0:
            return 0
        return numpy.max(numpy.bincount(sources))

    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        targets = self._conn_list["target"][mask]
        if targets.size == 0:
            return 0
        return numpy.max(numpy.bincount(targets))

    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        weights = self._conn_list["weight"][mask]
        if weights.size == 0:
            return 0
        return numpy.mean(weights)

    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        weights = self._conn_list["weight"][mask]
        if weights.size == 0:
            return 0
        return numpy.max(weights)

    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        weights = self._conn_list["weight"][mask]
        if weights.size == 0:
            return 0
        return numpy.var(weights)

    def generate_on_machine(self):
        return False

    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        items = self._conn_list[mask]
        block = numpy.zeros(
            items.size, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        block["source"] = items["source"]
        block["target"] = items["target"]
        block["weight"] = items["weight"]
        block["delay"] = self._clip_delays(items["delay"])
        block["synapse_type"] = synapse_type
        return block
