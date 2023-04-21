/*
 * Copyright (c) 2016 The University of Manchester
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

/*!
 * \dir
 * \brief Structural plasticity interface and algorithms
 * \file
 * \brief This file contains the main interface for structural plasticity
 * \author Petrut Bogdan
 */
#ifndef _SYNAPTOGENESIS_DYNAMICS_H_
#define _SYNAPTOGENESIS_DYNAMICS_H_

#include <common/neuron-typedefs.h>
#include <neuron/population_table/population_table.h>

//! \brief Initialisation of synaptic rewiring (synaptogenesis)
//!     parameters (random seed, spread of receptive field etc.)
//! \param[in] sdram_sp_address: Address of the start of the SDRAM region
//!     which contains synaptic rewiring params.
//! \param[in,out] recording_regions_used:
//!     Variable used to track what recording regions have been used
//! \return Whether we were successful.
bool synaptogenesis_dynamics_initialise(
        address_t sdram_sp_address, uint32_t *recording_regions_used);

//! \brief Trigger the process of synaptic rewiring
//! \details Usually called on a timer registered in c_main()
//! \param[in] time: the current timestep
//! \param[out] spike: variable to hold the spike
//! \param[out] result: The result of the population table lookup
//! \return True if a row is to be transferred, false otherwise
bool synaptogenesis_dynamics_rewire(uint32_t time,
        spike_t *spike, pop_table_lookup_result_t *result);

//! \brief Perform the actual restructuring of a row
//! \param[in] time: The time of the restructure
//! \param[in] row: The row to restructure
//! \return True if the row was changed and needs to be written back
bool synaptogenesis_row_restructure(uint32_t time, synaptic_row_t row);

//! \brief Indicates that a spike has been received
//! \param[in] time: The time that the spike was received at
//! \param[in] spike: The received spike
void synaptogenesis_spike_received(uint32_t time, spike_t spike);

//! \brief Number of updates to do of synaptogenesis this time step
//! \return The number of updates to do this time step
uint32_t synaptogenesis_n_updates(void);

//! \brief Print a certain data object
void print_post_to_pre_entry(void);

#endif // _SYNAPTOGENESIS_DYNAMICS_H_
