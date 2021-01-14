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

#ifndef _TIMING_BERN_H_
#define _TIMING_BERN_H_

//---------------------------------------
// Typedefines
//---------------------------------------
typedef int16_t post_trace_t;
typedef int16_t pre_trace_t;

#include <neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h>
#include "timing.h"

// Include debug header for log_info etc
#include <debug.h>

#include <round.h>

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>

//---------------------------------------
// Macros
//---------------------------------------
// Exponential decay lookup parameters
#define TAU_PLUS_TIME_SHIFT 0
#define TAU_PLUS_SIZE 256

#define TAU_MINUS_TIME_SHIFT 0
#define TAU_MINUS_SIZE 256

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace(void) {
    return 0;
}

static inline update_state_t timing_apply_rate(update_state_t current_state, REAL post_diff, REAL pre_rate) {

    REAL post_rate = post_diff * pre_rate;

    //io_printf(IO_BUF, " pre_rate %k rate product plast %k\n", pre_rate, post_rate);
    //io_printf(IO_BUF, "pre rate %k, post rate %k\n", pre_rate, post_rate);

    return weight_one_term_apply_update(current_state, post_rate);
}

static post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace){

        use(time);
        use(last_time);
        use(last_trace);

        return last_trace;
        }

static pre_trace_t timing_add_pre_spike(
        uint32_t time, uint32_t last_time, pre_trace_t last_trace){

        use(time);
        use(last_time);
        use(last_trace);

        return last_trace;
        }

static update_state_t timing_apply_pre_spike(
        uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace,  uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {

        use(time);
        use(trace);
        use(last_pre_time);
        use(last_pre_trace);
        use(last_post_time);
        use(last_post_trace);
        //use(previous_state);

        return previous_state;
        }

static update_state_t timing_apply_post_spike(
        uint32_t time, post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state){

        use(time);
        use(trace);
        use(last_pre_time);
        use(last_pre_trace);
        use(last_post_time);
        use(last_post_trace);
        //use(previous_state);

        return previous_state;
        }

#endif // _TIMING_BERN_H_