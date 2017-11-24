from .abstract_connector import AbstractConnector
import numpy
import logging

logger = logging.getLogger(__file__)


class FixedNumberPreConnector(AbstractConnector):
    """ Connects a fixed number of pre-synaptic neurons selected at random,
        to all post-synaptic neurons
    """
    def __init__(
            self, n, allow_self_connections=True, safe=True, verbose=False):
        """

        :param `int` n:
            number of random pre-synaptic neurons connected to output
        :param `bool` allow_self_connections:
            if the connector is used to connect a
            Population to itself, this flag determines whether a neuron is
            allowed to connect to itself, or only to other neurons in the
            Population.
        :param `pyNN.Space` space:
            a Space object, needed if you wish to specify distance-
            dependent weights or delays - not implemented
        """
        AbstractConnector.__init__(self, safe, verbose)
        self._n_pre = n
        self._allow_self_connections = allow_self_connections
        self._pre_neurons_set = False

    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays, self._n_pre * self._n_post_neurons)

    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(pre_vertex_slice, 0):
            return 0.0
        return self._get_delay_variance(self._delays, None)

    def _get_pre_neurons(self):
        # if we haven't set the array up yet, do it now
        if not self._pre_neurons_set:
            self._pre_neurons = [None] * self._n_post_neurons
            self._pre_neurons_set = True

        # loop over all the post neurons
        for n in range(0, self._n_post_neurons):
            if self._pre_neurons[n] is None:
                self._pre_neurons[n] = numpy.random.choice(
                    self._n_pre_neurons, self._n_pre, False)
                self._pre_neurons[n].sort()
        return self._pre_neurons

    def _pre_neurons_in_slice(self, pre_vertex_slice, n):
        pre_neurons = self._get_pre_neurons()

        # Take the nth array and get the bits from it we need
        # for this pre-vertex slice
        this_pre_neuron_array = pre_neurons[n]

        return this_pre_neuron_array[
            (this_pre_neuron_array >= pre_vertex_slice.lo_atom) &
            (this_pre_neuron_array <= pre_vertex_slice.hi_atom)]

    def _is_connected(self, pre_vertex_slice, n):
        return self._pre_neurons_in_slice(pre_vertex_slice, n).size > 0

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):

        if not self._is_connected(pre_vertex_slice, 0):
            return 0

        if min_delay is None or max_delay is None:
            return post_vertex_slice.n_atoms

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._delays, self._n_pre * self._n_post_neurons,
            post_vertex_slice.n_atoms, None, min_delay, max_delay)

    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(pre_vertex_slice, 0):
            return 0
        return self._n_pre

    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(pre_vertex_slice, 0):
            return 0.0
        return self._get_weight_mean(self._weights, None)

    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(pre_vertex_slice, 0):
            return 0.0

        # Get n_connections by adding length of each set of pre_neurons
        n_connections = 0
        lo = post_vertex_slice.lo_atom
        hi = post_vertex_slice.hi_atom
        for n in range(0, self._n_post_neurons):
            if (n >= lo and n <= hi):
                n_connections += len(self._pre_neurons_in_slice(
                    pre_vertex_slice, n))

        return self._get_weight_maximum(
            self._weights, n_connections, None)

    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        if not self._is_connected(pre_vertex_slice, 0):
            return 0.0
        return self._get_weight_variance(self._weights, None)

    def generate_on_machine(self):
        return (
            not self._generate_lists_on_host(self._weights) and
            not self._generate_lists_on_host(self._delays))

    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        if not self._is_connected(pre_vertex_slice, 0):
            return numpy.zeros(0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        # Get number of connections
        n_connections = 0
        lo = post_vertex_slice.lo_atom
        hi = post_vertex_slice.hi_atom
        for n in range(0, self._n_post_neurons):
            if (n >= lo and n <= hi):
                n_connections += len(self._pre_neurons_in_slice(
                    pre_vertex_slice, n))

        # If self connections are not allowed then subtract those connections
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            for n in range(0, self._n_post_neurons):
                if (n >= lo and n <= hi):
                    pre_neurons = self._pre_neurons_in_slice(
                        pre_vertex_slice, n)
                    for m in range(0, len(pre_neurons)):
                        if (n == pre_neurons[m]):
                            n_connections -= 1

        # Set up the block
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        # If self connections not allowed set up source and target accordingly
        if (not self._allow_self_connections and
                pre_vertex_slice is post_vertex_slice):
            pre_neurons_in_slice = []
            post_neurons_in_slice = []
            post_vertex_array = numpy.arange(
                post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1)
            for n in range(0, self._n_post_neurons):
                if (n >= lo and n <= hi):
                    pre_neurons = self._pre_neurons_in_slice(
                        pre_vertex_slice, n)
                    for m in range(0, len(pre_neurons)):
                        if (n != pre_neurons[m]):
                            pre_neurons_in_slice.append(pre_neurons[m])
                            post_neurons_in_slice.append(
                                post_vertex_array[n-post_vertex_slice.lo_atom])

            block["source"] = pre_neurons_in_slice
            block["target"] = post_neurons_in_slice
        else:
            # self connections are allowed, loop over everything and add
            # to source and target
            pre_neurons_in_slice = []
            post_neurons_in_slice = []
            post_vertex_array = numpy.arange(
                post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1)
            for n in range(0, self._n_post_neurons):
                if (n >= lo and n <= hi):
                    pre_neurons = self._pre_neurons_in_slice(
                        pre_vertex_slice, n)
                    for m in range(0, len(pre_neurons)):
                        pre_neurons_in_slice.append(pre_neurons[m])
                        post_neurons_in_slice.append(
                            post_vertex_array[n-post_vertex_slice.lo_atom])

            block["source"] = pre_neurons_in_slice
            block["target"] = post_neurons_in_slice

        block["weight"] = self._generate_weights(
            self._weights, n_connections, None)
        block["delay"] = self._generate_delays(
            self._delays, n_connections, None)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "FixedNumberPreConnector({})".format(self._n_pre)
