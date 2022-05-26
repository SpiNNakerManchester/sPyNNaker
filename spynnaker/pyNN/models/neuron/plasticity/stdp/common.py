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


def _get_last_non_zero_value(values):
    """ Get the last non-zero value (rescaled) from a LUT array
    """
    # Either the ultimate or penultimate value must be non-zero as generated
    # from the above function
    if values[-1] != 0:
        return values[-1] / STDP_FIXED_POINT_ONE
    return values[-2] / STDP_FIXED_POINT_ONE


def get_min_lut_value(
        exp_lut_array, time_step=None, max_stdp_spike_delta=None):
    """ Get the smallest non-zero value of an exponential lookup array,\
        or None if no such value

    :param numpy.ndarray exp_lut_array: The lookup array
    :param float time_step: The time step in milliseconds
    :param float max_stdp_spike_delta: The maximum expected difference between
        spike times in milliseconds
    :rtype: float
    """
    values = exp_lut_array.view("uint16")

    # If there isn't a time step and a limit
    if time_step is None or max_stdp_spike_delta is None:
        return _get_last_non_zero_value(values)

    # If there is a time step and limit, use it to work out which value
    pos = int(math.ceil(max_stdp_spike_delta / time_step)) + 1
    if pos >= len(values):
        return _get_last_non_zero_value(values)

    # Make sure we haven't just picked the last value which happens to be 0
    return _get_last_non_zero_value(values[:pos])
