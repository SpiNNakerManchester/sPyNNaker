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

//! \file
//! \brief Initialisation for timing_recurrent_dual_fsm_impl.h
#include "../../../../meanfield/plasticity/stdp/timing_dependence/timing_recurrent_dual_fsm_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
//! \brief Lookup table for picking exponentially distributed random value for
//! pre-traces
uint16_t pre_exp_dist_lookup[STDP_FIXED_POINT_ONE];
//! \brief Lookup table for picking exponentially distributed random value for
//! post-traces
uint16_t post_exp_dist_lookup[STDP_FIXED_POINT_ONE];

// Global plasticity parameter data
plasticity_trace_region_data_t plasticity_trace_region_data;

//! How the configuration data for dual_fsm is laid out in SDRAM.
typedef struct {
    int32_t accumulator_depression_plus_one;
    int32_t accumulator_potentiation_minus_one;
    uint16_t pre_exp_dist_lookup[STDP_FIXED_POINT_ONE];
    uint16_t post_exp_dist_lookup[STDP_FIXED_POINT_ONE];
    uint32_t following_data[];
} dual_fsm_config_t;

//---------------------------------------
// Functions
//---------------------------------------
uint32_t *timing_initialise(address_t address) {
    log_info("timing_initialise: starting");
    log_info("\tRecurrent dual-FSM STDP rule");
    dual_fsm_config_t *config = (dual_fsm_config_t *) address;

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
    spin1_memcpy(pre_exp_dist_lookup, config->pre_exp_dist_lookup,
            sizeof(config->pre_exp_dist_lookup));
    spin1_memcpy(post_exp_dist_lookup, config->post_exp_dist_lookup,
            sizeof(config->post_exp_dist_lookup));

    log_info("timing_initialise: completed successfully");

    return config->following_data;
}
