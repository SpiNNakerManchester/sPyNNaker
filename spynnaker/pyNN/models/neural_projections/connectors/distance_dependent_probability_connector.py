from pyNN.space import Space

from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector

import logging
import numpy
import math

# support for arbitrary expression for the distance dependence
# NOTE: Do NOT delete these to fix PEP8 issues

# noinspection PyUnresolvedReferences
from numpy import arccos, arcsin, arctan, arctan2, ceil, cos  # @UnusedImport

# noinspection PyUnresolvedReferences
from numpy import cosh, exp, fabs, floor, fmod, hypot, ldexp  # @UnusedImport

# noinspection PyUnresolvedReferences
from numpy import log, log10, modf, power, sin, sinh, sqrt  # @UnusedImport

# noinspection PyUnresolvedReferences
from numpy import tan, tanh, maximum, minimum, e, pi  # @UnusedImport

logger = logging.getLogger(__name__)


class DistanceDependentProbabilityConnector(AbstractConnector):
    """ Make connections using a distribution which varies with distance.
    """

    def __init__(self, d_expression, allow_self_connections=True,
                 weights=0.0, delays=1, space=Space(), safe=True,
                 verbose=False, n_connections=None):
        """

        :param `string` d_expression:
            the right-hand side of a valid python expression for
            probability, involving 'd', e.g. "exp(-abs(d))", or "d<3",
            that can be parsed by eval(), that computes the distance
            dependent distribution
        :param `bool` allow_self_connections:
            if the connector is used to connect a
            Population to itself, this flag determines whether a neuron is
            allowed to connect to itself, or only to other neurons in the
            Population.
        :param `float` weights:
            may either be a float, a !RandomDistribution object, a list/
            1D array with at least as many items as connections to be
            created, or a distance dependence as per a d_expression. Units nA.
        :param `float` delays:  -- as `weights`. If `None`, all synaptic delays
            will be set to the global minimum delay.
        :param `pyNN.Space` space:
            a Space object, needed if you wish to specify distance-
            dependent weights or delays
        :param `int` n_connections:
            The number of efferent synaptic connections per neuron.
        """
        AbstractConnector.__init__(self, safe, space, verbose)
        self._d_expression = d_expression
        self._allow_self_connections = allow_self_connections
        self._weights = weights
        self._delays = delays

        self._check_parameters(weights, delays, allow_lists=False)
        if n_connections is not None:
            raise NotImplementedError(
                "n_connections is not implemented for"
                " DistanceDependentProbabilityConnector on this platform")

        # Get the probabilities up-front for now
        # TODO: Work out how this can be done statistically
        expand_distances = self._expand_distances(self._d_expression)
        pre_positions = self._pre_population.positions
        post_positions = self._post_population.positions

        # d is apparently unused, but is in fact expected by d_expression
        # so is used when eval is called
        d = self._space.distances(  # @UnusedVariable
            pre_positions, post_positions, expand_distances)
        self._probs = eval(self._d_expression)

    def get_delay_maximum(self):
        return self._get_delay_maximum(
            self._delays, utility_calls.get_probable_maximum_selected(
                self._n_pre_neurons * self._n_post_neurons,
                self._n_pre_neurons * self._n_post_neurons,
                numpy.amax(self._probs)))

    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        return self._get_delay_variance(self._delays, None)

    def _get_n_connections(self, out_of, pre_vertex_slice, post_vertex_slice):
        max_prob = numpy.amax(
            self._probs[pre_vertex_slice.as_slice, post_vertex_slice.as_slice])
        return utility_calls.get_probable_maximum_selected(
            self._n_pre_neurons * self._n_post_neurons, out_of,
            max_prob)

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        n_connections = self._get_n_connections(
            post_vertex_slice.n_atoms, pre_vertex_slice, post_vertex_slice)

        if min_delay is None or max_delay is None:
            return int(math.ceil(n_connections))

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            self._delays, self._n_pre_neurons * self._n_post_neurons,
            n_connections, None, min_delay, max_delay)

    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        return self._get_n_connections(
            pre_vertex_slice.n_atoms, pre_vertex_slice, post_vertex_slice)

    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        return self._get_weight_mean(self._weights, None)

    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        n_connections = self._get_n_connections(
            pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms,
            pre_vertex_slice, post_vertex_slice)
        return self._get_weight_maximum(
            self._weights, n_connections, None)

    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        return self._get_weight_variance(self._weights, None)

    def generate_on_machine(self):
        return False

    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):

        probs = self._probs[
            pre_slice_index.to_slice, post_slice_index.to_slice]
        n_items = pre_vertex_slice.n_atoms * post_vertex_slice.n_atoms
        items = self._rng.next(n_items)

        # If self connections are not allowed, remove possibility the self
        # connections by setting them to a value of infinity
        if not self._allow_self_connections:
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
            self._weights, n_connections, None)
        block["delay"] = self._generate_delays(
            self._delays, n_connections, None)
        block["synapse_type"] = synapse_type
        return block
