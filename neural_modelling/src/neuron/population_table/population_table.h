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
//! \brief Master population tables
//! \file
//! \brief Master pop(ulation) table API
#ifndef _POPULATION_TABLE_H_
#define _POPULATION_TABLE_H_

#include <common/neuron-typedefs.h>
#include <bit_field.h>

//! \brief Sets up the table
//! \param[in] table_address: The address of the start of the table data
//! \param[in] synapse_rows_address: The address of the start of the synapse
//!                                  data
//! \param[in] direct_rows_address: The address of the start of the direct
//!                                 synapse data
//! \param[out] row_max_n_words: Updated with the maximum length of any row in
//!                              the table in words
//! \return True if the table was initialised successfully, False otherwise
bool population_table_initialise(
        address_t table_address, address_t synapse_rows_address,
        address_t direct_rows_address, uint32_t *row_max_n_words);

//! \brief Get the first row data for the given input spike
//! \param[in] spike: The spike received
//! \param[out] row_address: Updated with the address of the row
//! \param[out] n_bytes_to_transfer: Updated with the number of bytes to read
//! \return True if there is a row to read, False if not
bool population_table_get_first_address(
        spike_t spike, address_t* row_address, size_t* n_bytes_to_transfer);

//! \brief Get the position in the master population table.
//! \param[in] spike: The spike received
//! \param[out] position: The position found (only if returns true)
//! \return True if there is a matching entry, False otherwise
bool population_table_position_in_the_master_pop_array(
        spike_t spike, uint32_t *position);

//! \brief Get the next row data for a previously given spike.  If no spike has
//!        been given, return False.
//! \param[out] spike: The initiating spike
//! \param[out] row_address: Updated with the address of the row
//! \param[out] n_bytes_to_transfer: Updated with the number of bytes to read
//! \return True if there is a row to read, False if not
bool population_table_get_next_address(
        spike_t *spike, address_t* row_address, size_t* n_bytes_to_transfer);

//! \brief Reports how many DMAs were pointless
//! \return How many were done that were not required
uint32_t population_table_get_ghost_pop_table_searches(void);

//! \brief Sets the connectivity lookup map.
//! \param[in] connectivity_bit_fields: the connectivity lookup bitfield
void population_table_set_connectivity_bit_field(
        bit_field_t* connectivity_bit_fields);

//! \brief Get the number of master pop table key misses
//! \return the number of master pop table key misses
uint32_t population_table_get_invalid_master_pop_hits(void);

//! \brief Clears the DTCM allocated by the population table.
//! \return If the clearing was successful or not.
bool population_table_shut_down(void);

//! \brief Get the length of master population table.
//! \return Length of the master pop table
uint32_t population_table_length(void);

//! \brief Get the spike associated at a specific index.
//! \param[in] index: the index in the master pop table
//! \return the spike
spike_t population_table_get_spike_for_index(uint32_t index);

//! \brief Get the mask for the entry at a specific index
//! \param[in] index: the index in the master pop table
//! \return the mask associated with this entry
uint32_t population_table_get_mask_for_entry(uint32_t index);

//! \brief Get the number of packets that were filtered from the bitfield
//!     filter
//! \return the number of packets filtered by the bitfield filter
uint32_t population_table_get_filtered_packet_count(void);

#endif // _POPULATION_TABLE_H_
