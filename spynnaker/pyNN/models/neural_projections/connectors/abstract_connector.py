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

import logging
import math
import re
import numpy
from spinn_utilities.log import FormatAdapter
from pyNN.random import NumpyRNG, RandomDistribution

from spinn_utilities.logger_utils import warn_once
from spinn_utilities.safe_eval import SafeEval
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_front_end_common.interface.provenance import ProvenanceWriter
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID

# global objects
logger = FormatAdapter(logging.getLogger(__name__))
_expr_context = SafeEval(
    math, numpy, numpy.arccos, numpy.arcsin, numpy.arctan, numpy.arctan2,
    numpy.ceil, numpy.cos, numpy.cosh, numpy.exp, numpy.fabs, numpy.floor,
    numpy.fmod, numpy.hypot, numpy.ldexp, numpy.log, numpy.log10, numpy.modf,
    numpy.power, numpy.sin, numpy.sinh, numpy.sqrt, numpy.tan, numpy.tanh,
    numpy.maximum, numpy.minimum, e=numpy.e, pi=numpy.pi)


class AbstractConnector(object, metaclass=AbstractBase):
    """
    Abstract class that all PyNN Connectors extend.
    """
    # pylint: disable=unused-argument,too-many-arguments

    NUMPY_SYNAPSES_DTYPE = [("source", "uint32"), ("target", "uint16"),
                            ("weight", "float64"), ("delay", "float64"),
                            ("synapse_type", "uint8")]

    __slots__ = [
        "_delays",
        "__min_delay",
        "__n_clipped_delays",
        "_rng",
        "__safe",
        "__space",
        "__verbose",
        "_weights",
        "__param_seeds",
        "__synapse_info"]

    def __init__(self, safe=True, callback=None, verbose=False, rng=None):
        """
        :param bool safe: if True, check that weights and delays have valid
            values. If False, this check is skipped. (NB: SpiNNaker always
            checks.)
        :param callable callback: Ignored
        :param bool verbose:
        :param rng:
            Seeded random number generator, or None to make one when needed
        :type rng: ~pyNN.random.NumpyRNG or None
        """
        if callback is not None:
            warn_once(logger, "sPyNNaker ignores connector callbacks.")
        self.__safe = safe
        self.__space = None
        self.__verbose = verbose

        self._rng = rng

        self.__n_clipped_delays = numpy.int64(0)
        self.__min_delay = 0
        self.__param_seeds = dict()
        self.__synapse_info = None

    def set_space(self, space):
        """
        Set the space object (allowed after instantiation).

        :param ~pyNN.space.Space space:
        """
        self.__space = space

    def set_projection_information(self, synapse_info):
        """
        Sets a connectors projection info.

        :param SynapseInformation synapse_info: the synapse info
        """
        self._rng = (self._rng or NumpyRNG())
        self.__min_delay = SpynnakerDataView.get_simulation_time_step_ms()

    def _get_delay_minimum(self, delays, n_connections, synapse_info):
        """
        Get the minimum delay given a float or RandomDistribution.

        :param delays: the delays
        :type delays: ~numpy.ndarray or ~spynnaker.pyNN.RandomDistribution
            or int or float
        :param int n_connections: how many connections
        """
        if isinstance(delays, RandomDistribution):
            low_estimated_delay = utility_calls.get_minimum_probable_value(
                delays, n_connections)
            low = utility_calls.low(delays)
            if low is None:
                return low_estimated_delay

            # The minimum is the maximum of the possible maximums
            return max(low_estimated_delay, low, 1)
        elif isinstance(delays, str):
            d = self._get_distances(delays, synapse_info)
            return numpy.min(_expr_context.eval(delays, d=d))
        elif numpy.isscalar(delays):
            return delays
        raise SpynnakerException(
            f"Unrecognised delay format: {type(delays)}")

    def _get_delay_maximum(self, delays, n_connections, synapse_info):
        """
        Get the maximum delay given a float or RandomDistribution.

        :param delays:
        :type delays: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
        :param int n_connections:
        """
        if isinstance(delays, RandomDistribution):
            max_estimated_delay = utility_calls.get_maximum_probable_value(
                delays, n_connections)
            high = utility_calls.high(delays)
            if high is None:
                return max_estimated_delay

            # The maximum is the minimum of the possible maximums
            return min(max_estimated_delay, high)
        elif isinstance(delays, str):
            d = self._get_distances(delays, synapse_info)
            return numpy.max(_expr_context.eval(delays, d=d))
        elif numpy.isscalar(delays):
            return delays
        elif hasattr(delays, "__getitem__"):
            return numpy.max(delays)
        raise SpynnakerException(f"Unrecognised delay format: {type(delays)}")

    @abstractmethod
    def get_delay_maximum(self, synapse_info):
        """
        Get the maximum delay specified by the user in ms, or `None` if
        unbounded.

        :param SynapseInformation synapse_info: the synapse info
        :rtype: int or None
        """

    @abstractmethod
    def get_delay_minimum(self, synapse_info):
        """
        Get the minimum delay specified by the user in ms, or `None` if
        unbounded.

        :param SynapseInformation synapse_info:
        :rtype: int or None
        """

    def get_delay_variance(self, delays, synapse_info):
        """
        Get the variance of the delays.

        :param delays:
        :type delays: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
        :rtype: float
        """
        if isinstance(delays, RandomDistribution):
            return utility_calls.get_variance(delays)
        elif isinstance(delays, str):
            d = self._get_distances(delays, synapse_info)
            return numpy.var(_expr_context.eval(delays, d=d))
        elif numpy.isscalar(delays):
            return 0.0
        elif hasattr(delays, "__getitem__"):
            return numpy.var(delays)
        raise SpynnakerException("Unrecognised delay format")

    def _get_n_connections_from_pre_vertex_with_delay_maximum(
            self, delays, n_total_connections, n_connections,
            min_delay, max_delay, synapse_info):
        """
        Get the expected number of delays that will fall within min_delay and
        max_delay given given a float, RandomDistribution or list of delays.

        :param delays:
        :type delays: ~numpy.ndarray or spynnaker.pyNN.RandomDistribution
            or int or float
        :param int n_total_connections:
        :param int n_connections:
        :param float min_delay:
        :param float max_delay:
        :rtype: float
        """
        if isinstance(delays, RandomDistribution):
            prob_in_range = utility_calls.get_probability_within_range(
                delays, min_delay, max_delay)
            if prob_in_range > 0:
                v = int(math.ceil(utility_calls.get_probable_maximum_selected(
                    n_total_connections, n_connections, prob_in_range)))
                # If the probability is so low as to result in 0, assume
                # at least 1 if there is some probability that the delay is
                # in range
                return max(v, 1)
            else:
                return 0
        elif isinstance(delays, str):
            d = self._get_distances(delays, synapse_info)
            delays = _expr_context.eval(delays, d=d)
            n_delayed = sum([len([
                delay for delay in delays
                if min_delay <= delay <= max_delay])])
            if n_delayed == 0:
                return 0
            n_total = len(delays)
            prob_delayed = float(n_delayed) / float(n_total)
            return int(math.ceil(utility_calls.get_probable_maximum_selected(
                n_total_connections, n_connections, prob_delayed)))
        elif numpy.isscalar(delays):
            if min_delay <= delays <= max_delay:
                return int(math.ceil(n_connections))
            return 0
        raise SpynnakerException("Unrecognised delay format")

    @abstractmethod
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms, synapse_info, min_delay=None, max_delay=None):
        """
        Get the maximum number of connections from any
        neuron in the pre vertex to the neurons in the post_vertex_slice,
        for connections with a delay between min_delay and max_delay
        (inclusive) if both specified (otherwise all connections).

        :param delays:
        :type delays: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
        :param int n_post_atoms:
        :param SynapseInformation synapse_info:
        :param min_delay:
        :type min_delay: int or None
        :param max_delay:
        :type max_delay: int or None
        :rtype: int
        """

    @abstractmethod
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        """
        Get the maximum number of connections to any neuron
        in the post vertex from neurons in the pre vertex.

        :param SynapseInformation synapse_info:
        :rtype: int
        """

    def get_weight_mean(self, weights, synapse_info):
        """
        Get the mean of the weights.

        :param weights:
        :type weights: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
        :rtype: float
        """
        if isinstance(weights, RandomDistribution):
            return abs(utility_calls.get_mean(weights))
        elif isinstance(weights, str):
            d = self._get_distances(weights, synapse_info)
            return numpy.mean(_expr_context.eval(weights, d=d))
        elif numpy.isscalar(weights):
            return abs(weights)
        elif hasattr(weights, "__getitem__"):
            return numpy.mean(weights)
        raise SpynnakerException("Unrecognised weight format")

    def _get_weight_maximum(self, weights, n_connections, synapse_info):
        """
        Get the maximum of the weights.

        :param weights:
        :type weights: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
        :param int n_connections:
        :rtype: float
        """
        if isinstance(weights, RandomDistribution):
            mean_weight = utility_calls.get_mean(weights)
            if mean_weight < 0:
                min_weight = utility_calls.get_minimum_probable_value(
                    weights, n_connections)
                low = utility_calls.low(weights)
                if low is None:
                    return abs(min_weight)
                return abs(max(min_weight, low))
            else:
                max_weight = utility_calls.get_maximum_probable_value(
                    weights, n_connections)
                high = utility_calls.high(weights)
                if high is None:
                    return abs(max_weight)
                return abs(min(max_weight, high))
        elif isinstance(weights, str):
            d = self._get_distances(weights, synapse_info)
            return numpy.max(_expr_context.eval(weights, d=d))
        elif numpy.isscalar(weights):
            return abs(weights)
        elif hasattr(weights, "__getitem__"):
            return numpy.amax(numpy.abs(weights))
        raise SpynnakerException("Unrecognised weight format")

    @abstractmethod
    def get_weight_maximum(self, synapse_info):
        """
        Get the maximum of the weights for this connection.

        :param SynapseInformation synapse_info:
        :rtype: float
        """

    def get_weight_variance(self, weights, synapse_info):
        """
        Get the variance of the weights.

        :param weights:
        :type weights: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
        :rtype: float
        """
        if isinstance(weights, RandomDistribution):
            return utility_calls.get_variance(weights)
        elif isinstance(weights, str):
            d = self._get_distances(weights, synapse_info)
            return numpy.var(_expr_context.eval(weights, d=d))
        elif numpy.isscalar(weights):
            return 0.0
        elif hasattr(weights, "__getitem__"):
            return numpy.var(weights)
        raise SpynnakerException("Unrecognised weight format")

    def _expand_distances(self, d_expression):
        """
        Check if a distance expression contains at least one term `d[x]`.
        If yes, then the distances are expanded to distances in the
        separate coordinates rather than the overall distance over all
        coordinates, and we assume the user has specified an expression
        such as `d[0] + d[2]`.

        :param str d_expression:
        :rtype: bool
        """
        regexpr = re.compile(r'.*d\[\d*\].*')
        return regexpr.match(d_expression)

    def _get_distances(self, values, synapse_info):
        if self.__space is None:
            raise ValueError(
                f"Weights or delays are distance-dependent "
                f"but no space object was specified in projection "
                f"{synapse_info.pre_population}-"
                f"{synapse_info.post_population}")

        expand_distances = self._expand_distances(values)

        return self.__space.distances(
            synapse_info.pre_population.positions,
            synapse_info.post_population.positions,
            expand_distances)

    def _generate_random_values(
            self, values, n_connections, post_vertex_slice):
        """
        :param ~pyNN.random.NumpyRNG values:
        :param int n_connections:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :rtype: ~numpy.ndarray
        """
        key = (id(post_vertex_slice), id(values))
        seed = self.__param_seeds.get(key, None)
        if seed is None:
            seed = int(values.rng.next() * 0x7FFFFFFF)
            self.__param_seeds[key] = seed
        new_rng = NumpyRNG(seed)
        copy_rd = RandomDistribution(
            values.name, parameters_pos=None, rng=new_rng,
            **values.parameters)
        if n_connections == 1:
            return numpy.array([copy_rd.next(1)], dtype="float64")
        return copy_rd.next(n_connections)

    def _generate_values(
            self, values, sources, targets, n_connections, post_slice,
            synapse_info):
        """
        :param values:
        :type values: ~pyNN.random.NumpyRNG or int or float or str or callable
        :param int n_connections:
        :param ~pacman.model.graphs.common.Slice post_slice:
        :param SynapseInformation synapse_info:
        :rtype: ~numpy.ndarray
        """
        if isinstance(values, RandomDistribution):
            return self._generate_random_values(
                values, n_connections, post_slice)
        elif isinstance(values, str) or callable(values):
            if self.__space is None:
                raise SpynnakerException(
                    "No space object specified in projection "
                    f"{synapse_info.pre_population}-"
                    f"{synapse_info.post_population}")

            expand_distances = True
            if isinstance(values, str):
                expand_distances = self._expand_distances(values)

                # At this point we need to now get the values corresponding to
                # the distances between connections in "sources" and "targets"
                eval_values = numpy.zeros(n_connections, dtype="float64")
                for i in range(n_connections):
                    # get the distance for this source and target pair
                    dist = self.__space.distances(
                        synapse_info.pre_population.positions[sources[i]],
                        synapse_info.post_population.positions[targets[i]],
                        expand_distances)
                    # evaluate expression at this distance
                    eval_values[i] = _expr_context.eval(values, d=dist)
                return eval_values

            d = self.__space.distances(
                synapse_info.pre_population.positions[sources[i]],
                synapse_info.post_population.positions[targets[i]],
                expand_distances)

            return values(d)
        elif numpy.isscalar(values):
            return numpy.repeat([values], n_connections).astype("float64")
        elif hasattr(values, "__getitem__"):
            return numpy.array(values).astype("float64")
        raise SpynnakerException(f"Unrecognised values {values}")

    def _generate_weights(
            self, sources, targets, n_connections, post_slice, synapse_info):
        """
        Generate weight values.

        :param int n_connections:
        :param ~pacman.model.graphs.common.Slice post_slice:
        :param SynapseInformation synapse_info:
        :rtype: ~numpy.ndarray
        """
        weights = self._generate_values(
            synapse_info.weights, sources, targets, n_connections, post_slice,
            synapse_info)
        if self.__safe:
            if not weights.size:
                warn_once(logger, "No connection in " + str(self))
            # TODO: I think this is allowed for local_only so investigate what's
            #       going on there
        #     elif numpy.amin(weights) < 0 < numpy.amax(weights):
        #         raise SpynnakerException(
        #             "Weights must be either all positive or all negative in "
        #             f"projection {synapse_info.pre_population.label}->"
        #             f"{synapse_info.post_population.label}")
        # return numpy.abs(weights)
        return weights  # numpy.abs(weights)

    def _clip_delays(self, delays):
        """
        Clip delay values, keeping track of how many have been clipped.

        :param ~numpy.ndarray delays:
        :rtype: ~numpy.ndarray
        """
        # count values that could be clipped
        self.__n_clipped_delays = numpy.sum(delays < self.__min_delay)

        # clip values
        if numpy.isscalar(delays):
            if delays < self.__min_delay:
                delays = self.__min_delay
        else:
            if delays.size:
                delays[delays < self.__min_delay] = self.__min_delay
        return delays

    def _generate_delays(
            self, sources, targets, n_connections, post_slice, synapse_info):
        """
        Generate valid delay values.

        :param int n_connections:
        :param ~pacman.model.graphs.common.Slice post_slice:
        :param SynapseInformation synapse_info:
        :rtype: ~numpy.ndarray
        """
        delays = self._generate_values(
            synapse_info.delays, sources, targets, n_connections, post_slice,
            synapse_info)

        return self._clip_delays(delays)

    def get_provenance_data(self, synapse_info):
        """
        :param SynapseInformation synapse_info:
        """
        # Convert to native Python integer; provenance system assumption
        ncd = self.__n_clipped_delays.item()
        with ProvenanceWriter() as db:
            # pylint: disable=expression-not-assigned
            db.insert_connector(
                synapse_info.pre_population.label,
                synapse_info.post_population.label,
                self.__class__.__name__, "Times_synaptic_delays_got_clipped",
                ncd),
            if ncd > 0:
                db.insert_report(
                    f"The delays in the connector {self.__class__.__name__} "
                    f"from {synapse_info.pre_population.label} "
                    f"to {synapse_info.post_population.label} "
                    f"was clipped to {self.__min_delay} a total of {ncd} "
                    f"times. This can be avoided by reducing the timestep or "
                    f"increasing the minimum delay to one timestep")

    @property
    def safe(self):
        """
        :rtype: bool
        """
        return self.__safe

    @safe.setter
    def safe(self, new_value):
        self.__safe = new_value

    @property
    def space(self):
        """
        The space object (may be updated after instantiation).

        :rtype: ~pyNN.space.Space or None
        """
        return self.__space

    @space.setter
    def space(self, new_value):
        """
        Set the space object (allowed after instantiation).

        :param ~pyNN.space.Space new_value:
        """
        self.__space = new_value

    @property
    def synapse_info(self):
        """
        The synapse_info object (may be updated after instantiation).

        :rtype: synapse_info or None
        """
        return self.__synapse_info

    @property
    def verbose(self):
        """
        :rtype: bool
        """
        return self.__verbose

    @verbose.setter
    def verbose(self, new_value):
        self.__verbose = new_value

    def use_direct_matrix(self, synapse_info):
        """
        :param SynapseInformation synapse_info:
        :rtype: bool
        """
        return False

    def get_connected_vertices(self, s_info, source_vertex, target_vertex):
        """
        Get the machine vertices that are connected to each other with
        this connector

        :param SynapseInformation s_info:
            The synapse information of the connection
        :param source_vertex: The source of the spikes
        :type source_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :param target_vertex: The target of the spikes
        :type target_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :return: A list of tuples of (target machine vertex, list of sources)
        :rtype: list(tuple(~pacman.model.graphs.machine.MachineVertex,
            list(~pacman.model.graphs.AbstractVertex)))
        """
        # By default, just return that the whole target connects to the
        # whole source
        return [(m_vertex, [source_vertex])
                for m_vertex in target_vertex.splitter.get_in_coming_vertices(
                    SPIKE_PARTITION_ID)]

    def connect(self, projection):
        """
        Apply this connector to a projection.

        .. warning::
            Do *not* call this! SpyNNaker does not work that way.

        :param ~spynnaker.pyNN.models.projection.Projection projection:
        :raises SpynnakerException: Always. Method not supported; profiled out.
        """
        raise SpynnakerException("Standard pyNN connect method not supported")

    @staticmethod
    def _roundsize(size, label):
        """
        Ensures that the ``size`` is an integer. Approximate integers are
        rounded; other values cause exceptions.

        :param size: The value to be rounded
        :type size: int or float
        :param str label: The type-name of the connection, for messages
        :rtype: int
        :raises SpynnakerException: If the size is non-integer and not close
        """
        if isinstance(size, int):
            return size
        # Allow a float which has a near int value
        temp = int(round(size))
        if abs(temp - size) < 0.001:
            logger.warning("Size of {} rounded from {} to {}. "
                           "Please use int values for size",
                           label, size, temp)
            return temp
        raise SpynnakerException(
            f"Size of {label} must be an int, received {size}")

    def validate_connection(self, application_edge, synapse_info):
        """
        Checks that the edge supports the connector.  By default this does
        nothing i.e. assumes the edge is OK, but can be overridden if the
        connector has rules that need to be checked.  Returns nothing; it
        is assumed that an Exception will be raised if anything is wrong.

        :param application_edge: The edge of the connection
        :type application_edge:
            ~pacman.model.graphs.application.ApplicationEdge
        :param SynapseInformation synapse_info: The synaptic information
        """
        return
