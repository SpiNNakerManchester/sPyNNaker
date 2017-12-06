from .abstract_connector import AbstractConnector
from spynnaker.pyNN.exceptions import SpynnakerException
import numpy
import logging

logger = logging.getLogger(__file__)


class FixedNumberPostConnector(AbstractConnector):
    """ Connects a fixed number of post-synaptic neurons selected at random,
        to all pre-synaptic neurons
    """

    def __init__(
            self, n, allow_self_connections=True, safe=True, verbose=False):
        """
        :param `int` n:
            number of random post-synaptic neurons connected to output
        :param `bool` allow_self_connections:
            if the connector is used to connect a
            Population to itself, this flag determines whether a neuron is
            allowed to connect to itself, or only to other neurons in the
            Population.
        """
        AbstractConnector.__init__(self, safe, verbose)
        self._n_post = n
        self._allow_self_connections = allow_self_connections
        self._verbose = verbose
        self._post_neurons_set = False

    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays, self._n_pre_neurons * self._n_post)

    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # Get lo and hi for the pre vertex
        lo = pre_vertex_slice.lo_atom
        hi = pre_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(post_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == pre_vertex_slice.n_atoms):
            return 0.0
        return self._get_delay_variance(self._delays, None)

    def _get_post_neurons(self):
        # If we haven't set the array up yet, do it now
        if not self._post_neurons_set:
            self._post_neurons = [None] * self._n_pre_neurons
            self._post_neurons_set = True

            # if verbose open a file to output the connectivity
            if self._verbose:
                filename = self._pre_population.label + '_to_' + \
                    self._post_population.label + '_fixednumberpost-conn.csv'
                print 'Output post-connectivity to ', filename
                file_handle = file(filename, 'w')
                numpy.savetxt(file_handle,
                              [(self._n_pre_neurons, self._n_post_neurons,
                                self._n_post)],
                              fmt="%u,%u,%u")

        # Loop over all the pre neurons
        for m in range(0, self._n_pre_neurons):
            if self._post_neurons[m] is None:
                if (not self.with_replacement and
                        self._n_post > self._n_post_neurons):
                    raise SpynnakerException(
                        "FixedNumberPostConnector will not work when "
                        "with_replacement=False and n > n_post_neurons")

                if (not self.with_replacement and
                        not self._allow_self_connections and
                        self._n_post == self._n_post_neurons):
                    raise SpynnakerException(
                        "FixedNumberPostConnector will not work when "
                        "with_replacement=False, allow_self_connections=False "
                        "and n = n_post_neurons")

                # If the pre and post populations are the same
                # then deal with allow_self_connections=False
                if (self._pre_population is self._post_population and
                        not self._allow_self_connections):
                    # Exclude the current pre-neuron from the post-neuron list
                    no_self_post_neurons = []
                    for n in range(0, self._n_post_neurons):
                        if (m != n):
                            no_self_post_neurons.append(n)

                    # Now use this list in the random choice
                    self._post_neurons[m] = numpy.random.choice(
                        no_self_post_neurons, self._n_post,
                        self.with_replacement)
                else:
                    self._post_neurons[m] = numpy.random.choice(
                        self._n_post_neurons, self._n_post,
                        self.with_replacement)

                # Sort the neurons now that we have them
                self._post_neurons[m].sort()

                # If verbose then output the list connected to this pre-neuron
                if self._verbose:
                    numpy.savetxt(file_handle,
                                  self._post_neurons[m][None, :],
                                  fmt=("%u,"*(self._n_post-1)+"%u"))

        return self._post_neurons

    def _post_neurons_in_slice(self, post_vertex_slice, n):
        post_neurons = self._get_post_neurons()

        # Get the nth array and get the bits we need for
        # this post-vertex slice
        this_post_neuron_array = post_neurons[n]

        return this_post_neuron_array[
            (this_post_neuron_array >= post_vertex_slice.lo_atom) &
            (this_post_neuron_array <= post_vertex_slice.hi_atom)]

    def _is_connected(self, post_vertex_slice, n):
        return self._post_neurons_in_slice(post_vertex_slice, n).size > 0

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):

        # Get lo and hi for the pre vertex
        lo = pre_vertex_slice.lo_atom
        hi = pre_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(post_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == pre_vertex_slice.n_atoms):
            return 0

        n_connections = 0
        for n in range(lo, hi + 1):
            n_connections = max(n_connections,
                                len(self._post_neurons_in_slice(
                                    post_vertex_slice, n)))

        if min_delay is None or max_delay is None:
            return n_connections

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._delays, self._n_post * self._n_pre_neurons,
            n_connections, None, min_delay, max_delay)

    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # Get lo and hi for the pre vertex
        lo = pre_vertex_slice.lo_atom
        hi = pre_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(post_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == pre_vertex_slice.n_atoms):
            return 0
        return self._n_post

    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # Get lo and hi for the pre vertex
        lo = pre_vertex_slice.lo_atom
        hi = pre_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(post_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == pre_vertex_slice.n_atoms):
            return 0.0
        return self._get_weight_mean(self._weights, None)

    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # Get lo and hi for the pre vertex
        lo = pre_vertex_slice.lo_atom
        hi = pre_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(post_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == pre_vertex_slice.n_atoms):
            return 0.0

        # Get n_connections by adding length of each set of post neurons
        n_connections = 0
        for n in range(lo, hi + 1):
            n_connections += len(self._post_neurons_in_slice(
                post_vertex_slice, n))

        return self._get_weight_maximum(
            self._weights, n_connections, None)

    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # Get lo and hi for the pre vertex
        lo = pre_vertex_slice.lo_atom
        hi = pre_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(post_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == pre_vertex_slice.n_atoms):
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
        # Get lo and hi for the pre vertex
        lo = pre_vertex_slice.lo_atom
        hi = pre_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(post_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == pre_vertex_slice.n_atoms):
            return numpy.zeros(0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        # Get number of connections
        n_connections = 0
        for n in range(lo, hi + 1):
            n_connections += len(
                self._post_neurons_in_slice(post_vertex_slice, n))

        # Set up the block
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        # Set up source and target
        pre_neurons_in_slice = []
        post_neurons_in_slice = []
        pre_vertex_array = numpy.arange(lo, hi + 1)
        for n in range(lo, hi + 1):  # 0, self._n_pre_neurons):
            post_neurons = self._post_neurons_in_slice(
                post_vertex_slice, n)
            for m in range(0, len(post_neurons)):
                post_neurons_in_slice.append(post_neurons[m])
                pre_neurons_in_slice.append(pre_vertex_array[n-lo])

        block["source"] = pre_neurons_in_slice
        block["target"] = post_neurons_in_slice

        block["weight"] = self._generate_weights(
            self._weights, n_connections, None)
        block["delay"] = self._generate_delays(
            self._delays, n_connections, None)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "FixedNumberPostConnector({})".format(self._n_post)

    @property
    def allow_self_connections(self):
        return self._allow_self_connections

    @allow_self_connections.setter
    def allow_self_connections(self, new_value):
        self._allow_self_connections = new_value
