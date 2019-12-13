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

//! \brief Get the next row data for a previously given spike.  If no spike has
//!        been given, return False.
//! \param[out] spike The initiating spike
//! \param[out] row_address Updated with the address of the row
//! \param[out] n_bytes_to_transfer Updated with the number of bytes to read
//! \return True if there is a row to read, False if not
bool population_table_get_next_address(
        spike_t *spike, address_t* row_address, size_t* n_bytes_to_transfer);

#endif // _POPULATION_TABLE_H_
