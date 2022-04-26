# Copyright (c) 2022 The University of Manchester
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
import numpy
from data_specification.enums import DataType
from pyNN.random import RandomDistribution, available_distributions
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD


#: The generator param type for each data type
_GENERATOR_TYPES = {
    DataType.S1615: 0,
    DataType.UINT32: 1,
    DataType.INT32: 2,
    DataType.U032: 3
}


def get_generator_type(data_type):
    if data_type in _GENERATOR_TYPES:
        return _GENERATOR_TYPES[data_type]
    raise Exception(f"Ungeneratable type {data_type}")


def type_has_generator(data_type):
    return data_type in _GENERATOR_TYPES


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


def param_generator_id(value):
    # Scalars are fine on the machine
    if numpy.isscalar(value):
        return PARAM_TYPE_CONSTANT_ID

    # Only certain types of random distributions are supported for\
    # generation on the machine
    if isinstance(value, RandomDistribution):
        if value.name in PARAM_TYPE_BY_NAME:
            return PARAM_TYPE_BY_NAME[value.name]

    raise Exception(f"Ungeneratable parameter {value}")


def is_param_generatable(value):
    if isinstance(value, str):
        return False
    if numpy.isscalar(value):
        return True
    return (isinstance(value, RandomDistribution) and
            value.name in PARAM_TYPE_BY_NAME)


def param_generator_params(values):
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


#: At most, there are 4 words as param generator parameters
MAX_PARAMS_BYTES = 4 * BYTES_PER_WORD


def param_generator_params_size_in_bytes(values):
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