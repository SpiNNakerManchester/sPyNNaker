from pyNN.random import RandomDistribution
from pyNN.random import NumpyRNG
from pyNN.space import Space

from spynnaker.pyNN.models.neural_properties.randomDistributions\
    import generate_parameter
from spynnaker.pyNN.models.neural_projections.connectors.seed_info \
    import SeedInfo
from spynnaker.pyNN.models.neural_projections.connectors.from_list_connector \
    import FromListConnector
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_properties.synapse_row_info \
    import SynapseRowInfo
from spynnaker.pyNN.exceptions import ConfigurationException

import logging
import numpy
import math

logger = logging.getLogger(__name__)


class DistanceDependentProbabilityConnector(FromListConnector):
    """
    Make connections using a distribution which varies with distance.

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

    def __init__(self, d_expression, allow_self_connections=True,
                 weights=0.0, delays=None, space=Space(), safe=True,
                 verbose=False, n_connections=None):
        """
        Creates a new DistanceDependentConnector. Uses the underlying machinery
        for FromListConnector.
        """
        self.d_expression = d_expression
        self.allow_self_connections = allow_self_connections
        self.space = space
        # weights may be a fixed value, a list of values,
        # a RandomDistribution object, or a distance_dependence function.
        self.weights = weights
        self.delays = delays   # and similar for this value
        self.connections_per_neuron = n_connections
        self.connectionSeeds = SeedInfo()
        FromListConnector.__init__(self, conn_list=None, safe=safe,
                                   verbose=verbose)

    def _distance_dependence(self, *args, **kwargs):
        if "d_expression" not in kwargs or "distances" not in kwargs:
            raise UnboundLocalError(
                "To evaluate a distance dependence requires both d_expression"
                " and distances array in kwargs")
            return None
        d_expression = kwargs["d_expression"]
        distances = kwargs["distances"]
        if type(d_expression) == RandomDistribution:
            DD = numpy.reshape(d_expression.next(
                               numpy.ravel(distances).shape[0]),
                               distances.shape)
        elif type(d_expression) == str:
            dist_f = eval('lambda d: %s' % d_expression)
            DD = numpy.empty(distances.shape)
            for pt in numpy.nditer(args, flags=['buffered', 'multi_index']):
                DD[pt] = dist_f(distances[pt])
        else:
            DD = numpy.asarray(d_expression)
            if len(DD.shape) == 0:
                DD = numpy.empty(distances.shape)
                DD.fill(d_expression)
            else:
                DD.reshape(DD, distances.shape)
        return DD

    def _dd_is_there_a_connection(
            self, d_expression, distances, rng=None):
        if rng is None:
            rng = NumpyRNG(seed=self.connectionSeeds._parent_seed)
        dd_potential_prob = rng.uniform(low=0.0, high=1.0,
                                        size=distances.shape)
        dd_actual_prob = numpy.fromfunction(
            self._distance_dependence, shape=distances.shape, dtype=int,
            d_expression=d_expression, distances=distances)
        return dd_potential_prob < dd_actual_prob

    def generate_synapse_list(
            self, presynaptic_population, postsynaptic_population, delay_scale,
            weight_scale, synapse_type):

        prevertex = presynaptic_population._get_vertex
        postvertex = postsynaptic_population._get_vertex

        if (presynaptic_population.structure is None
                or postsynaptic_population.structure is None):
            raise ValueError("Attempted to create a"
                             "DistanceDependentProbabilityConnector"
                             "with un-structured populations")
            return None

        id_lists = list()
        weight_lists = list()
        delay_lists = list()
        type_lists = list()

        # distances are set by comparing positions. An attempt to access
        # positions that have not been set yet will trigger generation of
        # the positions, so this computation will create positions if
        # necessary.
        distances = self.space.distances(presynaptic_population.positions,
                                         postsynaptic_population.positions)
        connections = self._dd_is_there_a_connection(
            d_expression=self.d_expression, distances=distances)
        if (not self.allow_self_connections
                and presynaptic_population == postsynaptic_population):
            numpy.fill_diagonal(connections, False)
        weights = numpy.fromfunction(function=self._distance_dependence,
                                     shape=distances.shape, dtype=int,
                                     d_expression=self.weights,
                                     distances=distances)
        delays = numpy.fromfunction(function=self._distance_dependence,
                                    shape=distances.shape, dtype=int,
                                    d_expression=self.delays,
                                    distances=distances)

        for i in range(0, prevertex.n_atoms):
            self._conn_list.extend([(i, j, weights[i, j], delays[i, j])
                                    for j in range(postvertex.n_atoms)
                                    if connections[i, j]])
            id_lists.append(list())
            weight_lists.append(list())
            delay_lists.append(list())
            type_lists.append(list())

        for i in range(0, len(self._conn_list)):
            conn = self._conn_list[i]
            pre_atom = generate_parameter(conn[0], i)
            post_atom = generate_parameter(conn[1], i)
            if not 0 <= pre_atom < prevertex.n_atoms:
                raise ConfigurationException(
                    "Invalid neuron id in presynaptic population {}".format(
                        pre_atom))
            if not 0 <= post_atom < postvertex.n_atoms:
                raise ConfigurationException(
                    "Invalid neuron id in postsynaptic population {}".format(
                        post_atom))
            weight = generate_parameter(conn[2], i) * weight_scale
            delay = generate_parameter(conn[3], i) * delay_scale
            id_lists[pre_atom].append(post_atom)
            weight_lists[pre_atom].append(weight)
            delay_lists[pre_atom].append(delay)
            type_lists[pre_atom].append(synapse_type)

        connection_list = [SynapseRowInfo(id_lists[i], weight_lists[i],
                           delay_lists[i], type_lists[i])
                           for i in range(0, prevertex.n_atoms)]

        return SynapticList(connection_list)
