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

//! bits in a word
#define BITS_PER_WORD 32

//! \brief The highest bit within the word
#define TOP_BIT_IN_WORD 31

//! \brief The flag for when a spike isn't in the master pop table (so
//!     shouldn't happen)
#define NOT_IN_MASTER_POP_TABLE_FLAG -1

//! \brief The number of bits of address.
//!        This is a constant as it is used more than once below.
#define N_ADDRESS_BITS 23

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
    //! Flag to indicate if an extra_info struct is present
    uint32_t extra_info_flag: 1;
    //! The number of entries in ::address_list for this entry
    uint32_t count: 16;
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
    uint32_t is_single : 1;
} address_and_row_length;

//! \brief An entry in the address list is either an address and row length or extra
//! info if flagged.
typedef union {
    address_and_row_length addr;
    extra_info extra;
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

//! The master population table. This is sorted.
static master_population_table_entry *master_population_table;

//! The length of ::master_population_table
static uint32_t master_population_table_length;

//! The array of information that points into the synaptic matrix
static address_list_entry *address_list;

//! Base address for the synaptic matrix's indirect rows
static uint32_t synaptic_rows_base_address;

//! Base address for the synaptic matrix's direct rows
static uint32_t direct_rows_base_address;

//! \brief The last spike received
static spike_t last_spike = 0;

//! \brief The last neuron id for the key
static uint32_t last_neuron_id = 0;

//! the index for the next item in the ::address_list
static uint16_t next_item = 0;

//! The number of relevant items remaining in the ::address_list
//! NOTE: Exported for speed of check
uint16_t items_to_go = 0;

//! The bitfield map
static bit_field_t *connectivity_bit_field = NULL;

//! \brief the number of times a DMA resulted in 0 entries
uint32_t ghost_pop_table_searches = 0;

//! \brief the number of times packet isnt in the master pop table at all!
uint32_t invalid_master_pop_hits = 0;

//! \brief The number of bit fields which were not able to be read in due to
//!     DTCM limits.
uint32_t failed_bit_field_reads = 0;

//! \brief The number of packets dropped because the bitfield filter says
//!     they don't hit anything
uint32_t bit_field_filtered_packets = 0;

//! \name Support functions
//! \{

//! \brief Get the direct row address out of an entry
//! \param[in] entry: the table entry
//! \return a direct row address
static inline uint32_t get_direct_address(address_and_row_length entry) {
    return entry.address + direct_rows_base_address;
}

//! \brief Get the standard address offset out of an entry
//! \details The address is in units of four words, so this multiplies by 16
//!     (= up shifts by 4)
//! \param[in] entry: the table entry
//! \return a row address (which is an offset)
static inline uint32_t get_offset(address_and_row_length entry) {
    return entry.address << INDIRECT_ADDRESS_SHIFT;
}

//! \brief Get the standard address out of an entry
//! \param[in] entry: the table entry
//! \return a row address
static inline uint32_t get_address(address_and_row_length entry) {
    return get_offset(entry) + synaptic_rows_base_address;
}

//! \brief Get the length of the row from the entry
//!
//! Row lengths are stored offset by 1, to allow 1-256 length rows
//!
//! \param[in] entry: the table entry
//! \return the row length
static inline uint32_t get_row_length(address_and_row_length entry) {
    return entry.row_length + 1;
}

//! \brief Get the source core index from a spike
//! \param[in] extra: The extra info entry
//! \param[in] spike: The spike received
//! \return the source core index in the list of source cores
static inline uint32_t get_core_index(extra_info extra, spike_t spike) {
    return (spike >> extra.mask_shift) & extra.core_mask;
}

//! \brief Get the total number of neurons on cores which come before this core
//! \param[in] extra: The extra info entry
//! \param[in] spike: The spike received
//! \return the base neuron number of this core
static inline uint32_t get_core_sum(extra_info extra, spike_t spike) {
    return get_core_index(extra, spike) * extra.n_neurons;
}

//! \brief Get the total number of bits in bitfields for cores which came before
//!        this core.
//! \param[in] extra: The extra info entry
//! \param[in] spike: The spike received
//! \return the base bitfield bit index of this core
static inline uint32_t get_bitfield_sum(extra_info extra, spike_t spike) {
    return get_core_index(extra, spike) * extra.n_words * BITS_PER_WORD;
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
//! \param[in] extra: the extra info entry
//! \param[in] spike: the spike received
//! \return the source neuron id local to the core
static inline uint32_t get_local_neuron_id(
        master_population_table_entry entry, extra_info extra, spike_t spike) {
    return spike & ~(entry.mask | (extra.core_mask << extra.mask_shift));
}

//! \brief Prints the master pop table.
//! \details For debugging
static inline void print_master_population_table(void) {
#if log_level >= LOG_DEBUG
    log_debug("Master_population\n");
    for (uint32_t i = 0; i < master_population_table_length; i++) {
        master_population_table_entry entry = master_population_table[i];
        log_debug("key: 0x%08x, mask: 0x%08x", entry.key, entry.mask);
        int count = entry.count;
        int start = entry.start;
        if (entry.extra_info_flag) {
            extra_info extra = address_list[start].extra;
            start += 1;
            log_debug("    core_mask: 0x%08x, core_shift: %u, n_neurons: %u, n_words: %u",
                    extra.core_mask, extra.mask_shift, extra.n_neurons, extra.n_words);
        }
        for (uint16_t j = start; j < (start + count); j++) {
            address_and_row_length addr = address_list[j].addr;
            if (addr.address == INVALID_ADDRESS) {
                log_debug("    index %d: INVALID", j);
            } else if (!addr.is_single) {
                log_debug("    index %d: offset: %u, address: 0x%08x, row_length: %u",
                    j, get_offset(addr), get_address(addr), get_row_length(addr));
            } else {
                log_debug("    index %d: offset: %u, address: 0x%08x, single",
                    j, addr.address, get_direct_address(addr));
            }
        }
    }
    log_debug("Population table has %u entries", master_population_table_length);
#endif
}

//! \brief Check if the entry is a match for the given key
//! \param[in] mp_i: The master population table entry index
//! \param[in] key: The key to check
//! \return: Whether the key matches the entry
static inline bool matches(uint32_t mp_i, uint32_t key) {
    return (key & master_population_table[mp_i].mask) ==
            master_population_table[mp_i].key;
}

//! \brief Print bitfields for debugging
//! \param[in] mp_i: The master population table entry index
//! \param[in] start: The first index of the bitfield to print
//! \param[in] end: The index after the last bitfield to print
//! \param[in] filters: The bitfields to print
static inline void print_bitfields(uint32_t mp_i, uint32_t start,
        uint32_t end, filter_info_t *filters) {
#if LOG_LEVEL >= LOG_DEBUG
    // print out the bit field for debug purposes
    log_debug("Bit field(s) for key 0x%08x:", master_population_table[mp_i].key);
    uint32_t offset = 0;
    for (uint32_t bf_i = start; bf_i < end; bf_i++) {
        uint32_t n_words = get_bit_field_size(filters[bf_i].n_atoms);
        for (uint32_t i = 0; i < n_words; i++) {
            log_debug("0x%08x", connectivity_bit_field[mp_i][offset + i]);
        }
        offset += n_words;
    }
#else
    use(mp_i);
    use(start);
    use(end);
    use(filters);
#endif
}

bool population_table_load_bitfields(filter_region_t *filter_region) {

    if (master_population_table_length == 0) {
        return true;
    }
    // try allocating DTCM for starting array for bitfields
    connectivity_bit_field =
            spin1_malloc(sizeof(bit_field_t) * master_population_table_length);
    if (connectivity_bit_field == NULL) {
        log_warning(
                "Couldn't initialise basic bit field holder. Will end up doing"
                " possibly more DMA's during the execution than required."
                " We required %d bytes where %d are available",
                sizeof(bit_field_t) * master_population_table_length,
                sark_heap_max(sark.heap, 0));
        return true;
    }

    // Go through the population table, and the relevant bitfield list, both
    // of which are ordered by key...
    uint32_t bf_i = 0;
    uint32_t n_filters = filter_region->n_filters;
    filter_info_t* filters = filter_region->filters;
    for (uint32_t mp_i = 0; mp_i < master_population_table_length; mp_i++) {
         connectivity_bit_field[mp_i] = NULL;

         log_debug("Master pop key: 0x%08x, mask: 0x%08x",
                 master_population_table[mp_i].key, master_population_table[mp_i].mask);

//#ifdef LOG_DEBUG
//         // Sanity checking code; not needed in normal operation, and costs ITCM
//         // With both things being in key order, this should never happen...
//         if (bf_i < n_filters &&
//                 filters[bf_i].key < master_population_table[mp_i].key) {
//             log_error("Skipping bitfield %d for key 0x%08x", bf_i, filters[bf_i].key);
//             rt_error(RTE_SWERR);
//         }
//#endif

         // While there is a match, keep track of the start and end; note this
         // may recheck the first entry, but there might not be a first entry if
         // we have already gone off the end of the bitfield array
         uint32_t start = bf_i;
         uint32_t n_words_total = 0;
         uint32_t useful = 0;
//         log_debug("Starting with bit field %d with key 0x%08x", bf_i, filters[bf_i].key);
         while (bf_i < n_filters && matches(mp_i, filters[bf_i].key)) {
             log_debug("Using bit field %d with key 0x%08x, merged %d, redundant %d",
                     bf_i, filters[bf_i].key, filters[bf_i].merged, filters[bf_i].all_ones);
             n_words_total += get_bit_field_size(filters[bf_i].n_atoms);
             useful += !(filters[bf_i].merged || filters[bf_i].all_ones);
             bf_i++;
         }

         // If there is something to copy, copy them in now
         log_debug("Ended with bit field %d with key 0x%08x, n_words %d, useful %d",
                 bf_i, filters[bf_i].key, n_words_total, useful);
         if (bf_i != start && useful) {
             // Try to allocate all the bitfields for this entry
             connectivity_bit_field[mp_i] = spin1_malloc(
                     sizeof(bit_field_t) * n_words_total);
             if (connectivity_bit_field[mp_i] == NULL) {
                 // If allocation fails, we can still continue
                 log_debug(
                         "Could not initialise bit field for key %d, packets with "
                         "that key will use a DMA to check if the packet targets "
                         "anything within this core. Potentially slowing down the "
                         "execution of neurons on this core.",
                         master_population_table[mp_i].key);
                 // There might be more than one that has failed
                 failed_bit_field_reads += bf_i - start;
             } else {
                 // If allocation succeeds, copy the bitfields in
                 bit_field_t bf_pointer = &connectivity_bit_field[mp_i][0];
                 for (uint32_t i = start; i < bf_i; i++) {
                     uint32_t n_words = get_bit_field_size(filters[i].n_atoms);
                     spin1_memcpy(bf_pointer, filters[i].data, n_words * sizeof(uint32_t));
                     bf_pointer = &bf_pointer[n_words];
                 }

                 print_bitfields(mp_i, start, bf_i, filters);
             }
         }
    }
    return true;
}

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
//! \}

//! \name API functions
//! \{

bool population_table_initialise(
        address_t table_address, address_t synapse_rows_address,
        address_t direct_rows_address, uint32_t *row_max_n_words) {
    pop_table_config_t *config = (pop_table_config_t *) table_address;

    master_population_table_length = config->table_length;
    log_debug("Master pop table length is %d\n", master_population_table_length);
    log_debug("Master pop table entry size is %d\n",
            sizeof(master_population_table_entry));
    uint32_t n_master_pop_bytes =
            master_population_table_length * sizeof(master_population_table_entry);
    log_debug("Pop table size is %d\n", n_master_pop_bytes);

    // only try to malloc if there's stuff to malloc.
    if (n_master_pop_bytes != 0) {
        master_population_table = spin1_malloc(n_master_pop_bytes);
        if (master_population_table == NULL) {
            log_error("Could not allocate master population table");
            return false;
        }
    }

    uint32_t address_list_length = config->addr_list_length;
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

    log_debug("Pop table size: %u (%u bytes)",
            master_population_table_length, n_master_pop_bytes);
    log_debug("Address list size: %u (%u bytes)",
            address_list_length, n_address_list_bytes);

    // Copy the master population table
    spin1_memcpy(master_population_table, config->data, n_master_pop_bytes);
    spin1_memcpy(address_list, &config->data[master_population_table_length],
            n_address_list_bytes);

    // Store the base address
    log_debug("The stored synaptic matrix base address is located at: 0x%08x",
            synapse_rows_address);
    log_debug("The direct synaptic matrix base address is located at: 0x%08x",
            direct_rows_address);
    synaptic_rows_base_address = (uint32_t) synapse_rows_address;
    direct_rows_base_address = (uint32_t) direct_rows_address;

    *row_max_n_words = 0xFF + N_SYNAPSE_ROW_HEADER_WORDS;

    print_master_population_table();
    return true;
}

bool population_table_get_first_address(
        spike_t spike, synaptic_row_t *row_address,
        size_t *n_bytes_to_transfer) {
    // locate the position in the binary search / array
    log_debug("Searching for key 0x%08x", spike);

    // check we don't have a complete miss
    uint32_t position;
    if (!population_table_position_in_the_master_pop_array(spike, &position)) {
        invalid_master_pop_hits++;
        log_debug("Ghost searches: %u\n", ghost_pop_table_searches);
        log_debug("Spike %u (= %x): "
                "Population not found in master population table",
                spike, spike);
        return false;
    }

    master_population_table_entry entry = master_population_table[position];

    #if LOG_LEVEL >= LOG_DEBUG
    if (entry.count == 0) {
        log_debug("Spike %u (= %x): Population found in master population"
                "table but count is 0", spike, spike);
    }
    #endif

    last_spike = spike;
    next_item = entry.start;
    items_to_go = entry.count;
    if (entry.extra_info_flag) {
        extra_info extra = address_list[next_item++].extra;
        uint32_t local_neuron_id = get_local_neuron_id(entry, extra, spike);
        last_neuron_id = local_neuron_id + get_core_sum(extra, spike);
    } else {
        last_neuron_id = get_neuron_id(entry, spike);
    }

    // check we have a entry in the bit field for this (possible not to due to
    // DTCM limitations or router table compression). If not, go to DMA check.
    if (connectivity_bit_field != NULL &&
            connectivity_bit_field[position] != NULL) {
        // check that the bit flagged for this neuron id does hit a
        // neuron here. If not return false and avoid the DMA check.
        if (!bit_field_test(
                connectivity_bit_field[position], last_neuron_id)) {
//            log_debug("Tested and was not set");
            bit_field_filtered_packets += 1;
            items_to_go = 0;
            return false;
        }
//        log_debug("Was set, carrying on");
    } else {
        log_debug("Bit field was not set up. "
                "either its due to a lack of DTCM, or because the "
                "bit field was merged into the routing table");
    }

    log_debug("spike = %08x, entry_index = %u, start = %u, count = %u",
            spike, position, next_item, items_to_go);

    // A local address is used here as the interface requires something
    // to be passed in but using the address of an argument is odd!
    uint32_t local_spike_id;
    bool get_next = population_table_get_next_address(
            &local_spike_id, row_address, n_bytes_to_transfer);

    // tracks surplus DMAs
    if (!get_next) {
        log_debug("Found a entry which has a ghost entry for key %d", spike);
        ghost_pop_table_searches++;
    }
    return get_next;
}

bool population_table_get_next_address(
        spike_t *spike, synaptic_row_t *row_address,
        size_t *n_bytes_to_transfer) {
    // If there are no more items in the list, return false
    if (items_to_go == 0) {
        return false;
    }

    bool is_valid = false;
    do {
        address_and_row_length item = address_list[next_item].addr;
        if (item.address != INVALID_ADDRESS) {

            // If the row is a direct row, indicate this by specifying the
            // n_bytes_to_transfer is 0
            if (item.is_single) {
                *row_address = (synaptic_row_t) (get_direct_address(item) +
                    (last_neuron_id * sizeof(uint32_t)));
                *n_bytes_to_transfer = 0;
            } else {

                uint32_t row_length = get_row_length(item);
                uint32_t block_address = get_address(item);
                uint32_t stride = (row_length + N_SYNAPSE_ROW_HEADER_WORDS);
                uint32_t neuron_offset = last_neuron_id * stride * sizeof(uint32_t);

                *row_address = (synaptic_row_t) (block_address + neuron_offset);
                *n_bytes_to_transfer = stride * sizeof(uint32_t);
                log_debug("neuron_id = %u, block_address = 0x%.8x, "
                        "row_length = %u, row_address = 0x%.8x, n_bytes = %u",
                        last_neuron_id, block_address, row_length, *row_address,
                        *n_bytes_to_transfer);
                *spike = last_spike;
            }
            is_valid = true;
        }

        next_item++;
        items_to_go--;
    } while (!is_valid && (items_to_go > 0));

    return is_valid;
}

//! \}
