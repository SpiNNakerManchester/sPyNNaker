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
#include <filter_info.h>

//! \brief the number of times a DMA resulted in 0 entries
extern uint32_t ghost_pop_table_searches;

//! \brief the number of times packet isn't in the master pop table at all!
extern uint32_t invalid_master_pop_hits;

//! \brief The number of bit fields which were not able to be read in due to
//!     DTCM limits.
extern uint32_t failed_bit_field_reads;

//! \brief The number of packets dropped because the bitfield filter says
//!     they don't hit anything
extern uint32_t bit_field_filtered_packets;

//! \brief Set up the table
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

//! \brief Initialise the bitfield filtering system.
//! \param[in] filter_region: Where the bitfield configuration is
//! \return True on success
bool population_table_load_bitfields(filter_region_t *filter_region);

//! \brief Get the first row data for the given input spike
//! \param[in] spike: The spike received
//! \param[out] row_address: Updated with the address of the row
//! \param[out] n_bytes_to_transfer: Updated with the number of bytes to read
//! \return True if there is a row to read, False if not
bool population_table_get_first_address(
        spike_t spike, synaptic_row_t* row_address,
        size_t* n_bytes_to_transfer);

//! \brief Get the next row data for a previously given spike.  If no spike has
//!        been given, return False.
//! \param[out] spike: The initiating spike
//! \param[out] row_address: Updated with the address of the row
//! \param[out] n_bytes_to_transfer: Updated with the number of bytes to read
//! \return True if there is a row to read, False if not
bool population_table_get_next_address(
        spike_t *spike, synaptic_row_t* row_address,
        size_t* n_bytes_to_transfer);

#endif // _POPULATION_TABLE_H_
