# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import math
import numpy
from spinn_utilities.overrides import overrides
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.exceptions import SpynnakerException

logger = logging.getLogger(__file__)


class FixedNumberPreConnector(AbstractGenerateConnectorOnMachine):
    """ Connects a fixed number of pre-synaptic neurons selected at random,\
        to all post-synaptic neurons.
    """

    __slots__ = [
        "__allow_self_connections",
        "__n_pre",
        "__pre_neurons",
        "__pre_neurons_set",
        "__with_replacement",
        "__pre_connector_seed"]

    def __init__(
            self, n, allow_self_connections=True, with_replacement=False,
            safe=True, verbose=False, rng=None):
        """
        :param n: \
            number of random pre-synaptic neurons connected to output
        :type n: int
        :param allow_self_connections: \
            if the connector is used to connect a\
            Population to itself, this flag determines whether a neuron is\
            allowed to connect to itself, or only to other neurons in the\
            Population.
        :type allow_self_connections: bool
        :param with_replacement:
            this flag determines how the random selection of pre-synaptic\
            neurons is performed; if true, then every pre-synaptic neuron\
            can be chosen on each occasion, and so multiple connections\
            between neuron pairs are possible; if false, then once a\
            pre-synaptic neuron has been connected to a post-neuron, it\
            can't be connected again.
        :type with_replacement: bool
        """
        # :param space:
        # a Space object, needed if you wish to specify distance-dependent\
        # weights or delays - not implemented
        # :type space: pyNN.Space
        super(FixedNumberPreConnector, self).__init__(safe, verbose)
        self.__n_pre = n
        self.__allow_self_connections = allow_self_connections
        self.__with_replacement = with_replacement
        self.__pre_neurons_set = False
        self.__pre_neurons = None
        self.__pre_connector_seed = dict()

    def set_projection_information(
            self, pre_population, post_population, rng, machine_time_step):
        AbstractConnector.set_projection_information(
            self, pre_population, post_population, rng, machine_time_step)
        if (not self.__with_replacement and
                self.__n_pre > self._n_pre_neurons):
            raise SpynnakerException(
                "FixedNumberPreConnector will not work when "
                "with_replacement=False and n > n_pre_neurons")

        if (not self.__with_replacement and
                not self.__allow_self_connections and
                self.__n_pre == self._n_pre_neurons):
            raise SpynnakerException(
                "FixedNumberPreConnector will not work when "
                "with_replacement=False, allow_self_connections=False "
                "and n = n_pre_neurons")

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, delays):
        return self._get_delay_maximum(
            delays, self.__n_pre * self._n_post_neurons)

    def _get_pre_neurons(self):
        # If we haven't set the array up yet, do it now
        if not self.__pre_neurons_set:
            self.__pre_neurons = [None] * self._n_post_neurons
            self.__pre_neurons_set = True

            # if verbose open a file to output the connectivity
            if self.verbose:
                filename = self.pre_population.label + '_to_' + \
                    self.post_population.label + '_fixednumberpre-conn.csv'
                with open(filename, 'w') as file_handle:
                    numpy.savetxt(file_handle,
                                  [(self._n_pre_neurons, self._n_post_neurons,
                                    self.__n_pre)],
                                  fmt="%u,%u,%u")

            # Loop over all the post neurons
            for m in range(0, self._n_post_neurons):

                # If the pre and post populations are the same
                # then deal with allow_self_connections=False
                if (self.pre_population is self.post_population and
                        not self.__allow_self_connections):
                    # Exclude the current pre-neuron from the post-neuron
                    # list
                    no_self_pre_neurons = [
                        n for n in range(self._n_pre_neurons) if n != m]

                    # Now use this list in the random choice
                    self.__pre_neurons[m] = self._rng.choice(
                        no_self_pre_neurons, self.__n_pre,
                        self.__with_replacement)
                else:
                    self.__pre_neurons[m] = self._rng.choice(
                        self._n_pre_neurons, self.__n_pre,
                        self.__with_replacement)

                # Sort the neurons now that we have them
                self.__pre_neurons[m].sort()

                # If verbose then output the list connected to this
                # post-neuron
                if self.verbose:
                    numpy.savetxt(
                        file_handle,
                        self.__pre_neurons[m][None, :],
                        fmt=("%u," * (self.__n_pre - 1) + "%u"))

        return self.__pre_neurons

    def _pre_neurons_in_slice(self, pre_vertex_slice, n):
        pre_neurons = self._get_pre_neurons()

        # Take the nth array and get the bits from it we need
        # for this pre-vertex slice
        this_pre_neuron_array = pre_neurons[n]
        return this_pre_neuron_array[
            (this_pre_neuron_array >= pre_vertex_slice.lo_atom) &
            (this_pre_neuron_array <= pre_vertex_slice.hi_atom)]

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, delays, post_vertex_slice, min_delay=None, max_delay=None):
        # pylint: disable=too-many-arguments
        prob_selection = 1.0 / float(self._n_pre_neurons)
        n_connections_total = utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_post_neurons,
            self.__n_pre * self._n_post_neurons, prob_selection,
            chance=1.0/10000.0)
        prob_in_slice = (
            float(post_vertex_slice.n_atoms) / float(self._n_post_neurons))
        n_connections = utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_post_neurons,
            n_connections_total, prob_in_slice)

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            delays, self._n_pre_neurons * self._n_post_neurons,
            n_connections, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        # pylint: disable=too-many-arguments
        return self.__n_pre

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, weights):
        # pylint: disable=too-many-arguments
        return self._get_weight_maximum(
            weights, self.__n_pre * self._n_post_neurons)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, weights, delays, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        # pylint: disable=too-many-arguments

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
            weights, n_connections, None, pre_vertex_slice, post_vertex_slice)
        block["delay"] = self._generate_delays(
            delays, n_connections, None, pre_vertex_slice, post_vertex_slice)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "FixedNumberPreConnector({})".format(self.__n_pre)

    @property
    def allow_self_connections(self):
        return self.__allow_self_connections

    @allow_self_connections.setter
    def allow_self_connections(self, new_value):
        self.__allow_self_connections = new_value

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self):
        return ConnectorIDs.FIXED_NUMBER_PRE_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params)
    def gen_connector_params(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        # The same seed needs to be sent to each of the slices
        key = (id(pre_slices), id(post_slices))
        if key not in self.__pre_connector_seed:
            self.__pre_connector_seed[key] = [
                int(i * 0xFFFFFFFF) for i in self._rng.next(n=4)]

        # Only deal with self-connections if the two populations are the same
        self_connections = True
        if ((not self.__allow_self_connections) and (
                self.pre_population is self.post_population)):
            self_connections = False

        params = [
            self_connections,
            self.__with_replacement,
            self.__n_pre,
            self._n_pre_neurons]
        params.extend(self.__pre_connector_seed[key])
        return numpy.array(params, dtype="uint32")

    @property
    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        return 16 + 16
