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
//! \brief Recurrent stochastic timing rule
#ifndef _TIMING_RECURRENT_PRE_STOCHASTIC_IMPL_H_
#define _TIMING_RECURRENT_PRE_STOCHASTIC_IMPL_H_

typedef struct post_trace_t {
} post_trace_t;

typedef struct pre_trace_t {
} pre_trace_t;

//! Configuration information about plasticity traces
typedef struct {
    //! Threshold above which we won't hit depression trigger after decrement
    int32_t accumulator_depression_plus_one;
    //! Threshold below which we won't hit potentiation trigger after increment
    int32_t accumulator_potentiation_minus_one;
} plasticity_trace_region_data_t;

#define _STRUCTURE_PATH(file) <neuron/plasticity/stdp/synapse_structure/file>
#include _STRUCTURE_PATH(synapse_structure_weight_state_accumulator_window_impl.h)
#include "timing_recurrent_common.h"

//! \brief Check if there was an event in the pre-window
//! \param[in] time_since_last_event: Length of time since last event
//! \param[in] previous_state: The state we're in right now
//! \return True if an event is there.
static inline bool timing_recurrent_in_pre_window(
        uint32_t time_since_last_event, update_state_t previous_state) {
    return time_since_last_event < previous_state.window_length;
}

//! \brief Check if there was an event in the post-window
//! \param[in] time_since_last_event: Length of time since last event
//! \param[in] previous_state: The state we're in right now
//! \return True if an event is there.
static inline bool timing_recurrent_in_post_window(
        uint32_t time_since_last_event, update_state_t previous_state) {
    return time_since_last_event < previous_state.window_length;
}

//! \brief Update the state with the pre-window information
//! \param[in] previous_state: The state we're in right now
//! \return The new state.
static inline update_state_t timing_recurrent_calculate_pre_window(
        update_state_t previous_state) {
    extern uint16_t pre_exp_dist_lookup[STDP_FIXED_POINT_ONE];

    // Pick random number and use to draw from exponential distribution
    int32_t random = mars_kiss_fixed_point();
    previous_state.window_length = pre_exp_dist_lookup[random];
    log_debug("\t\tRandom=%d, Exp dist=%u",
            random, previous_state.window_length);

    return previous_state;
}

//! \brief Update the state with the post-window information
//! \param[in] previous_state: The state we're in right now
//! \return The new state.
static inline update_state_t timing_recurrent_calculate_post_window(
        update_state_t previous_state) {
    extern uint16_t post_exp_dist_lookup[STDP_FIXED_POINT_ONE];

    // Pick random number and use to draw from exponential distribution
    int32_t random = mars_kiss_fixed_point();
    previous_state.window_length = post_exp_dist_lookup[random];
    log_debug("\t\tRandom=%d, Exp dist=%u",
            random, previous_state.window_length);

    return previous_state;
}

#endif  // _TIMING_RECURRENT_PRE_STOCHASTIC_IMPL_H_
