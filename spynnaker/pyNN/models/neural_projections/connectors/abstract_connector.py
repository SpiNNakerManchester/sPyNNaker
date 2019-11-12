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
from six import string_types, with_metaclass
from spinn_utilities.logger_utils import warn_once
from spinn_utilities.safe_eval import SafeEval
from spinn_front_end_common.utilities.utility_objs import ProvenanceDataItem
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spynnaker.pyNN.utilities import utility_calls

# global objects
logger = logging.getLogger(__name__)
_expr_context = SafeEval(
    math, numpy, numpy.arccos, numpy.arcsin, numpy.arctan, numpy.arctan2,
    numpy.ceil, numpy.cos, numpy.cosh, numpy.exp, numpy.fabs, numpy.floor,
    numpy.fmod, numpy.hypot, numpy.ldexp, numpy.log, numpy.log10, numpy.modf,
    numpy.power, numpy.sin, numpy.sinh, numpy.sqrt, numpy.tan, numpy.tanh,
    numpy.maximum, numpy.minimum, e=numpy.e, pi=numpy.pi)


class AbstractConnector(with_metaclass(AbstractBase, object)):
    """ Abstract class that all PyNN Connectors extend.
    """

    NUMPY_SYNAPSES_DTYPE = [("source", "uint32"), ("target", "uint16"),
                            ("weight", "float64"), ("delay", "float64"),
                            ("synapse_type", "uint8")]

    __slots__ = [
        "_delays",
        "__min_delay",
        "__n_clipped_delays",
        "_n_post_neurons",
        "_n_pre_neurons",
        "_rng",
        "__safe",
        "__space",
        "__verbose",
        "_weights",
        "__param_seeds"]

    def __init__(self, safe=True, callback=None, verbose=False, rng=None):
        if callback is not None:
            warn_once(logger, "sPyNNaker ignores connector callbacks.")
        self.__safe = safe
        self.__space = None
        self.__verbose = verbose

        # something needs to be done about this?
        self._rng = rng

        self.__n_clipped_delays = 0
        self.__min_delay = 0
        self.__param_seeds = dict()

    def set_space(self, space):
        """ Set the space object (allowed after instantiation).

        :param space:
        :return:
        """
        self.__space = space

    def set_projection_information(self, machine_time_step, synapse_info):
        self._rng = (self._rng or get_simulator().get_pynn_NumpyRNG()())
        self.__min_delay = machine_time_step / 1000.0

    def _check_parameter(self, values, name, allow_lists):
        """ Check that the types of the values is supported.
        """
        if (not numpy.isscalar(values) and
                not (get_simulator().is_a_pynn_random(values)) and
                not hasattr(values, "__getitem__")):
            raise Exception("Parameter {} format unsupported".format(name))
        if not allow_lists and hasattr(values, "__getitem__"):
            raise NotImplementedError(
                "Lists of {} are not supported by the implementation of {} on "
                "this platform".format(name, self.__class__))

    def _check_parameters(self, weights, delays, allow_lists=False):
        """ Check the types of the weights and delays are supported; lists can\
            be disallowed if desired.
        """
        self._check_parameter(weights, "weights", allow_lists)
        self._check_parameter(delays, "delays", allow_lists)

    def _get_delay_maximum(self, delays, n_connections):
        """ Get the maximum delay given a float, RandomDistribution or list of\
            delays.
        """
        if get_simulator().is_a_pynn_random(delays):
            max_estimated_delay = utility_calls.get_maximum_probable_value(
                delays, n_connections)
            high = utility_calls.high(delays)
            if high is None:
                return max_estimated_delay

            # The maximum is the minimum of the possible maximums
            return min(max_estimated_delay, high)
        elif numpy.isscalar(delays):
            return delays
        elif hasattr(delays, "__getitem__"):
            return numpy.max(delays)
        raise Exception("Unrecognised delay format: {:s}".format(
            type(delays)))

    @abstractmethod
    def get_delay_maximum(self, synapse_info):
        """ Get the maximum delay specified by the user in ms, or None if\
            unbounded.
        """

    def get_delay_variance(self, delays):
        """ Get the variance of the delays.
        """
        if get_simulator().is_a_pynn_random(delays):
            return utility_calls.get_variance(delays)
        elif numpy.isscalar(delays):
            return 0.0
        elif hasattr(delays, "__getitem__"):
            return numpy.var(delays)
        raise Exception("Unrecognised delay format")

    def _get_n_connections_from_pre_vertex_with_delay_maximum(
            self, delays, n_total_connections, n_connections,
            min_delay, max_delay):
        """ Get the expected number of delays that will fall within min_delay\
            and max_delay given given a float, RandomDistribution or list of\
            delays.
        """
        # pylint: disable=too-many-arguments
        if get_simulator().is_a_pynn_random(delays):
            prob_in_range = utility_calls.get_probability_within_range(
                delays, min_delay, max_delay)
            return int(math.ceil(utility_calls.get_probable_maximum_selected(
                n_total_connections, n_connections, prob_in_range)))
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
        raise Exception("Unrecognised delay format")

    @abstractmethod
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, synapse_info, min_delay=None,
            max_delay=None):
        """ Get the maximum number of connections between those from any\
            neuron in the pre vertex to the neurons in the\
            post_vertex_slice, for connections with a delay between min_delay\
            and max_delay (inclusive) if both specified\
            (otherwise all connections).
        """
        # pylint: disable=too-many-arguments

    @abstractmethod
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        """ Get the maximum number of connections between those to any neuron\
            in the post vertex from neurons in the pre vertex.
        """
        # pylint: disable=too-many-arguments

    def get_weight_mean(self, weights):
        """ Get the mean of the weights.
        """
        if get_simulator().is_a_pynn_random(weights):
            return abs(utility_calls.get_mean(weights))
        elif numpy.isscalar(weights):
            return abs(weights)
        elif hasattr(weights, "__getitem__"):
            return numpy.mean(weights)
        raise Exception("Unrecognised weight format")

    def _get_weight_maximum(self, weights, n_connections):
        """ Get the maximum of the weights.
        """
        if get_simulator().is_a_pynn_random(weights):
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

        elif numpy.isscalar(weights):
            return abs(weights)
        elif hasattr(weights, "__getitem__"):
            return numpy.amax(numpy.abs(weights))
        raise Exception("Unrecognised weight format")

    @abstractmethod
    def get_weight_maximum(self, synapse_info):
        """ Get the maximum of the weights for this connection.
        """
        # pylint: disable=too-many-arguments

    def get_weight_variance(self, weights):
        """ Get the variance of the weights.
        """
        if get_simulator().is_a_pynn_random(weights):
            return utility_calls.get_variance(weights)
        elif numpy.isscalar(weights):
            return 0.0
        elif hasattr(weights, "__getitem__"):
            return numpy.var(weights)
        raise Exception("Unrecognised weight format")

    def _expand_distances(self, d_expression):
        """ Check if a distance expression contains at least one term `d[x]`.\
            If yes, then the distances are expanded to distances in the\
            separate coordinates rather than the overall distance over all\
            coordinates, and we assume the user has specified an expression\
            such as `d[0] + d[2]`.
        """
        regexpr = re.compile(r'.*d\[\d*\].*')
        return regexpr.match(d_expression)

    def _generate_random_values(
            self, values, n_connections, pre_vertex_slice, post_vertex_slice):
        key = (id(pre_vertex_slice), id(post_vertex_slice), id(values))
        seed = self.__param_seeds.get(key, None)
        if seed is None:
            seed = int(values.rng.next() * 0x7FFFFFFF)
            self.__param_seeds[key] = seed
        new_rng = get_simulator().get_pynn_NumpyRNG()(seed)
        copy_rd = get_simulator().get_random_distribution()(
            values.name, parameters_pos=None, rng=new_rng,
            **values.parameters)
        if n_connections == 1:
            return numpy.array([copy_rd.next(1)], dtype="float64")
        return copy_rd.next(n_connections)

    def _generate_values(self, values, n_connections, connection_slices,
                         pre_slice, post_slice, synapse_info):
        if get_simulator().is_a_pynn_random(values):
            return self._generate_random_values(
                values, n_connections, pre_slice, post_slice)
        elif numpy.isscalar(values):
            return numpy.repeat([values], n_connections).astype("float64")
        elif hasattr(values, "__getitem__"):
            return numpy.concatenate([
                values[connection_slice]
                for connection_slice in connection_slices]).astype("float64")
        elif isinstance(values, string_types) or callable(values):
            if self.__space is None:
                raise Exception(
                    "No space object specified in projection {}-{}".format(
                        synapse_info.pre_population,
                        synapse_info.post_population))

            expand_distances = True
            if isinstance(values, string_types):
                expand_distances = self._expand_distances(values)

            d = self.__space.distances(
                synapse_info.pre_population.positions,
                synapse_info.post_population.positions,
                expand_distances)

            if isinstance(values, string_types):
                return _expr_context.eval(values)
            return values(d)
        raise Exception("what on earth are you giving me?")

    def _generate_weights(self, n_connections, connection_slices,
                          pre_slice, post_slice, synapse_info):
        """ Generate weight values.
        """
        weights = self._generate_values(
            synapse_info.weights, n_connections, connection_slices, pre_slice,
            post_slice, synapse_info)
        if self.__safe:
            if not weights.size:
                warn_once(logger, "No connection in " + str(self))
            elif numpy.amin(weights) < 0 < numpy.amax(weights):
                raise Exception(
                    "Weights must be either all positive or all negative"
                    " in projection {}->{}".format(
                        synapse_info.pre_population.label,
                        synapse_info.post_population.label))
        return numpy.abs(weights)

    def _clip_delays(self, delays):
        """ Clip delay values, keeping track of how many have been clipped.
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

    def _generate_delays(self, n_connections, connection_slices,
                         pre_slice, post_slice, synapse_info):
        """ Generate valid delay values.
        """

        delays = self._generate_values(
            synapse_info.delays, n_connections, connection_slices, pre_slice,
            post_slice, synapse_info)

        return self._clip_delays(delays)

    @abstractmethod
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        """ Create a synaptic block from the data.
        """
        # pylint: disable=too-many-arguments

    def get_provenance_data(self, synapse_info):
        name = "{}_{}_{}".format(
            synapse_info.pre_population.label,
            synapse_info.post_population.label, self.__class__.__name__)
        return [ProvenanceDataItem(
            [name, "Times_synaptic_delays_got_clipped"],
            self.__n_clipped_delays,
            report=self.__n_clipped_delays > 0,
            message=(
                "The delays in the connector {} from {} to {} was clipped "
                "to {} a total of {} times.  This can be avoided by reducing "
                "the timestep or increasing the minimum delay to one "
                "timestep".format(
                    self.__class__.__name__, synapse_info.pre_population.label,
                    synapse_info.post_population.label, self.__min_delay,
                    self.__n_clipped_delays)))]

    @property
    def safe(self):
        return self.__safe

    @safe.setter
    def safe(self, new_value):
        self.__safe = new_value

    @property
    def space(self):
        return self.__space

    @space.setter
    def space(self, new_value):
        self.__space = new_value

    @property
    def verbose(self):
        return self.__verbose

    @verbose.setter
    def verbose(self, new_value):
        self.__verbose = new_value

    def use_direct_matrix(self, synapse_info):
        return False
