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

#ifndef _TIMING_NEAREST_PAIR_IMPL_H_
#define _TIMING_NEAREST_PAIR_IMPL_H_

//---------------------------------------
// Structures
//---------------------------------------
typedef struct post_trace_t {
} post_trace_t;

typedef struct pre_trace_t {
} pre_trace_t;

#include <synapse/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h>
#include "timing.h"
#include <synapse/plasticity/stdp/weight_dependence/weight_one_term.h>

// Include debug header for log_info etc
#include <debug.h>

// Include generic plasticity maths functions
#include <synapse/plasticity/stdp/maths.h>

//---------------------------------------
// Macros
//---------------------------------------
// Exponential decay lookup parameters
#define TAU_PLUS_TIME_SHIFT 0
#define TAU_PLUS_SIZE 256

#define TAU_MINUS_TIME_SHIFT 0
#define TAU_MINUS_SIZE 256

// Helper macros for looking up decays
#define DECAY_LOOKUP_TAU_PLUS(time) \
    maths_lut_exponential_decay( \
	        time, TAU_PLUS_TIME_SHIFT, TAU_PLUS_SIZE, tau_plus_lookup)
#define DECAY_LOOKUP_TAU_MINUS(time) \
    maths_lut_exponential_decay( \
            time, TAU_MINUS_TIME_SHIFT, TAU_MINUS_SIZE, tau_minus_lookup)

//---------------------------------------
// Externals
//---------------------------------------
extern int16_t tau_plus_lookup[TAU_PLUS_SIZE];
extern int16_t tau_minus_lookup[TAU_MINUS_SIZE];

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace(void) {
    return (post_trace_t) {};
}

//---------------------------------------
static inline post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {
    use(&last_time);
    use(&last_trace);

    log_debug("\tdelta_time=%u\n", time - last_time);

    // Return new pre- synaptic event with decayed trace values with energy
    // for new spike added
    return (post_trace_t) {};
}

//---------------------------------------
static inline pre_trace_t timing_add_pre_spike(
        uint32_t time, uint32_t last_time, pre_trace_t last_trace) {
    use(&last_time);
    use(&last_trace);

    log_debug("\tdelta_time=%u\n", time - last_time);

    return (pre_trace_t ) {};
}

//---------------------------------------
static inline update_state_t timing_apply_pre_spike(
        uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(&trace);
    use(&last_pre_time);
    use(&last_pre_trace);
    use(&last_post_trace);

    // Get time of event relative to last post-synaptic event
    uint32_t time_since_last_post = time - last_post_time;
    if (time_since_last_post > 0) {
        int32_t decayed_o1 = DECAY_LOOKUP_TAU_MINUS(time_since_last_post);

        log_debug("\t\t\ttime_since_last_post=%u, decayed_o1=%d\n",
                time_since_last_post, decayed_o1);

        // Apply depression to state (which is a weight_state)
        return weight_one_term_apply_depression(previous_state, decayed_o1);
    } else {
        return previous_state;
    }
}

//---------------------------------------
static inline update_state_t timing_apply_post_spike(
        uint32_t time, post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(&trace);
    use(&last_pre_trace);
    use(&last_post_time);
    use(&last_post_trace);

    // Get time of event relative to last pre-synaptic event
    uint32_t time_since_last_pre = time - last_pre_time;
    uint32_t time_since_last_post = time - last_post_time;

    if (time_since_last_pre > 0) {
        int32_t decayed_r1 = DECAY_LOOKUP_TAU_PLUS(time_since_last_pre);

        log_debug("\t\t\ttime_since_last_pret=%u, decayed_r1=%d\n",
                time_since_last_pre, decayed_r1);
        log_debug("\t\t\ttime_since_last_post=%u, decayed_r1=%d\n",
                time_since_last_post, decayed_r1);

        if (time_since_last_post < time_since_last_pre) {
            log_debug("\t\t\tSetting trace to zero as not first pre-post pairing");
            decayed_r1 = 0;
        }

        // Apply potentiation to state (which is a weight_state)
        return weight_one_term_apply_potentiation(previous_state, decayed_r1);
    } else {
        return previous_state;
    }
}

#endif	// _TIMING_NEAREST_PAIR_IMPL_H_
