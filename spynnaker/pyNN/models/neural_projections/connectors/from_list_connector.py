from spinn_utilities.overrides import overrides
from .abstract_connector import AbstractConnector
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.utilities.utility_calls import convert_param_to_numpy
import logging
import numpy

logger = logging.getLogger(__name__)


class FromListConnector(AbstractConnector):
    """ Make connections according to a list.
    """
    __slots__ = [
        "_conn_list",
        "_converted_weights_and_delays"]

    CONN_LIST_DTYPE = numpy.dtype([
        ("source", numpy.uint32), ("target", numpy.uint32),
        ("weight", numpy.float64), ("delay", numpy.float64)])

    def __init__(self, conn_list, safe=True, verbose=False):
        """
        :param: conn_list:
            a list of tuples, one tuple for each connection. Each\
            tuple should contain::

                (pre_idx, post_idx, weight, delay)

            where pre_idx is the index (i.e. order in the Population,\
            not the ID) of the presynaptic neuron, and post_idx is\
            the index of the postsynaptic neuron.
        """
        super(FromListConnector, self).__init__(safe, verbose)
        if conn_list is None or not len(conn_list):
            raise InvalidParameterType(
                "The connection list for the FromListConnector must contain"
                " at least a list of tuples, each of which should contain:"
                " (pre_idx, post_idx)")
        self._conn_list = conn_list
        self._conn_matrix = None

        # supports setting these at different times
        self._weights = None
        self._delays = None
        self._converted_weights_and_delays = False

    @overrides(AbstractConnector.set_weights_and_delays)
    def set_weights_and_delays(self, weights, delays):
        # set the data if not already set (supports none overriding via
        # synapse data)
        if self._weights is None:
            self._weights = convert_param_to_numpy(
                weights, len(self._conn_list))
        if self._delays is None:
            self._delays = convert_param_to_numpy(
                delays, len(self._conn_list))

        # if got data, build connlist with correct dtypes
        if (self._weights is not None and self._delays is not None and not
                self._converted_weights_and_delays):
            try:
                self._conn_matrix = numpy.zeros(
                    (int(self._conn_list[:, 0].max() + 1), int(self._conn_list[:, 1].max() + 1)), dtype=bool)
            except IndexError:
                print "too many indices for array"

            for [pre, post] in self._conn_list:
                self._conn_matrix[int(pre)][int(post)] = 1

            # add weights and delays to the conn list
            temp_conn_list = numpy.dstack(
                (self._conn_list[:, 0], self._conn_list[:, 1],
                 self._weights, self._delays))[0]

            self._conn_list = list()
            for element in temp_conn_list:
                self._conn_list.append((element[0], element[1], element[2],
                                        element[3]))

            # set dtypes (cant we just set them within the array?)
            self._conn_list = numpy.asarray(self._conn_list,
                                            dtype=self.CONN_LIST_DTYPE)
            self._converted_weights_and_delays = True


    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self):
        return numpy.max(self._conn_list["delay"])

    @overrides(AbstractConnector.get_delay_variance)
    def get_delay_variance(self):
        return numpy.var(self._conn_list["delay"])

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, min_delay=None, max_delay=None):
        # pylint: disable=too-many-arguments
        mask = None
        if min_delay is None or max_delay is None:
            mask = ((self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                    (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        else:
            mask = ((self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                    (self._conn_list["target"] <= post_vertex_slice.hi_atom) &
                    (self._conn_list["delay"] >= min_delay) &
                    (self._conn_list["delay"] <= max_delay))
        sources = self._conn_list["source"][mask]
        if sources.size == 0:
            return 0
        return numpy.max(numpy.bincount(sources.view('int32')))

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        # pylint: disable=too-many-arguments
        return numpy.max(numpy.bincount(self._conn_list["target"]))

    @overrides(AbstractConnector.get_weight_mean)
    def get_weight_mean(self):
        return numpy.mean(numpy.abs(self._conn_list["weight"]))

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self):
        # pylint: disable=too-many-arguments
        return numpy.amax(numpy.abs(self._conn_list["weight"]))

    @overrides(AbstractConnector.get_weight_variance)
    def get_weight_variance(self):
        # pylint: disable=too-many-arguments
        return numpy.var(numpy.abs(self._conn_list["weight"]))

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        # pylint: disable=too-many-arguments
        mask = ((self._conn_list["source"] >= pre_vertex_slice.lo_atom) &
                (self._conn_list["source"] <= pre_vertex_slice.hi_atom) &
                (self._conn_list["target"] >= post_vertex_slice.lo_atom) &
                (self._conn_list["target"] <= post_vertex_slice.hi_atom))
        items = self._conn_list[mask]
        block = numpy.zeros(items.size, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = items["source"]
        block["target"] = items["target"]
        block["weight"] = items["weight"]
        block["delay"] = self._clip_delays(items["delay"])
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "FromListConnector(n_connections={})".format(
            len(self._conn_list))

    @property
    def conn_list(self):
        return self._conn_list

    @conn_list.setter
    def conn_list(self, new_value):
        self._conn_list = new_value
