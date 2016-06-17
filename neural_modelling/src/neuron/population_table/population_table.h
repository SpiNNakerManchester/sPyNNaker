#ifndef _POPULATION_TABLE_H_
#define _POPULATION_TABLE_H_

#include "../../common/neuron-typedefs.h"

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
//! \param[out] row_address Updated with the address of the row
//! \param[out] n_bytes_to_transfer Updated with the number of bytes to read
//! \return True if there is a row to read, False if not
bool population_table_get_next_address(
    address_t* row_address, size_t* n_bytes_to_transfer);

#endif // _POPULATION_TABLE_H_
