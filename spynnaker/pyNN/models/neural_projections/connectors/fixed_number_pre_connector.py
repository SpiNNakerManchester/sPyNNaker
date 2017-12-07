from .abstract_connector import AbstractConnector
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.exceptions import SpynnakerException
import numpy
import logging

logger = logging.getLogger(__file__)


class FixedNumberPreConnector(AbstractConnector):
    """ Connects a fixed number of pre-synaptic neurons selected at random,
        to all post-synaptic neurons
    """

    def __init__(
            self, n, allow_self_connections=True, with_replacement=False,
            safe=True, verbose=False):
        """
        :param `int` n:
            number of random pre-synaptic neurons connected to output
        :param `bool` allow_self_connections:
            if the connector is used to connect a
            Population to itself, this flag determines whether a neuron is
            allowed to connect to itself, or only to other neurons in the
            Population.
        :param `bool` with_replacement:
            this flag determines how the random selection of pre-synaptic
            neurons is performed; if true, then every pre-synaptic neuron
            can be chosen on each occasion, and so multiple connections
            between neuron pairs are possible; if false, then once a pre-
            synaptic neuron has been connected to a post-neuron, it can't be
            connected again
        """
        AbstractConnector.__init__(self, safe, verbose)
        self._n_pre = n
        self._allow_self_connections = allow_self_connections
        self._with_replacement = with_replacement
        self._verbose = verbose
        self._pre_neurons_set = False
        self._p_connect = 1.0  # for setting maxima later

    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays, self._n_pre * self._n_post_neurons)

    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # Get lo and hi for the post vertex
        lo = post_vertex_slice.lo_atom
        hi = post_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(pre_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == post_vertex_slice.n_atoms):
            return 0.0
        return self._get_delay_variance(self._delays, None)

    def _get_pre_neurons(self):
        # If we haven't set the array up yet, do it now
        if not self._pre_neurons_set:
            self._pre_neurons = [None] * self._n_post_neurons
            self._pre_neurons_set = True

            # if verbose open a file to output the connectivity
            if self._verbose:
                filename = self._pre_population.label + '_to_' + \
                    self._post_population.label + '_fixednumberpre-conn.csv'
                file_handle = file(filename, 'w')
                numpy.savetxt(file_handle,
                              [(self._n_pre_neurons, self._n_post_neurons,
                                self._n_pre)],
                              fmt="%u,%u,%u")

        # Loop over all the post neurons
        for m in range(0, self._n_post_neurons):
            if self._pre_neurons[m] is None:
                if (not self._with_replacement and
                        self._n_pre > self._n_pre_neurons):
                    # Throw an exception
                    raise SpynnakerException(
                        "FixedNumberPreConnector will not work when "
                        "with_replacement=False and n > n_pre_neurons")

                if (not self._with_replacement and
                        not self._allow_self_connections and
                        self._n_pre == self._n_pre_neurons):
                    raise SpynnakerException(
                        "FixedNumberPreConnector will not work when "
                        "with_replacement=False, allow_self_connections=False "
                        "and n = n_pre_neurons")

                # If the pre and post populations are the same
                # then deal with allow_self_connections=False
                if (self._pre_population is self._post_population and
                        not self._allow_self_connections):
                    # Exclude the current pre-neuron from the post-neuron list
                    no_self_pre_neurons = []
                    for n in range(0, self._n_pre_neurons):
                        if (m != n):
                            no_self_pre_neurons.append(n)

                    # Now use this list in the random choice
                    self._pre_neurons[m] = numpy.random.choice(
                        no_self_pre_neurons, self._n_pre,
                        self._with_replacement)
                else:
                    self._pre_neurons[m] = numpy.random.choice(
                        self._n_pre_neurons, self._n_pre,
                        self._with_replacement)

                # Sort the neurons now that we have them
                self._pre_neurons[m].sort()

                # If verbose then output the list connected to this post-neuron
                if self._verbose:
                    numpy.savetxt(file_handle,
                                  self._pre_neurons[m][None, :],
                                  fmt=("%u,"*(self._n_pre-1)+"%u"))

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

    def _get_n_connections(self, out_of):
        return utility_calls.get_probable_maximum_selected(
            self._n_pre * self._n_post_neurons, out_of,
            self._p_connect)

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):

        # Get lo and hi for the post vertex
        lo = post_vertex_slice.lo_atom
        hi = post_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(pre_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == post_vertex_slice.n_atoms):
            return 0

        # Get the probable max number of connections
        n_connections = self._get_n_connections(self._n_pre_neurons)

        if min_delay is None or max_delay is None:
            return n_connections

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._delays, self._n_pre * self._n_post_neurons,
            n_connections, None, min_delay, max_delay)

    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # Get lo and hi for the post vertex
        lo = post_vertex_slice.lo_atom
        hi = post_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(pre_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == post_vertex_slice.n_atoms):
            return 0

        return self._get_n_connections(self._n_pre)

    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # Get lo and hi for the post vertex
        lo = post_vertex_slice.lo_atom
        hi = post_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(pre_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == post_vertex_slice.n_atoms):
            return 0.0
        return self._get_weight_mean(self._weights, None)

    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        # Get lo and hi for the post vertex
        lo = post_vertex_slice.lo_atom
        hi = post_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(pre_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == post_vertex_slice.n_atoms):
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
        # Get lo and hi for the post vertex
        lo = post_vertex_slice.lo_atom
        hi = post_vertex_slice.hi_atom

        # Only return zero here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(pre_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == post_vertex_slice.n_atoms):
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
        # Get lo and hi for the post vertex
        lo = post_vertex_slice.lo_atom
        hi = post_vertex_slice.hi_atom

        # Only return zero array here if *every* neuron is not connected
        n_not_connected = 0
        for n in range(lo, hi + 1):
            if not self._is_connected(pre_vertex_slice, n):
                n_not_connected += 1

        if (n_not_connected == post_vertex_slice.n_atoms):
            return numpy.zeros(0, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        # Get lo and hi for the post vertex
        lo = post_vertex_slice.lo_atom
        hi = post_vertex_slice.hi_atom

        # Get number of connections
        n_connections = 0
        for n in range(lo, hi + 1):
            n_connections += len(self._pre_neurons_in_slice(
                pre_vertex_slice, n))

        # Set up the block
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        # Set up source and target
        pre_neurons_in_slice = []
        post_neurons_in_slice = []
        post_vertex_array = numpy.arange(lo, hi + 1)
        for n in range(lo, hi + 1):
            pre_neurons = self._pre_neurons_in_slice(
                pre_vertex_slice, n)
            for m in range(0, len(pre_neurons)):
                pre_neurons_in_slice.append(pre_neurons[m])
                post_neurons_in_slice.append(post_vertex_array[n-lo])

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

    @property
    def allow_self_connections(self):
        return self._allow_self_connections

    @allow_self_connections.setter
    def allow_self_connections(self, new_value):
        self._allow_self_connections = new_value
