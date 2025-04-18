/*
 * Copyright (c) 2017 The University of Manchester
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

//! \file
//! \brief Synapses made of weight and accumulator
#ifndef _SYNAPSE_STRUCUTRE_WEIGHT_STATE_ACCUMULATOR_IMPL_H_
#define _SYNAPSE_STRUCUTRE_WEIGHT_STATE_ACCUMULATOR_IMPL_H_

//---------------------------------------
// Structures
//---------------------------------------
//! Plastic synapse contains normal 16-bit weight and an accumulator
typedef struct plastic_synapse_t {
    //! The state
    weight_t weight;
    //! The accumulator
    int16_t accumulator;
} plastic_synapse_t;

//! The update state is a weight state with 32-bit ARM-friendly version of the
//! accumulator
typedef struct update_state_t {
    //! The weight staet
    weight_state_t weight_state;
    //! The accumulator (in ARM-friendly format)
    int32_t accumulator;
} update_state_t;

//! Final states are actually directly what is stored
typedef plastic_synapse_t final_state_t;

#include "synapse_structure.h"

//! \brief Get the update state from the synapse structure
//! \param[in] synaptic_word: The plastic synapse data
//! \param[in] synapse_type: What (supported) type of synapse is this?
//! \return The update state
//! \details
//!     Creates the update state, using weight-dependence to initialise the
//!     weight state, and copying other parameters from the synaptic word into
//!     32-bit form.
static inline update_state_t synapse_structure_get_update_state(
        plastic_synapse_t synaptic_word, index_t synapse_type) {
    update_state_t update_state;
    update_state.weight_state =
            weight_get_initial(synaptic_word.weight, synapse_type);
    update_state.accumulator = (int32_t) synaptic_word.accumulator;
    return update_state;
}

//---------------------------------------
//! \brief Get the final state from the update state.
//! \param[in] state: the update state
//! \return the final state
static inline final_state_t synapse_structure_get_final_state(
        update_state_t state) {
    // Get weight from state
    weight_t weight = weight_get_final(state.weight_state);

    // Build this into synaptic word along with updated accumulator and state
    return (final_state_t) {
        .weight = weight,
        .accumulator = (int16_t) state.accumulator
    };
}

//---------------------------------------
//! \brief Get the final weight from the final state
//! \param[in] final_state: the final state
//! \return the final weight
static inline weight_t synapse_structure_get_final_weight(
        final_state_t final_state) {
    return final_state.weight;
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
    return (plastic_synapse_t) {
        .weight = weight,
        .accumulator = 0
    };
}

//---------------------------------------
//! \brief Get the current synaptic weight from the plastic synapse data
//! \param[in] synaptic_word: the plastic synapse data
//! \return the current synaptic weight
static inline weight_t synapse_structure_get_weight(
        plastic_synapse_t synaptic_word) {
    return synaptic_word.weight;
}

static inline void synapse_structure_decay_weight(
        update_state_t *state, uint32_t decay) {
    weight_decay(&(state->weight_state), decay);
}

static inline accum synapse_structure_get_update_weight(update_state_t state) {
    return weight_get_update(state.weight_state);
}

#endif // _SYNAPSE_STRUCUTRE_WEIGHT_STATE_ACCUMULATOR_IMPL_H_
