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

#ifndef _SYNAPSE_DYNAMICS_H_
#define _SYNAPSE_DYNAMICS_H_

#include <common/neuron-typedefs.h>
#include <synapse/synapse_row.h>
#include <synapse/structural_plasticity/sp_structs.h>

// Used for post event buffer DMA read
//Maybe move inside a syn typedef with the other defines?
// Defined in spike_processing.c as well!!!!
#define DMA_TAG_READ_POST_BUFFER 2

address_t synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts, bool *has_plastic_synapses);

bool synapse_dynamics_process_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        weight_t *ring_buffers, uint32_t time);

void synapse_dynamics_process_post_synaptic_event(
        uint32_t time);

input_t synapse_dynamics_get_intrinsic_bias(
        uint32_t time, index_t neuron_index);

void synapse_dynamics_print_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        uint32_t *ring_buffer_to_input_buffer_left_shifts);

//! \brief returns the counters for plastic pre synaptic events based
//!        on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or
//!        returns 0
//! \return counters for plastic pre synaptic events or 0
uint32_t synapse_dynamics_get_plastic_pre_synaptic_events(void);

//! \brief returns the number of ring buffer saturation events due to adding
//! plastic weights.
//! \return counter for saturation events or 0
uint32_t synapse_dynamics_get_plastic_saturation_count(void);

//-----------------------------------------------------------------------------
// Synaptic rewiring functions
//-----------------------------------------------------------------------------

//! \brief  Searches the synaptic row for the the connection with the
//!         specified post-synaptic ID
//! \param[in] id: the (core-local) ID of the neuron to search for in the
//! synaptic row
//! \param[in] row: the core-local address of the synaptic row
//! \param[out] sp_data: the address of a struct through which to return
//! weight, delay information
//! \return bool: was the search successful?
bool find_plastic_neuron_with_id(
        uint32_t id, address_t row, structural_plasticity_data_t *sp_data);

//! \brief  Remove the entry at the specified offset in the synaptic row
//! \param[in] offset: the offset in the row at which to remove the entry
//! \param[in] row: the core-local address of the synaptic row
//! \return bool: was the removal successful?
bool remove_plastic_neuron_at_offset(uint32_t offset, address_t row);

//! \brief  Add a plastic entry in the synaptic row
//! \param[in] id: the (core-local) ID of the post-synaptic neuron to be added
//! \param[in] row: the core-local address of the synaptic row
//! \param[in] weight: the initial weight associated with the connection
//! \param[in] delay: the delay associated with the connection
//! \param[in] type: the type of the connection (e.g. inhibitory)
//! \return bool: was the addition successful?
bool add_plastic_neuron_with_id(
        uint32_t id, address_t row, uint32_t weight, uint32_t delay, uint32_t type);


//! \brief  Get the address for the postsynaptic buffer in SDRAM
//! \param[in] tag: the memory tag for the address
//! \return None
void synapse_dynamics_set_post_buffer_region(uint32_t tag);

//! \brief  Allocate the postsynaptic buffer in SDRAM
//! \param[in] tag: the memory tag for the address
//! \return None
void synapse_dynamics_allocate_post_buffer_region(uint32_t tag);

//! \brief Read the postsynaptic buffer
//! \return None
void synapse_dynamics_read_post_buffer();

#endif // _SYNAPSE_DYNAMICS_H_
