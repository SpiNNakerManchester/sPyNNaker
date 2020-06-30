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

//---------------------------------------
//! \brief Add a post spike to the post trace
//! \param[in] time: the time of the spike
//! \param[in] last_time: the time of the previous spike update
//! \param[in] last_trace: the post trace to update
//! \return the updated post trace
static inline post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {
    use(time);
    use(&last_time);
    use(&last_trace);

    log_debug("\tdelta_time=%u", time - last_time);

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
        uint32_t time, uint32_t last_time, pre_trace_t last_trace) {
    use(time);
    use(&last_time);
    use(&last_trace);

    log_debug("\tdelta_time=%u", time - last_time);

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
        uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(&trace);
    use(&last_pre_trace);
    use(&last_post_trace);

    switch (previous_state.state) {
    case STATE_IDLE:
        // If we're idle, transition to pre-open state
        log_debug("\tOpening pre-window");
        previous_state.state = STATE_PRE_OPEN;
        previous_state =
                timing_recurrent_calculate_pre_window(previous_state);
        break;
    case STATE_PRE_OPEN:
        // If we're in pre-open state
        _no_op(); // <<< empty statement for C syntax reasons
        // Get time of event relative to last pre-synaptic event
        uint32_t time_since_last_pre = time - last_pre_time;

        log_debug("\tTime_since_last_pre_event=%u", time_since_last_pre);

        if (timing_recurrent_in_pre_window(time_since_last_pre, previous_state)) {
            // If pre-window is still open
            log_debug("\t\tClosing pre-window");
            previous_state.state = STATE_IDLE;
        } else {
            // Otherwise, leave state alone (essentially re-opening window)
            log_debug("\t\tRe-opening pre-window");
            previous_state =
                    timing_recurrent_calculate_pre_window(previous_state);
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
                log_debug("\t\tApplying depression");

                previous_state.accumulator = 0;
                previous_state.weight_state = weight_one_term_apply_depression(
                        previous_state.weight_state, STDP_FIXED_POINT_ONE);
            }

            // Transition back to idle
            previous_state.state = STATE_IDLE;
        } else {
            // Otherwise, if post-window has closed, skip idle state and go
            // straight to pre-open
            log_debug("\t\tPost-window closed - Opening pre-window");
            previous_state.state = STATE_PRE_OPEN;
            previous_state =
                    timing_recurrent_calculate_pre_window(previous_state);
        }
        break;
    default:
        log_debug("\tInvalid state %u", previous_state.state);
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
        uint32_t time, post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(&trace);
    use(&last_pre_trace);
    use(&last_post_trace);

    switch (previous_state.state) {
    case STATE_IDLE:
        // If we're idle, transition to post-open state
        log_debug("\tOpening post-window");
        previous_state.state = STATE_POST_OPEN;
        previous_state =
                timing_recurrent_calculate_post_window(previous_state);
        break;
    case STATE_POST_OPEN:
        // If we're in post-open state
        _no_op(); // <<< empty statement for C syntax reasons
        // Get time of event relative to last post-synaptic event
        uint32_t time_since_last_post = time - last_post_time;

        log_debug("\tTime_since_last_post_event=%u", time_since_last_post);

        if (timing_recurrent_in_post_window(
                time_since_last_post, previous_state)) {
            // If post window's still open
            log_debug("\t\tClosing post-window");
            previous_state.state = STATE_IDLE;
        } else {
            // Otherwise, leave state alone (essentially re-opening window)
            log_debug("\t\tRe-opening post-window");
            previous_state =
                    timing_recurrent_calculate_post_window(previous_state);
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
            log_debug("\t\tIgnoring coinciding spikes");

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
                log_debug("\t\tApplying potentiation");

                previous_state.accumulator = 0;
                previous_state.weight_state = weight_one_term_apply_potentiation(
                        previous_state.weight_state, STDP_FIXED_POINT_ONE);
            }

            // Transition back to idle
            previous_state.state = STATE_IDLE;
        } else {
            // Otherwise, if post-window has closed, skip idle state and go
            // straight to pre-open
            log_debug("\t\tPre-window closed - Opening post-window");
            previous_state.state = STATE_POST_OPEN;
            previous_state =
                    timing_recurrent_calculate_post_window(previous_state);
        }
        break;
    default:
        log_debug("\tInvalid state %u", previous_state.state);
    }

    return previous_state;
}

#endif// _TIMING_RECURRENT_COMMON_H_
