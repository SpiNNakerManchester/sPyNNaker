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

#ifndef _TIMING_RECURRENT_PRE_STOCHASTIC_IMPL_H_
#define _TIMING_RECURRENT_PRE_STOCHASTIC_IMPL_H_

typedef struct post_trace_t {
} post_trace_t;

typedef struct pre_trace_t {
} pre_trace_t;


typedef struct {
    int32_t accumulator_depression_plus_one;
    int32_t accumulator_potentiation_minus_one;
} plasticity_trace_region_data_t;

#define STRUCTURE_PATH(file) <synapse/plasticity/stdp/synapse_structure/file>
#include STRUCTURE_PATH(synapse_structure_weight_state_accumulator_window_impl.h)
#include "timing_recurrent_common.h"

extern uint16_t pre_exp_dist_lookup[STDP_FIXED_POINT_ONE];
extern uint16_t post_exp_dist_lookup[STDP_FIXED_POINT_ONE];

static inline bool timing_recurrent_in_pre_window(
        uint32_t time_since_last_event, update_state_t previous_state) {
    return time_since_last_event < previous_state.window_length;
}

static inline bool timing_recurrent_in_post_window(
        uint32_t time_since_last_event, update_state_t previous_state) {
    return time_since_last_event < previous_state.window_length;
}

static inline update_state_t timing_recurrent_calculate_pre_window(
        update_state_t previous_state) {
    // Pick random number and use to draw from exponential distribution
    int32_t random = mars_kiss_fixed_point();
    previous_state.window_length = pre_exp_dist_lookup[random];
    log_debug("\t\tRandom=%d, Exp dist=%u",
            random, previous_state.window_length);

    return previous_state;
}

static inline update_state_t timing_recurrent_calculate_post_window(
        update_state_t previous_state) {
    // Pick random number and use to draw from exponential distribution
    int32_t random = mars_kiss_fixed_point();
    previous_state.window_length = post_exp_dist_lookup[random];
    log_debug("\t\tRandom=%d, Exp dist=%u",
            random, previous_state.window_length);

    return previous_state;
}

#endif  // _TIMING_RECURRENT_PRE_STOCHASTIC_IMPL_H_
