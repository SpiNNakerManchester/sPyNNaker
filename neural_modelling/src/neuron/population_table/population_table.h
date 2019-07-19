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

#ifndef _POPULATION_TABLE_H_
#define _POPULATION_TABLE_H_

#include <common/neuron-typedefs.h>
#include <bit_field.h>

//! \brief Sets up the table
//! \param[in] table_address The address of the start of the table data
//! \param[in] synapse_rows_address The address of the start of the synapse
//!                                 data
//! \param[in] direct_rows_address The address of the start of the direct
//!                                synapse data
//! \param[out] row_max_n_words Updated with the maximum length of any row in
//!                             the table in words
//! \return True if the table was initialised successfully, False otherwise
bool population_table_initialise(
    address_t table_address, address_t synapse_rows_address,
    address_t direct_rows_address, uint32_t *row_max_n_words);

//! \brief Get the first row data for the given input spike
//! \param[in] spike The spike received
//! \param[out] row_address Updated with the address of the row
//! \param[out] n_bytes_to_transfer Updated with the number of bytes to read
//! \return True if there is a row to read, False if not
bool population_table_get_first_address(
    spike_t spike, address_t* row_address, size_t* n_bytes_to_transfer);

//! \brief get the position in the master pop table
//! \param[in] spike: The spike received
//! \return the position in the master pop table
int population_table_position_in_the_master_pop_array(spike_t spike);

//! \brief Get the next row data for a previously given spike.  If no spike has
//!        been given, return False.
//! \param[out] row_address Updated with the address of the row
//! \param[out] n_bytes_to_transfer Updated with the number of bytes to read
//! \return True if there is a row to read, False if not
bool population_table_get_next_address(
    address_t* row_address, size_t* n_bytes_to_transfer);

//! \brief generates how many dma's were pointless
//! \return uint of how many were done
uint32_t population_table_get_ghost_pop_table_searches(void);

//! \brief sets the connectivity lookup element
//! \param[in] connectivity_lookup: the connectivity bitfield
void population_table_set_connectivity_bit_field(
    bit_field_t* connectivity_bit_fields);

//! \brief get the number of master pop table key misses
//! \return the number of master pop table key misses
uint32_t population_table_get_invalid_master_pop_hits();

//! \brief clears the dtcm allocated by the population table.
//! \return bool that says if the clearing was successful or not.
bool population_table_shut_down();

//! \brief length of master pop table
//! \return length of the master pop table
uint32_t population_table_length();

//! \brief gets the spike associated at a specific index
//! \param[in] index: the index in the master pop table
//! \return the spike
spike_t population_table_get_spike_for_index(uint32_t index);

//! \brief get the mask for the entry at a specific index
//! \param[in] index: the index in the master pop table
//! \return the mask associated with this entry
uint32_t population_table_get_mask_for_entry(uint32_t index);

//! \brief get the number of packets that were filtered from the bitfield filter
//! \return the number of packets filtered by the bitfield filter
uint32_t population_table_get_filtered_packet_count();

#endif // _POPULATION_TABLE_H_
