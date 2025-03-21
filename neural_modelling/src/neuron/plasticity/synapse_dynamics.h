/*
 * Copyright (c) 2015 The University of Manchester
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

//! \dir
//! \brief Dynamic synapses
//! \file
//! \brief API for synapse dynamics
#ifndef _SYNAPSE_DYNAMICS_H_
#define _SYNAPSE_DYNAMICS_H_

#include <common/neuron-typedefs.h>
#include <neuron/synapse_row.h>

//! \brief Initialise the synapse dynamics
//! \param[in] address: Where the configuration data is
//! \param[in] n_neurons: Number of neurons
//! \param[in] n_synapse_types: Number of synapse types
//! \param[in] ring_buffer_to_input_buffer_left_shifts:
//!     How to interpret the values from the ring buffers
//! \return Whether the initialisation succeeded.
bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts);

//! \brief Process the dynamics of the synapses
//! \param[in,out] plastic_region_data: Where the plastic data is
//! \param[in] fixed_region: Where the fixed data is
//! \param[in,out] ring_buffers: The ring buffers
//! \param[in] time: The current simulation time
//! \param[out] Whether to write back anything
//! \return Whether the processing was successful or not
bool synapse_dynamics_process_plastic_synapses(
        synapse_row_plastic_data_t *plastic_region_data,
        synapse_row_fixed_part_t *fixed_region,
        weight_t *ring_buffers, uint32_t time, uint32_t colour_delay,
        bool *write_back);

//! \brief Inform the synapses that the neuron fired
//! \param[in] time: The current simulation time
//! \param[in] neuron_index: Which neuron are we processing
void synapse_dynamics_process_post_synaptic_event(
        uint32_t time, index_t neuron_index);

//! \brief Print the synapse dynamics
//! \param[in] plastic_region_data: Where the plastic data is
//! \param[in] fixed_region: Where the fixed data is
//! \param[in] ring_buffer_to_input_buffer_left_shifts:
//!     How to interpret the values from the ring buffers
void synapse_dynamics_print_plastic_synapses(
        synapse_row_plastic_data_t *plastic_region_data,
        synapse_row_fixed_part_t *fixed_region,
        uint32_t *ring_buffer_to_input_buffer_left_shifts);

//! \brief Get the counters for plastic pre synaptic events based on (if
//!     the model was compiled with SYNAPSE_BENCHMARK parameter) or returns 0
//! \return counters for plastic pre synaptic events or 0
uint32_t synapse_dynamics_get_plastic_pre_synaptic_events(void);

//! \brief Get the number of ring buffer saturation events due to adding
//!     plastic weights.
//! \return counter for saturation events or 0
uint32_t synapse_dynamics_get_plastic_saturation_count(void);

//-----------------------------------------------------------------------------
// Synaptic rewiring functions
//-----------------------------------------------------------------------------

//! \brief Search the synaptic row for the the connection with the
//!     specified post-synaptic ID
//! \param[in] id: the (core-local) ID of the neuron to search for in the
//!     synaptic row
//! \param[in] row: the core-local address of the synaptic row
//! \param[out] weight: address to contain the weight of the connection
//! \param[out] delay: address to contain the delay of the connection
//! \param[out] offset: address to contain the offset of the connection
//! \param[out] synapse_type: the synapse type of the connection
//! \return was the search successful?
bool synapse_dynamics_find_neuron(
        uint32_t id, synaptic_row_t row, weight_t *weight, uint16_t *delay,
        uint32_t *offset, uint32_t *synapse_type);

//! \brief Remove the entry at the specified offset in the synaptic row
//! \param[in] offset: the offset in the row at which to remove the entry
//! \param[in] row: the core-local address of the synaptic row
//! \return was the removal successful?
bool synapse_dynamics_remove_neuron(uint32_t offset, synaptic_row_t row);

//! \brief Add an entry in the synaptic row
//! \param[in] id: the (core-local) ID of the post-synaptic neuron to be added
//! \param[in] row: the core-local address of the synaptic row
//! \param[in] weight: the initial weight associated with the connection
//! \param[in] delay: the delay associated with the connection
//! \param[in] type: the type of the connection (e.g. inhibitory)
//! \return was the addition successful?
bool synapse_dynamics_add_neuron(
        uint32_t id, synaptic_row_t row, weight_t weight,
        uint32_t delay, uint32_t type);

//! \brief Get the number of connections in the given row
//! \param[in] fixed: the fixed region of the synaptic row
//! \return The number of connections in the row
uint32_t synapse_dynamics_n_connections_in_row(synapse_row_fixed_part_t *fixed);

#endif // _SYNAPSE_DYNAMICS_H_
