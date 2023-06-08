/*
 * Copyright (c) 2019 The University of Manchester
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

#ifndef _WEIGHT_EPROPREG_ONE_TERM_IMPL_H_
#define _WEIGHT_EPROPREG_ONE_TERM_IMPL_H_

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>
#include <neuron/synapse_row.h>

#include <debug.h>

//---------------------------------------
// Structures
//---------------------------------------
typedef struct {
    accum min_weight;
    accum max_weight;
    accum a2_plus;
    accum a2_minus;

    REAL reg_rate;
} plasticity_weight_region_data_t;

typedef struct {
    accum weight;

    uint32_t weight_shift;

    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "weight_one_term.h"

//---------------------------------------
// Externals
//---------------------------------------
//extern plasticity_weight_region_data_t *plasticity_weight_region_data;

//---------------------------------------
// STDP weight dependence functions
//---------------------------------------
static inline weight_state_t weight_get_initial(
        weight_t weight, index_t synapse_type) {
    extern plasticity_weight_region_data_t *plasticity_weight_region_data;
    extern uint32_t *weight_shift;

	accum s1615_weight = kbits(weight << weight_shift[synapse_type]);

    return (weight_state_t) {
        .weight = s1615_weight,
        .weight_shift = weight_shift[synapse_type],
        .weight_region = &plasticity_weight_region_data[synapse_type]
    };
}

//---------------------------------------
static inline weight_state_t weight_one_term_apply_depression(
        weight_state_t state, int32_t a2_minus) {

	if (PRINT_PLASTICITY){
		io_printf(IO_BUF, "depressing: %d\n", a2_minus);
	}
    state.weight -= kbits(a2_minus);
    state.weight = kbits(MAX(bitsk(state.weight), bitsk(state.weight_region->min_weight)));
    return state;
}

//---------------------------------------
static inline weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t a2_plus) {

	if (PRINT_PLASTICITY){
		io_printf(IO_BUF, "potentiating: %d\n", a2_plus);
	}
    state.weight += kbits(a2_plus);
    state.weight = kbits(MIN(bitsk(state.weight), bitsk(state.weight_region->max_weight)));
    return state;
}

//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state,
		REAL reg_error) {
    // Apply eprop plasticity updates to initial weight
	accum new_weight = new_state.weight;
    accum reg_weight = new_weight;
    accum reg_change = 0.0k;
    REAL reg_boundary = 1.0k;

    // Calculate regularisation
    if (new_state.weight_region->reg_rate > 0.0k && (
    		reg_error > reg_boundary || reg_error < -reg_boundary)) {
    	// if reg rate is zero or error small, regularisation is turned off
        reg_change = new_state.weight_region->max_weight * (
        		new_state.weight_region->reg_rate * reg_error);
        reg_weight = new_weight + reg_change;
    }
	if (PRINT_PLASTICITY){
        io_printf(IO_BUF, "\tbefore minmax reg_w:%d, reg_shift:%d, max:%d",
        		reg_weight, reg_change, new_state.weight_region->max_weight);
    }

	if (PRINT_PLASTICITY){
		io_printf(IO_BUF, "\told_weight:%d, a2+:%d, a2-:%d, "
            " new_weight:%d, reg_weight:%d, reg_l_rate:%k, reg_error:%k\n",
            new_state.weight, new_state.weight_region->a2_plus,
			new_state.weight_region->a2_minus, new_weight, reg_weight,
			new_state.weight_region->reg_rate, reg_error);
	}

    return (weight_t) (bitsk(reg_weight) >> new_state.weight_shift);
}

#endif // _WEIGHT_EPROPREG_ONE_TERM_IMPL_H_
