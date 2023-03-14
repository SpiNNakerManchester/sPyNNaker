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
//! \brief Common code for recurrent timing rules.
//!
//! Recurrent timing rules use a small state machine to decide how to react to
//! spike events rather than a simple accumulator.
#ifndef _TIMING_RECURRENT_COMMON_H_
#define _TIMING_RECURRENT_COMMON_H_

#include "timing.h"
#include <neuron/plasticity/stdp/weight_dependence/weight_one_term.h>

// Include debug header for log_info etc
#include <debug.h>

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>

#include "random_util.h"

//! \brief API: Check if there was an event in the pre-window
//! \param[in] time_since_last_event: Length of time since last event
//! \param[in] previous_state: The state we're in right now
//! \return True if an event is there.
static bool timing_recurrent_in_pre_window(
        uint32_t time_since_last_event, update_state_t previous_state);

//! \brief API: Check if there was an event in the post-window
//! \param[in] time_since_last_event: Length of time since last event
//! \param[in] previous_state: The state we're in right now
//! \return True if an event is there.
static bool timing_recurrent_in_post_window(
        uint32_t time_since_last_event, update_state_t previous_state);

//! \brief API: Update the state with the pre-window information
//! \param[in] previous_state: The state we're in right now
//! \return The new state.
static update_state_t timing_recurrent_calculate_pre_window(
        update_state_t previous_state);

//! \brief API: Update the state with the post-window information
//! \param[in] previous_state: The state we're in right now
//! \return The new state.
static update_state_t timing_recurrent_calculate_post_window(
        update_state_t previous_state);

//! Synapse states
enum recurrent_state_machine_state_t {
    STATE_IDLE,      //!< Initial state; neither window is open
    STATE_PRE_OPEN,  //!< Pre-window is open
    STATE_POST_OPEN  //!< Post-window is open
};

//---------------------------------------
// Timing dependence functions
//---------------------------------------

static inline void _no_op(void) {
}

//! \brief Get an initial post-synaptic timing trace
//! \return the post trace
static inline post_trace_t timing_get_initial_post_trace(void) {
    return (post_trace_t){};
}

static inline post_trace_t timing_decay_post(
        UNUSED uint32_t time, UNUSED uint32_t last_time,
        UNUSED post_trace_t last_trace) {
    return (post_trace_t) {};
}

//---------------------------------------
//! \brief Add a post spike to the post trace
//! \param[in] time: the time of the spike
//! \param[in] last_time: the time of the previous spike update
//! \param[in] last_trace: the post trace to update
//! \return the updated post trace
static inline post_trace_t timing_add_post_spike(
        UNUSED uint32_t time, UNUSED uint32_t last_time, UNUSED post_trace_t last_trace) {
    // Return new pre- synaptic event with decayed trace values with energy
    // for new spike added
    return (post_trace_t) {};
}

//---------------------------------------
//! \brief Add a pre spike to the pre trace
//! \param[in] time: the time of the spike
//! \param[in] last_time: the time of the previous spike update
//! \param[in] last_trace: the pre trace to update
//! \return the updated pre trace
static inline pre_trace_t timing_add_pre_spike(
        UNUSED uint32_t time, UNUSED uint32_t last_time, UNUSED pre_trace_t last_trace) {

    return (pre_trace_t){};
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
        uint32_t time, UNUSED pre_trace_t trace, uint32_t last_pre_time,
        UNUSED pre_trace_t last_pre_trace, uint32_t last_post_time,
        UNUSED post_trace_t last_post_trace, update_state_t previous_state) {
	bool update_state = false;
    switch (previous_state.state) {
    case STATE_IDLE:
        // If we're idle, transition to pre-open state
        previous_state.state = STATE_PRE_OPEN;
        update_state = true;
        break;
    case STATE_PRE_OPEN:
        // If we're in pre-open state
        _no_op(); // <<< empty statement for C syntax reasons
        // Get time of event relative to last pre-synaptic event
        uint32_t time_since_last_pre = time - last_pre_time;

        if (timing_recurrent_in_pre_window(time_since_last_pre, previous_state)) {
            // If pre-window is still open
            previous_state.state = STATE_IDLE;
        } else {
            // Otherwise, leave state alone (essentially re-opening window)
            update_state = true;
        }
        break;
    case STATE_POST_OPEN:
        // Otherwise, if we're in post-open
        _no_op(); // <<< empty statement for C syntax reasons
        // Get time of event relative to last post-synaptic event
        uint32_t time_since_last_post = time - last_post_time;

        log_debug("\tTime_since_last_post_event=%u", time_since_last_post);

        if (timing_recurrent_in_post_window(
                time_since_last_post, previous_state)) {
            extern plasticity_trace_region_data_t plasticity_trace_region_data;

            // Otherwise, if post-window is still open
            if (previous_state.accumulator >
                    plasticity_trace_region_data.accumulator_depression_plus_one) {
                // If accumulator's not going to hit depression limit, decrement
                // it
                previous_state.accumulator--;
                log_debug("\t\tDecrementing accumulator=%d",
                        previous_state.accumulator);
            } else {
                // Otherwise, reset accumulator and apply depression
                previous_state.accumulator = 0;
                previous_state.weight_state = weight_one_term_apply_depression(
                        previous_state.weight_state, STDP_FIXED_POINT_ONE);
            }

            // Transition back to idle
            previous_state.state = STATE_IDLE;
        } else {
            // Otherwise, if post-window has closed, skip idle state and go
            // straight to pre-open
            previous_state.state = STATE_PRE_OPEN;
            update_state = true;
        }
        break;
    default:
        log_debug("\tInvalid state %u", previous_state.state);
    }

    if (update_state) {
    	previous_state = timing_recurrent_calculate_pre_window(previous_state);
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
        UNUSED pre_trace_t last_pre_trace, uint32_t last_post_time,
        UNUSED post_trace_t last_post_trace, update_state_t previous_state) {
	bool update_state = false;
    switch (previous_state.state) {
    case STATE_IDLE:
        // If we're idle, transition to post-open state
        previous_state.state = STATE_POST_OPEN;
        update_state = true;
        break;
    case STATE_POST_OPEN:
        // If we're in post-open state
        _no_op(); // <<< empty statement for C syntax reasons
        // Get time of event relative to last post-synaptic event
        uint32_t time_since_last_post = time - last_post_time;

        if (timing_recurrent_in_post_window(
                time_since_last_post, previous_state)) {
            // If post window's still open
            previous_state.state = STATE_IDLE;
        } else {
            // Otherwise, leave state alone (essentially re-opening window)
            update_state = true;
        }
        break;
    case STATE_PRE_OPEN:
        // Otherwise, if we're in pre-open
        _no_op(); // <<< empty statement for C syntax reasons
        // Get time of event relative to last pre-synaptic event
        uint32_t time_since_last_pre = time - last_pre_time;

        log_debug("\tTime_since_last_pre_event=%u", time_since_last_pre);

        if (time_since_last_pre == 0) {
            // If post-synaptic spike occurred at the same time, ignore it

            // Transition back to idle
            previous_state.state = STATE_IDLE;
        } else if (timing_recurrent_in_pre_window(
                time_since_last_pre, previous_state)) {
            extern plasticity_trace_region_data_t plasticity_trace_region_data;

            // Otherwise, if pre-window's still open
            if (previous_state.accumulator <
                    plasticity_trace_region_data.accumulator_potentiation_minus_one) {
                // If accumulator's not going to hit potentiation limit,
                // increment it
                previous_state.accumulator++;
                log_debug("\t\tIncrementing accumulator=%d",
                        previous_state.accumulator);
            } else {
                // Otherwise, reset accumulator and apply potentiation
                previous_state.accumulator = 0;
                previous_state.weight_state = weight_one_term_apply_potentiation(
                        previous_state.weight_state, STDP_FIXED_POINT_ONE);
            }

            // Transition back to idle
            previous_state.state = STATE_IDLE;
        } else {
            // Otherwise, if post-window has closed, skip idle state and go
            // straight to pre-open
            previous_state.state = STATE_POST_OPEN;
            update_state = true;
        }
        break;
    default:
        log_debug("\tInvalid state %u", previous_state.state);
    }

    if (update_state) {
        previous_state = timing_recurrent_calculate_post_window(previous_state);
    }

    return previous_state;
}

#endif// _TIMING_RECURRENT_COMMON_H_
