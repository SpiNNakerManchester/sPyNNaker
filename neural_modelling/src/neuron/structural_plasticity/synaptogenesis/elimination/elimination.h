/*
 * Copyright (c) 2017-2023 The University of Manchester
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
//! \brief Synapse elimination algorithms
//! \file
//! \brief API for synapse elimination
#ifndef _ELIMINATION_H_
#define _ELIMINATION_H_

#include <neuron/structural_plasticity/synaptogenesis/sp_structs.h>
typedef struct elimination_params elimination_params_t;

//! \brief Read and return an elimination parameter data structure from the
//!     data stream
//! \param[in,out] data: The data stream to read from, updated to the new
//!     position after the read is done
//! \return the read parameters data structure
elimination_params_t *synaptogenesis_elimination_init(uint8_t **data);

//! \brief Elimination rule for synaptogenesis
//! \param[in,out] current_state: Pointer to current state
//! \param[in] params: The elimination rule configuration.
//! \param[in] time: Time of elimination
//! \param[in,out] row: The row to eliminate from
//! \return if row was modified
static inline bool synaptogenesis_elimination_rule(
        current_state_t *current_state, const elimination_params_t *params,
        uint32_t time, synaptic_row_t row);

#endif // _ELIMINATION_H_
