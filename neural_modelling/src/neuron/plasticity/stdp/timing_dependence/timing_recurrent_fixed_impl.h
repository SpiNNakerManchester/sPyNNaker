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

#ifndef _TIMING_RECURRENT_FIXED_IMPL_H_
#define _TIMING_RECURRENT_FIXED_IMPL_H_

typedef struct post_trace_t {
} post_trace_t;

typedef struct pre_trace_t {
} pre_trace_t;

typedef struct {
    int32_t accumulator_depression_plus_one;
    int32_t accumulator_potentiation_minus_one;
    uint32_t pre_window_length;
    uint32_t post_window_length;
} plasticity_trace_region_data_t;

#define STRUCTURE_PATH(file) <neuron/plasticity/stdp/synapse_structure/file>
#include STRUCTURE_PATH(synapse_structure_weight_state_accumulator_impl.h)
#include "timing_recurrent_common.h"

static inline bool timing_recurrent_in_pre_window(
        uint32_t time_since_last_event, update_state_t previous_state) {
    return (time_since_last_event
            < plasticity_trace_region_data.pre_window_length);
}

static inline bool timing_recurrent_in_post_window(
        uint32_t time_since_last_event, update_state_t previous_state) {
    return (time_since_last_event
            < plasticity_trace_region_data.post_window_length);
}

static inline update_state_t timing_recurrent_calculate_pre_window(
        update_state_t previous_state) {
    return previous_state;
}

static inline update_state_t timing_recurrent_calculate_post_window(
        update_state_t previous_state) {
    return previous_state;
}

#endif  // _TIMING_RECURRENT_FIXED_IMPL_H_
