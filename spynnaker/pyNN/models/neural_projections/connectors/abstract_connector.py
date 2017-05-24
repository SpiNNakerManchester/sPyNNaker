from six import add_metaclass
from spinn_utilities.safe_eval import SafeEval
from spinn_front_end_common.utilities.utility_objs\
    .provenance_data_item import ProvenanceDataItem
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spynnaker.pyNN.utilities import globals_variables
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
    """ Abstract class which PyNN Connectors extend
    """

    NUMPY_SYNAPSES_DTYPE = [("source", "uint32"), ("target", "uint16"),
                            ("weight", "float64"), ("delay", "float64"),
                            ("synapse_type", "uint8")]

    __slots__ = ()

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
        """ allows setting of the space object after instantiation

        :param space:
        :return:
        """
        self._space = space

    def set_weights_and_delays(self, weights, delays):
        """ sets the weights and delays as needed

        :param `float` weights:
            may either be a float, a !RandomDistribution object, a list\
            1D array with at least as many items as connections to be\
            created, or a distance dependence as per a d_expression. Units nA.
        :param `float` delays:  -- as `weights`. If `None`, all synaptic \
            delays will be set to the global minimum delay.
        :raises Exception: when not a standard interface of list, scaler, \
            or random number generator
        :raises NotImplementedError: when lists are not supported and entered
        """
        self._weights = weights
        self._delays = delays
        self._check_parameters(weights, delays)

    def set_projection_information(
            self, pre_population, post_population, rng, machine_time_step):
        self._pre_population = pre_population
        self._post_population = post_population
        self._n_pre_neurons = pre_population.size
        self._n_post_neurons = post_population.size
        self._rng = rng
        if self._rng is None:
            self._rng = globals_variables.get_simulator().get_pynn_NumpyRNG()
        self._min_delay = machine_time_step / 1000.0

    def _check_parameter(self, values, name, allow_lists):
        """ Check that the types of the values is supported
        """
        if (not numpy.isscalar(values) and
                not (globals_variables.get_simulator().
                     is_a_pynn_random(values)) and
                not hasattr(values, "__getitem__")):
            raise Exception("Parameter {} format unsupported".format(name))
        if not allow_lists and hasattr(values, "__getitem__"):
            raise NotImplementedError(
                "Lists of {} are not supported the implementation of"
                " {} on this platform".format(self.__class__))

    def _check_parameters(self, weights, delays, allow_lists=False):
        """ Check the types of the weights and delays are supported; lists can\
            be disallowed if desired
        """
        self._check_parameter(weights, "weights", allow_lists)
        self._check_parameter(delays, "delays", allow_lists)

    @staticmethod
    def _get_delay_maximum(delays, n_connections):
        """ Get the maximum delay given a float, RandomDistribution or list of\
            delays
        """
        if globals_variables.get_simulator().is_a_pynn_random(delays):
            max_estimated_delay = utility_calls.get_maximum_probable_value(
                delays, n_connections)
            if hasattr(delays, "boundaries"):
                if delays.boundaries is not None:
                    return min(max(delays.boundaries), max_estimated_delay)
            elif isinstance(delays.parameters, dict):
                if "max" in delays.parameters:
                    return delays.parameters['max']

            return max_estimated_delay
        elif numpy.isscalar(delays):
            return delays
        elif hasattr(delays, "__getitem__"):
            return max(delays)
        raise Exception("Unrecognised delay format")

    @abstractmethod
    def get_delay_maximum(self):
        """ Get the maximum delay specified by the user in ms, or None if\
            unbounded
        """

    @staticmethod
    def _get_delay_variance(delays, connection_slices):
        """ Get the variance of the delays
        """
        if globals_variables.get_simulator().is_a_pynn_random(delays):
            return utility_calls.get_variance(delays)
        elif numpy.isscalar(delays):
            return 0.0
        elif hasattr(delays, "__getitem__"):
            return numpy.var([
                delays[connection_slice]
                for connection_slice in connection_slices])
        raise Exception("Unrecognised delay format")

    @abstractmethod
    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        """ Get the variance of the delays for this connection
        """

    @staticmethod
    def _get_n_connections_from_pre_vertex_with_delay_maximum(
            delays, n_total_connections, n_connections, connection_slices,
            min_delay, max_delay):
        """ Gets the expected number of delays that will fall within min_delay\
            and max_delay given given a float, RandomDistribution or list of\
            delays
        """
        if globals_variables.get_simulator().is_a_pynn_random(delays):
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
                delay for delay in delays[connection_slice]
                if min_delay <= delay <= max_delay])
                for connection_slice in connection_slices])
            n_total = sum([
                len(delays[connection_slice])
                for connection_slice in connection_slices])
            prob_delayed = float(n_delayed) / float(n_total)
            return int(math.ceil(utility_calls.get_probable_maximum_selected(
                n_total_connections, n_delayed, prob_delayed)))
        raise Exception("Unrecognised delay format")

    @abstractmethod
    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        """ Get the maximum number of connections between those from each of\
            the neurons in the pre_vertex_slice to neurons in the\
            post_vertex_slice, for connections with a delay between min_delay\
            and max_delay (inclusive) if both specified\
            (otherwise all connections)
        """

    @abstractmethod
    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        """ Get the maximum number of connections between those to each of the\
            neurons in the post_vertex_slice from neurons in the\
            pre_vertex_slice
        """

    @staticmethod
    def _get_weight_mean(weights, connection_slices):
        """ Get the mean of the weights
        """
        if globals_variables.get_simulator().is_a_pynn_random(weights):
            return abs(utility_calls.get_mean(weights))
        elif numpy.isscalar(weights):
            return abs(weights)
        elif hasattr(weights, "__getitem__"):
            return numpy.mean([
                numpy.abs(weights[connection_slice])
                for connection_slice in connection_slices])
        raise Exception("Unrecognised weight format")

    @abstractmethod
    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        """ Get the mean of the weights for this connection
        """

    @staticmethod
    def _get_weight_maximum(weights, n_connections, connection_slices):
        """ Get the maximum of the weights
        """
        if globals_variables.get_simulator().is_a_pynn_random(weights):
            mean_weight = utility_calls.get_mean(weights)
            if mean_weight < 0:
                min_weight = utility_calls.get_minimum_probable_value(
                    weights, n_connections)
                if weights.boundaries is not None:
                    return abs(max(min_weight, min(weights.boundaries)))
                return abs(min_weight)
            else:
                max_weight = utility_calls.get_maximum_probable_value(
                    weights, n_connections)
                if weights.boundaries is not None:
                    return abs(min(max_weight, max(weights.boundaries)))
                return abs(max_weight)

        elif numpy.isscalar(weights):
            return abs(weights)
        elif hasattr(weights, "__getitem__"):
            return numpy.amax([
                numpy.abs(weights[connection_slice])
                for connection_slice in connection_slices])
        raise Exception("Unrecognised weight format")

    @abstractmethod
    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        """ Get the maximum of the weights for this connection
        """

    @staticmethod
    def _get_weight_variance(weights, connection_slices):
        """ Get the variance of the weights
        """
        if globals_variables.get_simulator().is_a_pynn_random(weights):
            return utility_calls.get_variance(weights)
        elif numpy.isscalar(weights):
            return 0.0
        elif hasattr(weights, "__getitem__"):
            return numpy.var([
                numpy.abs(weights[connection_slice])
                for connection_slice in connection_slices])
        raise Exception("Unrecognised weight format")

    @abstractmethod
    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):
        """ Get the variance of the weights for this connection
        """

    def _expand_distances(self, d_expression):
        """ Check if a distance expression contains at least one term d[x]. \
            If yes, then the distances are expanded to distances in the\
            separate coordinates rather than the overall distance over all\
            coordinates, and we assume the user has specified an expression\
            such as d[0] + d[2].
        """
        regexpr = re.compile(r'.*d\[\d*\].*')
        if regexpr.match(d_expression):
            return True
        return False

    def _generate_values(self, values, n_connections, connection_slices):
        if globals_variables.get_simulator().is_a_pynn_random(values):
            if n_connections == 1:
                return numpy.array([values.next(n_connections)])
            return values.next(n_connections)
        elif numpy.isscalar(values):
            return numpy.repeat([values], n_connections)
        elif hasattr(values, "__getitem__"):
            return numpy.concatenate([
                values[connection_slice]
                for connection_slice in connection_slices])
        elif isinstance(values, basestring) or callable(values):
            if self._space is None:
                raise Exception(
                    "No space object specified in projection {}-{}".format(
                        self._pre_population, self._post_population))

            expand_distances = True
            if isinstance(values, basestring):
                expand_distances = self._expand_distances(values)

            d = self._space.distances(
                self._pre_population.positions,
                self._post_population.positions,
                expand_distances)

            if isinstance(values, basestring):
                return _expr_context.eval(values)
            return values(d)

    def _generate_weights(self, values, n_connections, connection_slices):
        """ Generate weight values
        """
        weights = self._generate_values(
            values, n_connections, connection_slices)
        if self._safe:
            if len(weights) == 0:
                logger.warning("No connection in " + str(self))
            elif numpy.amin(weights) < 0 < numpy.amax(weights):
                raise Exception(
                    "Weights must be either all positive or all negative"
                    " in projection {}->{}".format(
                        self._pre_population.label,
                        self._post_population.label))
        return numpy.abs(weights)

    def _clip_delays(self, delays):
        """ Clip delay values, keeping track of how many have been clipped
        """

        # count values that could be clipped
        self._n_clipped_delays = numpy.sum(delays < self._min_delay)

        # clip values
        if numpy.isscalar(delays):
            if delays < self._min_delay:
                delays = self._min_delay
        else:
            if delays.size > 0:
                delays[delays < self._min_delay] = self._min_delay
        return delays

    def _generate_delays(self, values, n_connections, connection_slices):
        """ Generate valid delay values
        """
        delays = self._generate_values(
            values, n_connections, connection_slices)

        return self._clip_delays(delays)

    def _generate_lists_on_host(self, values):
        """ Checks if the connector should generate lists on host rather than\
            trying to generate the connectivity data on the machine, based on\
            the types of the weights and/or delays
        """

        # Scalars are fine on the machine
        if numpy.isscalar(values):
            return True

        # Only certain types of random distributions are supported for\
        # generation on the machine
        if globals_variables.get_simulator().is_a_pynn_random(values):
            return values.name in (
                "uniform", "uniform_int", "poisson", "normal", "exponential")

        return False

    @abstractmethod
    def generate_on_machine(self):
        """ Determines if the connector generation is supported on the machine\
            or if the connector must be generated on the host
        """

    @abstractmethod
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        """ Create a synaptic block from the data
        """

    def get_provenance_data(self):
        data_items = list()
        name = "{}_{}_{}".format(
            self._pre_population.label, self._post_population.label,
            self.__class__.__name__)
        data_items.append(ProvenanceDataItem(
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
                    self._n_clipped_delays))))
        return data_items

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
