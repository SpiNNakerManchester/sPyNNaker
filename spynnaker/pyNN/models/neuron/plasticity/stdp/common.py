# Copyright (c) 2014 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
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


def write_pfpc_lut(spec, peak_time, lut_size, shift, time_probe,
                   kernel_scaling=1.0):
    sin_pwr = 20

    # Calculate required time constant
    time_constant = peak_time / math.atan(sin_pwr)
    inv_tau = (1.0 / float(time_constant))  # * (machine_time_step / 1000.0)

    # calculate time of peak (from differentiating kernel and setting to zero)
    # kernel_peak_time = math.atan(20) / inv_tau

    # evaluate peak value of kernel to normalise LUT
    kernel_peak_value = (math.exp(-peak_time * inv_tau) *
                         math.sin(peak_time * inv_tau) ** sin_pwr)

    # Generate LUT
    out_float = []
    out_fixed = []

    final_exp_fix = []

    for i in range(0, lut_size):  # note that i corresponds to 1 timestep!

        # Multiply by inverse of time constant
        value = float(i) * inv_tau

        # Only take first peak from kernel
        if (value > math.pi):
            exp_float = 0
        else:
            # Evaluate kernel
            exp_float = (math.exp(-value) * math.sin(value) **
                         sin_pwr / kernel_peak_value) * kernel_scaling

        # Convert to fixed-point
        exp_fix = float_to_fixed(exp_float)

        if spec is None:  # in testing mode so print
            out_float.append(exp_float)
            out_fixed.append(exp_fix)
            if i == time_probe:
                print("dt = {}, kernel value = {} (fixed-point = {})".format(
                    time_probe, exp_float, exp_fix))

        else:  # at runtime, so write to spec
            final_exp_fix.append(exp_fix)
            # spec.write_value(data=exp_fix, data_type=DataType.INT16)

    if spec is None:
        print("peak: time {}, value {}".format(peak_time, kernel_peak_value))
        t = numpy.arange(0, lut_size)
        out_fixed = numpy.array(out_fixed)
        out_float = numpy.array(out_float)

        compare_t_values = numpy.array([15, 20, 30, 35, 45, 47,
                                        99, 115, 135, 140, 150])
        print("LUT VALUES TO COMPARE TO SPINNAKER:")
        print("TIME DELTAS | FIXED MULTIPLIERS | FLOAT MULTIPLIERS")
        for x, y, z, in zip(compare_t_values, out_fixed[compare_t_values],
                            out_float[compare_t_values]):
            print("{:8} | {:8} | {:8.4f}".format(x, y, z))

        return compare_t_values, out_float, out_fixed, t
    else:
        header = numpy.array([len(final_exp_fix), shift], dtype="uint16")
        array_to_write = numpy.concatenate((
            header,
            numpy.array(final_exp_fix).astype("uint16"))).view("uint32")
        #
        spec.write_array(array_to_write)
        return array_to_write


def write_mfvn_lut(spec, sigma, beta, lut_size, shift, time_probe,
                   kernel_scaling=1.0):
    cos_pwr = 2

    # Calculate required time constant
    inv_sigma = (1.0 / float(sigma))  # * (machine_time_step / 1000.0)
    peak_time = 0

    # evaluate peak value of kernel to normalise LUT
    kernel_peak_value = (math.exp(-abs(peak_time * inv_sigma * beta)) *
                         math.cos(peak_time * inv_sigma) ** cos_pwr)

    # Generate LUT
    out_float = []
    out_fixed = []
    plot_times = []

    final_exp_fix = []

    for i in range(0, lut_size):  # note that i corresponds to 1 timestep!

        # Multiply by inverse of time constant
        value = float(i) * inv_sigma

        # Only take first peak from kernel
        if (value > math.pi / 2):
            exp_float = 0
        else:
            # Evaluate kernel
            exp_float = (math.exp(-abs(value * beta)) * math.cos(value) **
                         cos_pwr / kernel_peak_value) * kernel_scaling

        # Convert to fixed-point
        exp_fix = float_to_fixed(exp_float)

        if spec is None:  # in testing mode so print
            out_float.append(exp_float)
            out_fixed.append(exp_fix)
            plot_times.append(i)
            if i == time_probe:
                print("dt = {}, kernel value = {} (fixed-point = {})".format(
                    time_probe, exp_float, exp_fix))

        else:  # at runtime, so write to spec
            final_exp_fix.append(exp_fix)

    if spec is None:
        print("peak: time {}, value {}".format(peak_time, kernel_peak_value))
        out_fixed = numpy.array(out_fixed)
        out_float = numpy.array(out_float)

        compare_t_values = numpy.array([15, 20, 30, 35, 45, 47,
                                        99, 115, 135, 140, 150])
        print("LUT VALUES TO COMPARE TO SPINNAKER:")
        print("TIME DELTAS | FIXED MULTIPLIERS | FLOAT MULTIPLIERS")
        for x, y, z, in zip(compare_t_values, out_fixed[compare_t_values],
                            out_float[compare_t_values]):
            print("{:8} | {:8} | {:8.4f}".format(x, y, z))
        # plt.show()
        return compare_t_values, out_float, plot_times
    else:
        header = numpy.array([len(final_exp_fix), shift], dtype="uint16")
        array_to_write = numpy.concatenate((
            header,
            numpy.array(final_exp_fix).astype("uint16"))).view("uint32")
        spec.write_array(array_to_write)
        return array_to_write
