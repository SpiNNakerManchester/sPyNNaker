from spinn_utilities.abstract_base import abstractproperty, AbstractBase
from six import add_metaclass
import numpy
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spynnaker.pyNN.models.neural_projections.connectors\
    import AbstractConnector
from data_specification.enums.data_type import DataType
from pyNN import __version__ as pyNNVersion, random
from distutils.version import StrictVersion
from enum import Enum

IS_PYNN_8 = StrictVersion(pyNNVersion) >= StrictVersion("0.8")

PARAM_TYPE_STATIC_ID = 0

PARAM_TYPE_BY_NAME = {
    "uniform": 1,
    "uniform_int": 1,
    "poisson": 2,
    "normal": 3,
    "normal_clipped": 4,
    "normal_clipped_to_boundary": 5,
    "exponential": 6
}


class ConnectorIDs(Enum):
    ONE_TO_ONE_CONNECTOR = 0
    ALL_TO_ALL_CONNECTOR = 1
    FIXED_PROBABILITY_CONNECTOR = 2


@add_metaclass(AbstractBase)
class AbstractGenerateConnectorOnMachine(AbstractConnector):
    """ Indicates that the connectivity can be generated on the machine
    """

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

    def _param_generator_params(self, values):
        if numpy.isscalar(values):
            return numpy.array(
                [round(values / DataType.S1615.scale)], dtype="uint32")

        if IS_PYNN_8 and get_simulator().is_a_pynn_random(values):
            parameters = random.available_distributions[values.name]
            values = [
                values.parameters.get(param, None) for param in parameters]
            values = [
                round(value / DataType.S1615.scale) for value in values
                if value is not None]
            return numpy.array(values, dtype="uint32")

        raise ValueError("Unexpected value {}".format(values))

    def _param_generator_params_size_in_bytes(self, values):
        if numpy.isscalar(values):
            return 4

        if IS_PYNN_8 and get_simulator().is_a_pynn_random(values):
            parameters = random.available_distributions[values.name]
            return len(parameters) * 4

        raise ValueError("Unexpected value {}".format(values))

    def _param_generator_id(self, values):
        if numpy.isscalar(values):
            return PARAM_TYPE_STATIC_ID

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

    @property
    def gen_weights_params(self):
        """ Get the parameters of the weight generator on the machine

        :rtype: numpy array of uint32
        """
        return self._param_generator_params(self._weights)

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

    @property
    def gen_delay_params(self):
        """ Get the parameters of the delay generator on the machine

        :rtype: numpy array of uint32
        """
        return self._param_generator_params(self._delays)

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

    @property
    def gen_connector_params(self):
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
