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
 *  \brief This file contains the static impl of synaptogenesis.
 *  No functionality is gained with this class
 *
 */
#include "synaptogenesis_dynamics.h"
#include <debug.h>

static const char* sp_error_message = "Non-structurally plastic impl.";

//! \brief Initialisation of synaptic rewiring (synaptogenesis)
//! parameters (random seed, spread of receptive field etc.)
//! \param[in] sdram_sp_address Address of the start of the SDRAM region
//! which contains synaptic rewiring params.
//! \return address_t Address after the final word read from SDRAM.
address_t synaptogenesis_dynamics_initialise(
	address_t sdram_sp_address){
	use(sdram_sp_address);
	log_debug("%s", sp_error_message);
    return sdram_sp_address;
}

//! \brief Function called (usually on a timer from c_main) to
//! trigger the process of synaptic rewiring
//! \param[in] time: the current timestep
//! \return None
void synaptogenesis_dynamics_rewire(uint32_t time){
    use(time);
    log_error("%s", sp_error_message);
}

//! \brief This function is a rewiring DMA callback
//! \param[in] dma_id: the ID of the DMA
//! \param[in] dma_tag: the DMA tag, i.e. the tag used for reading row for rew.
//! \return nothing
void synaptic_row_restructure(){
    log_error("%s", sp_error_message);
}

//!
//!   Formation and elimination are structurally agnostic, i.e. they don't
//!   care how synaptic rows are organised in physical memory.
//!
//!   As such, they need to call functions that have a knowledge of how the
//!   memory is physically organised to be able to modify Plastic-Plastic
//!   synaptic regions.
//!
//!   The formation rule calls the add neuron function in the appropriate
//!   module (STDP or static).
//!
bool synaptogenesis_dynamics_formation_rule(){
    return false;
}

//!
//!   Formation and elimination are structurally agnostic, i.e. they don't
//!   care how synaptic rows are organised in physical memory.
//!
//!   As such, they need to call functions that have a knowledge of how the
//!   memory is physically organised to be able to modify Plastic-Plastic
//!   synaptic regions.
//!
//!   The elimination rule calls the remove neuron function in the appropriate
//!   module (STDP or static).
//!
bool synaptogenesis_dynamics_elimination_rule(){
    return false;
}

//! retrieve the period of rewiring
//! based on is_fast(), this can either mean how many times rewiring happens
//! in a timestep, or how many timesteps have to pass until rewiring happens.
int32_t get_p_rew() {
    return -1;
}

//! controls whether rewiring is attempted multiple times per timstep
//! or after a number of timesteps.
bool is_fast() {
    return false;
}

//! after a set of rewiring attempts, update the indices in the circular buffer
//! between which we will be looking at the next batch of attempts
void update_goal_posts(uint32_t time) {
    use(time);
}
