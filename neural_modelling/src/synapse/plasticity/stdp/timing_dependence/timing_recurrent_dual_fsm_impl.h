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

#ifndef _TIMING_RECURRENT_DUAL_FSM_IMPL_H_
#define _TIMING_RECURRENT_DUAL_FSM_IMPL_H_

//---------------------------------------
// Typedefines
//---------------------------------------
typedef uint16_t post_trace_t;
typedef uint16_t pre_trace_t;

#include <synapse/plasticity/stdp/synapse_structure/synapse_structure_weight_accumulator_impl.h>

#include "timing.h"
#include <synapse/plasticity/stdp/weight_dependence/weight_one_term.h>

// Include debug header for log_info etc
#include <debug.h>

// Include generic plasticity maths functions
#include <synapse/plasticity/stdp/maths.h>
#include <synapse/plasticity/stdp/stdp_typedefs.h>

#include "random_util.h"

typedef struct {
    int32_t accumulator_depression_plus_one;
    int32_t accumulator_potentiation_minus_one;
} plasticity_trace_region_data_t;

//---------------------------------------
// Externals
//---------------------------------------
extern uint16_t pre_exp_dist_lookup[STDP_FIXED_POINT_ONE];
extern uint16_t post_exp_dist_lookup[STDP_FIXED_POINT_ONE];
extern plasticity_trace_region_data_t plasticity_trace_region_data;

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace(void) {
    return 0;
}

//---------------------------------------
static inline post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {
    use(&time);
    use(&last_time);
    use(&last_trace);

    // Pick random number and use to draw from exponential distribution
    uint32_t random = mars_kiss_fixed_point();
    uint16_t window_length = post_exp_dist_lookup[random];
    log_debug("\t\tResetting post-window: random=%d, window_length=%u",
            random, window_length);

    // Return window length
    return window_length;
}

//---------------------------------------
static inline pre_trace_t timing_add_pre_spike(
        uint32_t time, uint32_t last_time, pre_trace_t last_trace) {
    use(&time);
    use(&last_time);
    use(&last_trace);

    // Pick random number and use to draw from exponential distribution
    uint32_t random = mars_kiss_fixed_point();
    uint16_t window_length = pre_exp_dist_lookup[random];
    log_debug("\t\tResetting pre-window: random=%d, window_length=%u",
            random, window_length);

    // Return window length
    return window_length;
}

//---------------------------------------
static inline update_state_t timing_apply_pre_spike(
        uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(&trace);
    use(&last_pre_time);
    use(&last_pre_trace);

    // Get time of event relative to last post-synaptic event
    uint32_t time_since_last_post = time - last_post_time;

    log_debug("\t\t\ttime_since_last_post:%u, post_window_length:%u",
            time_since_last_post, last_post_trace);

    // If spikes don't coincide
    if (time_since_last_post > 0) {
        // If this pre-spike has arrived within the last post window
        if (time_since_last_post < last_post_trace) {
            if (previous_state.accumulator >
                    plasticity_trace_region_data.accumulator_depression_plus_one) {
                // If accumulator's not going to hit depression limit,
                // decrement it
                previous_state.accumulator--;
                log_debug("\t\t\t\tDecrementing accumulator=%d",
                        previous_state.accumulator);
            } else {
                // Otherwise, reset accumulator and apply depression
                log_debug("\t\t\t\tApplying depression");

                previous_state.accumulator = 0;
                previous_state.weight_state = weight_one_term_apply_depression(
                        previous_state.weight_state, STDP_FIXED_POINT_ONE);
            }
        }
    }

    return previous_state;
}

//---------------------------------------
static inline update_state_t timing_apply_post_spike(
        uint32_t time, post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(&trace);
    use(&last_post_time);
    use(&last_post_trace);

    // Get time of event relative to last pre-synaptic event
    uint32_t time_since_last_pre = time - last_pre_time;

    log_debug("\t\t\ttime_since_last_pre:%u, pre_window_length:%u",
            time_since_last_pre, last_pre_trace);

    // If spikes don't coincide
    if (time_since_last_pre > 0) {
        // If this post-spike has arrived within the last pre window
        if (time_since_last_pre < last_pre_trace) {
            if (previous_state.accumulator <
                    plasticity_trace_region_data.accumulator_potentiation_minus_one) {
                // If accumulator's not going to hit potentiation limit,
                // increment it
                previous_state.accumulator++;
                log_debug("\t\t\t\tIncrementing accumulator=%d",
                        previous_state.accumulator);
            } else {
                // Otherwise, reset accumulator and apply potentiation
                log_debug("\t\t\t\tApplying potentiation");

                previous_state.accumulator = 0;
                previous_state.weight_state = weight_one_term_apply_potentiation(
                        previous_state.weight_state, STDP_FIXED_POINT_ONE);
            }
        }
    }

    return previous_state;
}

#endif  // _TIMING_RECURRENT_DUAL_FSM_IMPL_H_
