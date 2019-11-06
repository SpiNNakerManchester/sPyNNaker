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

#ifndef _TIMING_IZHIKEVICH_NEUROMODULATION_H_
#define _TIMING_IZHIKEVICH_NEUROMODULATION_H_

//---------------------------------------
// Typedefines
//---------------------------------------
typedef int32_t post_trace_t;
typedef int16_t pre_trace_t;

#include <neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_eligibility_trace.h>
//#include "timing.h"

// Include debug header for log_info etc
#include <debug.h>

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>

//---------------------------------------
// Externals
//---------------------------------------
extern int16_lut *tau_plus_lookup; //[TAU_PLUS_SIZE];
extern int16_lut *tau_minus_lookup; //[TAU_MINUS_SIZE];
extern int16_lut *tau_c_lookup; //[TAU_C_SIZE];
extern int16_lut *tau_d_lookup; //[TAU_D_SIZE];

//---------------------------------------
// Macros
//---------------------------------------
// Exponential decay lookup parameters
//#define TAU_PLUS_TIME_SHIFT 0
//#define TAU_PLUS_SIZE 256
//
//#define TAU_MINUS_TIME_SHIFT 0
//#define TAU_MINUS_SIZE 256
//
//#define TAU_C_TIME_SHIFT 4
//#define TAU_C_SIZE 520
//
//#define TAU_D_TIME_SHIFT 2
//#define TAU_D_SIZE 370

// Helper macros for looking up decays
#define DECAY_LOOKUP_TAU_PLUS(time) \
    maths_lut_exponential_decay(time, tau_plus_lookup)
#define DECAY_LOOKUP_TAU_MINUS(time) \
    maths_lut_exponential_decay(time, tau_minus_lookup)
#define DECAY_LOOKUP_TAU_C(time) \
    maths_lut_exponential_decay(time, tau_c_lookup)
#define DECAY_LOOKUP_TAU_D(time) \
    maths_lut_exponential_decay(time, tau_d_lookup)

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace() {
    return (post_trace_t) 0;
}

// Trace get and set helper funtions
static inline int32_t get_post_trace(int32_t trace) {
    return (trace >> 16);
}

static inline int32_t get_dopamine_trace(int32_t trace) {
    return (trace & 0xFFFF);
}

static inline int32_t trace_build(int32_t post_trace, int32_t dopamine_trace) {
    return (post_trace << 16 | dopamine_trace);
}

//---------------------------------------
static inline post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {

    // Get time since last spike
    uint32_t delta_time = time - last_time;

    // Decay previous post trace
    int32_t decayed_post_trace = STDP_FIXED_MUL_16X16(get_post_trace(last_trace),
            DECAY_LOOKUP_TAU_MINUS(delta_time));

    // Add energy caused by new spike to trace
    int32_t new_post_trace = decayed_post_trace + STDP_FIXED_POINT_ONE;

    // Decay previous dopamine trace
    int32_t new_dopamine_trace = STDP_FIXED_MUL_16X16(get_dopamine_trace(last_trace),
            DECAY_LOOKUP_TAU_D(delta_time));

    // Return new pre- synaptic event with decayed trace values with energy
    // for new spike added
    return (post_trace_t) trace_build(new_post_trace, new_dopamine_trace);
}

//---------------------------------------
static inline pre_trace_t timing_add_pre_spike(
        uint32_t time, uint32_t last_time, pre_trace_t last_trace) {

    // Get time since last spike
    uint32_t delta_time = time - last_time;

    // Decay previous pre-synaptic trace
    int32_t decayed_pre_trace = STDP_FIXED_MUL_16X16(
        last_trace, DECAY_LOOKUP_TAU_PLUS(delta_time));

    // Add energy caused by new spike to trace
    int32_t new_pre_trace = decayed_pre_trace + STDP_FIXED_POINT_ONE;

    // Return new pre-synaptic event with decayed trace values with energy
    // for new spike added
    return (pre_trace_t) new_pre_trace;
}

#endif // _TIMING_IZHIKEVICH_NEUROMODULATION_H_
