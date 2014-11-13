from data_specification.enums.data_type import DataType

import math

import logging
logger = logging.getLogger(__name__)

FixedPointOne = (1 << 11)


def float_to_fixed_point(value):
    return int(round(float(value) * float(FixedPointOne)))


def write_exponential_decay_lut(spec, time_constant, size, shift):
    # Calculate time constant reciprocal
    time_constant_reciprocal = 1.0 / float(time_constant)

    # Check that the last 
    last_time = (size - 1) << shift
    last_value = float(last_time) * time_constant_reciprocal
    last_exp_float = math.exp(-last_value)
    if float_to_fixed_point(last_exp_float) != 0:
        logger.warning("STDP lookup table with size %u is too short to contain "
                       "decay with time constant %u - last entry is %f"
                       % (size, time_constant, last_exp_float))

    # Generate LUT
    for i in range(size):
        # Apply shift to get time from index 
        time = (i << shift)

        # Multiply by time constant and calculate negative exponential
        value = float(time) * time_constant_reciprocal
        exp_float = math.exp(-value)

        # Convert to fixed-point and write to spec
        spec.write_value(data=float_to_fixed_point(exp_float),
                         data_type=DataType.INT16)
