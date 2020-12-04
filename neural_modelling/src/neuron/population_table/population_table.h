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

//! \brief The number of bits of address.
//!        This is a constant as it is used more than once below.
#define N_ADDRESS_BITS 22

//!================================================

//! \brief An entry in the master population table.
typedef struct master_population_table_entry {
    //! The key to match against the incoming message
    uint32_t key;
    //! The mask to select the relevant bits of \p key for matching
    uint32_t mask;
    //! The index into ::address_list for this entry
    uint32_t start: 15;
    //! Flag to indicate if an extra_info struct is present
    uint32_t extra_info_flag: 1;
    //! The number of entries in ::address_list for this entry
    uint32_t count: 15;
    //! Flag to indicate if the synaptic block should be cached in DTCM.
    uint32_t cache_in_dtcm: 1;
} master_population_table_entry;

//! \brief A packed extra info (note: same size as address and row length)
typedef struct extra_info {
    //! The mask to apply to the key once shifted get the core index
    uint32_t core_mask: 10;
    //! The number of words required for n_neurons
    uint32_t n_words: 6;
    //! The shift to apply to the key to get the core part (0-31)
    uint32_t mask_shift: 5;
    //! The number of neurons per core (up to 2048)
    uint32_t n_neurons: 11;
} extra_info;

//! \brief A packed address and row length (note: same size as extra info)
typedef struct {
    //! the length of the row
    uint32_t row_length : 8;
    //! the address
    uint32_t address : N_ADDRESS_BITS;
    //! whether this is a direct/single address
    uint32_t representation: 2;
} address_and_row_length;

//! \brief A enum for representing other data representations
typedef enum representation_values {
    //! representation of a direct 1 to 1
    SINGLE = 0,
    //! Binary Search
    BINARY_SEARCH = 1,
    //! 1d array
    ARRAY = 2,
    // other
    OTHER = 3
} representation_values;

//! \brief An entry in the address list is either an address and row length or extra
//! info if flagged.
typedef union {
    address_and_row_length addr;
    extra_info extra;
} address_list_entry;

//! ===========================================

//! \brief the jump in the global data structure to get to the master pop entries.
#define SKIP_COUNTERS 2

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

//! The array of information that points into the synaptic matrix
extern address_list_entry *address_list;

//! The master population table. This is sorted.
extern master_population_table_entry *master_population_table;

//! The length of ::master_population_table
extern uint32_t master_population_table_length;

static inline master_population_table_entry*
        population_table_get_master_pop_entry_from_sdram(
            address_t table_address, uint32_t position) {
    master_population_table_entry* start_of_entry_list =
        (master_population_table_entry*) table_address[SKIP_COUNTERS];
    uint32_t bytes_in = position * sizeof(master_population_table_entry);
    uint32_t words_in = bytes_in >> 2;
    return &start_of_entry_list[words_in];
}

//! \brief get a master pop entry from array
//! \param[in] index: index to get element from
//! \return master pop table entry.
static inline master_population_table_entry population_table_entry(
        uint32_t index) {
    return master_population_table[index];
}

//! \brief get a address_list_entry from array
//! \param[in] index: index to get element from
//! \return the address_list_entry.
static inline address_list_entry population_table_get_address_entry(
        uint32_t index) {
    return address_list[index];
}

static inline address_list_entry* population_table_get_address_entry_from_sdram(
        address_t table_address, uint32_t address_entry_index) {
    uint32_t master_population_table_length = table_address[0];
    uint32_t n_master_pop_bytes =
            master_population_table_length * sizeof(master_population_table_entry);
    uint32_t n_master_pop_words = n_master_pop_bytes >> 2;
    address_list_entry* addresses = (address_list_entry*) table_address[
        SKIP_COUNTERS + n_master_pop_words];
    uint32_t skip_to_correct_entry_bytes =
        address_entry_index * sizeof(address_list_entry);
    uint32_t skip_to_correct_entry_words = skip_to_correct_entry_bytes >> 2;
    return &addresses[skip_to_correct_entry_words];
}

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
        spike_t spike, address_t* row_address, size_t* n_bytes_to_transfer);

//! \brief Get the next row data for a previously given spike.  If no spike has
//!        been given, return False.
//! \param[out] spike: The initiating spike
//! \param[out] row_address: Updated with the address of the row
//! \param[out] n_bytes_to_transfer: Updated with the number of bytes to read
//! \return True if there is a row to read, False if not
bool population_table_get_next_address(
        spike_t *spike, address_t* row_address, size_t* n_bytes_to_transfer);

//! \brief Get the position in the master population table.
//! \param[in] spike: The spike received
//! \param[out] position: The position found (only if returns true)
//! \return True if there is a matching entry, False otherwise
static inline bool population_table_position_in_the_master_pop_array(
        spike_t spike, uint32_t *position) {
    uint32_t imin = 0;
    uint32_t imax = master_population_table_length;

    while (imin < imax) {
        uint32_t imid = (imax + imin) >> 1;
        master_population_table_entry entry = master_population_table[imid];
        if ((spike & entry.mask) == entry.key) {
            *position = imid;
            return true;
        } else if (entry.key < spike) {

            // Entry must be in upper part of the table
            imin = imid + 1;
        } else {
            // Entry must be in lower part of the table
            imax = imid;
        }
    }
    return false;
}

#endif // _POPULATION_TABLE_H_
