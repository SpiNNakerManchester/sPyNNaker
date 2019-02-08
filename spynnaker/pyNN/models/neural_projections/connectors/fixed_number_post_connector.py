from __future__ import print_function
from spinn_utilities.overrides import overrides
from .abstract_connector import AbstractConnector
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.exceptions import SpynnakerException
import numpy
import logging
import math

logger = logging.getLogger(__file__)


class FixedNumberPostConnector(AbstractConnector):
    """ Connects a fixed number of post-synaptic neurons selected at random,\
        to all pre-synaptic neurons.
    """

    __slots__ = [
        "_allow_self_connections",
        "_n_post",
        "_post_neurons",
        "_post_neurons_set",
        "_with_replacement"]

    def __init__(
            self, n, allow_self_connections=True, with_replacement=False,
            safe=True, verbose=False):
        """
        :param n: \
            number of random post-synaptic neurons connected to pre-neurons.
        :type n: int
        :param allow_self_connections: \
            if the connector is used to connect a Population to itself, this\
            flag determines whether a neuron is allowed to connect to itself,\
            or only to other neurons in the Population.
        :type allow_self_connections: bool
        :param with_replacement: \
            this flag determines how the random selection of post-synaptic\
            neurons is performed; if true, then every post-synaptic neuron\
            can be chosen on each occasion, and so multiple connections\
            between neuron pairs are possible; if false, then once a\
            post-synaptic neuron has been connected to a pre-neuron, it can't\
            be connected again.
        :type with_replacement: bool
        """
        super(FixedNumberPostConnector, self).__init__(safe, verbose)
        self._n_post = n
        self._allow_self_connections = allow_self_connections
        self._with_replacement = with_replacement
        self._verbose = verbose
        self._post_neurons_set = False

    def set_projection_information(
            self, pre_population, post_population, rng, machine_time_step):
        AbstractConnector.set_projection_information(
            self, pre_population, post_population, rng, machine_time_step)
        if (not self._with_replacement and
                self._n_post > self._n_post_neurons):
            raise SpynnakerException(
                "FixedNumberPostConnector will not work when "
                "with_replacement=False and n > n_post_neurons")
        if (not self._with_replacement and
                not self._allow_self_connections and
                self._n_post == self._n_post_neurons):
            raise SpynnakerException(
                "FixedNumberPostConnector will not work when "
                "with_replacement=False, allow_self_connections=False "
                "and n = n_post_neurons")

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self):
        n_connections = self._n_pre_neurons * self._n_post
        return self._get_delay_maximum(n_connections)

    def _get_post_neurons(self):
        # If we haven't set the array up yet, do it now
        if not self._post_neurons_set:
            self._post_neurons = [None] * self._n_pre_neurons
            self._post_neurons_set = True

            # if verbose open a file to output the connectivity
            if self._verbose:
                filename = self._pre_population.label + '_to_' + \
                    self._post_population.label + '_fixednumberpost-conn.csv'
                print('Output post-connectivity to ', filename)
                with open(filename, 'w') as file_handle:
                    numpy.savetxt(file_handle,
                                  [(self._n_pre_neurons, self._n_post_neurons,
                                    self._n_post)],
                                  fmt="%u,%u,%u")

            # Loop over all the pre neurons
            for m in range(0, self._n_pre_neurons):
                if self._post_neurons[m] is None:

                    # If the pre and post populations are the same
                    # then deal with allow_self_connections=False
                    if (self._pre_population is self._post_population and
                            not self._allow_self_connections):

                        # Create a list without the pre_neuron in it
                        no_self_post_neurons = numpy.concatenate(
                            [numpy.arange(0, m),
                             numpy.arange(m + 1, self._n_post_neurons)])

                        # Now use this list in the random choice
                        self._post_neurons[m] = numpy.random.choice(
                            no_self_post_neurons, self._n_post,
                            self._with_replacement)
                    else:
                        self._post_neurons[m] = numpy.random.choice(
                            self._n_post_neurons, self._n_post,
                            self._with_replacement)

                    # If verbose then output the list connected to this
                    # pre-neuron
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

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, min_delay=None, max_delay=None):
        # pylint: disable=too-many-arguments
        prob_in_slice = (
            post_vertex_slice.n_atoms / float(self._n_post_neurons))
        n_connections = utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_pre_neurons,
            self._n_post, prob_in_slice)

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._n_post_neurons * self._n_pre_neurons, n_connections,
            min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        # pylint: disable=too-many-arguments
        selection_prob = 1.0 / float(self._n_post_neurons)
        n_connections = utility_calls.get_probable_maximum_selected(
            self._n_post_neurons * self._n_pre_neurons,
            self._n_post * self._n_pre_neurons, selection_prob,
            chance=1.0/10000.0)
        return int(math.ceil(n_connections))

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self):
        n_connections = self._n_pre_neurons * self._n_post
        return self._get_weight_maximum(n_connections)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        # pylint: disable=too-many-arguments
        # Get lo and hi for the pre vertex
        lo = pre_vertex_slice.lo_atom
        hi = pre_vertex_slice.hi_atom

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
        for n in range(lo, hi + 1):
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
