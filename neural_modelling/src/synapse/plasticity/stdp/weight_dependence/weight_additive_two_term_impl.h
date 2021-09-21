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

#ifndef _WEIGHT_ADDITIVE_TWO_TERM_IMPL_H_
#define _WEIGHT_ADDITIVE_TWO_TERM_IMPL_H_

// Include generic plasticity maths functions
#include <synapse/plasticity/stdp/maths.h>
#include <synapse/plasticity/stdp/stdp_typedefs.h>
#include <synapse/synapse_row.h>

#include <debug.h>

//---------------------------------------
// Structures
//---------------------------------------
typedef struct {
    int32_t min_weight;
    int32_t max_weight;

    int32_t a2_plus;
    int32_t a2_minus;
    int32_t a3_plus;
    int32_t a3_minus;
} plasticity_weight_region_data_t;

typedef struct weight_state_t {
    int32_t initial_weight;

    int32_t a2_plus;
    int32_t a2_minus;
    int32_t a3_plus;
    int32_t a3_minus;

    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "weight_two_term.h"

//---------------------------------------
// Externals
//---------------------------------------
extern plasticity_weight_region_data_t *plasticity_weight_region_data;

//---------------------------------------
// STDP weight dependance functions
//---------------------------------------
static inline weight_state_t weight_get_initial(
        weight_t weight, index_t synapse_type) {
    return (weight_state_t) {
        .initial_weight = (int32_t) weight,
        .a2_plus = 0,
        .a2_minus = 0,
        .a3_plus = 0,
        .a3_minus = 0,
        .weight_region =&plasticity_weight_region_data[synapse_type]
    };
}

//---------------------------------------
static inline weight_state_t weight_two_term_apply_depression(
        weight_state_t state, int32_t a2_minus, int32_t a3_minus) {
    state.a2_minus += a2_minus;
    state.a3_minus += a3_minus;
    return state;
}

//---------------------------------------
static inline weight_state_t weight_two_term_apply_potentiation(
        weight_state_t state, int32_t a2_plus, int32_t a3_plus) {
    state.a2_plus += a2_plus;
    state.a3_plus += a3_plus;
    return state;
}

//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state) {
    // Scale potentiation and depression
    // **NOTE** A2+, A2-, A3+ and A3- are pre-scaled into weight format
    int32_t scaled_a2_plus = STDP_FIXED_MUL_16X16(
            new_state.a2_plus, new_state.weight_region->a2_plus);
    int32_t scaled_a2_minus = STDP_FIXED_MUL_16X16(
            new_state.a2_minus, new_state.weight_region->a2_minus);
    int32_t scaled_a3_plus = STDP_FIXED_MUL_16X16(
            new_state.a3_plus, new_state.weight_region->a3_plus);
    int32_t scaled_a3_minus = STDP_FIXED_MUL_16X16(
            new_state.a3_minus, new_state.weight_region->a3_minus);

    // Apply all terms to initial weight
    int32_t new_weight = new_state.initial_weight + scaled_a2_plus
            + scaled_a3_plus - scaled_a2_minus - scaled_a3_minus;

    // Clamp new weight
    new_weight = MIN(new_state.weight_region->max_weight,
            MAX(new_weight, new_state.weight_region->min_weight));

    log_debug("\told_weight:%u, a2+:%d, a2-:%d, a3+:%d, a3-:%d",
            new_state.initial_weight, new_state.a2_plus,
            new_state.a2_minus, new_state.a3_plus, new_state.a3_minus);
    log_debug("\tscaled a2+:%d, scaled a2-:%d, scaled a3+:%d, scaled a3-:%d,"
            " new_weight:%d",
            scaled_a2_plus, scaled_a2_minus, scaled_a3_plus,
            scaled_a3_minus, new_weight);

    return (weight_t) new_weight;
}

#endif  // _WEIGHT_ADDITIVE_TWO_TERM_IMPL_H_
