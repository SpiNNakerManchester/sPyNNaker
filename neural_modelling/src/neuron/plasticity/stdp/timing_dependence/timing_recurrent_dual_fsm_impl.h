/*
 * Copyright (c) 2017 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Recurrent timing rule using finite state machine
#ifndef _TIMING_RECURRENT_DUAL_FSM_IMPL_H_
#define _TIMING_RECURRENT_DUAL_FSM_IMPL_H_

//---------------------------------------
// Typedefines
//---------------------------------------
//! The type of post-traces
typedef uint16_t post_trace_t;
//! The type of pre-traces
typedef uint16_t pre_trace_t;

#include <neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_accumulator_impl.h>

#include "timing.h"
#include <neuron/plasticity/stdp/weight_dependence/weight_one_term.h>

// Include debug header for log_info etc
#include <debug.h>

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>

#include "random_util.h"

typedef struct {
    int32_t accumulator_depression_plus_one;
    int32_t accumulator_potentiation_minus_one;
} plasticity_trace_region_data_t;

//---------------------------------------
// Externals
//---------------------------------------
//! Global plasticity parameter data
extern plasticity_trace_region_data_t plasticity_trace_region_data;

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
//! \brief Get an initial post-synaptic timing trace
//! \return the post trace
static inline post_trace_t timing_get_initial_post_trace(void) {
    return 0;
}

//---------------------------------------
//! \brief Add a post spike to the post trace
//! \param[in] time: the time of the spike
//! \param[in] last_time: the time of the previous spike update
//! \param[in] last_trace: the post trace to update
//! \return the updated post trace
static inline post_trace_t timing_add_post_spike(
        UNUSED uint32_t time, UNUSED uint32_t last_time,
        UNUSED post_trace_t last_trace) {
    extern uint16_t post_exp_dist_lookup[STDP_FIXED_POINT_ONE];

    // Pick random number and use to draw from exponential distribution
    uint32_t random = mars_kiss_fixed_point();
    uint16_t window_length = post_exp_dist_lookup[random];
    log_debug("\t\tResetting post-window: random=%d, window_length=%u",
            random, window_length);

    // Return window length
    return window_length;
}

static inline post_trace_t timing_decay_post(
        UNUSED uint32_t time, UNUSED uint32_t last_time, post_trace_t last_trace) {
    return last_trace;
}

//---------------------------------------
//! \brief Add a pre spike to the pre trace
//! \param[in] time: the time of the spike
//! \param[in] last_time: the time of the previous spike update
//! \param[in] last_trace: the pre trace to update
//! \return the updated pre trace
static inline pre_trace_t timing_add_pre_spike(
        UNUSED uint32_t time, UNUSED uint32_t last_time,
        UNUSED pre_trace_t last_trace) {
    extern uint16_t pre_exp_dist_lookup[STDP_FIXED_POINT_ONE];

    // Pick random number and use to draw from exponential distribution
    uint32_t random = mars_kiss_fixed_point();
    uint16_t window_length = pre_exp_dist_lookup[random];
    log_debug("\t\tResetting pre-window: random=%d, window_length=%u",
            random, window_length);

    // Return window length
    return window_length;
}

//---------------------------------------
//! \brief Apply a pre-spike timing rule state update
//! \param[in] time: the current time
//! \param[in] trace: the current pre-spike trace
//! \param[in] last_pre_time: the time of the last pre-spike
//! \param[in] last_pre_trace: the trace of the last pre-spike
//! \param[in] last_post_time: the time of the last post-spike
//! \param[in] last_post_trace: the trace of the last post-spike
//! \param[in] previous_state: the state to update
//! \return the updated state
static inline update_state_t timing_apply_pre_spike(
        uint32_t time, UNUSED pre_trace_t trace, UNUSED uint32_t last_pre_time,
        UNUSED pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    // Get time of event relative to last post-synaptic event
    uint32_t time_since_last_post = time - last_post_time;

    log_debug("\t\t\ttime_since_last_post:%u, post_window_length:%u",
            time_since_last_post, last_post_trace);

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

    return previous_state;
}

//---------------------------------------
//! \brief Apply a post-spike timing rule state update
//! \param[in] time: the current time
//! \param[in] trace: the current post-spike trace
//! \param[in] last_pre_time: the time of the last pre-spike
//! \param[in] last_pre_trace: the trace of the last pre-spike
//! \param[in] last_post_time: the time of the last post-spike
//! \param[in] last_post_trace: the trace of the last post-spike
//! \param[in] previous_state: the state to update
//! \return the updated state
static inline update_state_t timing_apply_post_spike(
        uint32_t time, UNUSED post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, UNUSED uint32_t last_post_time,
        UNUSED post_trace_t last_post_trace, update_state_t previous_state) {
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
