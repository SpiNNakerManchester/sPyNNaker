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

#ifndef _SYNAPSE_STRUCTURE_WEIGHT_STATE_ACCUMULATOR_WINDOW_H_
#define _SYNAPSE_STRUCTURE_WEIGHT_STATE_ACCUMULATOR_WINDOW_H_

// Plastic synapse contains normal 16-bit weight, a small state machine and an
// accumulator
typedef struct plastic_synapse_t {
    unsigned int weight :16;
    int accumulator :4;
    unsigned int state :2;
    unsigned int window_length :10;
} plastic_synapse_t;

// The update state is a weight state with 32-bit ARM-friendly versions of the
// accumulator and the state
typedef struct update_state_t {
    weight_state_t weight_state;

    int32_t accumulator;
    int32_t state;

    uint32_t window_length;
} update_state_t;

typedef plastic_synapse_t final_state_t;

#include "synapse_structure.h"

static inline update_state_t synapse_structure_get_update_state(
        plastic_synapse_t synaptic_word, index_t synapse_type) {
    // Create update state, using weight dependance to initialise the weight
    // state and copying other parameters from the synaptic word into 32-bit
    // form
    update_state_t update_state;
    update_state.weight_state =
            weight_get_initial(synaptic_word.weight, synapse_type);
    update_state.accumulator = (int32_t) synaptic_word.accumulator;
    update_state.state = (uint32_t) synaptic_word.state;
    update_state.window_length = (uint32_t) synaptic_word.window_length;
    return update_state;
}

//---------------------------------------
static inline final_state_t synapse_structure_get_final_state(
        update_state_t state) {
    // Get weight from state
    weight_t weight = weight_get_final(state.weight_state);

    // Build this into synaptic word along with updated accumulator and state
    return (final_state_t) {
        .weight = weight,
        .accumulator = (int) state.accumulator,
        .state = (unsigned int) state.state,
        .window_length = (unsigned int)state.window_length
    };
}

//---------------------------------------
static inline weight_t synapse_structure_get_final_weight(
        final_state_t final_state) {
    return final_state.weight;
}

//---------------------------------------
static inline plastic_synapse_t synapse_structure_get_final_synaptic_word(
        final_state_t final_state) {
    return final_state;
}

//---------------------------------------
static inline plastic_synapse_t synapse_structure_create_synapse(
        weight_t weight) {
    return (plastic_synapse_t) {
        .weight = weight,
        .accumulator = 0,
        .state = 0,
        .window_length = 0
    };
}

//---------------------------------------
static inline weight_t synapse_structure_get_weight(
        plastic_synapse_t synaptic_word) {
    return synaptic_word.weight;
}

#endif // _SYNAPSE_STRUCTURE_WEIGHT_STATE_ACCUMULATOR_WINDOW_H_
