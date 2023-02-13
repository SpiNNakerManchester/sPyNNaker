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
