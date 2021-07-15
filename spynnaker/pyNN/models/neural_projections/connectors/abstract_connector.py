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
import re
import numpy
from spinn_utilities.log import FormatAdapter
from pyNN.random import NumpyRNG, RandomDistribution

from spinn_utilities.logger_utils import warn_once
from spinn_utilities.safe_eval import SafeEval
from spinn_front_end_common.utilities.globals_variables import (
    machine_time_step_ms)
from spinn_front_end_common.utilities.utility_objs import ProvenanceDataItem
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.exceptions import SpynnakerException

# global objects
logger = FormatAdapter(logging.getLogger(__name__))
_expr_context = SafeEval(
    math, numpy, numpy.arccos, numpy.arcsin, numpy.arctan, numpy.arctan2,
    numpy.ceil, numpy.cos, numpy.cosh, numpy.exp, numpy.fabs, numpy.floor,
    numpy.fmod, numpy.hypot, numpy.ldexp, numpy.log, numpy.log10, numpy.modf,
    numpy.power, numpy.sin, numpy.sinh, numpy.sqrt, numpy.tan, numpy.tanh,
    numpy.maximum, numpy.minimum, e=numpy.e, pi=numpy.pi)


class AbstractConnector(object, metaclass=AbstractBase):
    """ Abstract class that all PyNN Connectors extend.
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
        """ Set the space object (allowed after instantiation).

        :param ~pyNN.space.Space space:
        """
        self.__space = space

    def set_projection_information(self, synapse_info):
        """ sets a connectors projection info
        :param SynapseInformation synapse_info: the synapse info
        """
        self._rng = (self._rng or NumpyRNG())
        self.__min_delay = machine_time_step_ms()

    def _check_parameter(self, values, name, allow_lists):
        """ Check that the types of the values is supported.

        :param values:
        :type values: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
        :param str name:
        :param bool allow_lists:
        """
        if (not numpy.isscalar(values) and
                not (isinstance(values, RandomDistribution)) and
                not hasattr(values, "__getitem__")):
            raise SpynnakerException("Parameter {} format unsupported".format(
                name))
        if not allow_lists and hasattr(values, "__getitem__"):
            raise NotImplementedError(
                "Lists of {} are not supported by the implementation of {} on "
                "this platform".format(name, self.__class__))

    def _check_parameters(self, weights, delays, allow_lists=False):
        """ Check the types of the weights and delays are supported; lists can\
            be disallowed if desired.

        :param weights:
        :type weights: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
        :param delays:
        :type delays: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
        :param bool allow_lists:
        """
        self._check_parameter(weights, "weights", allow_lists)
        self._check_parameter(delays, "delays", allow_lists)

    def _get_delay_minimum(self, delays, n_connections, synapse_info):
        """ Get the minimum delay given a float, RandomDistribution or list of\
            delays.

        :param delays: the delays
        :type delays: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
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
        elif hasattr(delays, "__getitem__"):
            return numpy.min(delays)
        raise SpynnakerException("Unrecognised delay format: {:s}".format(
            type(delays)))

    def _get_delay_maximum(self, delays, n_connections, synapse_info):
        """ Get the maximum delay given a float, RandomDistribution or list of\
            delays.

        :param delays:
        :type delays: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
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
        raise SpynnakerException("Unrecognised delay format: {:s}".format(
            type(delays)))

    @abstractmethod
    def get_delay_maximum(self, synapse_info):
        """ Get the maximum delay specified by the user in ms, or None if\
            unbounded.

        :param SynapseInformation synapse_info: the synapse info
        :rtype: int or None
        """

    @abstractmethod
    def get_delay_minimum(self, synapse_info):
        """Get the minimum delay specified by the user in ms, or None if\
            unbounded.

        :param SynapseInformation synapse_info:
        :rtype: int or None
        """

    def get_delay_variance(self, delays, synapse_info):
        """ Get the variance of the delays.

        :param delays:
        :type delays: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
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
        """ Get the expected number of delays that will fall within min_delay
            and max_delay given given a float, RandomDistribution or list of
            delays.

        :param delays:
        :type delays: ~numpy.ndarray or pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
        :param int n_total_connections:
        :param int n_connections:
        :param float min_delay:
        :param float max_delay:
        :rtype: float
        """
        if isinstance(delays, RandomDistribution):
            prob_in_range = utility_calls.get_probability_within_range(
                delays, min_delay, max_delay)
            return int(math.ceil(utility_calls.get_probable_maximum_selected(
                n_total_connections, n_connections, prob_in_range)))
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
        elif hasattr(delays, "__getitem__"):
            n_delayed = sum([len([
                delay for delay in delays
                if min_delay <= delay <= max_delay])])
            if n_delayed == 0:
                return 0
            n_total = len(delays)
            prob_delayed = float(n_delayed) / float(n_total)
            return int(math.ceil(utility_calls.get_probable_maximum_selected(
                n_total_connections, n_connections, prob_delayed)))
        raise SpynnakerException("Unrecognised delay format")

    @abstractmethod
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, synapse_info, min_delay=None,
            max_delay=None):
        """ Get the maximum number of connections between those from any
            neuron in the pre vertex to the neurons in the post_vertex_slice,
            for connections with a delay between min_delay and max_delay
            (inclusive) if both specified (otherwise all connections).

        :param delays:
        :type delays: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param SynapseInformation synapse_info:
        :param min_delay:
        :type min_delay: int or None
        :param max_delay:
        :type max_delay: int or None
        :rtype: int
        """

    @abstractmethod
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        """ Get the maximum number of connections between those to any neuron
            in the post vertex from neurons in the pre vertex.

        :param SynapseInformation synapse_info:
        :rtype: int
        """

    def get_weight_mean(self, weights, synapse_info):
        """ Get the mean of the weights.

        :param weights:
        :type weights: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
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
        """ Get the maximum of the weights.

        :param weights:
        :type weights: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
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
        """ Get the maximum of the weights for this connection.

        :param SynapseInformation synapse_info:
        :rtype: float
        """

    def get_weight_variance(self, weights, synapse_info):
        """ Get the variance of the weights.

        :param weights:
        :type weights: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
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
        """ Check if a distance expression contains at least one term `d[x]`.
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
            raise Exception(
                "Weights or delays are distance-dependent but no space object"
                "was specified in projection {}-{}".format(
                    synapse_info.pre_population,
                    synapse_info.post_population))

        expand_distances = self._expand_distances(values)

        return self.__space.distances(
            synapse_info.pre_population.positions,
            synapse_info.post_population.positions,
            expand_distances)

    def _generate_random_values(
            self, values, n_connections, pre_vertex_slice, post_vertex_slice):
        """
        :param ~pyNN.random.NumpyRNG values:
        :param int n_connections:
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :rtype: ~numpy.ndarray
        """
        key = (id(pre_vertex_slice), id(post_vertex_slice), id(values))
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
            self, values, sources, targets, n_connections, connection_slices,
            pre_slice, post_slice, synapse_info):
        """
        :param values:
        :type values: ~pyNN.random.NumpyRNG or int or float or list(int) or
            list(float) or ~numpy.ndarray or str or callable
        :param int n_connections:
        :param list(slice) connection_slices:
        :param ~pacman.model.graphs.common.Slice pre_slice:
        :param ~pacman.model.graphs.common.Slice post_slice:
        :param SynapseInformation synapse_info:
        :rtype: ~numpy.ndarray
        """
        if isinstance(values, RandomDistribution):
            return self._generate_random_values(
                values, n_connections, pre_slice, post_slice)
        elif isinstance(values, str) or callable(values):
            if self.__space is None:
                raise SpynnakerException(
                    "No space object specified in projection {}-{}".format(
                        synapse_info.pre_population,
                        synapse_info.post_population))

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
            return numpy.concatenate([
                values[connection_slice]
                for connection_slice in connection_slices]).astype("float64")
        raise SpynnakerException("Unrecognised values format {} - what on "
                                 "earth are you giving me?".format(values))

    def _generate_weights(
            self, sources, targets, n_connections, connection_slices,
            pre_slice, post_slice, synapse_info):
        """ Generate weight values.

        :param int n_connections:
        :param list(slice) connection_slices:
        :param ~pacman.model.graphs.common.Slice pre_slice:
        :param ~pacman.model.graphs.common.Slice post_slice:
        :param SynapseInformation synapse_info:
        :rtype: ~numpy.ndarray
        """
        weights = self._generate_values(
            synapse_info.weights, sources, targets, n_connections,
            connection_slices, pre_slice, post_slice, synapse_info)
        if self.__safe:
            if not weights.size:
                warn_once(logger, "No connection in " + str(self))
            elif numpy.amin(weights) < 0 < numpy.amax(weights):
                raise SpynnakerException(
                    "Weights must be either all positive or all negative"
                    " in projection {}->{}".format(
                        synapse_info.pre_population.label,
                        synapse_info.post_population.label))
        return numpy.abs(weights)

    def _clip_delays(self, delays):
        """ Clip delay values, keeping track of how many have been clipped.

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
            self, sources, targets, n_connections, connection_slices,
            pre_slice, post_slice, synapse_info):
        """ Generate valid delay values.

        :param int n_connections:
        :param list(slice) connection_slices:
        :param ~pacman.model.graphs.common.Slice pre_slice:
        :param ~pacman.model.graphs.common.Slice post_slice:
        :param SynapseInformation synapse_info:
        :rtype: ~numpy.ndarray
        """
        delays = self._generate_values(
            synapse_info.delays, sources, targets, n_connections,
            connection_slices, pre_slice, post_slice, synapse_info)

        return self._clip_delays(delays)

    @abstractmethod
    def create_synaptic_block(
            self, pre_slices, post_slices, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        """ Create a synaptic block from the data.

        :param weights:
        :type weights: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
        :param delays:
        :type delays: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
        :param list(~pacman.model.graphs.common.Slice) pre_slices:
        :param list(~pacman.model.graphs.common.Slice) post_slices:
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param AbstractSynapseType synapse_type:
        :param SynapseInformation synapse_info:
        :returns:
            The synaptic matrix data to go to the machine, as a Numpy array
        :rtype: ~numpy.ndarray
        """

    _CLIPPED_MSG = (
        "The delays in the connector {} from {} to {} was clipped to {} a "
        "total of {} times.  This can be avoided by reducing the timestep "
        "or increasing the minimum delay to one timestep")

    def get_provenance_data(self, synapse_info):
        """
        :param SynapseInformation synapse_info:
        :rtype:
            iterable(~spinn_front_end_common.utilities.utility_objs.ProvenanceDataItem)
        """
        name = "connector_{}_{}_{}".format(
            synapse_info.pre_population.label,
            synapse_info.post_population.label, self.__class__.__name__)
        # Convert to native Python integer; provenance system assumption
        ncd = self.__n_clipped_delays.item()
        yield ProvenanceDataItem(
            [name, "Times_synaptic_delays_got_clipped"], ncd,
            report=(ncd > 0), message=self._CLIPPED_MSG.format(
                self.__class__.__name__, synapse_info.pre_population.label,
                synapse_info.post_population.label, self.__min_delay,
                ncd))

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
        """ The space object (may be updated after instantiation).

        :rtype: ~pyNN.space.Space or None
        """
        return self.__space

    @space.setter
    def space(self, new_value):
        """ Set the space object (allowed after instantiation).

        :param ~pyNN.space.Space new_value:
        """
        self.__space = new_value

    @property
    def synapse_info(self):
        """ The synapse_info object (may be updated after instantiation).

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

    def could_connect(
            self, synapse_info, src_machine_vertex, dest_machine_vertex):
        """
        Checks if a pre slice and a post slice could connect.

        Typically used to determine if a Machine Edge should be created by
        checking that at least one of the indexes in the pre slice could
        over time connect to at least one of the indexes in the post slice.

        .. note::
            This method should never return a false negative,
            but may return a false positives

        :param SynapseInformation synapse_info:
        :param ~pacman.model.graphs.machine.MachineVertex src_machine_vertexx:
        :param ~pacman.model.graphs.machine.MachineVertex dest_machine_vertex:
        :rtype: bool
        """
        # Unless we know for sure we must say they could connect
        return True

    def connect(self, projection):
        """ Apply this connector to a projection.

        .. warning::
            Do *not* call this! SpyNNaker does not work that way.

        :param ~spynnaker.pyNN.models.projection.Projection projection:
        :raises SpynnakerException: Always. Method not supported; profiled out.
        """
        raise SpynnakerException("Standard pyNN connect method not supported")

    @staticmethod
    def _roundsize(size, label):
        """ Ensures that the ``size`` is an integer. Approximate integers are\
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
            "Size of {} must be an int, received {}".format(label, size))

    def validate_connection(self, application_edge, synapse_info):
        """ Checks that the edge supports the connector.  By default this does
            nothing i.e. assumes the edge is OK, but can be overridden if the
            connector has rules that need to be checked.  Returns nothing; it
            is assumed that an Exception will be raised if anything is wrong.

        :param ApplicationEdge application_edge: The edge of the connection
        :param SynapseInformation synapse_info: The synaptic information
        """
        return
