# Copyright (c) 2014-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
import numpy

# Default value of fixed-point one for STDP
STDP_FIXED_POINT_ONE = (1 << 11)


def float_to_fixed(value):
    """
    :param float value:
    :rtype: int
    """
    return int(round(float(value) * STDP_FIXED_POINT_ONE))


def get_exp_lut_array(time_step, time_constant, shift=0):
    """
    :param int time_step:
    :param float time_constant:
    :param int shift:
    :rtype: ~numpy.ndarray
    """
    # Compute the actual exponential decay parameter
    # NB: lambda is a reserved word in Python
    l_ambda = time_step / float(time_constant)

    # Compute the size of the array, which must be a multiple of 2
    size = math.log(STDP_FIXED_POINT_ONE) / l_ambda
    size, extra = divmod(size / (1 << shift), 2)
    size = ((int(size) + (extra > 0)) * 2)

    # Fill out the values in the array
    a = numpy.exp((numpy.arange(size) << shift) * -l_ambda)
    a = numpy.floor(a * STDP_FIXED_POINT_ONE)

    # Concatenate with the header
    header = numpy.array([len(a), shift], dtype="uint16")
    return numpy.concatenate((header, a.astype("uint16"))).view("uint32")
