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

/*! \file
 *
 * SUMMARY
 *  \brief This file contains the main interface for structural plasticity
 *
 *
 * Author: Petrut Bogdan
 *
 */
#ifndef _SYNAPTOGENESIS_DYNAMICS_H_
#define _SYNAPTOGENESIS_DYNAMICS_H_

#include <common/neuron-typedefs.h>

//! \brief Initialisation of synaptic rewiring (synaptogenesis)
//! parameters (random seed, spread of receptive field etc.)
//! \param[in] sdram_sp_address Address of the start of the SDRAM region
//! which contains synaptic rewiring params.
//! \return address_t Address after the final word read from SDRAM.
address_t synaptogenesis_dynamics_initialise(
    address_t sdram_sp_address);

//! \brief Function called (usually on a timer from c_main) to
//! trigger the process of synaptic rewiring
//! \param[in] time: the current timestep
//! \param[out] spike: variable to hold the spike
//! \param[out] synaptic_row_address: variable to hold the address of the row
//! \param[out] n_bytes: variable to hold the size of the row
//! \return True if a row is to be transferred, false otherwise
bool synaptogenesis_dynamics_rewire(uint32_t time,
    spike_t *spike, address_t *synaptic_row_address, uint32_t *n_bytes);


//! \brief Formation and elimination are structurally agnostic, i.e. they don't
//! care how synaptic rows are organised in physical memory.
//!
//!  As such, they need to call functions that have a knowledge of how the
//!  memory is physically organised to be able to modify Plastic-Plastic
//!  synaptic regions.
//!
//!  The formation rule calls the add neuron function in the appropriate
//!  module (STDP or static).
//!  \return true if formation was successful
bool synaptogenesis_dynamics_formation_rule(uint32_t time, address_t row);


//! \brief Formation and elimination are structurally agnostic, i.e. they don't
//! care how synaptic rows are organised in physical memory.
//!
//!  As such, they need to call functions that have a knowledge of how the
//!  memory is physically organised to be able to modify Plastic-Plastic
//!  synaptic regions.
//!
//!  The elimination rule calls the remove neuron function in the appropriate
//!  module (STDP or static).
//!  \return true if elimination was successful
bool synaptogenesis_dynamics_elimination_rule(uint32_t time, address_t row);

//! \brief Performs the actual restructuring of a row
//! \param[in] time: The time of the restructure
//! \param[in] row: The row to restructure
//! \return True if the row was changed and needs to be written back
bool synaptogenesis_row_restructure(uint32_t time, address_t row);

//! retrieve the period of rewiring
//! based on is_fast(), this can either mean how many times rewiring happens
//! in a timestep, or how many timesteps have to pass until rewiring happens.
int32_t synaptogenesis_rewiring_period();

//! controls whether rewiring is attempted multiple times per timestep
//! or after a number of timesteps.
bool synaptogenesis_is_fast();

//! Indicates that a spike has been received
void synaptogenesis_spike_received(uint32_t time, spike_t spike);

#endif // _SYNAPTOGENESIS_DYNAMICS_H_
