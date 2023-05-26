# Copyright (c) 2014 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import math
import numpy
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.exceptions import SpynnakerException
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)


class FixedNumberPreConnector(AbstractGenerateConnectorOnMachine,
                              AbstractGenerateConnectorOnHost):
    """
    Connects a fixed number of pre-synaptic neurons selected at random,
    to all post-synaptic neurons.
    """

    __slots__ = (
        "__allow_self_connections",
        "__n_pre",
        "__pre_neurons",
        "__pre_neurons_set",
        "__with_replacement")

    def __init__(
            self, n, allow_self_connections=True, safe=True, verbose=False,
            with_replacement=False, rng=None, callback=None):
        """
        :param int n:
            number of random pre-synaptic neurons connected to output
        :param bool allow_self_connections:
            if the connector is used to connect a Population to itself,
            this flag determines whether a neuron is allowed to connect to
            itself, or only to other neurons in the Population.
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param bool with_replacement:
            this flag determines how the random selection of pre-synaptic
            neurons is performed; if true, then every pre-synaptic neuron
            can be chosen on each occasion, and so multiple connections
            between neuron pairs are possible; if false, then once a
            pre-synaptic neuron has been connected to a post-neuron, it
            can't be connected again.
        :param rng:
            Seeded random number generator, or `None` to make one when needed
        :type rng: ~pyNN.random.NumpyRNG or None
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        """
        # :param ~pyNN.space.Space space:
        # a Space object, needed if you wish to specify distance-dependent
        # weights or delays - not implemented
        super().__init__(safe, callback, verbose)
        # We absolutely require an integer at this point!
        self.__n_pre = self._roundsize(n, "FixedNumberPreConnector")
        self.__allow_self_connections = allow_self_connections
        self.__with_replacement = with_replacement
        self.__pre_neurons_set = False
        self.__pre_neurons = None
        self._rng = rng

    def set_projection_information(self, synapse_info):
        super().set_projection_information(synapse_info)
        if (not self.__with_replacement and
                self.__n_pre > synapse_info.n_pre_neurons):
            raise SpynnakerException(
                "FixedNumberPreConnector will not work when "
                "with_replacement=False and n > n_pre_neurons")

        if (not self.__with_replacement and
                not self.__allow_self_connections and
                self.__n_pre == synapse_info.n_pre_neurons):
            raise SpynnakerException(
                "FixedNumberPreConnector will not work when "
                "with_replacement=False, allow_self_connections=False "
                "and n = n_pre_neurons")

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        return self._get_delay_maximum(
            synapse_info.delays, self.__n_pre * synapse_info.n_post_neurons,
            synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info):
        return self._get_delay_minimum(
            synapse_info.delays, self.__n_pre * synapse_info.n_post_neurons,
            synapse_info)

    def _get_pre_neurons(self, synapse_info):
        """
        :param SynapseInformation synapse_info:
        :rtype: list(~numpy.ndarray)
        """
        # If we haven't set the array up yet, do it now
        if not self.__pre_neurons_set:
            self.__pre_neurons = [None] * synapse_info.n_post_neurons
            self.__pre_neurons_set = True

            # if verbose open a file to output the connectivity
            if self.verbose:
                filename = "{}_to_{}_fixednumberpre-conn.csv".format(
                    synapse_info.pre_population.label,
                    synapse_info.post_population.label)
                with open(filename, 'w', encoding="utf-8") as file_handle:
                    numpy.savetxt(file_handle,
                                  [(synapse_info.n_pre_neurons,
                                    synapse_info.n_post_neurons,
                                    self.__n_pre)],
                                  fmt="%u,%u,%u")

            # Loop over all the post neurons
            for m in range(0, synapse_info.n_post_neurons):
                # If the pre and post populations are the same
                # then deal with allow_self_connections=False
                if (synapse_info.pre_population is synapse_info.post_population
                        and not self.__allow_self_connections):
                    # Exclude the current pre-neuron from the post-neuron
                    # list
                    no_self_pre_neurons = [
                        n for n in range(synapse_info.n_pre_neurons) if n != m]

                    # Now use this list in the random choice
                    self.__pre_neurons[m] = self._rng.choice(
                        no_self_pre_neurons, self.__n_pre,
                        self.__with_replacement)
                else:
                    self.__pre_neurons[m] = self._rng.choice(
                        synapse_info.n_pre_neurons, self.__n_pre,
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

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms, synapse_info, min_delay=None,
            max_delay=None):
        prob_selection = 1.0 / float(synapse_info.n_pre_neurons)
        n_connections_total = utility_calls.get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            self.__n_pre * synapse_info.n_post_neurons, prob_selection,
            chance=1.0/10000.0)
        prob_in_slice = min(
            float(n_post_atoms) / float(synapse_info.n_post_neurons), 1.0)
        n_connections = utility_calls.get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            n_connections_total, prob_in_slice, chance=1.0/100000.0)

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            n_connections, min_delay, max_delay, synapse_info)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        return self.__n_pre

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        return self._get_weight_maximum(
           synapse_info.weights, self.__n_pre * synapse_info.n_post_neurons,
           synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices, post_vertex_slice, synapse_type, synapse_info):
        # Get lo and hi for the post vertex
        lo = post_vertex_slice.lo_atom
        hi = post_vertex_slice.hi_atom

        pre_neurons = self._get_pre_neurons(synapse_info)

        # Get number of connections
        n_connections = self.__n_pre * post_vertex_slice.n_atoms

        # Set up the block
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        # Set up source and target
        pre_neurons_in_slice = []
        post_neurons_in_slice = []
        post_vertex_array = numpy.arange(lo, hi + 1)
        for n in range(lo, hi + 1):
            for pn in pre_neurons[n]:
                pre_neurons_in_slice.append(pn)
                post_neurons_in_slice.append(post_vertex_array[n - lo])

        block["source"] = pre_neurons_in_slice
        block["target"] = post_neurons_in_slice

        block["weight"] = self._generate_weights(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["delay"] = self._generate_delays(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return f"FixedNumberPreConnector({self.__n_pre})"

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

    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_params)
    def gen_connector_params(self):
        return numpy.array([
            int(self.__allow_self_connections),
            int(self.__with_replacement),
            self.__n_pre], dtype="uint32")

    @property
    @overrides(
        AbstractGenerateConnectorOnMachine.gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        return 3 * BYTES_PER_WORD
