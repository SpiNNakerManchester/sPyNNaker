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

#ifndef _WEIGHT_MFVN_IMPL_H_
#define _WEIGHT_MFVN_IMPL_H_

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

    accum a2_plus; // Note: this value is pot_alpha from the python side
    accum a2_minus;
} plasticity_weight_region_data_t;

typedef struct {
    accum weight;

    uint32_t weight_shift;
    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "weight_one_term.h"


//---------------------------------------
// Weight dependance functions
//---------------------------------------
static inline weight_state_t weight_get_initial(weight_t weight,
        index_t synapse_type) {
    //---------------------------------------
    // Externals
    //---------------------------------------
    extern plasticity_weight_region_data_t *plasticity_weight_region_data;
    extern uint32_t *weight_shift;

    accum s1615_weight = kbits(weight << weight_shift[synapse_type]);

    return (weight_state_t ) {
        .weight = s1615_weight,
        .weight_shift = weight_shift[synapse_type],
        .weight_region = &plasticity_weight_region_data[synapse_type]
    };
}

//---------------------------------------
static inline weight_state_t weight_one_term_apply_depression(
        weight_state_t state, int32_t depression_multiplier) {
	if (print_plasticity){
		io_printf(IO_BUF, "\n      Do Depression\n");
		io_printf(IO_BUF, "          Weight prior to depression: %u\n", state.weight);
	}

    // Multiply by depression and subtract
    state.weight -= mul_accum_fixed(state.weight, depression_multiplier);
    state.weight = kbits(MAX(bitsk(state.weight), bitsk(state.weight_region->min_weight)));

    if (print_plasticity){
    	io_printf(IO_BUF, "          Weight after depression: %u\n\n",
    			state.weight);
    }

    return state;
}
//---------------------------------------
static inline weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t a2_plus) {

	// add fixed amount
	if (print_plasticity){
		io_printf(IO_BUF, "        Adding fixed coontribution: %k (int %u)\n",
			state.weight_region->a2_plus << 4,
			state.weight_region->a2_plus);
	}

    state.weight += state.weight_region->a2_plus;
    state.weight = kbits(MIN(bitsk(state.weight), bitsk(state.weight_region->max_weight)));

    return state;

}
//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state) {

    log_debug("\tnew_weight:%d\n", new_state.weight);

    return (weight_t) (bitsk(new_state.weight) >> new_state.weight_shift);
}

static inline void weight_decay(weight_state_t *state, int32_t decay) {
    state->weight = mul_accum_fixed(state->weight, decay);
}

static inline accum weight_get_update(weight_state_t state) {
    return state.weight;
}

#endif  // _WEIGHT_MFVN_IMPL_H_
