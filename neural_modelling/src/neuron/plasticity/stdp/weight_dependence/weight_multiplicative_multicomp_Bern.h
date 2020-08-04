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

#ifndef _WEIGHT_MULTIPLICATIVE_BERN_H_
#define _WEIGHT_MULTIPLICATIVE_BERN_H_

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>
#include <neuron/synapse_row.h>

#include <debug.h>
#include <round.h>

//---------------------------------------
// Structures
//---------------------------------------
typedef struct {

    int32_t min_weight;
    int32_t max_weight;

    REAL learning_rate;

} plasticity_weight_region_data_t;

typedef struct {

    int32_t weight;

    uint32_t weight_shift;
    const plasticity_weight_region_data_t *weight_region;

} weight_state_t;

#include "weight_one_term.h"

//---------------------------------------
// Externals
//---------------------------------------
extern plasticity_weight_region_data_t *plasticity_weight_region_data;
extern uint32_t *weight_shift;

//---------------------------------------
// Weight dependance functions
//---------------------------------------
static inline weight_state_t weight_get_initial(
        weight_t weight, index_t synapse_type) {
    return (weight_state_t ) {
        .weight = (int32_t) weight,
        .weight_shift =
                weight_shift[synapse_type],
        .weight_region = &plasticity_weight_region_data[synapse_type]
    };
}
//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state) {
    log_debug("\tnew_weight:%d\n", new_state.weight);

    return (weight_t) new_state.weight;
}

static inline int32_t convert_real_to_int(REAL value) {
    union {
        REAL input_type;
        int32_t output_type;
    } converter;

    converter.input_type = (value);

    //io_printf(IO_BUF, "weight conv %k returning %k\n", value, converter.output_type);

    return converter.output_type;
}

//---------------------------------------
static inline weight_state_t weight_one_term_apply_update(weight_state_t state, REAL total_rate) {

    //io_printf(IO_BUF, "pre weight %k, learning rate %k\n", state.weight, state.weight_region->learning_rate);

    //io_printf(IO_BUF, "learning rate * rate %k, shift %d\n", state.weight_region->learning_rate * total_rate, state.weight_shift);

    state.weight = state.weight + ((convert_real_to_int(state.weight_region->learning_rate * total_rate)) >> state.weight_shift);

    //io_printf(IO_BUF, "weight updated %k\n", state.weight);

    //MORE EFFICIENT WAY TO DO THIS?
    if(state.weight < state.weight_region->min_weight) {

        state.weight = state.weight_region->min_weight;
    }
    else if(state.weight > state.weight_region->max_weight) {

        state.weight = state.weight_region->max_weight;
    }

    //io_printf(IO_BUF, "max %k min %k\n", state.weight_region->max_weight, state.weight_region->min_weight);

    return state;
}

static inline uint32_t weight_get_shift(weight_state_t state) {

    return state.weight_shift;
}

static weight_state_t weight_one_term_apply_depression(
        weight_state_t state, int32_t depression) {

        //use(state);
        use(depression);

        return state;
        }

static weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t potentiation){

        //use(state);
        use(potentiation);

        return state;
        }

#endif  // _WEIGHT_MULTIPLICATIVE_BERN_H_