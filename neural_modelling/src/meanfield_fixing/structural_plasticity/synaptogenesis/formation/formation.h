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
//! \brief Synapse formation algorithms
//! \file
//! \brief API for synapse formation
#ifndef _FORMATION_H_
#define _FORMATION_H_

#include <neuron/structural_plasticity/synaptogenesis/sp_structs.h>
typedef struct formation_params formation_params_t;

//! \brief Read and return an formation parameter data structure from the
//!     data stream
//! \param[in,out] data: The data stream to read from, updated to the new
//!     position after the read is done
//! \return the read parameters data structure
formation_params_t *synaptogenesis_formation_init(uint8_t **data);

//! \brief Formation rule for synaptogenesis; picks what neuron in the
//!     _current_ population will have a synapse added, and then performs the
//!     addition.
//! \param[in] current_state: Pointer to current state
//! \param[in] params: Pointer to rewiring data
//! \param[in] time: Time of formation
//! \param[in] row: The row to form within
//! \return if row was modified
static inline bool synaptogenesis_formation_rule(
        current_state_t *current_state, const formation_params_t *params,
        uint32_t time, synaptic_row_t row);

#endif // _FORMATION_H_
