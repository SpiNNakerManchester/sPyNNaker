from spinn_utilities.abstract_base import abstractproperty, AbstractBase
from six import add_metaclass
import numpy
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spynnaker.pyNN.models.neural_projections.connectors\
    import AbstractConnector
from data_specification.enums.data_type import DataType
from distutils.version import StrictVersion
from enum import Enum
import decimal

# Travis fix - when sPyNNaker is installed, you will likely always have
# PyNN installed as well, but sPyNNaker itself doesn't rely on PyNN
# explicitly as it tries to be version agnostic.  In this case, PyNN 0.7
# random doesn't give us enough information to load the data, so PyNN >= 0.8
# is required here...
try:
    from pyNN import __version__ as pyNNVersion, random
except ImportError:
    pyNNVersion = "0.7"

# Generation on host only works for PyNN >= 0.8
IS_PYNN_8 = StrictVersion(pyNNVersion) >= StrictVersion("0.8")

# Hash of the constant parameter generator
PARAM_TYPE_CONSTANT_ID = 0

# Hashes of the parameter generators supported by the synapse expander
PARAM_TYPE_BY_NAME = {
    "uniform": 1,
    "uniform_int": 1,
    "normal": 2,
    "normal_clipped": 3,
    "normal_clipped_to_boundary": 4,
    "exponential": 5
}


# Hashes of the connection generators supported by the synapse expander
class ConnectorIDs(Enum):
    ONE_TO_ONE_CONNECTOR = 0
    ALL_TO_ALL_CONNECTOR = 1
    FIXED_PROBABILITY_CONNECTOR = 2
    FIXED_TOTAL_NUMBER_CONNECTOR = 3


@add_metaclass(AbstractBase)
class AbstractGenerateConnectorOnMachine(AbstractConnector):
    """ Indicates that the connectivity can be generated on the machine
    """

    __slots__ = [
        "_delay_seed",
        "_weight_seed",
        "_connector_seed"
    ]

    def __init__(self, safe=True, verbose=False):
        AbstractConnector.__init__(self, safe=safe, verbose=verbose)
        self._delay_seed = dict()
        self._weight_seed = dict()
        self._connector_seed = dict()

    def _generate_lists_on_machine(self, values):
        """ Checks if the connector should generate lists on machine rather\
            than trying to generate the connectivity data on host, based on\
            the types of the weights and/or delays
        """

        # Scalars are fine on the machine
        if numpy.isscalar(values):
            return True

        # Only certain types of random distributions are supported for\
        # generation on the machine
        if IS_PYNN_8 and get_simulator().is_a_pynn_random(values):
            return values.name in PARAM_TYPE_BY_NAME

        return False

    def _get_connector_seed(self, pre_vertex_slice, post_vertex_slice, rng):
        """ Get the seed of the connector for a given pre-post pairing
        """
        key = (id(pre_vertex_slice), id(post_vertex_slice))
        if key not in self._connector_seed:
            self._connector_seed[key] = [
                int(i * 0xFFFFFFFF) for i in rng.next(n=4)]
        return self._connector_seed[key]

    def _generate_param_seed(
            self, pre_vertex_slice, post_vertex_slice, values, seeds):
        """ Get the seed of a parameter generator for a given pre-post pairing
        """
        if not get_simulator().is_a_pynn_random(values):
            return None
        key = (id(pre_vertex_slice), id(post_vertex_slice), id(values))
        if key not in seeds:
            seeds[key] = [int(i * 0xFFFFFFFF) for i in values.rng.next(n=4)]
        return seeds[key]

    def _param_generator_params(self, values, seed):
        """ Get the parameter generator parameters as a numpy array
        """
        if numpy.isscalar(values):
            return numpy.array(
                [round(decimal.Decimal(str(values)) * DataType.S1615.scale)],
                dtype="uint32")

        if IS_PYNN_8 and get_simulator().is_a_pynn_random(values):
            parameters = random.available_distributions[values.name]
            params = [
                values.parameters.get(param, None) for param in parameters]
            params = [
                DataType.S1615.max if param == numpy.inf
                else DataType.S1615.min if param == -numpy.inf else param
                for param in params if param is not None]
            params = [
                round(decimal.Decimal(str(param)) * DataType.S1615.scale)
                for param in params if param is not None]
            params.extend(seed)
            return numpy.array(params, dtype="uint32")

        raise ValueError("Unexpected value {}".format(values))

    def _param_generator_params_size_in_bytes(self, values):
        """ Get the size of the parameter generator parameters in bytes
        """
        if numpy.isscalar(values):
            return 4

        if IS_PYNN_8 and get_simulator().is_a_pynn_random(values):
            parameters = random.available_distributions[values.name]
            return (len(parameters) + 4) * 4

        raise ValueError("Unexpected value {}".format(values))

    def _param_generator_id(self, values):
        """ Get the id of the parameter generator
        """
        if numpy.isscalar(values):
            return PARAM_TYPE_CONSTANT_ID

        if IS_PYNN_8 and get_simulator().is_a_pynn_random(values):
            return PARAM_TYPE_BY_NAME[values.name]

        raise ValueError("Unexpected value {}".format(values))

    @property
    def generate_on_machine(self):
        """ Determine if this instance can generate on the machine.

        Default implementation returns True if the weights and delays can\
        be generated on the machine

        :rtype: bool
        """

        return (IS_PYNN_8 and
                self._generate_lists_on_machine(self._weights) and
                self._generate_lists_on_machine(self._delays))

    @property
    def gen_weights_id(self):
        """ Get the id of the weight generator on the machine

        :rtype: int
        """
        return self._param_generator_id(self._weights)

    def gen_weights_params(self, pre_vertex_slice, post_vertex_slice):
        """ Get the parameters of the weight generator on the machine

        :rtype: numpy array of uint32
        """
        seed = self._generate_param_seed(
            pre_vertex_slice, post_vertex_slice, self._weights,
            self._weight_seed)
        return self._param_generator_params(self._weights, seed)

    @property
    def gen_weight_params_size_in_bytes(self):
        """ The size of the weight parameters in bytes

        :rtype: int
        """
        return self._param_generator_params_size_in_bytes(self._weights)

    @property
    def gen_delays_id(self):
        """ Get the id of the delay generator on the machine

        :rtype: int
        """
        return self._param_generator_id(self._delays)

    def gen_delay_params(self, pre_vertex_slice, post_vertex_slice):
        """ Get the parameters of the delay generator on the machine

        :rtype: numpy array of uint32
        """
        seed = self._generate_param_seed(
            pre_vertex_slice, post_vertex_slice, self._delays,
            self._delay_seed)
        return self._param_generator_params(self._delays, seed)

    @property
    def gen_delay_params_size_in_bytes(self):
        """ The size of the delay parameters in bytes

        :rtype: int
        """
        return self._param_generator_params_size_in_bytes(self._delays)

    @abstractproperty
    def gen_connector_id(self):
        """ Get the id of the connection generator on the machine

        :rtype: int
        """

    def gen_connector_params(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        """ Get the parameters of the on machine generation.

        :rtype: numpy array of uint32
        """
        return numpy.zeros(0, dtype="uint32")

    @property
    def gen_connector_params_size_in_bytes(self):
        """ The size of the connector parameters in bytes.

        :rtype: int
        """
        return 0
