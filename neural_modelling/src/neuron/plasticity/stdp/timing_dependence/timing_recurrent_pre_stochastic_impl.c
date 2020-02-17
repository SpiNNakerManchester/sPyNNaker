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

#include "timing_recurrent_pre_stochastic_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
uint16_t pre_exp_dist_lookup[STDP_FIXED_POINT_ONE];
uint16_t post_exp_dist_lookup[STDP_FIXED_POINT_ONE];

// Global plasticity parameter data
plasticity_trace_region_data_t plasticity_trace_region_data;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {
    log_debug("timing_initialise: starting");
    log_debug("\tRecurrent pre-calculated stochastic STDP rule");

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    plasticity_trace_region_data.accumulator_depression_plus_one =
            (int32_t) address[0];
    plasticity_trace_region_data.accumulator_potentiation_minus_one =
            (int32_t) address[1];

    log_debug("\tAccumulator depression=%d, Accumulator potentiation=%d",
            plasticity_trace_region_data.accumulator_depression_plus_one - 1,
            plasticity_trace_region_data.accumulator_potentiation_minus_one + 1);

    // Copy LUTs from following memory
    // Copy LUTs from following memory
        uint32_t word_size = STDP_FIXED_POINT_ONE / 2;
        spin1_memcpy(pre_exp_dist_lookup, &address[2],
                STDP_FIXED_POINT_ONE * sizeof(uint16_t));
        spin1_memcpy(post_exp_dist_lookup, &address[2 + word_size],
                STDP_FIXED_POINT_ONE * sizeof(uint16_t));

    log_debug("timing_initialise: completed successfully");

    return &address[2 + word_size + word_size];
}
