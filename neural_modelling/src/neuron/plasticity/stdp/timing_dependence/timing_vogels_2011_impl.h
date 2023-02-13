/*
 * Copyright (c) 2017-2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Timing rule from Vogels 2011
//! \details
//! <strong>Citation:</strong><br>
//! Inhibitory plasticity balances excitation and inhibition in sensory pathways
//! and memory networks,
//! **Vogels** TP, **Sprekeler** H, **Zenke** F, **Clopath** C, **Gerstner** W.,
//! _Science._ 2011 Dec 16;334(6062):1569-73.<br>
//! doi: [10.1126/science.1211095](https://doi.org/10.1126/science.1211095).
#ifndef VOGELS_2011_IMPL_H
#define VOGELS_2011_IMPL_H

//---------------------------------------
// Typedefines
//---------------------------------------
//! Type of post-traces
typedef int16_t post_trace_t;
//! Type of pre-traces
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
// Structures
//---------------------------------------
typedef struct {
    int32_t alpha;
} plasticity_trace_region_data_t;

//---------------------------------------
// Externals
//---------------------------------------
extern int16_lut *tau_lookup;

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------

static inline int16_t timing_decay_post(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {
    // Get time since last spike
    uint32_t delta_time = time - last_time;

    // Decay previous trace
    int32_t decayed_trace = STDP_FIXED_MUL_16X16(last_trace,
        maths_lut_exponential_decay(delta_time, tau_lookup));

    return (uint16_t) decayed_trace;

}

//! \brief Common code for adding a spike to the trace
//! \param[in] time: the time of the spike
//! \param[in] last_time: the time of the previous spike update
//! \param[in] last_trace: the trace to update
//! \return the updated trace
static inline int16_t timing_add_spike(
        uint32_t time, uint32_t last_time, int16_t last_trace) {

    // Decay previous trace
    int32_t decayed_trace = timing_decay_post(time, last_time, last_trace);

    // Add new spike to trace
    int32_t new_trace = decayed_trace + STDP_FIXED_POINT_ONE;

    return (int16_t)new_trace;
}

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
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {
    return timing_add_spike(time, last_time, last_trace);
}
//---------------------------------------
//! \brief Add a pre spike to the pre trace
//! \param[in] time: the time of the spike
//! \param[in] last_time: the time of the previous spike update
//! \param[in] last_trace: the pre trace to update
//! \return the updated pre trace
static inline pre_trace_t timing_add_pre_spike(
        uint32_t time, uint32_t last_time, pre_trace_t last_trace) {
    return timing_add_spike(time, last_time, last_trace);
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
    extern plasticity_trace_region_data_t plasticity_trace_region_data;

    // Get time of event relative to last post-synaptic event
    uint32_t time_since_last_post = time - last_post_time;
    int32_t exponential_decay = maths_lut_exponential_decay(
            time_since_last_post, tau_lookup);
    int32_t decayed_o1 = STDP_FIXED_MUL_16X16(last_post_trace, exponential_decay)
            - plasticity_trace_region_data.alpha;

    log_debug("\t\t\ttime_since_last_post_event=%u, decayed_o1=%d\n",
            time_since_last_post, decayed_o1);

    // Apply potentiation to state (which is a weight_state)
    return weight_one_term_apply_potentiation(previous_state, decayed_o1);

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
    int32_t exponential_decay = maths_lut_exponential_decay(
            time_since_last_pre, tau_lookup);
    int32_t decayed_r1 = STDP_FIXED_MUL_16X16(last_pre_trace, exponential_decay);

    log_debug("\t\t\ttime_since_last_pre_event=%u, decayed_r1=%d\n",
            time_since_last_pre, decayed_r1);

    // Apply potentiation to state (which is a weight_state)
    return weight_one_term_apply_potentiation(previous_state, decayed_r1);
}

#endif  // VOGELS_2011_IMPL_H
