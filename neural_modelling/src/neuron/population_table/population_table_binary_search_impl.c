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

#include "population_table.h"
#include <neuron/synapse_row.h>
#include <debug.h>

typedef struct master_population_table_entry {
    // The routing key to match against
    uint32_t key;
    // The mask to apply to the key to match the routing key
    uint32_t mask;
    // The first entry in the address list for this entry
    // + a flag (MSB) to indicate if the first entry is an extra_info struct
    uint16_t start_and_flag;
    // The number of entries in the address list for this entry
    uint16_t count;
} master_population_table_entry;

// Mask of count_and_flag for extra info flag
#define EXTRA_INFO_FLAG_MASK 0x8000
// Mask of count_and_flag for count
#define START_MASK 0x7FFF

typedef struct extra_info {
    // The mask to apply to the key once shifted get the core index
    uint16_t core_mask;
    // The shift to apply to the key to get the core part (lower 5 bits)
    // + the number of neurons per core (upper 11 bits)
    uint16_t n_neurons_and_mask_shift;
} extra_info;

// The amount to shift n_neurons_and_mask_shift by to get the number of neurons
// Note 11 bits is enough for 2048 neurons on a core
#define N_NEURONS_SHIFT 5
// The amount to shift n_neurons_and_mask_shift by to get the core mask shift
// Note 5 bits is enough for values between 0-31 which is enough for a word!
#define CORE_MASK_SHIFT_MASK 0x1F

// An address and row length entry in the address and row length table
typedef uint32_t address_and_row_length;
// An entry in the address list is either an address and row length or extra
// info if flagged.
typedef union {
    address_and_row_length addr;
    extra_info extra;
} address_list_entry;
// An Invalid address and row length; used to keep indices aligned between
// delayed and undelayed tables
#define INVALID_ADDRESS_AND_ROW_LENGTH 0xFFFFFFFF
// The mask to use to extract that the row is direct (single synapse)
#define IS_SINGLE_FLAG_MASK 0x80000000
// The mask to extract the address
#define ADDRESS_MASK 0x7FFFFF00
// The shift for a direct (singly synapse) address to get the actual byte address
#define DIRECT_ADDRESS_SHIFT 8
// The shift for an indirect address to get the actual byte address
// The offset is in words and is the top 23-bits but 1, so this down
// shifts by 8 and then multiplies by 16 (= up shifts by 4) = down shift by 4
#define INDIRECT_ADDRESS_SHIFT 4
// The mask of the row length
#define ROW_LENGTH_MASK 0xFF

// The master population table itself
static master_population_table_entry *master_population_table;
// The length of the master population table
static uint32_t master_population_table_length;
// The address list of the population table; for multiple matrices between
// the same pair of populations
static address_list_entry *address_list;
// The address where the first synaptic row is stored (as a uint32_t)
static uint32_t synaptic_rows_base_address;
// The address where the first direct (single synapse) row is stored
static uint32_t direct_rows_base_address;

// The spike key of the last master pop entry matched
static spike_t last_spike = 0;
// The neuron id of the last master pop entry matched
static uint32_t last_neuron_id = 0;
// The next item in the address list of the last master pop entry matched
static uint16_t next_item = 0;
// The count of items in the address list of the last master pop entry matched
static uint16_t items_to_go = 0;

//! \brief Get the direct row address from an entry
static inline uint32_t get_direct_address(address_and_row_length entry) {
    return ((entry & ADDRESS_MASK) >> DIRECT_ADDRESS_SHIFT) +
            direct_rows_base_address;
}

//! \brief Get the address from an entry
static inline uint32_t get_address(address_and_row_length entry) {
    return ((entry & ADDRESS_MASK) >> INDIRECT_ADDRESS_SHIFT) +
            synaptic_rows_base_address;
}

//! \brief Get the row length of an entry
static inline uint32_t get_row_length(address_and_row_length entry) {
    // Row lengths are stored offset by 1, to allow 1-256 length rows
    return (entry & ROW_LENGTH_MASK) + 1;
}

//! \brief Determine if this entry is a direct (single synapse) matrix
static inline uint32_t is_single(address_and_row_length entry) {
    return entry & IS_SINGLE_FLAG_MASK;
}

//! \brief Determine if this master population table entry has extra information
static inline uint32_t is_extended(master_population_table_entry entry) {
    return entry.start_and_flag & EXTRA_INFO_FLAG_MASK;
}

//! \brief Get the start address entry index for this element
static inline uint32_t get_start(master_population_table_entry entry) {
    return entry.start_and_flag & START_MASK;
}

//! \brief Get the number of neurons per core from the extra info
static inline uint32_t get_n_neurons(extra_info extra) {
    return extra.n_neurons_and_mask_shift >> N_NEURONS_SHIFT;
}

//! \brief Get the mask shift to get the core bits
static inline uint32_t get_core_shift(extra_info extra) {
    return extra.n_neurons_and_mask_shift & CORE_MASK_SHIFT_MASK;
}

//! \brief Get the total number of neurons on cores which come before this core
static inline uint32_t get_core_sum(extra_info extra, spike_t spike) {
    return ((spike >> get_core_shift(extra)) & extra.core_mask) *
            get_n_neurons(extra);
}

//! \brief Get the neuron id for a spike without extra info
static inline uint32_t get_neuron_id(
        master_population_table_entry entry, spike_t spike) {
    return spike & ~entry.mask;
}

//! \brief Get the neuron id for a spike with extra info
static inline uint32_t get_extended_neuron_id(
        master_population_table_entry entry, extra_info extra, spike_t spike) {
    return (spike & ~(entry.mask | (extra.core_mask << get_core_shift(extra)))) +
            get_core_sum(extra, spike);
}

//! \brief Print the population table
static inline void print_master_population_table(void) {
    log_info("master_population\n");
    log_info("------------------------------------------\n");
    for (uint32_t i = 0; i < master_population_table_length; i++) {
        master_population_table_entry entry = master_population_table[i];
        log_info("key: 0x%08x, mask: 0x%08x", entry.key, entry.mask);
        int count = entry.count;
        int start = get_start(entry);
        if (is_extended(entry)) {
            extra_info extra = address_list[start].extra;
            start += 1;
            log_info("    core_mask: 0x%08x, core_shift: %u, n_neurons: %u",
                    extra.core_mask, get_core_shift(extra), get_n_neurons(extra));
        }
        for (uint16_t j = start; j < (start + count); j++) {
            address_and_row_length addr = address_list[j].addr;
            if (addr == INVALID_ADDRESS_AND_ROW_LENGTH) {
                log_info("    index %d: INVALID", j);
            } else if (!is_single(addr)) {
                log_info("    index %d: address: 0x%08x, row_length: %u",
                    j, get_address(addr), get_row_length(addr));
            } else {
                log_info("    index %d: address: 0x%08x, single",
                    j, get_direct_address(addr));
            }
        }
    }
    log_info("------------------------------------------\n");
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
            address_list_length * sizeof(address_list_entry);

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
    uint32_t imin = 0;
    uint32_t imax = master_population_table_length;

    while (imin < imax) {
        int imid = (imax + imin) >> 1;
        master_population_table_entry entry = master_population_table[imid];
        if ((spike & entry.mask) == entry.key) {
            if (entry.count == 0) {
                log_debug("spike %u (= %x): population found in master population"
                        "table but count is 0", spike, spike);
            }

            last_spike = spike;
            next_item = get_start(entry);
            items_to_go = entry.count;
            if (is_extended(entry)) {
                extra_info extra = address_list[next_item++].extra;
                last_neuron_id = get_extended_neuron_id(entry, extra, spike);
            } else {
                last_neuron_id = get_neuron_id(entry, spike);
            }

            log_debug("spike = %08x, entry_index = %u, start = %u, count = %u",
                    spike, imid, next_item, items_to_go);

            // A local address is used here as the interface requires something
            // to be passed in but using the address of an argument is odd!
            uint32_t local_spike_id;
            return population_table_get_next_address(
                    &local_spike_id, row_address, n_bytes_to_transfer);
        } else if (entry.key < spike) {
            // Entry must be in upper part of the table
            imin = imid + 1;
        } else {
            // Entry must be in lower part of the table
            imax = imid;
        }
    }
    log_debug("spike %u (= %x): population not found in master population table",
            spike, spike);
    return false;
}

bool population_table_get_next_address(
        spike_t *spike, address_t *row_address, size_t *n_bytes_to_transfer) {
    // If there are no more items in the list, return false
    if (items_to_go <= 0) {
        return false;
    }

    bool is_valid = false;
    do {
        address_and_row_length item = address_list[next_item].addr;
        if (item != INVALID_ADDRESS_AND_ROW_LENGTH) {

            // If the row is a direct row, indicate this by specifying the
            // n_bytes_to_transfer is 0
            if (is_single(item)) {
                *row_address = (address_t) (get_direct_address(item) +
                    (last_neuron_id * sizeof(uint32_t)));
                *n_bytes_to_transfer = 0;
                is_valid = true;
            } else {

                uint32_t row_length = get_row_length(item);
                uint32_t block_address = get_address(item);
                uint32_t stride = (row_length + N_SYNAPSE_ROW_HEADER_WORDS);
                uint32_t neuron_offset = last_neuron_id * stride * sizeof(uint32_t);

                *row_address = (address_t) (block_address + neuron_offset);
                *n_bytes_to_transfer = stride * sizeof(uint32_t);
                log_debug("neuron_id = %u, block_address = 0x%.8x,"
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
