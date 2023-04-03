/*
 * Copyright (c) 2015 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Synapses just hold weight
#ifndef _SYNAPSE_STRUCUTRE_WEIGHT_EPROP_IMPL_H_
#define _SYNAPSE_STRUCUTRE_WEIGHT_EPROP_IMPL_H_

//---------------------------------------
// Structures
//---------------------------------------
//! Plastic synapse types are just weights;
typedef weight_t plastic_synapse_t;

//! The update state is purely a weight state
typedef weight_state_t update_state_t;

// The final state is just a weight as this is
//! Both the weight and the synaptic word
typedef weight_t final_state_t;

#include "synapse_structure.h"

//---------------------------------------
// Synapse interface functions
//---------------------------------------
//! \brief Get the update state from the synapse structure
//! \param[in] synaptic_word: The plastic synapse data
//! \param[in] synapse_type: What (supported) type of synapse is this?
//! \return The update state
static inline update_state_t synapse_structure_get_update_state(
        plastic_synapse_t synaptic_word, index_t synapse_type) {
    return weight_get_initial(synaptic_word, synapse_type);
}

//---------------------------------------
//! \brief Get the final state from the update state.
//! \param[in] state: the update state
//! \return the final state
static inline final_state_t synapse_structure_get_final_state(
        update_state_t state, REAL reg_error) {
    return weight_get_final(state, reg_error);
}

//---------------------------------------
//! \brief Get the final weight from the final state
//! \param[in] final_state: the final state
//! \return the final weight
static inline weight_t synapse_structure_get_final_weight(
        final_state_t final_state) {
    return final_state;
}

//---------------------------------------
//! \brief Get the final plastic synapse data from the final state
//! \param[in] final_state: the final state
//! \return the final plastic synapse data, ready to be stored
static inline plastic_synapse_t synapse_structure_get_final_synaptic_word(
        final_state_t final_state) {
    return final_state;
}

//---------------------------------------
//! \brief Create the initial plastic synapse data
//! \param[in] weight: the initial synaptic weight
//! \return the plastic synapse data
static inline plastic_synapse_t synapse_structure_create_synapse(
        weight_t weight) {
    return weight;
}

//---------------------------------------
//! \brief Get the current synaptic weight from the plastic synapse data
//! \param[in] synaptic_word: the plastic synapse data
//! \return the current synaptic weight
static inline weight_t synapse_structure_get_weight(
        plastic_synapse_t synaptic_word) {
    return synaptic_word;
}

static inline void synapse_structure_decay_weight(
        update_state_t *state, uint32_t decay) {
    return weight_decay(state, decay);
}

static inline accum synapse_structure_get_update_weight(update_state_t state) {
    return weight_get_update(state);
}

#endif  // _SYNAPSE_STRUCUTRE_WEIGHT_EPROP_IMPL_H_
