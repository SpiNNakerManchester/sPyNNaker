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
from data_specification.enums import DataType
from spinn_front_end_common.utilities.utility_objs import ProvenanceDataItem

logger = logging.getLogger(__name__)
# Default value of fixed-point one for STDP
STDP_FIXED_POINT_ONE = (1 << 11)


def float_to_fixed(value, fixed_point_one):
    return int(round(float(value) * float(fixed_point_one)))


def write_exp_lut(spec, time_constant, size, shift,
                  fixed_point_one=STDP_FIXED_POINT_ONE):
    # Calculate time constant reciprocal
    time_constant_reciprocal = 1.0 / float(time_constant)

    # Generate LUT
    last_value = None
    for i in range(size):

        # Apply shift to get time from index
        time = (i << shift)

        # Multiply by time constant and calculate negative exponential
        value = float(time) * time_constant_reciprocal
        exp_float = math.exp(-value)

        # Convert to fixed-point and write to spec
        last_value = float_to_fixed(exp_float, fixed_point_one)
        spec.write_value(data=last_value, data_type=DataType.INT16)

    # return last value reverted to float (should be 0 if correct)
    return float(last_value) / float(fixed_point_one)


def get_lut_provenance(
        pre_population_label, post_population_label, rule_name, entry_name,
        param_name, last_entry):
    # pylint: disable=too-many-arguments
    top_level_name = "{}_{}_STDP_{}".format(
        pre_population_label, post_population_label, rule_name)
    report = False
    if last_entry is not None:
        report = last_entry > 0
    return ProvenanceDataItem(
        [top_level_name, entry_name], last_entry, report=report,
        message=(
            "The last entry in the STDP exponential lookup table for the {}"
            " parameter of the {} between {} and {} was {} rather than 0,"
            " indicating that the lookup table was not big enough at this"
            " timestep and value.  Try reducing the parameter value, or"
            " increasing the timestep".format(
                param_name, rule_name, pre_population_label,
                post_population_label, last_entry)))
