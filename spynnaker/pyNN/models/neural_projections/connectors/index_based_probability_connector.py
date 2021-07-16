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

import math
import numpy
from numpy import (
    arccos, arcsin, arctan, arctan2, ceil, cos, cosh, exp, fabs, floor, fmod,
    hypot, ldexp, log, log10, modf, power, sin, sinh, sqrt, tan, tanh, maximum,
    minimum, e, pi)
from spinn_utilities.overrides import overrides
from spinn_utilities.safe_eval import SafeEval
from spynnaker.pyNN.utilities import utility_calls
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)

# support for arbitrary expression for the indices
_index_expr_context = SafeEval(math, numpy, arccos, arcsin, arctan, arctan2,
                               ceil, cos, cosh, exp, fabs, floor, fmod, hypot,
                               ldexp, log, log10, modf, power, sin, sinh, sqrt,
                               tan, tanh, maximum, minimum, e=e, pi=pi)


class IndexBasedProbabilityConnector(AbstractConnector,
                                     AbstractGenerateConnectorOnHost):
    """ Make connections using a probability distribution which varies\
        dependent upon the indices of the pre- and post-populations.
    """

    __slots = [
        "__allow_self_connections",
        "__index_expression",
        "__probs"]

    def __init__(
            self, index_expression, allow_self_connections=True, rng=None,
            safe=True, callback=None, verbose=False):
        """
        :param str index_expression:
            the right-hand side of a valid python expression for
            probability, involving the indices of the pre and post populations,
            that can be parsed by eval(), that computes a probability dist;
            the indices will be given as variables ``i`` and ``j`` when the
            expression is evaluated.
        :param bool allow_self_connections:
            if the connector is used to connect a Population to itself, this
            flag determines whether a neuron is allowed to connect to itself,
            or only to other neurons in the Population.
        :param rng:
            Seeded random number generator, or ``None`` to make one when
            needed.
        :type rng: ~pyNN.random.NumpyRNG or None
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        """
        super().__init__(safe, callback, verbose)
        self._rng = rng
        self.__index_expression = index_expression
        self.__allow_self_connections = allow_self_connections
        self.__probs = None

    def _update_probs_from_index_expression(self, synapse_info):
        """
        :param SynapseInformation synapse_info:
        """
        # note: this only needs to be done once
        if self.__probs is None:
            # numpy array of probabilities using the index_expression
            self.__probs = numpy.fromfunction(
                lambda i, j: _index_expr_context.eval(
                    self.__index_expression, i=i, j=j),
                (synapse_info.n_pre_neurons, synapse_info.n_post_neurons))

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        self._update_probs_from_index_expression(synapse_info)
        n_connections = utility_calls.get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            numpy.amax(self.__probs))
        return self._get_delay_maximum(
            synapse_info.delays, n_connections, synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info):
        self._update_probs_from_index_expression(synapse_info)
        n_connections = utility_calls.get_probable_minimum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            numpy.amax(self.__probs))
        return self._get_delay_minimum(
            synapse_info.delays, n_connections, synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, synapse_info, min_delay=None,
            max_delay=None):
        self._update_probs_from_index_expression(synapse_info)
        n_connections = utility_calls.get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            post_vertex_slice.n_atoms, numpy.amax(self.__probs))

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            n_connections, min_delay, max_delay, synapse_info)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        self._update_probs_from_index_expression(synapse_info)
        return utility_calls.get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info.n_pre_neurons, numpy.amax(self.__probs))

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        self._update_probs_from_index_expression(synapse_info)
        n_connections = utility_calls.get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            numpy.amax(self.__probs))
        return self._get_weight_maximum(
            synapse_info.weights, n_connections, synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, post_slices, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        # setup probs here
        self._update_probs_from_index_expression(synapse_info)

        probs = self.__probs[
            pre_vertex_slice.as_slice, post_vertex_slice.as_slice].reshape(-1)

        n_items = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        items = self._rng.next(n_items)

        # If self connections are not allowed, remove the possibility of self
        # connections by setting the probability to a value of infinity
        if not self.__allow_self_connections:
            items[0:n_items:post_vertex_slice.n_atoms + 1] = numpy.inf

        present = items < probs
        ids = numpy.where(present)[0]
        n_connections = numpy.sum(present)

        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        block["source"] = (
            (ids / post_vertex_slice.n_atoms) + pre_vertex_slice.lo_atom)
        block["target"] = (
            (ids % post_vertex_slice.n_atoms) + post_vertex_slice.lo_atom)
        block["weight"] = self._generate_weights(
            block["source"], block["target"], n_connections, None,
            pre_vertex_slice, post_vertex_slice, synapse_info)
        block["delay"] = self._generate_delays(
            block["source"], block["target"], n_connections, None,
            pre_vertex_slice, post_vertex_slice, synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "IndexBasedProbabilityConnector({})".format(
            self.__index_expression)

    @property
    def allow_self_connections(self):
        """ If the connector is used to connect a Population to itself, this\
            flag determines whether a neuron is allowed to connect to itself,\
            or only to other neurons in the Population.

        :rtype: bool
        """
        return self.__allow_self_connections

    @allow_self_connections.setter
    def allow_self_connections(self, new_value):
        self.__allow_self_connections = new_value

    @property
    def index_expression(self):
        """ The right-hand side of a valid python expression for probability,\
            involving the indices of the pre and post populations, that can\
            be parsed by eval(), that computes a probability dist.

        :rtype: str
        """
        return self.__index_expression

    @index_expression.setter
    def index_expression(self, new_value):
        self.__index_expression = new_value
