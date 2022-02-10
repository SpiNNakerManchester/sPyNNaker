/*
 * Copyright (c) 2017-2021 The University of Manchester
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

#ifndef _TIMING_MFVN_IMPL_H_
#define _TIMING_MFVN_IMPL_H_

//---------------------------------------
// Typedefines
//---------------------------------------
typedef int16_t post_trace_t;
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
// Macros
//---------------------------------------
// Exponential decay lookup parameters
#define TAU_PLUS_TIME_SHIFT 0

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace(void) {
    return 0;
}

static inline post_trace_t timing_decay_post(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {
    extern int16_lut *exp_cos_lookup;
    // Get time since last spike
    uint32_t delta_time = time - last_time;

    // Decay previous o1 and o2 traces
    return (post_trace_t) STDP_FIXED_MUL_16X16(last_trace,
            maths_lut_exponential_decay(delta_time, exp_cos_lookup));
}

//---------------------------------------
static inline post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {
    use(time);
    use(last_time);
    use(&last_trace);

	if (print_plasticity){
		io_printf(IO_BUF, "Adding pre spike to event history (from vestibular nuclei)\n");
	}

    // Add energy caused by new spike to trace
    // **NOTE** o2 trace is pre-multiplied by a3_plus
    int32_t new_o1_trace = 0; //decayed_o1_trace + STDP_FIXED_POINT_ONE;

    // Return new pre- synaptic event with decayed trace values with energy
    // for new spike added
    return (post_trace_t) new_o1_trace;
}

//---------------------------------------
static inline pre_trace_t timing_add_pre_spike(
        uint32_t time, uint32_t last_time, pre_trace_t last_trace) {
    use(time);
    use(last_time);
    use(&last_trace);

    return (pre_trace_t) 0; //new_r1_trace;
}

//---------------------------------------
static inline update_state_t timing_apply_pre_spike(
        uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(time);
    use(&trace);
    use(last_pre_time);
    use(last_post_time);
    use(&last_pre_trace);
    use(&last_post_trace);

    // Here we will potentiate by the fixed amount alpha
    if (print_plasticity){
    	io_printf(IO_BUF, "\n############ Phase 3 #############");
    	io_printf(IO_BUF, "\n    Now do potentiation\n");
    }

    return weight_one_term_apply_potentiation(previous_state, 0);
}

//---------------------------------------
static inline update_state_t timing_apply_post_spike(
        uint32_t time, post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(time);
    use(&trace);
    use(last_pre_time);
    use(last_post_time);
    use(&last_pre_trace);
    use(&last_post_trace);
    extern int16_lut *exp_cos_lookup;

    // This is where we lookup the value of e^(-bx) * cos(x)^2

    // Get time of event relative to last pre-synaptic event
    uint32_t time_since_last_pre = last_pre_time; //time - last_pre_time;

    if (print_plasticity){
    	io_printf(IO_BUF, "        delta t = %u,    ", time_since_last_pre);
    }

    if (time_since_last_pre < 255){
        int32_t multiplier = maths_lut_exponential_decay_time_shifted(
                time_since_last_pre, TAU_PLUS_TIME_SHIFT, exp_cos_lookup);

        if (print_plasticity){
        	io_printf(IO_BUF, "multiplier: %k (fixed = %u)\n", multiplier << 4, multiplier);
        }

        return weight_one_term_apply_depression(previous_state, multiplier);
    }

    if (print_plasticity){
    	io_printf(IO_BUF, "        delta t = %u,    ", time_since_last_pre);
    	io_printf(IO_BUF, "        out of LUT range - do nothing");
    }

    return previous_state;
}

#endif // _TIMING_MFVN_IMPL_H_
