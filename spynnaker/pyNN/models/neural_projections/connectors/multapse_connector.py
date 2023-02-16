# Copyright (c) 2014 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
import numpy.random
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.exceptions import SpynnakerException
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)


class MultapseConnector(AbstractGenerateConnectorOnMachine,
                        AbstractGenerateConnectorOnHost):
    """ Create a multapse connector. The size of the source and destination\
        populations are obtained when the projection is connected. The number\
        of synapses is specified. when instantiated, the required number of\
        synapses is created by selecting at random from the source and target\
        populations with replacement. Uniform selection probability is assumed.
    """
    __slots__ = [
        "__allow_self_connections",
        "__num_synapses",
        "__post_slices",
        "__synapses_per_edge",
        "__with_replacement"]

    def __init__(self, n, allow_self_connections=True,
                 with_replacement=True, safe=True,
                 verbose=False, rng=None, callback=None):
        """
        :param int n:
            This is the total number of synapses in the connection.
        :param bool allow_self_connections:
            Allow a neuron to connect to itself or not.
        :param bool with_replacement:
            When selecting, allow a neuron to be re-selected or not.
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param rng:
            Seeded random number generator, or ``None`` to make one when
            needed.
        :type rng: ~pyNN.random.NumpyRNG or None
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        """
        super().__init__(safe, callback, verbose)
        # We absolutely require an integer at this point!
        self.__num_synapses = self._roundsize(n, "MultapseConnector")
        self.__allow_self_connections = allow_self_connections
        self.__with_replacement = with_replacement
        self.__post_slices = None
        self.__synapses_per_edge = None
        self._rng = rng

    def set_projection_information(self, synapse_info):
        super().set_projection_information(synapse_info)
        n_pairs = synapse_info.n_post_neurons * synapse_info.n_pre_neurons
        if not self.__with_replacement and self.__num_synapses > n_pairs:
            raise SpynnakerException(
                "FixedTotalNumberConnector will not work when "
                "with_replacement=False and n > n_pre * n_post")
        if (not self.__with_replacement and
                not self.__allow_self_connections and
                self.__num_synapses == n_pairs):
            raise SpynnakerException(
                "FixedNumberPostConnector will not work when "
                "with_replacement=False, allow_self_connections=False "
                "and n = n_pre * n_post")

    def get_rng_next(self, num_synapses, prob_connect):
        """ Get the required RNGs

        :param int num_synapses:
            The number of synapses to make random numbers for in this call
        :param list(float) prob_connect: The probability of connection
        :rtype: ~numpy.ndarray
        """
        # Below is how numpy does multinomial internally...
        size = len(prob_connect)
        multinomial = numpy.zeros(size, int)
        total = 1.0
        dn = num_synapses
        for j in range(0, size - 1):
            multinomial[j] = self._rng.next(
                1, distribution="binomial",
                parameters={'n': dn, 'p': prob_connect[j] / total})
            dn = dn - multinomial[j]
            if dn <= 0:
                break
            total = total - prob_connect[j]
        if dn > 0:
            multinomial[size - 1] = dn

        return multinomial

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        return self._get_delay_maximum(
            synapse_info.delays, self.__num_synapses, synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info):
        return self._get_delay_minimum(
            synapse_info.delays, self.__num_synapses, synapse_info)

    def _update_synapses_per_post_vertex(self, post_slices, n_pre_atoms):
        """
        :param list(~pacman.model.graphs.common.Slice) post_slices:
        """
        if (self.__synapses_per_edge is None or
                len(self.__post_slices) != len(post_slices)):
            n_post_atoms = sum(post.n_atoms for post in post_slices if post)
            n_connections = n_pre_atoms * n_post_atoms
            if (not self.__with_replacement and
                    n_connections < self.__num_synapses):
                raise SpynnakerException(
                    "FixedNumberTotalConnector will not work correctly when "
                    "with_replacement=False & num_synapses > n_pre * n_post")
            prob_connect = [
                n_pre_atoms * post.n_atoms / float(n_connections)
                if n_pre_atoms and post.n_atoms else 0 for post in post_slices]
            # Use the multinomial directly if possible
            if (hasattr(self._rng, "rng") and
                    hasattr(self._rng.rng, "multinomial")):
                self.__synapses_per_edge = self._rng.rng.multinomial(
                    self.__num_synapses, prob_connect)
            else:
                self.__synapses_per_edge = self.get_rng_next(
                    self.__num_synapses, prob_connect)
            if sum(self.__synapses_per_edge) != self.__num_synapses:
                raise SpynnakerException("{} of {} synapses generated".format(
                    sum(self.__synapses_per_edge), self.__num_synapses))
            self.__post_slices = post_slices

    def _get_n_connections(self, post_slice_index):
        """
        :param int post_slice_index:
        :rtype: int
        """
        return self.__synapses_per_edge[post_slice_index]

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms, synapse_info, min_delay=None,
            max_delay=None):

        # If the chance of there being a connection in the slice is almost 0,
        # there will probably be at least 1 connection somewhere
        prob_in_slice = min(
            n_post_atoms / float(synapse_info.n_post_neurons),
            1.0)
        max_in_slice = max(utility_calls.get_probable_maximum_selected(
            self.__num_synapses, self.__num_synapses, prob_in_slice), 1.0)

        # Similarly if the chance of there being one in a row is 0, there will
        # probably be 1
        prob_in_row = 1.0 / synapse_info.n_pre_neurons
        n_connections = max(utility_calls.get_probable_maximum_selected(
            self.__num_synapses, max_in_slice, prob_in_row), 1.0)

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            n_connections, min_delay, max_delay, synapse_info)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        prob_of_choosing_post_atom = 1.0 / synapse_info.n_post_neurons
        return utility_calls.get_probable_maximum_selected(
            self.__num_synapses, self.__num_synapses,
            prob_of_choosing_post_atom)

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        return self._get_weight_maximum(
            synapse_info.weights, self.__num_synapses, synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices, post_vertex_slice, synapse_type, synapse_info):
        # pylint: disable=too-many-arguments
        # update the synapses as required, and get the number of connections

        post_slice_index = post_slices.index(post_vertex_slice)
        self._update_synapses_per_post_vertex(
            post_slices, synapse_info.n_pre_neurons)
        n_connections = self._get_n_connections(post_slice_index)
        if n_connections == 0:
            return numpy.zeros(0, dtype=self.NUMPY_SYNAPSES_DTYPE)

        # set up array for synaptic block
        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)

        # Create pairs between the pre- and post-vertex slices
        pairs = numpy.mgrid[0:synapse_info.n_pre_neurons,
                            post_vertex_slice.as_slice].T.reshape((-1, 2))

        # Deal with case where self-connections aren't allowed
        if (not self.__allow_self_connections and
                synapse_info.pre_population is synapse_info.post_population):
            pairs = pairs[pairs[:, 0] != pairs[:, 1]]

        # Now do the actual random choice from the available connections
        try:
            chosen = numpy.random.choice(
                pairs.shape[0], size=n_connections,
                replace=self.__with_replacement)
        except Exception as e:
            raise SpynnakerException(
                "MultapseConnector: The number of connections is too large "
                "for sampling without replacement; "
                "reduce the value specified in the connector") from e

        # Set up synaptic block
        block["source"] = pairs[chosen, 0]
        block["target"] = pairs[chosen, 1]
        block["weight"] = self._generate_weights(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["delay"] = self._generate_delays(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "MultapseConnector({})".format(self.__num_synapses)

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self):
        return ConnectorIDs.FIXED_TOTAL_NUMBER_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_params)
    def gen_connector_params(self):
        return numpy.array([
            int(self.__allow_self_connections),
            int(self.__with_replacement),
            self.__num_synapses], dtype=numpy.uint32)

    @property
    @overrides(
        AbstractGenerateConnectorOnMachine.gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        return (3 * BYTES_PER_WORD)
