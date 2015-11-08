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

    def __init__(self, conn_list=None, safe=True, verbose=False):
        """
        Creates a new FromListConnector.
        """
        if not safe:
            logger.warn("the modification of the safe parameter will be "
                        "ignored")
        if verbose:
            logger.warn("the modification of the verbose parameter will be "
                        "ignored")
        if conn_list is None:
            self._conn_list = numpy.zeros(0)
        else:
            self._conn_list = numpy.array(
                conn_list, dtype=[("source", "uint32"), ("target", "uint16"),
                                  ("weight", "float64"), ("delay", "float64")])

    def get_delay_maximum(self):
        return numpy.max(self._conn_list["delay"])

    def get_n_connections_from_pre_vertex_maximum(
            self, n_pre_slices, pre_slice_index, n_post_slices,
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
            self, pre_vertex_slice, post_vertex_slice):
        mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        targets = self._conn_list["target"][mask]
        if targets.size == 0:
            return 0
        return numpy.max(numpy.bincount(targets))

    def get_weight_mean(self, pre_vertex_slice, post_vertex_slice):
        mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        return numpy.mean(self._conn_list["weight"][mask])

    def get_weight_maximum(self, pre_vertex_slice, post_vertex_slice):
        mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        return numpy.max(self._conn_list["weight"][mask])

    def get_weight_variance(self, pre_vertex_slice, post_vertex_slice):
        mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        return numpy.var(self._conn_list["weight"][mask])

    def create_synaptic_block(
            self, n_pre_slices, pre_slice_index, n_post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        return self._conn_list[mask]
