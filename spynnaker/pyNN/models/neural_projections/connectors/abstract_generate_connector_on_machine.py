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
from six import with_metaclass
from spinn_utilities.abstract_base import abstractproperty, AbstractBase
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
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


class AbstractGenerateConnectorOnMachine(with_metaclass(
        AbstractBase, AbstractConnector)):
    """ Indicates that the connectivity can be generated on the machine
    """

    __slots__ = [
        "__delay_seed",
        "__weight_seed",
        "__connector_seed"
    ]

    def __init__(self, safe=True, callback=None, verbose=False):
        AbstractConnector.__init__(
            self, safe=safe, callback=callback, verbose=verbose)
        self.__delay_seed = dict()
        self.__weight_seed = dict()
        self.__connector_seed = dict()

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
        if isinstance(values, RandomDistribution):
            return values.name in PARAM_TYPE_BY_NAME

        return False

    def _get_connector_seed(self, pre_vertex_slice, post_vertex_slice, rng):
        """ Get the seed of the connector for a given pre-post pairing
        """
        key = (id(pre_vertex_slice), id(post_vertex_slice))
        if key not in self.__connector_seed:
            self.__connector_seed[key] = [
                int(i * 0xFFFFFFFF) for i in rng.next(n=4)]
        return self.__connector_seed[key]

    @staticmethod
    def _generate_param_seed(
            pre_vertex_slice, post_vertex_slice, values, seeds):
        """ Get the seed of a parameter generator for a given pre-post pairing
        """
        if not isinstance(values, RandomDistribution):
            return None
        key = (id(pre_vertex_slice), id(post_vertex_slice), id(values))
        if key not in seeds:
            seeds[key] = [int(i * 0xFFFFFFFF) for i in values.rng.next(n=4)]
        return seeds[key]

    @staticmethod
    def _param_generator_params(values, seed):
        """ Get the parameter generator parameters as a numpy array
        """
        if numpy.isscalar(values):
            return numpy.array(
                [DataType.S1615.encode_as_int(values)],
                dtype="uint32")

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
            params.extend(seed)
            return numpy.array(params, dtype="uint32")

        raise ValueError("Unexpected value {}".format(values))

    @staticmethod
    def _param_generator_params_size_in_bytes(values):
        """ Get the size of the parameter generator parameters in bytes
        """
        if numpy.isscalar(values):
            return BYTES_PER_WORD

        if isinstance(values, RandomDistribution):
            parameters = available_distributions[values.name]
            return (len(parameters) + 4) * BYTES_PER_WORD

        raise ValueError("Unexpected value {}".format(values))

    @staticmethod
    def _param_generator_id(values):
        """ Get the id of the parameter generator
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

        :rtype: bool
        """

        return (self._generate_lists_on_machine(weights) and
                self._generate_lists_on_machine(delays))

    def gen_weights_id(self, weights):
        """ Get the id of the weight generator on the machine

        :rtype: int
        """
        return self._param_generator_id(weights)

    def gen_weights_params(self, weights, pre_vertex_slice, post_vertex_slice):
        """ Get the parameters of the weight generator on the machine

        :rtype: numpy array of uint32
        """
        seed = self._generate_param_seed(
            pre_vertex_slice, post_vertex_slice, weights,
            self.__weight_seed)
        return self._param_generator_params(weights, seed)

    def gen_weight_params_size_in_bytes(self, weights):
        """ The size of the weight parameters in bytes

        :rtype: int
        """
        return self._param_generator_params_size_in_bytes(weights)

    def gen_delays_id(self, delays):
        """ Get the id of the delay generator on the machine

        :rtype: int
        """
        return self._param_generator_id(delays)

    def gen_delay_params(self, delays, pre_vertex_slice, post_vertex_slice):
        """ Get the parameters of the delay generator on the machine

        :rtype: numpy array of uint32
        """
        seed = self._generate_param_seed(
            pre_vertex_slice, post_vertex_slice, delays,
            self.__delay_seed)
        return self._param_generator_params(delays, seed)

    def gen_delay_params_size_in_bytes(self, delays):
        """ The size of the delay parameters in bytes

        :rtype: int
        """
        return self._param_generator_params_size_in_bytes(delays)

    @abstractproperty
    def gen_connector_id(self):
        """ Get the id of the connection generator on the machine

        :rtype: int
        """

    def gen_connector_params(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
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
