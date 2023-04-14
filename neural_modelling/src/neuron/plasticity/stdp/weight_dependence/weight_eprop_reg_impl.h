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
//    state.weight -= mul_accum_fixed(state.weight_region->a2_minus, a2_minus);
    state.weight -= kbits(a2_minus);
    state.weight = kbits(MAX(bitsk(state.weight), bitsk(state.weight_region->min_weight)));
    return state;
//    state.a2_minus += a2_minus;
//    return state;
}

//---------------------------------------
static inline weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t a2_plus) {

	if (PRINT_PLASTICITY){
		io_printf(IO_BUF, "potentiating: %d\n", a2_plus);
	}
//	log_info("weight %k a2_plus %d converted to %k bitsk(weight) %d",
//			state.weight, a2_plus, kbits(a2_plus), bitsk(state.weight));
//    state.weight += mul_accum_fixed(state.weight_region->a2_plus, a2_plus);
    state.weight += kbits(a2_plus);
    state.weight = kbits(MIN(bitsk(state.weight), bitsk(state.weight_region->max_weight)));
//    log_info("weight after min of max %k", state.weight);
    return state;
//    state.a2_plus += a2_plus;
//    return state;
}

//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state,
		REAL reg_error) {
    // Scale potentiation and depression
    // **NOTE** A2+ and A2- are pre-scaled into weight format
//    int32_t scaled_a2_plus = STDP_FIXED_MUL_16X16(
//            new_state.a2_plus, new_state.weight_region->a2_plus);
//    int32_t scaled_a2_minus = STDP_FIXED_MUL_16X16(
//            new_state.a2_minus, new_state.weight_region->a2_minus);

    // Apply eprop plasticity updates to initial weight
//	accum new_weight = bitsk(new_state.weight) >> new_state.weight_shift;
	accum new_weight = new_state.weight;
//    int32_t new_weight =
//            new_state.initial_weight + new_state.a2_plus + new_state.a2_minus;
    accum reg_weight = new_weight;
    accum reg_change = 0.0k;
    REAL reg_boundary = 1.0k;

    // Calculate regularisation
    if (new_state.weight_region->reg_rate > 0.0k && (reg_error > reg_boundary || reg_error < -reg_boundary)){ // if reg rate is zero or error small, regularisation is turned off
//        reg_change = new_weight * new_state.weight_region->reg_rate * reg_error;
//    	if (reg_error > 0){
//    		reg_error -= reg_boundary;
//    	} else if (reg_error < 0){
//    		reg_error += reg_boundary;
//    	}
        reg_change = new_state.weight_region->max_weight * new_state.weight_region->reg_rate * reg_error;
        reg_weight = new_weight + reg_change;
//        io_printf(IO_BUF, "\tw:%d + reg_shift:%d = reg_w:%d -- err:%k\n", new_weight, reg_change, reg_weight, reg_error);
    }
	if (PRINT_PLASTICITY){
        io_printf(IO_BUF, "\tbefore minmax reg_w:%d, reg_shift:%d, max:%d", reg_weight, reg_change, new_state.weight_region->max_weight);
    }
    // Clamp new weight to bounds (not sure this is needed now?)
//    reg_weight = MIN(new_state.weight_region->max_weight,
//            MAX(reg_weight, new_state.weight_region->min_weight));

	if (PRINT_PLASTICITY){
		io_printf(IO_BUF, "\told_weight:%d, a2+:%d, a2-:%d, "
				//    		"scaled a2+:%d, scaled a2-:%d,"
            " new_weight:%d, reg_weight:%d, reg_l_rate:%k, reg_error:%k\n",
            new_state.weight, new_state.weight_region->a2_plus, new_state.weight_region->a2_minus,
			//            scaled_a2_plus, scaled_a2_minus,
			new_weight, reg_weight, new_state.weight_region->reg_rate, reg_error);
	}

//	log_info("reg_weight %k new_weight %k reg_error %k reg_change %k reg_boundary %k",
//			reg_weight, new_weight, reg_error, reg_change, reg_boundary);

    return (weight_t) (bitsk(reg_weight) >> new_state.weight_shift);
}

#endif // _WEIGHT_EPROPREG_ONE_TERM_IMPL_H_
