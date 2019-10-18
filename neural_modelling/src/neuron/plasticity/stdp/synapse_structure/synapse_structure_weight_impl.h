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

#ifndef _SYNAPSE_STRUCUTRE_WEIGHT_IMPL_H_
#define _SYNAPSE_STRUCUTRE_WEIGHT_IMPL_H_

//---------------------------------------
// Structures
//---------------------------------------
// Plastic synapse types are just weights;
typedef weight_t plastic_synapse_t;

// The update state is purely a weight state
typedef weight_state_t update_state_t;

// The final state is just a weight as this is
// Both the weight and the synaptic word
typedef weight_t final_state_t;

//---------------------------------------
// Synapse interface functions
//---------------------------------------
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

//---------------------------------------
static inline plastic_synapse_t synapse_structure_create_synapse(
        weight_t weight) {
    return weight;
}

//---------------------------------------
static inline weight_t synapse_structure_get_weight(
        plastic_synapse_t synaptic_word) {
    return synaptic_word;
}

#endif  // _SYNAPSE_STRUCUTRE_WEIGHT_IMPL_H_
