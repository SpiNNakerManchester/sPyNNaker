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
//! \brief Timing rule using spike pairs
#ifndef _TIMING_PAIR_IMPL_H_
#define _TIMING_PAIR_IMPL_H_

//---------------------------------------
// Typedefines
//---------------------------------------
//! The type of post-spike traces
typedef int16_t post_trace_t;
//! The type of pre-spike traces
typedef int16_t pre_trace_t;

#include <neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h>
#include "timing.h"
#include <neuron/plasticity/stdp/weight_dependence/weight_one_term.h>

// Include debug header for log_info etc
#include <debug.h>

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
//! \brief Get an initial post-synaptic timing trace
//! \return the post trace
static inline post_trace_t timing_get_initial_post_trace(void) {
    return 0;
}

static inline post_trace_t timing_decay_post(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {
    extern int16_lut *tau_minus_lookup;
    // Get time since last spike
    uint32_t delta_time = time - last_time;

    // Decay previous o1 and o2 traces
    return (post_trace_t) STDP_FIXED_MUL_16X16(last_trace,
            maths_lut_exponential_decay(delta_time, tau_minus_lookup));
}

//---------------------------------------
//! \brief Add a post spike to the post trace
//! \param[in] time: the time of the spike
//! \param[in] last_time: the time of the previous spike update
//! \param[in] last_trace: the post trace to update
//! \return the updated post trace
static inline post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {

    // Decay previous o1 and o2 traces
    int16_t decayed_o1_trace = timing_decay_post(time, last_time, last_trace);

    // Add energy caused by new spike to trace
    // **NOTE** o2 trace is pre-multiplied by a3_plus
    int16_t new_o1_trace = decayed_o1_trace + STDP_FIXED_POINT_ONE;

    // Return new pre- synaptic event with decayed trace values with energy
    // for new spike added
    return (post_trace_t) new_o1_trace;
}

//---------------------------------------
//! \brief Add a pre spike to the pre trace
//! \param[in] time: the time of the spike
//! \param[in] last_time: the time of the previous spike update
//! \param[in] last_trace: the pre trace to update
//! \return the updated pre trace
static inline pre_trace_t timing_add_pre_spike(
        uint32_t time, uint32_t last_time, pre_trace_t last_trace) {
    extern int16_lut *tau_plus_lookup;
    // Get time since last spike
    uint32_t delta_time = time - last_time;

    // Decay previous r1 and r2 traces
    int32_t decayed_r1_trace = STDP_FIXED_MUL_16X16(last_trace,
        maths_lut_exponential_decay(delta_time, tau_plus_lookup));

    // Add energy caused by new spike to trace
    int32_t new_r1_trace = decayed_r1_trace + STDP_FIXED_POINT_ONE;

    log_debug("\tdelta_time=%u, r1=%d\n", delta_time, new_r1_trace);

    // Return new pre-synaptic event with decayed trace values with energy
    // for new spike added
    return (pre_trace_t) new_r1_trace;
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
    extern int16_lut *tau_minus_lookup;

    // Get time of event relative to last post-synaptic event
    uint32_t time_since_last_post = time - last_post_time;
    int32_t decayed_o1 = STDP_FIXED_MUL_16X16(last_post_trace,
        maths_lut_exponential_decay(time_since_last_post, tau_minus_lookup));

    log_debug("\t\t\ttime_since_last_post_event=%u, decayed_o1=%d\n",
            time_since_last_post, decayed_o1);

    // Apply depression to state (which is a weight_state)
    return weight_one_term_apply_depression(previous_state, decayed_o1);
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
    extern int16_lut *tau_plus_lookup;

    // Get time of event relative to last pre-synaptic event
    uint32_t time_since_last_pre = time - last_pre_time;
    if (time_since_last_pre > 0) {
        int32_t decayed_r1 = STDP_FIXED_MUL_16X16(last_pre_trace,
            maths_lut_exponential_decay(time_since_last_pre, tau_plus_lookup));

        log_debug("\t\t\ttime_since_last_pre_event=%u, decayed_r1=%d\n",
                time_since_last_pre, decayed_r1);

        // Apply potentiation to state (which is a weight_state)
        return weight_one_term_apply_potentiation(previous_state, decayed_r1);
    } else {
        return previous_state;
    }
}

#endif // _TIMING_PAIR_IMPL_H_
