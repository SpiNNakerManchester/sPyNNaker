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
#include <debug.h>

//! \brief The number of bits of address.
//!        This is a constant as it is used more than once below.
#define N_ADDRESS_BITS 22

//! \brief The shift to apply to indirect addresses.
//!    The address is in units of four words, so this multiplies by 16 (= up
//!    shifts by 4)
#define INDIRECT_ADDRESS_SHIFT 4

// An Invalid address and row length; used to keep indices aligned between
// delayed and undelayed tables
#define INVALID_ADDRESS ((1 << N_ADDRESS_BITS) - 1)


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

//! \brief The memory layout in SDRAM of the first part of the population table
//!     configuration. Address list data (array of ::address_and_row_length) is
//!     packed on the end.
typedef struct {
    // length of master_population_table_entry array.
    uint32_t table_length;
    // length of address_list_entry array.
    uint32_t addr_list_length;
    // length of array_blocks array.
    uint32_t n_array_blocks;
    // length of binary_blocks array.
    uint32_t n_binary_search_blocks;
    // start of pop array
    master_population_table_entry data[];
} pop_table_config_t;

// \brief struct for holding a binary search element
typedef struct binary_search_element {
    // the src neuron id
    uint32_t src_neuron_id;
    // row linked
    synaptic_row_t row;
} binary_search_element;

// stores binary search components
typedef struct binary_search_top {
    // the number of none empty rows
    uint32_t len_of_array;
    // pointer to the array store of none empty rows.
    binary_search_element* elements;
} binary_search_top;

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
    //! contains representation_values enum value.
    uint32_t representation: 2;
} address_and_row_length;

//! \brief A enum for representing other data representations
typedef enum representation_values {
    //! sdram store
    DEFAULT = 0,
    //! representation of a direct 1 to 1
    DIRECT = 1,
    //! Binary Search
    BINARY_SEARCH = 2,
    //! 1d array
    ARRAY = 3,
} representation_values;

//! \brief An entry in the address list is either an address and row length or extra
//! info if flagged.
typedef union {
    address_and_row_length addr;
    extra_info extra;
} address_list_entry;

//! ===========================================

//! \brief The number of cached look ups.
extern uint32_t n_master_pop_cached_look_ups;

//! \brief The number of sdram look ups.
extern uint32_t n_master_pop_sdram_look_ups;

//! \brief The number of direct matrix look ups.
extern uint32_t n_master_pop_direct_matrix_look_ups;

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

//! Base address for the synaptic matrix's indirect rows
extern uint32_t synaptic_rows_base_address;

//! Base address for the synaptic matrix's direct rows
extern uint32_t direct_rows_base_address;

//! =================================================================

//! debug bits to change dtcm state for printing
void print_cache_arrays(address_t table_address);


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

//! \brief Get the source neuron ID for a spike given its table entry (without extra info)
//! \param[in] entry: the table entry
//! \param[in] spike: the spike
//! \return the neuron ID
static inline uint32_t get_neuron_id(
        master_population_table_entry entry, spike_t spike) {
    return spike & ~entry.mask;
}

//! \brief Get the neuron id of the neuron on the source core, for a spike with
//         extra info
//! \param[in] entry: the table entry
//! \param[in] extra_info: the extra info entry
//! \param[in] spike: the spike received
//! \return the source neuron id local to the core
static inline uint32_t get_local_neuron_id(
        master_population_table_entry entry, extra_info extra, spike_t spike) {
    return spike & ~(entry.mask | (extra.core_mask << extra.mask_shift));
}

//! \brief Get the full source neuron id for a spike with extra info
//! \param[in] entry: the table entry
//! \param[in] extra_info: the extra info entry
//! \param[in] spike: the spike received
//! \return the source neuron id
static inline uint32_t get_extended_neuron_id(
        master_population_table_entry entry, extra_info extra, spike_t spike) {
    uint32_t local_neuron_id = get_local_neuron_id(entry, extra, spike);
    uint32_t neuron_id = local_neuron_id + get_core_sum(extra, spike);
    return neuron_id;
}

//! \brief sets a address list element to a different rep
//! \param[in] index: position in address list.
//! \param[in] rep: the new rep to set to.
static inline void population_table_set_address_to_rep(
        uint32_t index, uint32_t rep) {
    address_list[index].addr.representation = rep;
}

//! \brief sets a population table entry to be cached.
//! \param[in] position: the position in the master table to set to cache
static inline void population_table_entry_set_to_cache(uint32_t position) {
    master_population_table[position].cache_in_dtcm = 1;
}

//! =============================================================

//! \brief Get the direct row address out of an entry
//! \param[in] entry: the table entry
//! \return a direct row address
static inline uint32_t get_direct_address(address_and_row_length entry) {
    return entry.address + direct_rows_base_address;
}

static inline master_population_table_entry*
        population_table_get_master_pop_entry_from_sdram(
            address_t table_address, uint32_t position) {
    pop_table_config_t* store = (pop_table_config_t*) table_address;
    return &(store->data[position]);
}

//! \brief get a master pop entry from array
//! \param[in] index: index to get element from
//! \return master pop table entry.
static inline master_population_table_entry population_table_entry(
        uint32_t index) {
    return master_population_table[index];
}

//! \brief Get the length of the row from the entry
//!
//! Row lengths are stored offset by 1, to allow 1-256 length rows
//!
//! \param[in] entry: the table entry
//! \return the row length
static inline uint32_t population_table_get_row_length(
        address_and_row_length entry) {
    return entry.row_length + 1;
}

//! \brief Get the standard address offset out of an entry
//!
//! The address is in units of four words, so this multiplies by 16 (= up
//! shifts by 4)
//! \param[in] entry: the table entry
//! \return a row address (which is an offset)
static inline uint32_t population_table_get_offset(address_and_row_length entry) {
    return entry.address << INDIRECT_ADDRESS_SHIFT;
}

//! \brief Get the standard address out of an entry
//! \param[in] entry: the table entry
//! \return a row address
static inline uint32_t population_table_get_address(address_and_row_length entry) {
    return population_table_get_offset(entry) + synaptic_rows_base_address;
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
    pop_table_config_t* store = (pop_table_config_t*) table_address;
    address_list_entry* addresses = (address_list_entry*) (
        &store->data[store->table_length]);
    return &(addresses[address_entry_index]);
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


//! \brief finds position in master pop table
//! \param[in] key: master pop key
//! \param[out] position: the position in the array where this key entry lives.
//! \return bool stating if finding was successful or not
static bool population_table_get_position_in_master_pop(
        uint32_t key, uint32_t* position) {
    bool success  = population_table_position_in_the_master_pop_array(
        key, position);
    if (!success) {
        log_error("WTF how did this happen. cant find the position");
        return false;
    }
    return true;
}

//! \brief finds the number of atoms for a core via filter via a key
//! \param[in] key: the base key of a core
//! \param[in] filter_region: the bitfield filters region.
//! \param[out] filter: the filter containing data found.
//! \return bool if successful or not
static inline bool find_bit_field_filter(
        uint32_t key, filter_region_t *filter_region, filter_info_t* filter) {
    for (uint32_t f_id = 0; f_id < filter_region->n_filters; f_id++) {
        if (filter_region->filters[f_id].key == key) {
            *filter = filter_region->filters[f_id];
            return true;
        }
        log_info("searched with key %d", filter_region->filters[f_id].key);
    }
    return false;
}

//! \brief ensures we only deal with basic addresses and not the extra ones.
//! \param[in] master_entry: master pop entry.
//! \param[out] start: the start point in the address array
//! \param[out] count: the number of entries to iterate over in address array.
//! \param[out] n_atoms: the atom offset for src atom ids
//! \return bool success or not
static inline bool population_table_set_start_and_count(
        master_population_table_entry master_entry, uint32_t* start,
        uint32_t* count, uint32_t* n_atoms, filter_region_t *filter_region) {
    // if an extra info flag is set, skip it as that is not cachable.
    *start = master_entry.start;
    *count = master_entry.count;
    uint32_t position = 0;
    if (master_entry.extra_info_flag) {
        if (!population_table_get_position_in_master_pop(
                master_entry.key, &position)) {
            return false;
        }
        *start += 1;
        extra_info extra = address_list[master_entry.start].extra;

        // accum all atoms from all cores, ensure the capture of the last
        // cores lack of power of 2 atoms
        for (uint32_t core_id = 0; core_id < 2; core_id ++) {
            uint32_t core_key = master_entry.key & (core_id << extra.mask_shift);
            uint32_t atom_key = get_extended_neuron_id(master_entry, extra, core_key);
            log_info("core key %d, atom key = %d", core_key, atom_key);
            filter_info_t filter;
            bool success = find_bit_field_filter(atom_key, filter_region, &filter);
            if (!success) {
                log_error("failed to find filter for key %d.", core_key);
                return false;
            }
            *n_atoms = *n_atoms + filter.n_atoms;
        }
        log_debug("found extra info at index %d. skipping", position);
    }
    else {
        if (!population_table_get_position_in_master_pop(
                master_entry.key, &position)) {
            return false;
        }
        filter_info_t filter;
        bool success = find_bit_field_filter(
            master_entry.key, filter_region, &filter);
        if (!success) {
            log_error("failed to find filter for key %d.", master_entry.key);
            return false;
        }

        *n_atoms = filter.n_atoms;
        log_debug("basic entry at master pop array at index %d", position);
    }
    return true;
}

//! \brief Prints the master pop table.
//! \details For debugging
static inline void print_master_population_table(void) {
    log_info("Master_population\n");
    for (uint32_t i = 0; i < master_population_table_length; i++) {
        master_population_table_entry entry = master_population_table[i];
        log_info(
            "key: 0x%08x, mask: 0x%08x, start:%d, extra_info_flag:%d, "
            "count:%d, cache_in_dtcm:%d",
            entry.key, entry.mask, entry.start, entry.extra_info_flag,
            entry.count, entry.cache_in_dtcm);
        int count = entry.count;
        int start = entry.start;
        if (entry.extra_info_flag) {
            extra_info extra = address_list[start].extra;
            log_info(
                "    index %d: extra entry: core_mask: 0x%08x, core_shift: %u,"
                " n_neurons: %u",
                start, extra.core_mask, extra.mask_shift, extra.n_neurons);
            start += 1;
        }
        for (uint16_t j = start; j < (start + count); j++) {
            address_and_row_length addr = address_list[j].addr;
            if (addr.address == INVALID_ADDRESS) {
                log_info("    index %d: INVALID", j);
            } else if (!(addr.representation == DIRECT)) {
                log_info(
                    "    index %d: offset: %u, address: 0x%08x, "
                    "row_length: %u, representation %d",
                    j, population_table_get_offset(addr),
                    population_table_get_address(addr),
                    population_table_get_row_length(addr),
                    addr.representation);
            } else {
                log_info(
                    "    index %d: offset: %u, address: 0x%08x, representation %d",
                    j, addr.address, get_direct_address(addr), addr.representation);
            }
        }
    }
    log_info("Population table has %u entries", master_population_table_length);
}

//! \brief Set up the table
//! \param[in] table_address: The address of the start of the table data
//! \param[in] synapse_rows_address: The address of the start of the synapse
//!                                  data
//! \param[in] direct_rows_address: The address of the start of the direct
//!                                 synapse data
//! \param[in] filter_region: The address of the start of the bitfield region.
//! \param[out] row_max_n_words: Updated with the maximum length of any row in
//!                              the table in words
//! \return True if the table was initialised successfully, False otherwise
bool population_table_initialise(
        address_t table_address, address_t synapse_rows_address,
        address_t direct_rows_address, filter_region_t *filter_region,
        uint32_t *row_max_n_words);

//! \brief Initialise the bitfield filtering system.
//! \param[in] filter_region: Where the bitfield configuration is
//! \return True on success
bool population_table_load_bitfields(filter_region_t *filter_region);

//! \brief Get the first row data for the given input spike
//! \param[in] spike: The spike received
//! \param[out] row_address: Updated with the address of the row
//! \param[out] n_bytes_to_transfer: Updated with the number of bytes to read
//! \param[out] representation: the rep of the data for this block
//! \return True if there is a row to read, False if not
bool population_table_get_first_address(
        spike_t spike, synaptic_row_t* row_address,
        size_t* n_bytes_to_transfer, uint32_t* representation);

//! \brief Get the next row data for a previously given spike.  If no spike has
//!        been given, return False.
//! \param[out] spike: The initiating spike
//! \param[out] row_address: Updated with the address of the row
//! \param[out] n_bytes_to_transfer: Updated with the number of bytes to read
//! \param[out] representation: the rep of the data for this block
//! \return True if there is a row to read, False if not
bool population_table_get_next_address(
        spike_t *spike, synaptic_row_t* row_address,
        size_t* n_bytes_to_transfer, uint32_t* representation);


#endif // _POPULATION_TABLE_H_
