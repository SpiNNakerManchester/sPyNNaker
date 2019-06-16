import logging
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

logger = logging.getLogger(__name__)
# support for arbitrary expression for the distance dependence
_d_expr_context = SafeEval(math, numpy, arccos, arcsin, arctan, arctan2, ceil,
                           cos, cosh, exp, fabs, floor, fmod, hypot, ldexp,
                           log, log10, modf, power, sin, sinh, sqrt, tan, tanh,
                           maximum, minimum, e=e, pi=pi)


class DistanceDependentProbabilityConnector(AbstractConnector):
    """ Make connections using a distribution which varies with distance.
    """

    __slots__ = [
        "__allow_self_connections",
        "__d_expression",
        "__probs"]

    def __init__(
            self, d_expression, allow_self_connections=True, safe=True,
            verbose=False, n_connections=None, rng=None):
        """
        :param d_expression:\
            the right-hand side of a valid python expression for\
            probability, involving 'd', e.g. "exp(-abs(d))", or "d<3",\
            that can be parsed by eval(), that computes the distance\
            dependent distribution.
        :type d_expression: str
        :param allow_self_connections:\
            if the connector is used to connect a Population to itself, this\
            flag determines whether a neuron is allowed to connect to itself,\
            or only to other neurons in the Population.
        :type d_expression: bool
        :param space:\
            a Space object, needed if you wish to specify distance-dependent\
            weights or delays.
        :type space: pyNN.Space
        :param n_connections:\
            The number of efferent synaptic connections per neuron.
        :type n_connections: int or None
        """
        # pylint: disable=too-many-arguments
        super(DistanceDependentProbabilityConnector, self).__init__(
            safe, verbose)
        self.__d_expression = d_expression
        self.__allow_self_connections = allow_self_connections
        self._rng = rng
        if n_connections is not None:
            raise NotImplementedError(
                "n_connections is not implemented for"
                " DistanceDependentProbabilityConnector on this platform")

    @overrides(AbstractConnector.set_projection_information)
    def set_projection_information(
            self, pre_population, post_population, rng, machine_time_step):
        AbstractConnector.set_projection_information(
            self, pre_population, post_population, rng, machine_time_step)
        self._set_probabilities()

    def _set_probabilities(self):
        # Set the probabilities up-front for now
        # TODO: Work out how this can be done statistically
        expand_distances = self._expand_distances(self.__d_expression)
        pre_positions = self.pre_population.positions
        post_positions = self.post_population.positions

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
    def get_delay_maximum(self, delays):
        return self._get_delay_maximum(
            delays,
            utility_calls.get_probable_maximum_selected(
                self._n_pre_neurons * self._n_post_neurons,
                self._n_pre_neurons * self._n_post_neurons,
                numpy.amax(self.__probs)))

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, delays, post_vertex_slice, min_delay=None, max_delay=None):
        # pylint: disable=too-many-arguments
        max_prob = numpy.amax(
            self.__probs[0:self._n_pre_neurons, post_vertex_slice.as_slice])
        n_connections = utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_post_neurons,
            post_vertex_slice.n_atoms, max_prob)

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            delays, self._n_pre_neurons * self._n_post_neurons,
            n_connections, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        # pylint: disable=too-many-arguments
        return utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_post_neurons, self._n_post_neurons,
            numpy.amax(self.__probs))

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, weights):
        # pylint: disable=too-many-arguments
        return self._get_weight_maximum(
            weights,
            utility_calls.get_probable_maximum_selected(
                self._n_pre_neurons * self._n_post_neurons,
                self._n_pre_neurons * self._n_post_neurons,
                numpy.amax(self.__probs)))

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, weights, delays, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):

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
            weights, n_connections, None)
        block["delay"] = self._generate_delays(
            delays, n_connections, None)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "DistanceDependentProbabilityConnector({})".format(
            self.__d_expression)

    @property
    def allow_self_connections(self):
        return self.__allow_self_connections

    @allow_self_connections.setter
    def allow_self_connections(self, new_value):
        self.__allow_self_connections = new_value

    @property
    def d_expression(self):
        return self.__d_expression

    @d_expression.setter
    def d_expression(self, new_value):
        self.__d_expression = new_value
