from spinn_utilities.overrides import overrides
from .abstract_connector import AbstractConnector
import numpy
import logging

logger = logging.getLogger(__file__)


class AllToAllConnector(AbstractConnector):
    """ Connects all cells in the presynaptic population to all cells in \
        the postsynaptic population
    """

    __slots__ = [
        "_allow_self_connections"]

    def __init__(self, allow_self_connections=True, safe=True, verbose=None):
        """

        :param `bool` allow_self_connections:
            if the connector is used to connect a
            Population to itself, this flag determines whether a neuron is
            allowed to connect to itself, or only to other neurons in the
            Population.
    """
        super(AllToAllConnector, self).__init__(safe, verbose)
        self._allow_self_connections = allow_self_connections
#         self._weights = None
#         self._delays = None
#
#     @overrides(AbstractConnector.set_weights_and_delays)
#     def set_weights_and_delays(self, weights, delays):
#         """ sets the weights and delays as needed
#
#         :param `float` weights:
#             may either be a float, a !RandomDistribution object, a list \
#             1D array with at least as many items as connections to be \
#             created, or a distance dependence as per a d_expression. Units nA.
#         :param `float` delays:  -- as `weights`. If `None`, all synaptic \
#             delays will be set to the global minimum delay.
#         :raises Exception: when not a standard interface of list, scaler, \
#             or random number generator
#         :raises NotImplementedError: when lists are not supported and entered
#         """
#         self._weights = weights
#         self._delays = delays
#         self._check_parameters(weights, delays, allow_lists=True)

    def _connection_slices(self, pre_vertex_slice, post_vertex_slice):
        """ Get a slice of the overall set of connections
        """
        n_post_neurons = self._n_post_neurons
        stop_atom = post_vertex_slice.hi_atom + 1
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_post_neurons -= 1
            stop_atom -= 1
        return [
            slice(n + post_vertex_slice.lo_atom, n + stop_atom)
            for n in range(
                pre_vertex_slice.lo_atom * n_post_neurons,
                (pre_vertex_slice.hi_atom + 1) * n_post_neurons,
                n_post_neurons)]

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, delays):
        return self._get_delay_maximum(
            delays, self._n_pre_neurons * self._n_post_neurons)

    @overrides(AbstractConnector.get_delay_variance)
    def get_delay_variance(
            self, delays, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        connection_slices = self._connection_slices(
            pre_vertex_slice, post_vertex_slice)
        return self._get_delay_variance(delays, connection_slices)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, delays, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        # pylint: disable=too-many-arguments
        total_n_connections_per_pre_neuron = self._n_post_neurons
        n_connections_per_pre_neuron = post_vertex_slice.n_atoms
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_connections_per_pre_neuron -= 1
            total_n_connections_per_pre_neuron -= 1

        if min_delay is None or max_delay is None:
            return n_connections_per_pre_neuron

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            delays, self._n_pre_neurons * total_n_connections_per_pre_neuron,
            n_connections_per_pre_neuron,
            self._connection_slices(pre_vertex_slice, post_vertex_slice),
            min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            return pre_vertex_slice.n_atoms - 1
        return pre_vertex_slice.n_atoms

    @overrides(AbstractConnector.get_weight_mean)
    def get_weight_mean(
            self, weights, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        n_connections = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_connections -= post_vertex_slice.n_atoms
        connection_slices = self._connection_slices(
            pre_vertex_slice, post_vertex_slice)
        return self._get_weight_mean(weights, connection_slices)

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(
            self, weights, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        n_connections = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_connections -= post_vertex_slice.n_atoms
        connection_slices = self._connection_slices(
            pre_vertex_slice, post_vertex_slice)
        return self._get_weight_maximum(
            weights, n_connections, connection_slices)

    @overrides(AbstractConnector.get_weight_variance)
    def get_weight_variance(
            self, weights, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # pylint: disable=too-many-arguments
        connection_slices = self._connection_slices(
            pre_vertex_slice, post_vertex_slice)
        return self._get_weight_variance(weights, connection_slices)

    @overrides(AbstractConnector.generate_on_machine)
    def generate_on_machine(self, weights, delays):
        return (
            not self._generate_lists_on_host(weights) and
            not self._generate_lists_on_host(delays))

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, weights, delays, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        # pylint: disable=too-many-arguments
        n_connections = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_connections -= post_vertex_slice.n_atoms
        connection_slices = self._connection_slices(
            pre_vertex_slice, post_vertex_slice)
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            n_atoms = pre_vertex_slice.n_atoms
            block["source"] = numpy.where(numpy.diag(
                numpy.repeat(1, n_atoms)) == 0)[0]
            block["target"] = [block["source"][
                ((n_atoms * i) + (n_atoms - 1)) - j]
                for j in range(n_atoms) for i in range(n_atoms - 1)]
            block["source"] += pre_vertex_slice.lo_atom
            block["target"] += post_vertex_slice.lo_atom
        else:
            block["source"] = numpy.repeat(numpy.arange(
                pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom + 1),
                post_vertex_slice.n_atoms)
            block["target"] = numpy.tile(numpy.arange(
                post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1),
                pre_vertex_slice.n_atoms)
        block["weight"] = self._generate_weights(
            weights, n_connections, connection_slices)
        block["delay"] = self._generate_delays(
            delays, n_connections, connection_slices)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "AllToAllConnector()"

    @property
    def allow_self_connections(self):
        return self._allow_self_connections

    @allow_self_connections.setter
    def allow_self_connections(self, new_value):
        self._allow_self_connections = new_value
