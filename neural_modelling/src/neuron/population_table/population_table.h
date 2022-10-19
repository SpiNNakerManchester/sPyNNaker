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
#include <neuron/synapse_row.h>
#include <debug.h>


//! bits in a word
#define BITS_PER_WORD 32

//! \brief The highest bit within the word
#define TOP_BIT_IN_WORD 31

//! \brief The flag for when a spike isn't in the master pop table (so
//!     shouldn't happen)
#define NOT_IN_MASTER_POP_TABLE_FLAG -1

//! \brief The number of bits of address.
//!        This is a constant as it is used more than once below.
#define N_ADDRESS_BITS 24

//! \brief The shift to apply to indirect addresses.
//!    The address is in units of four words, so this multiplies by 16 (= up
//!    shifts by 4)
#define INDIRECT_ADDRESS_SHIFT 4

//! \brief An entry in the master population table.
typedef struct master_population_table_entry {
    //! The key to match against the incoming message
    uint32_t key;
    //! The mask to select the relevant bits of \p key for matching
    uint32_t mask;
    //! The index into ::address_list for this entry
    uint32_t start: 15;
    //! Flag to indicate if core mask etc. is valid
    uint32_t extra_info_flag: 1;
    //! The number of entries in ::address_list for this entry
    uint32_t count: 16;
    //! The mask to apply to the key once shifted to get the core index
    uint32_t core_mask: 16;
    //! The shift to apply to the key to get the core part
    uint32_t mask_shift: 16;
    //! The number of neurons per core
    uint32_t n_neurons: 16;
    //! The number of words for n_neurons
    uint32_t n_words: 16;
} master_population_table_entry;

//! \brief A packed address and row length (note: same size as extra info)
typedef struct {
    //! the length of the row
    uint32_t row_length : 8;
    //! the address
    uint32_t address : N_ADDRESS_BITS;
} address_list_entry;

//! \brief An Invalid address and row length
//! \details Used to keep indices aligned between delayed and undelayed tables
#define INVALID_ADDRESS ((1 << N_ADDRESS_BITS) - 1)

//! \brief The memory layout in SDRAM of the first part of the population table
//!     configuration. Address list data (array of ::address_and_row_length) is
//!     packed on the end.
typedef struct {
    uint32_t table_length;
    uint32_t addr_list_length;
    master_population_table_entry data[];
} pop_table_config_t;

//! \name Support functions
//! \{

//! \brief Get the standard address offset out of an entry
//! \details The address is in units of four words, so this multiplies by 16
//!     (= up shifts by 4)
//! \param[in] entry: the table entry
//! \return a row address (which is an offset)
static inline uint32_t get_offset(address_list_entry entry) {
    return entry.address << INDIRECT_ADDRESS_SHIFT;
}

//! \brief Get the standard address out of an entry
//! \param[in] entry: the table entry
//! \return a row address
static inline uint32_t get_address(address_list_entry entry, uint32_t addr) {
    return get_offset(entry) + addr;
}

//! \brief Get the length of the row from the entry
//!
//! Row lengths are stored offset by 1, to allow 1-256 length rows
//!
//! \param[in] entry: the table entry
//! \return the row length
static inline uint32_t get_row_length(address_list_entry entry) {
    return entry.row_length + 1;
}

//! \brief Get the source core index from a spike
//! \param[in] entry: The master pop table entry
//! \param[in] spike: The spike received
//! \return the source core index in the list of source cores
static inline uint32_t get_core_index(master_population_table_entry entry, spike_t spike) {
    return (spike >> entry.mask_shift) & entry.core_mask;
}

//! \brief Get the total number of neurons on cores which come before this core
//! \param[in] entry: The master pop table entry
//! \param[in] spike: The spike received
//! \return the base neuron number of this core
static inline uint32_t get_core_sum(master_population_table_entry entry, spike_t spike) {
    return get_core_index(entry, spike) * entry.n_neurons;
}

//! \brief Get the source neuron ID for a spike given its table entry (without extra info)
//! \param[in] entry: the table entry
//! \param[in] spike: the spike
//! \return the neuron ID
static inline uint32_t get_neuron_id(
        master_population_table_entry entry, spike_t spike) {
    return spike & ~entry.mask;
}

//! \brief Get the neuron id of the neuron on the source core, for a spike with
//!        extra info
//! \param[in] entry: the table entry
//! \param[in] spike: the spike received
//! \return the source neuron id local to the core
static inline uint32_t get_local_neuron_id(
        master_population_table_entry entry, spike_t spike) {
    return spike & ~(entry.mask | (entry.core_mask << entry.mask_shift));
}

//! \brief Get the row address and size for a given neuron
//! \param[in] item The address list item
//! \param[in] synaptic_rows_based_address The address of all synaptic rows
//! \param[in] neuron_id The incoming neuron to get the address of
//! \param[out] row_address Holder of the row address on return
//! \param[out] n_bytes_to_transfer Holder of the bytes to transfer on return
static inline void get_row_addr_and_size(address_list_entry item,
		uint32_t synaptic_rows_base_address, uint32_t neuron_id,
		synaptic_row_t *row_address, uint32_t *n_bytes_to_transfer) {
	uint32_t row_length = get_row_length(item);
	uint32_t block_address = get_address(item, synaptic_rows_base_address);
	uint32_t stride = (row_length + N_SYNAPSE_ROW_HEADER_WORDS);
	uint32_t neuron_offset = neuron_id * stride * sizeof(uint32_t);

	*row_address = (synaptic_row_t) (block_address + neuron_offset);
	*n_bytes_to_transfer = stride * sizeof(uint32_t);

    log_debug("neuron_id = %u, block_address = 0x%.8x, "
            "row_length = %u, row_address = 0x%.8x, n_bytes = %u",
            neuron_id, block_address, row_length, *row_address,
            *n_bytes_to_transfer);
}

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

//! \brief The number of addresses from the same spike left to process
extern uint16_t items_to_go;

//! \brief Set up and return the table for outside use
//! \param[in] table_address: The address of the start of the table data
//! \param[out] row_max_n_words: Updated with the maximum length of any row in
//!                              the table in words
//! \param[out] master_pop_table_length: Updated with the length of the table
//! \param[out] master_pop_table: Updated with the table entries
//! \param[out] address_list: Updated with the address list
//! \return True if the table was setup successfully, False otherwise
bool population_table_setup(address_t table_address, uint32_t *row_max_n_words,
    uint32_t *master_pop_table_length,
    master_population_table_entry **master_pop_table,
    address_list_entry **address_list);

//! \brief Set up the table
//! \param[in] table_address: The address of the start of the table data
//! \param[in] synapse_rows_address: The address of the start of the synapse
//!                                  data
//! \param[out] row_max_n_words: Updated with the maximum length of any row in
//!                              the table in words
//! \return True if the table was initialised successfully, False otherwise
bool population_table_initialise(
        address_t table_address, address_t synapse_rows_address,
        uint32_t *row_max_n_words);

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

//! \brief Determine if there are more items with the same key
//! \return Whether there are more items
static inline bool population_table_is_next(void) {
    return items_to_go > 0;
}

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
