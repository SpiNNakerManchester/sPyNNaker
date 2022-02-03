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

from pyNN.random import available_distributions, RandomDistribution
from enum import Enum
import numpy
from spinn_utilities.abstract_base import abstractproperty, AbstractBase
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector)

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

PARAM_TYPE_KERNEL = 6


# Hashes of the connection generators supported by the synapse expander
class ConnectorIDs(Enum):
    ONE_TO_ONE_CONNECTOR = 0
    ALL_TO_ALL_CONNECTOR = 1
    FIXED_PROBABILITY_CONNECTOR = 2
    FIXED_TOTAL_NUMBER_CONNECTOR = 3
    FIXED_NUMBER_PRE_CONNECTOR = 4
    FIXED_NUMBER_POST_CONNECTOR = 5
    KERNEL_CONNECTOR = 6


class AbstractGenerateConnectorOnMachine(
        AbstractConnector, metaclass=AbstractBase):
    """ Indicates that the connectivity can be generated on the machine
    """

    __slots__ = [
        "__connector_seed"
    ]

    def __init__(self, safe=True, callback=None, verbose=False):
        """
        :param bool safe:
        :param callable callback: Ignored
        :param bool verbose:
        """
        super().__init__(safe=safe, callback=callback, verbose=verbose)
        self.__connector_seed = dict()

    def _generate_lists_on_machine(self, values):
        """ Checks if the connector should generate lists on machine rather\
            than trying to generate the connectivity data on host, based on\
            the types of the weights and/or delays

        :param values:
        :type values: int or ~pyNN.random.NumpyRNG
        :rtype: bool
        """
        # Strings (i.e. for distance-dependent weights/delays) not supported
        if isinstance(values, str):
            return False

        # Scalars are fine on the machine
        if numpy.isscalar(values):
            return True

        # Only certain types of random distributions are supported for\
        # generation on the machine
        if isinstance(values, RandomDistribution):
            return values.name in PARAM_TYPE_BY_NAME

        return False

    def _get_connector_seed(self, pre_vertex_slice, post_vertex_slice, rng):
        """ Get the seed of the connector for a given pre-post pairing

        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param ~pyNN.random.NumpyRNG rng:
        """
        key = (id(pre_vertex_slice), id(post_vertex_slice))
        if key not in self.__connector_seed:
            self.__connector_seed[key] = utility_calls.create_mars_kiss_seeds(
                rng)
        return self.__connector_seed[key]

    @staticmethod
    def _param_generator_params(values):
        """ Get the parameter generator parameters as a numpy array

        :param values:
        :type values: int or ~pyNN.random.NumpyRNG
        :rtype: ~numpy.ndarray
        """
        if numpy.isscalar(values):
            return numpy.array(
                [DataType.S1615.encode_as_int(values)],
                dtype=numpy.uint32)

        if isinstance(values, RandomDistribution):
            parameters = (
                values.parameters.get(param_name, None)
                for param_name in available_distributions[values.name])
            parameters = (
                DataType.S1615.max if param == numpy.inf
                else DataType.S1615.min if param == -numpy.inf else param
                for param in parameters if param is not None)
            params = [
                DataType.S1615.encode_as_int(param) for param in parameters]
            return numpy.array(params, dtype=numpy.uint32)

        raise ValueError("Unexpected value {}".format(values))

    @staticmethod
    def _param_generator_params_size_in_bytes(values):
        """ Get the size of the parameter generator parameters in bytes

        :param values:
        :type values: int or ~pyNN.random.NumpyRNG
        :rtype: int
        """
        if numpy.isscalar(values):
            return BYTES_PER_WORD

        if isinstance(values, RandomDistribution):
            parameters = available_distributions[values.name]
            return len(parameters) * BYTES_PER_WORD

        raise ValueError("Unexpected value {}".format(values))

    @staticmethod
    def _param_generator_id(values):
        """ Get the id of the parameter generator

        :param values:
        :type values: int or ~pyNN.random.NumpyRNG
        :rtype: int
        """
        if numpy.isscalar(values):
            return PARAM_TYPE_CONSTANT_ID

        if isinstance(values, RandomDistribution):
            return PARAM_TYPE_BY_NAME[values.name]

        raise ValueError("Unexpected value {}".format(values))

    def generate_on_machine(self, weights, delays):
        """ Determine if this instance can generate on the machine.

        Default implementation returns True if the weights and delays can\
        be generated on the machine

        :param weights:
        :type weights: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or
            float or list(int) or list(float)
        :param delays:
        :type delays: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or
            float or list(int) or list(float)
        :rtype: bool
        """
        return (self._generate_lists_on_machine(weights) and
                self._generate_lists_on_machine(delays))

    def gen_weights_id(self, weights):
        """ Get the id of the weight generator on the machine

        :param weights:
        :type weights: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or
            float or list(int) or list(float)
        :rtype: int
        """
        return self._param_generator_id(weights)

    def gen_weights_params(self, weights):
        """ Get the parameters of the weight generator on the machine

        :param weights:
        :type weights: ~pyNN.random.NumpyRNG or int or float
        :rtype: ~numpy.ndarray(~numpy.uint32)
        """
        return self._param_generator_params(weights)

    def gen_weight_params_size_in_bytes(self, weights):
        """ The size of the weight parameters in bytes

        :param weights:
        :type weights: ~pyNN.random.NumpyRNG or int or float
        :rtype: int
        """
        return self._param_generator_params_size_in_bytes(weights)

    def gen_delays_id(self, delays):
        """ Get the id of the delay generator on the machine

        :param delays:
        :type delays: ~pyNN.random.NumpyRNG or int or float
        :rtype: int
        """
        return self._param_generator_id(delays)

    def gen_delay_params(self, delays):
        """ Get the parameters of the delay generator on the machine

        :param delays:
        :type delays: ~pyNN.random.NumpyRNG or int or float
        :rtype: ~numpy.ndarray(~numpy.uint32)
        """
        return self._param_generator_params(delays)

    def gen_delay_params_size_in_bytes(self, delays):
        """ The size of the delay parameters in bytes

        :param delays:
        :type delays: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or
            float or list(int) or list(float)
        :rtype: int
        """
        return self._param_generator_params_size_in_bytes(delays)

    @abstractproperty
    def gen_connector_id(self):
        """ The ID of the connection generator on the machine.

        :rtype: int
        """

    def gen_connector_params(self):
        """ Get the parameters of the on machine generation.

        :rtype: ~numpy.ndarray(uint32)
        """
        # pylint: disable=unused-argument
        return numpy.zeros(0, dtype="uint32")

    @property
    def gen_connector_params_size_in_bytes(self):
        """ The size of the connector parameters in bytes.

        :rtype: int
        """
        return 0

    @staticmethod
    def _get_view_lo_hi(view):
        """ Get the range of neuron IDs covered by a view.

        :param ~spynnaker.pyNN.models.populations.PopulationView view:
        :rtype: tuple(int,int)
        """
        # Evil forward reference to subpackage implementation of type!
        indexes = view._indexes
        view_lo = indexes[0]
        view_hi = indexes[-1]
        return view_lo, view_hi
