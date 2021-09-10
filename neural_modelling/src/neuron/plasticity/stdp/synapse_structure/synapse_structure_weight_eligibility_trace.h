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

#ifndef _SYNAPSE_STRUCTURE_WEIGHT_ELIGIBILITY_TRACE_H_
#define _SYNAPSE_STRUCTURE_WEIGHT_ELIGIBILITY_TRACE_H_

//---------------------------------------
// Structures
//---------------------------------------
// Plastic synapse types have weights and eligibility traces
typedef int32_t plastic_synapse_t;

// The update state is purely a weight state
typedef weight_state_t update_state_t;

// The final state is just a weight as this is
// Both the weight and the synaptic word
typedef weight_t final_state_t;

#include "synapse_structure.h"

//---------------------------------------
// Synapse interface functions
//---------------------------------------
// Synapse parameter get and set helpers
static inline int32_t synapse_structure_get_eligibility_weight(plastic_synapse_t state) {
    return (state >> 16);
}

static inline int32_t synapse_structure_get_eligibility_trace(plastic_synapse_t state) {
    return (state & 0xFFFF);
}

static inline int32_t synapse_structure_update_state(int32_t trace, int32_t weight) {
    return (plastic_synapse_t)(weight << 16 | trace);
}

static inline update_state_t synapse_structure_get_update_state(
        plastic_synapse_t synaptic_word, index_t synapse_type) {
    return weight_get_initial(synaptic_word, synapse_type);
}

//---------------------------------------
static inline final_state_t synapse_structure_get_final_state(
        update_state_t state) {
    return weight_get_final(state);
}

//---------------------------------------
static inline weight_t synapse_structure_get_final_weight(
        final_state_t final_state) {
    return final_state;
}

//---------------------------------------
static inline plastic_synapse_t synapse_structure_get_final_synaptic_word(
        final_state_t final_state) {
    return final_state;
}

// The issue here is that plastic_synapse_t and weight_t aren't the same.. ?
// I'm pretty sure the simple conversion will be problematic at higher weights...
//---------------------------------------
static inline plastic_synapse_t synapse_structure_create_synapse(
        weight_t weight) {
    return (weight_t)weight;
}

static inline weight_t synapse_structure_get_weight(
        plastic_synapse_t synaptic_word) {
    return (weight_t)synaptic_word;
}

static inline void synapse_structure_decay_weight(
        update_state_t state, uint32_t decay) {
    return weight_decay(state, decay);
}

static inline int32_t synapse_structure_get_update_weight(update_state_t state) {
    return weight_get_update(state);
}

#endif  // _SYNAPSE_STRUCTURE_WEIGHT_ELIGIBILITY_TRACE_H_
