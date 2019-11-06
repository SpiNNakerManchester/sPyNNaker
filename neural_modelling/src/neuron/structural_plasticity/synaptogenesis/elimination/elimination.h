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

#ifndef _ELIMINATION_H_
#define _ELIMINATION_H_

#include <neuron/structural_plasticity/synaptogenesis/sp_structs.h>

//! \brief Read and return an elimination parameter data structure from the
//!        data stream
//! \param[in/out] The data stream to read from, updated to the new position
//!                after the read is done
//! \return the read parameters data structure
struct elimination_params *synaptogenesis_elimination_init(uint8_t **data);

//! \brief Elimination rule for synaptogenesis
//! \param[in] current_state Pointer to current state
//! \param[in] time Time of elimination
//! \param[in] row The row to eliminate from
//! \return if row was modified
static inline bool synaptogenesis_elimination_rule(
        current_state_t *current_state, struct elimination_params *params,
        uint32_t time, address_t row);

#endif // _ELIMINATION_H_
