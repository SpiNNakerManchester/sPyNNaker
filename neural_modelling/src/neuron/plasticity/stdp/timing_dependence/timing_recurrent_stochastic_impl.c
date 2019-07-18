/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "timing_recurrent_fixed_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_trace_region_data_t plasticity_trace_region_data;

int16_t pre_cdf_lookup[STDP_TRACE_PRE_CDF_SIZE];
int16_t post_cdf_lookup[STDP_TRACE_POST_CDF_SIZE];

typedef struct {
    int32_t accumulator_depression_plus_one;
    int32_t accumulator_potentiation_minus_one;
    uint32_t pre_cdf_lookup[STDP_FIXED_POINT_ONE];
    uint32_t post_cdf_lookup[STDP_FIXED_POINT_ONE];
} stochastic_timing_config_t;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {
    log_info("timing_initialise: starting");
    log_info("\tRecurrent stochastic STDP rule");

    stochastic_timing_config_t *config =
            (stochastic_timing_config_t *) address;

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    plasticity_trace_region_data.accumulator_depression_plus_one =
            config->accumulator_depression_plus_one;
    plasticity_trace_region_data.accumulator_potentiation_minus_one =
            config->accumulator_potentiation_minus_one;

    log_info("\tAccumulator depression=%d, Accumulator potentiation=%d",
            plasticity_trace_region_data.accumulator_depression_plus_one - 1,
            plasticity_trace_region_data.accumulator_potentiation_minus_one + 1);

    // Copy LUTs from following memory
    maths_copy_int16_lut(
            config->pre_cdf_lookup, STDP_FIXED_POINT_ONE, pre_cdf_lookup);
    maths_copy_int16_lut(
            config->post_cdf_lookup, STDP_FIXED_POINT_ONE, post_cdf_lookup);

    log_info("timing_initialise: completed successfully");

    return (address_t) &config[1];
}
