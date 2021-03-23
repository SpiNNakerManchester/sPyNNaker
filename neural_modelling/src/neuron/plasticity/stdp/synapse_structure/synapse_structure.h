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

#endif // _SYNAPSE_STRUCTURE_H_
