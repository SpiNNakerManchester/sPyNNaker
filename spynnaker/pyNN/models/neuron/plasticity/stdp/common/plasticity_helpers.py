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

import math
import logging
import numpy

logger = logging.getLogger(__name__)
# Default value of fixed-point one for STDP
STDP_FIXED_POINT_ONE = (1 << 11)


def float_to_fixed(value, fixed_point_one):
    return int(round(float(value) * float(fixed_point_one)))


def get_exp_lut_values(
        time_step, time_constant, shift=0,
        fixed_point_one=STDP_FIXED_POINT_ONE, size=None):
    # Calculate time constant reciprocal
    time_constant_reciprocal = time_step / float(time_constant)

    # Generate LUT
    last_value = 1.0
    index = 0
    values = list()
    while last_value > 0.0 and (size is None or len(values) < size):

        # Apply shift to get time from index
        time = (index << shift)
        index += 1

        # Multiply by time constant and calculate negative exponential
        value = float(time) * time_constant_reciprocal
        exp_float = math.exp(-value)

        # Convert to fixed-point and write to spec
        last_value = float_to_fixed(exp_float, fixed_point_one)
        if last_value > 0.0:
            values.append(last_value)
    if size is not None and size > len(values):
        values.extend([0] * (size - len(values)))
    return values


def get_exp_lut_array(
        time_step, time_constant, shift=0,
        fixed_point_one=STDP_FIXED_POINT_ONE, size=None):
    values = get_exp_lut_values(
        time_step, time_constant, shift, fixed_point_one, size)
    values_size = len(values)
    if len(values) % 2 != 0:
        values.append(0)
    return numpy.concatenate(
        ([values_size, shift], values)).astype("uint16").view("uint32")
