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
from spynnaker.pyNN.utilities.utility_calls import (
    get_probable_maximum_selected, get_probable_minimum_selected)
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)

# support for arbitrary expression for the distance dependence
_d_expr_context = SafeEval(math, numpy, arccos, arcsin, arctan, arctan2, ceil,
                           cos, cosh, exp, fabs, floor, fmod, hypot, ldexp,
                           log, log10, modf, power, sin, sinh, sqrt, tan, tanh,
                           maximum, minimum, e=e, pi=pi)


class DistanceDependentProbabilityConnector(
        AbstractConnector, AbstractGenerateConnectorOnHost):
    """ Make connections using a distribution which varies with distance.
    """

    __slots__ = [
        "__allow_self_connections",
        "__d_expression",
        "__probs"]

    def __init__(
            self, d_expression, allow_self_connections=True, safe=True,
            verbose=False, n_connections=None, rng=None, callback=None):
        """
        :param str d_expression:
            the right-hand side of a valid python expression for
            probability, involving ``d``,
            (e.g. ``"exp(-abs(d))"``, or ``"d < 3"``),
            that can be parsed by ``eval()``, that computes the distance
            dependent distribution.
        :param bool allow_self_connections:
            if the connector is used to connect a Population to itself, this
            flag determines whether a neuron is allowed to connect to itself,
            or only to other neurons in the Population.
        :param bool safe:
            if ``True``, check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param n_connections:
            The number of efferent synaptic connections per neuron.
        :type n_connections: int or None
        :param rng:
            Seeded random number generator, or ``None`` to make one when
            needed.
        :type rng: ~pyNN.random.NumpyRNG or None
        :param callable callback:
        """
        # :param ~pyNN.space.Space space:
        #    a Space object, needed if you wish to specify distance-dependent
        #    weights or delays.

        # pylint: disable=too-many-arguments
        super().__init__(safe, callback, verbose)
        self.__d_expression = d_expression
        self.__allow_self_connections = allow_self_connections
        self._rng = rng
        self.__probs = None
        if n_connections is not None:
            raise NotImplementedError(
                "n_connections is not implemented for"
                " DistanceDependentProbabilityConnector on this platform")

    @overrides(AbstractConnector.set_projection_information)
    def set_projection_information(self, synapse_info):
        super().set_projection_information(synapse_info)
        self._set_probabilities(synapse_info)

    def _set_probabilities(self, synapse_info):
        """
        :param SynapseInformation synapse_info:
        """
        # Set the probabilities up-front for now
        # TODO: Work out how this can be done statistically
        expand_distances = self._expand_distances(self.__d_expression)
        pre_positions = synapse_info.pre_population.positions
        post_positions = synapse_info.post_population.positions

        d1 = self.space.distances(
            pre_positions, post_positions, expand_distances)

        # PyNN 0.8 returns a flattened (C-style) array from space.distances,
        # so the easiest thing to do here is to reshape back to the "expected"
        # PyNN 0.7 shape; otherwise later code gets confusing and difficult
        if (len(d1.shape) == 1):
            d = numpy.reshape(d1, (pre_positions.shape[0],
                                   post_positions.shape[0]))
        else:
            d = d1

        self.__probs = _d_expr_context.eval(self.__d_expression, d=d)

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        return self._get_delay_maximum(
            synapse_info.delays,
            get_probable_maximum_selected(
                synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
                synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
                numpy.amax(self.__probs)),
            synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info):
        return self._get_delay_minimum(
            synapse_info.delays,
            get_probable_minimum_selected(
                synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
                synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
                numpy.amax(self.__probs)),
            synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, synapse_info, min_delay=None,
            max_delay=None):
        # pylint: disable=too-many-arguments
        max_prob = numpy.amax(
            self.__probs[0:synapse_info.n_pre_neurons,
                         post_vertex_slice.as_slice])
        n_connections = get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            post_vertex_slice.n_atoms, max_prob)

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            n_connections, min_delay, max_delay, synapse_info)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        # pylint: disable=too-many-arguments
        return get_probable_maximum_selected(
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            synapse_info.n_post_neurons,
            numpy.amax(self.__probs))

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        # pylint: disable=too-many-arguments
        return self._get_weight_maximum(
            synapse_info.weights,
            get_probable_maximum_selected(
                synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
                synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
                numpy.amax(self.__probs)),
            synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, post_slices, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        probs = self.__probs[
            pre_vertex_slice.as_slice, post_vertex_slice.as_slice].reshape(-1)
        n_items = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        items = self._rng.next(n_items)

        # If self connections are not allowed, remove the possibility of
        # self connections by setting them to a value of infinity
        if not self.__allow_self_connections:
            items[0:n_items:post_vertex_slice.n_atoms + 1] = numpy.inf

        present = items < probs
        ids = numpy.where(present)[0]
        n_connections = numpy.sum(present)

        block = numpy.zeros(
            n_connections, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = (
            (ids // post_vertex_slice.n_atoms) + pre_vertex_slice.lo_atom)
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
        return "DistanceDependentProbabilityConnector({})".format(
            self.__d_expression)

    @property
    def allow_self_connections(self):
        """
        :rtype: bool
        """
        return self.__allow_self_connections

    @allow_self_connections.setter
    def allow_self_connections(self, new_value):
        self.__allow_self_connections = new_value

    @property
    def d_expression(self):
        """ The distance expression.

        :rtype: str
        """
        return self.__d_expression

    @d_expression.setter
    def d_expression(self, new_value):
        self.__d_expression = new_value
