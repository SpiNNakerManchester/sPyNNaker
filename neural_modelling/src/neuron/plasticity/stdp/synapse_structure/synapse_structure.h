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

//! \dir
//! \brief Synaptic state management
//! \file
//! \brief API for synaptic state
//!
//! Implementations of this have one or more of:
//! * weight
//! * state
//! * accumulator
//! * event window
#ifndef _SYNAPSE_STRUCTURE_H_
#define _SYNAPSE_STRUCTURE_H_

#include <neuron/plasticity/stdp/weight_dependence/weight.h>

//! \brief Get the update state from the synapse structure
//! \param[in] synaptic_word: The plastic synapse data
//! \param[in] synapse_type: What (supported) type of synapse is this?
//! \return The update state
static update_state_t synapse_structure_get_update_state(
        plastic_synapse_t synaptic_word, index_t synapse_type);

//! \brief Get the final state from the update state.
//! \param[in] state: the update state
//! \return the final state
static final_state_t synapse_structure_get_final_state(
        update_state_t state);

//! \brief Get the final weight from the final state
//! \param[in] final_state: the final state
//! \return the final weight
static weight_t synapse_structure_get_final_weight(
        final_state_t final_state);

//! \brief Get the final plastic synapse data from the final state
//! \param[in] final_state: the final state
//! \return the final plastic synapse data, ready to be stored
static plastic_synapse_t synapse_structure_get_final_synaptic_word(
        final_state_t final_state);

//! \brief Create the initial plastic synapse data
//! \param[in] weight: the initial synaptic weight
//! \return the plastic synapse data
static plastic_synapse_t synapse_structure_create_synapse(weight_t weight);

//! \brief Get the current synaptic weight from the plastic synapse data
//! \param[in] synaptic_word: the plastic synapse data
//! \return the current synaptic weight
static weight_t synapse_structure_get_weight(plastic_synapse_t synaptic_word);

//! \brief Decay the synaptic weight value stored by multiplication
//! \param[in] state The update state containing the current weight
//! \param[in] decay The "decay" to multiply the weight by, in STDP fixed point
//!                  format
static void synapse_structure_decay_weight(update_state_t *state, uint32_t decay);

//! \brief Get the current synaptic weight stored in the update state
//! \param[in] state The update state containing the current weight
//! \return The current weight in s1615 fixed point format
static accum synapse_structure_get_update_weight(update_state_t state);

#endif // _SYNAPSE_STRUCTURE_H_
