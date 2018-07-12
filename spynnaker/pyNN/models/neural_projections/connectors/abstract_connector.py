from six import add_metaclass, string_types
from spinn_utilities.safe_eval import SafeEval
from spinn_front_end_common.utilities.utility_objs import ProvenanceDataItem
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spynnaker.pyNN.utilities import utility_calls
import logging
import numpy
import math
import re

# global objects
logger = logging.getLogger(__name__)
_expr_context = SafeEval(
    math, numpy, numpy.arccos, numpy.arcsin, numpy.arctan, numpy.arctan2,
    numpy.ceil, numpy.cos, numpy.cosh, numpy.exp, numpy.fabs, numpy.floor,
    numpy.fmod, numpy.hypot, numpy.ldexp, numpy.log, numpy.log10, numpy.modf,
    numpy.power, numpy.sin, numpy.sinh, numpy.sqrt, numpy.tan, numpy.tanh,
    numpy.maximum, numpy.minimum, e=numpy.e, pi=numpy.pi)


@add_metaclass(AbstractBase)
class AbstractConnector(object):
    """ Abstract class that all PyNN Connectors extend.
    """

    NUMPY_SYNAPSES_DTYPE = [("source", "uint32"), ("target", "uint16"),
                            ("weight", "float64"), ("delay", "float64"),
                            ("synapse_type", "uint8")]

    __slots__ = [
        "_delays",
        "_min_delay",
        "_pre_population",
        "_post_population",
        "_n_clipped_delays",
        "_n_post_neurons",
        "_n_pre_neurons",
        "_rng",
        "_safe",
        "_space",
        "_verbose",
        "_weights"]

    def __init__(self, safe=True, verbose=False):
        self._safe = safe
        self._space = None
        self._verbose = verbose

        self._pre_population = None
        self._post_population = None
        self._n_pre_neurons = None
        self._n_post_neurons = None
        self._rng = None

        self._n_clipped_delays = 0
        self._min_delay = 0
        self._weights = None
        self._delays = None

    def set_space(self, space):
        """ Set the space object (allowed after instantiation).

        :param space:
        :return:
        """
        self._space = space

    def _set_weights_and_delays(self, weights, delays, allow_lists):
        """ Set the weights and delays as needed.

        :param weights:
            May either be a float, a !RandomDistribution object, a list 1D\
            array with at least as many items as connections to be created,\
            or a distance dependence as per a d_expression. Units nA/uS.
        :param delays: -- as `weights`. If `None`, all synaptic\
            delays will be set to the global minimum delay. Units ms.
        :raises Exception: when not a standard interface of list, scalar,\
            or random number generator
        :raises NotImplementedError: when lists are not supported and entered
        """
        if self._weights is not None:
            logger.warning(
                'Weights were already set in '+str(self)+', possibly in '
                'another projection: currently this will overwrite the values '
                'in the previous projection. For now, set up a new connector.')
        if self._delays is not None:
            logger.warning(
                'Delays were already set in '+str(self)+', possibly in '
                'another projection: currently this will overwrite the values '
                'in the previous projection. For now, set up a new connector.')
        self._weights = weights
        self._delays = delays
        self._check_parameters(weights, delays, allow_lists)

    def set_weights_and_delays(self, weights, delays):
        self._set_weights_and_delays(weights, delays, allow_lists=False)

    def set_projection_information(
            self, pre_population, post_population, rng, machine_time_step):
        self._pre_population = pre_population
        self._post_population = post_population
        self._n_pre_neurons = pre_population.size
        self._n_post_neurons = post_population.size
        self._rng = rng
        if self._rng is None:
            self._rng = get_simulator().get_pynn_NumpyRNG()
        self._min_delay = machine_time_step / 1000.0

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

    def _get_delay_maximum(self, n_connections):
        """ Get the maximum delay given a float, RandomDistribution or list of\
            delays.
        """
        if get_simulator().is_a_pynn_random(self._delays):
            max_estimated_delay = utility_calls.get_maximum_probable_value(
                self._delays, n_connections)
            high = utility_calls.high(self._delays)
            if high is None:
                return max_estimated_delay

            # The maximum is the minimum of the possible maximums
            return min(max_estimated_delay, high)
        elif numpy.isscalar(self._delays):
            return self._delays
        elif hasattr(self._delays, "__getitem__"):
            return numpy.max(self._delays)
        raise Exception("Unrecognised delay format: {:s}".format(
            type(self._delays)))

    @abstractmethod
    def get_delay_maximum(self):
        """ Get the maximum delay specified by the user in ms, or None if\
            unbounded.
        """

    def get_delay_variance(self):
        """ Get the variance of the delays.
        """
        if get_simulator().is_a_pynn_random(self._delays):
            return utility_calls.get_variance(self._delays)
        elif numpy.isscalar(self._delays):
            return 0.0
        elif hasattr(self._delays, "__getitem__"):
            return numpy.var(self._delays)
        raise Exception("Unrecognised delay format")

    def _get_n_connections_from_pre_vertex_with_delay_maximum(
            self, n_total_connections, n_connections, min_delay, max_delay):
        """ Get the expected number of delays that will fall within min_delay\
            and max_delay given given a float, RandomDistribution or list of\
            delays.
        """
        # pylint: disable=too-many-arguments
        if get_simulator().is_a_pynn_random(self._delays):
            prob_in_range = utility_calls.get_probability_within_range(
                self._delays, min_delay, max_delay)
            return int(math.ceil(utility_calls.get_probable_maximum_selected(
                n_total_connections, n_connections, prob_in_range)))
        elif numpy.isscalar(self._delays):
            if min_delay <= self._delays <= max_delay:
                return int(math.ceil(n_connections))
            return 0
        elif hasattr(self._delays, "__getitem__"):
            n_delayed = sum([len([
                delay for delay in self._delays
                if min_delay <= delay <= max_delay])])
            if n_delayed == 0:
                return 0
            n_total = len(self._delays)
            prob_delayed = float(n_delayed) / float(n_total)
            return int(math.ceil(utility_calls.get_probable_maximum_selected(
                n_total_connections, n_connections, prob_delayed)))
        raise Exception("Unrecognised delay format")

    @abstractmethod
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, min_delay=None, max_delay=None):
        """ Get the maximum number of connections between those from any\
            neuron in the pre vertex to the neurons in the\
            post_vertex_slice, for connections with a delay between min_delay\
            and max_delay (inclusive) if both specified\
            (otherwise all connections).
        """
        # pylint: disable=too-many-arguments

    @abstractmethod
    def get_n_connections_to_post_vertex_maximum(self):
        """ Get the maximum number of connections between those to any neuron\
            in the post vertex from neurons in the pre vertex.
        """
        # pylint: disable=too-many-arguments

    def get_weight_mean(self):
        """ Get the mean of the weights.
        """
        if get_simulator().is_a_pynn_random(self._weights):
            return abs(utility_calls.get_mean(self._weights))
        elif numpy.isscalar(self._weights):
            return abs(self._weights)
        elif hasattr(self._weights, "__getitem__"):
            return numpy.mean(self._weights)
        raise Exception("Unrecognised weight format")

    def _get_weight_maximum(self, n_connections):
        """ Get the maximum of the weights.
        """
        if get_simulator().is_a_pynn_random(self._weights):
            mean_weight = utility_calls.get_mean(self._weights)
            if mean_weight < 0:
                min_weight = utility_calls.get_minimum_probable_value(
                    self._weights, n_connections)
                low = utility_calls.low(self._weights)
                if low is None:
                    return abs(min_weight)
                return abs(max(min_weight, low))
            else:
                max_weight = utility_calls.get_maximum_probable_value(
                    self._weights, n_connections)
                high = utility_calls.high(self._weights)
                if high is None:
                    return abs(max_weight)
                return abs(min(max_weight, high))

        elif numpy.isscalar(self._weights):
            return abs(self._weights)
        elif hasattr(self._weights, "__getitem__"):
            return numpy.amax(numpy.abs(self._weights))
        raise Exception("Unrecognised weight format")

    @abstractmethod
    def get_weight_maximum(self):
        """ Get the maximum of the weights for this connection.
        """
        # pylint: disable=too-many-arguments

    def get_weight_variance(self):
        """ Get the variance of the weights.
        """
        if get_simulator().is_a_pynn_random(self._weights):
            return utility_calls.get_variance(self._weights)
        elif numpy.isscalar(self._weights):
            return 0.0
        elif hasattr(self._weights, "__getitem__"):
            return numpy.var(self._weights)
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

    def _generate_values(self, values, n_connections, connection_slices):
        if get_simulator().is_a_pynn_random(values):
            if n_connections == 1:
                return numpy.array([values.next(n_connections)],
                                   dtype="float64")
            return values.next(n_connections)
        elif numpy.isscalar(values):
            return numpy.repeat([values], n_connections).astype("float64")
        elif hasattr(values, "__getitem__"):
            return numpy.concatenate([
                values[connection_slice]
                for connection_slice in connection_slices]).astype("float64")
        elif isinstance(values, string_types) or callable(values):
            if self._space is None:
                raise Exception(
                    "No space object specified in projection {}-{}".format(
                        self._pre_population, self._post_population))

            expand_distances = True
            if isinstance(values, string_types):
                expand_distances = self._expand_distances(values)

            d = self._space.distances(
                self._pre_population.positions,
                self._post_population.positions,
                expand_distances)

            if isinstance(values, string_types):
                return _expr_context.eval(values)
            return values(d)
        raise Exception("what on earth are you giving me?")

    def _generate_weights(self, values, n_connections, connection_slices):
        """ Generate weight values.
        """
        weights = self._generate_values(
            values, n_connections, connection_slices)
        if self._safe:
            if not weights.size:
                logger.warning("No connection in " + str(self))
            elif numpy.amin(weights) < 0 < numpy.amax(weights):
                raise Exception(
                    "Weights must be either all positive or all negative"
                    " in projection {}->{}".format(
                        self._pre_population.label,
                        self._post_population.label))
        return numpy.abs(weights)

    def _clip_delays(self, delays):
        """ Clip delay values, keeping track of how many have been clipped.
        """

        # count values that could be clipped
        self._n_clipped_delays = numpy.sum(delays < self._min_delay)

        # clip values
        if numpy.isscalar(delays):
            if delays < self._min_delay:
                delays = self._min_delay
        else:
            if delays.size:
                delays[delays < self._min_delay] = self._min_delay
        return delays

    def _generate_delays(self, values, n_connections, connection_slices):
        """ Generate valid delay values.
        """

        delays = self._generate_values(
            values, n_connections, connection_slices)

        return self._clip_delays(delays)

    @abstractmethod
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        """ Create a synaptic block from the data.
        """
        # pylint: disable=too-many-arguments

    def get_provenance_data(self):
        name = "{}_{}_{}".format(
            self._pre_population.label, self._post_population.label,
            self.__class__.__name__)
        return [ProvenanceDataItem(
            [name, "Times_synaptic_delays_got_clipped"],
            self._n_clipped_delays,
            report=self._n_clipped_delays > 0,
            message=(
                "The delays in the connector {} from {} to {} was clipped "
                "to {} a total of {} times.  This can be avoided by reducing "
                "the timestep or increasing the minimum delay to one "
                "timestep".format(
                    self.__class__.__name__, self._pre_population.label,
                    self._post_population.label, self._min_delay,
                    self._n_clipped_delays)))]

    @property
    def safe(self):
        return self._safe

    @safe.setter
    def safe(self, new_value):
        self._safe = new_value

    @property
    def space(self):
        return self._space

    @space.setter
    def space(self, new_value):
        self._space = new_value

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, new_value):
        self._verbose = new_value

    @property
    def pre_population(self):
        return self._pre_population

    @property
    def post_population(self):
        return self._post_population
