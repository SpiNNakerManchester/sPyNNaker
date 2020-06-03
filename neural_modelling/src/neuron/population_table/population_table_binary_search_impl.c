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

//! \file
//! \brief Master population table implementation that uses binary search
#include "population_table.h"
#include <neuron/synapse_row.h>
#include <debug.h>
#include <stdbool.h>
#include <bit_field.h>

//! bits in a word
#define BITS_PER_WORD 32

//! \brief The highest bit within the word
#define TOP_BIT_IN_WORD 31

//! \brief The flag for when a spike isn't in the master pop table (so
//! shouldn't happen)
#define NOT_IN_MASTER_POP_TABLE_FLAG -1

//! \brief An entry in the master population table.
typedef struct master_population_table_entry {
    //! The key to match against the incoming message
    uint32_t key;
    //! The mask to select the relevant bits of \p key for matching
    uint32_t mask;
    //! The index into ::address_list for this entry
    uint16_t start;
    //! The number of entries in ::address_list for this entry
    uint16_t count;
} master_population_table_entry;

//! \brief A packed address and row length
typedef struct {
    uint32_t row_length : 8; //!< the length of the row
    uint32_t address : 23;   //!< the address
    uint32_t is_single : 1;  //!< whether this is a direct/single address
} address_and_row_length;

//! The master population table. This is sorted.
static master_population_table_entry *master_population_table;

//! The length of ::master_population_table
static uint32_t master_population_table_length;

//! The array of information that points into the synaptic matrix
static address_and_row_length *address_list;

//! Base address for the synaptic matrix's indirect rows
static address_t synaptic_rows_base_address;

//! Base address for the synaptic matrix's direct rows
static uint32_t direct_rows_base_address;

//! \brief the number of times a DMA resulted in 0 entries
static uint32_t ghost_pop_table_searches = 0;

//! \brief the number of times packet isnt in the master pop table at all!
static uint32_t invalid_master_pop_hits = 0;

//! \brief The last spike received
static spike_t last_spike = 0;

//! \brief The last neuron id for the key
static uint32_t last_neuron_id = 0;

//! the index for the next item in the ::address_list
static uint16_t next_item = 0;

//! The number of relevant items remaining in the ::address_list
static uint16_t items_to_go = 0;

//! \brief The number of packets dropped because the bitfield filter says
//! they don't hit anything
static uint32_t bit_field_filtered_packets = 0;

//! The bitfield map
bit_field_t *connectivity_bit_field;

//! \brief Get the direct address out of an entry
//! \param[in] entry: the table entry
//! \return a direct row address
static inline uint32_t get_direct_address(address_and_row_length entry) {
    // Direct row address is just the direct address bit
    return entry.address;
}

//! \brief Get the standard address out of an entry
//!
//! The address is in words and is the top 23-bits but 1, so this down
//! shifts by 8 and then multiplies by 16 (= up shifts by 4)
//! \param[in] entry: the table entry
//! \return a row address
static inline uint32_t get_address(address_and_row_length entry) {
    return entry.address << 4;
}

//! \brief Get the length of the row from the entry
//! \param[in] entry: the table entry
//! \return the row length
static inline uint32_t get_row_length(address_and_row_length entry) {
    return entry.row_length;
}

//! \brief Get whether this is a single-valued row (i.e. if it uses direct
//!     addressing) from the entry
//! \param[in] entry: the table entry
//! \return true if this is a single-valued row
static inline bool is_single(address_and_row_length entry) {
    return entry.is_single;
}

//! \brief Get the neuron ID for a spike given its table entry
//! \param[in] entry: the table entry
//! \param[in] spike: the spike
//! \return the neuron ID
static inline uint32_t get_neuron_id(
        master_population_table_entry entry, spike_t spike) {
    return spike & ~entry.mask;
}

//! \brief Prints the master pop table.
//!
//! For debugging
static inline void print_master_population_table(void) {
    log_info("master_population\n");
    for (uint32_t i = 0; i < master_population_table_length; i++) {
        master_population_table_entry entry = master_population_table[i];
        for (uint16_t j = entry.start; j < (entry.start + entry.count); j++) {
            if (!is_single(address_list[j])) {
                log_info("index (%d, %d), key: 0x%.8x, mask: 0x%.8x, "
                        "offset: 0x%.8x, address: 0x%.8x, row_length: %u",
                        i, j, entry.key, entry.mask,
                        get_address(address_list[j]),
                        get_address(address_list[j]) +
                                (uint32_t) synaptic_rows_base_address,
                        get_row_length(address_list[j]));
            } else {
                log_info("index (%d, %d), key: 0x%.8x, mask: 0x%.8x, "
                        "offset: 0x%.8x, address: 0x%.8x, single",
                        i, j, entry.key, entry.mask,
                        get_direct_address(address_list[j]),
                        get_direct_address(address_list[j]) +
                                direct_rows_base_address);
            }
        }
    }
    log_info("Population table has %u entries", master_population_table_length);
}

bool population_table_initialise(
        address_t table_address, address_t synapse_rows_address,
        address_t direct_rows_address, uint32_t *row_max_n_words) {
    log_debug("population_table_initialise: starting");

    master_population_table_length = table_address[0];
    log_debug("master pop table length is %d\n", master_population_table_length);
    log_debug("master pop table entry size is %d\n",
            sizeof(master_population_table_entry));
    uint32_t n_master_pop_bytes =
            master_population_table_length * sizeof(master_population_table_entry);
    uint32_t n_master_pop_words = n_master_pop_bytes >> 2;
    log_debug("pop table size is %d\n", n_master_pop_bytes);

    // only try to malloc if there's stuff to malloc.
    if (n_master_pop_bytes != 0) {
        master_population_table = spin1_malloc(n_master_pop_bytes);
        if (master_population_table == NULL) {
            log_error("Could not allocate master population table");
            return false;
        }
    }

    uint32_t address_list_length = table_address[1];
    uint32_t n_address_list_bytes =
            address_list_length * sizeof(address_and_row_length);

    // only try to malloc if there's stuff to malloc.
    if (n_address_list_bytes != 0) {
        address_list = spin1_malloc(n_address_list_bytes);
        if (address_list == NULL) {
            log_error("Could not allocate master population address list");
            return false;
        }
    }

    log_debug("pop table size: %u (%u bytes)",
            master_population_table_length, n_master_pop_bytes);
    log_debug("address list size: %u (%u bytes)",
            address_list_length, n_address_list_bytes);

    // Copy the master population table
    spin1_memcpy(master_population_table, &table_address[2],
            n_master_pop_bytes);
    spin1_memcpy(address_list, &table_address[2 + n_master_pop_words],
            n_address_list_bytes);

    // Store the base address
    log_info("the stored synaptic matrix base address is located at: 0x%08x",
            synapse_rows_address);
    log_info("the direct synaptic matrix base address is located at: 0x%08x",
            direct_rows_address);
    synaptic_rows_base_address = synapse_rows_address;
    direct_rows_base_address = (uint32_t) direct_rows_address;

    *row_max_n_words = 0xFF + N_SYNAPSE_ROW_HEADER_WORDS;

    print_master_population_table();
    return true;
}

bool population_table_get_first_address(
        spike_t spike, address_t* row_address, size_t* n_bytes_to_transfer) {
    // locate the position in the binary search / array
    log_debug("searching for key %d", spike);
    int position = population_table_position_in_the_master_pop_array(spike);
    log_debug("position = %d", position);

    // check we don't have a complete miss
    if (position == NOT_IN_MASTER_POP_TABLE_FLAG) {
        invalid_master_pop_hits++;
        log_debug("Ghost searches: %u\n", ghost_pop_table_searches);
        log_debug("spike %u (= %x): "
                "population not found in master population table",
                spike, spike);
        return false;
    }

    master_population_table_entry entry = master_population_table[position];
    if (entry.count == 0) {
        log_debug("spike %u (= %x): population found in master population"
                "table but count is 0", spike, spike);
    }

    log_debug("about to try to find neuron id");
    last_neuron_id = get_neuron_id(entry, spike);

    // check we have a entry in the bit field for this (possible not to due to
    // DTCM limitations or router table compression). If not, go to DMA check.
    log_debug("checking bit field");
    if (connectivity_bit_field[position] != NULL) {
        log_debug("can be checked, bitfield is allocated");
        // check that the bit flagged for this neuron id does hit a
        // neuron here. If not return false and avoid the DMA check.
        if (!bit_field_test(
                connectivity_bit_field[position], last_neuron_id)) {
            log_debug("tested and was not set");
            bit_field_filtered_packets += 1;
            return false;
        }
        log_debug("was set, carrying on");
    } else {
        log_debug("bit_field was not set up. "
                "either its due to a lack of dtcm, or because the "
                "bitfield was merged into the routing table");
    }

    // going to do a DMA to read the matrix and see if there's a hit.
    log_debug("about to set items");
    next_item = entry.start;
    items_to_go = entry.count;
    last_spike = spike;

    log_debug("spike = %08x, entry_index = %u, start = %u, count = %u",
            spike, position, next_item, items_to_go);

    // A local address is used here as the interface requires something
    // to be passed in but using the address of an argument is odd!
    uint32_t local_spike_id;
    bool get_next = population_table_get_next_address(
            &local_spike_id, row_address, n_bytes_to_transfer);

    // tracks surplus dmas
    if (!get_next) {
        log_debug("found a entry which has a ghost entry for key %d", spike);
        ghost_pop_table_searches++;
    }
    return get_next;
}

//! \brief get the position in the master pop table
//! \param[in] spike: The spike received
//! \return the position in the master pop table
int population_table_position_in_the_master_pop_array(spike_t spike) {
    uint32_t imin = 0;
    uint32_t imax = master_population_table_length;

    while (imin < imax) {
        int imid = (imax + imin) >> 1;
        master_population_table_entry entry = master_population_table[imid];
        if ((spike & entry.mask) == entry.key) {
            return imid;
        } else if (entry.key < spike) {

            // Entry must be in upper part of the table
            imin = imid + 1;
        } else {
            // Entry must be in lower part of the table
            imax = imid;
        }
    }
    return NOT_IN_MASTER_POP_TABLE_FLAG;
}

bool population_table_get_next_address(
        spike_t *spike, address_t *row_address, size_t *n_bytes_to_transfer) {
    // If there are no more items in the list, return false
    if (items_to_go <= 0) {
        return false;
    }

    bool is_valid = false;
    do {
        address_and_row_length item = address_list[next_item];

        // If the row is a direct row, indicate this by specifying the
        // n_bytes_to_transfer is 0
        if (is_single(item)) {
            *row_address = (address_t) (
                    get_direct_address(item) + direct_rows_base_address +
                    (last_neuron_id * sizeof(uint32_t)));
            *n_bytes_to_transfer = 0;
            *spike = last_spike;
            is_valid = true;
        } else {
            uint32_t row_length = get_row_length(item);
            if (row_length > 0) {
                uint32_t block_address = get_address(item) +
                        (uint32_t) synaptic_rows_base_address;
                uint32_t stride = (row_length + N_SYNAPSE_ROW_HEADER_WORDS);
                uint32_t neuron_offset =
                        last_neuron_id * stride * sizeof(uint32_t);

                *row_address = (address_t) (block_address + neuron_offset);
                *n_bytes_to_transfer = stride * sizeof(uint32_t);
                log_debug(
                    "neuron_id = %u, block_address = 0x%.8x,"
                    "row_length = %u, row_address = 0x%.8x, n_bytes = %u",
                    last_neuron_id, block_address, row_length, *row_address,
                    *n_bytes_to_transfer);
                *spike = last_spike;
                is_valid = true;
            }
        }

        next_item++;
        items_to_go--;
    } while (!is_valid && (items_to_go > 0));

    return is_valid;
}

//! \brief generates how many dma's were pointless
//! \return uint of how many were done
uint32_t population_table_get_ghost_pop_table_searches(void) {
    return ghost_pop_table_searches;
}

//! \brief get the number of master pop table key misses
//! \return the number of master pop table key misses
uint32_t population_table_get_invalid_master_pop_hits(void) {
    return invalid_master_pop_hits;
}

//! \brief sets the connectivity lookup element
//! \param[in] connectivity_lookup: the connectivity lookup
void population_table_set_connectivity_bit_field(
        bit_field_t* connectivity_bit_fields){
    connectivity_bit_field = connectivity_bit_fields;
}

//! \brief clears the dtcm allocated by the population table.
//! \return bool that says if the clearing was successful or not.
bool population_table_shut_down(void) {
    sark_free(address_list);
    sark_free(master_population_table);
    ghost_pop_table_searches = 0;
    invalid_master_pop_hits = 0;
    last_neuron_id = 0;
    next_item = 0;
    bit_field_filtered_packets = 0;
    items_to_go = 0;
    connectivity_bit_field = NULL;
    return true;
}

//! \brief length of master pop table
//! \return length of the master pop table
uint32_t population_table_length(void) {
    return master_population_table_length;
}

//! \brief gets the spike associated at a specific index
//! \param[in] index: the index in the master pop table
//! \return the spike
spike_t population_table_get_spike_for_index(uint32_t index) {
    return master_population_table[index].key;
}

//! \brief get the mask for the entry at a specific index
//! \param[in] index: the index in the master pop table
//! \return the mask associated with this entry
uint32_t population_table_get_mask_for_entry(uint32_t index) {
    return master_population_table[index].mask;
}

//! \brief get the number of packets that were filtered from the bitfield filter
//! \return the number of packets filtered by the bitfield filter
uint32_t population_table_get_filtered_packet_count(void) {
    return bit_field_filtered_packets;
}
