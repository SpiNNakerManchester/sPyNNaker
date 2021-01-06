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

//! Byte to word conversion
#define BYTE_TO_WORD_CONVERSION 4

//! bits in a word
#define BITS_PER_WORD 32

//! \brief The highest bit within the word
#define TOP_BIT_IN_WORD 31

//! \brief The flag for when a spike isn't in the master pop table (so
//!     shouldn't happen)
#define NOT_IN_MASTER_POP_TABLE_FLAG -1

//! \brief The last spike received
static spike_t last_spike = 0;

//! \brief The last neuron id for the key
static uint32_t last_neuron_id = 0;

//! the index for the next item in the ::address_list
static uint16_t next_item = 0;

//! The number of relevant items remaining in the ::address_list
static uint16_t items_to_go = 0;

//! The bitfield map
static bit_field_t *connectivity_bit_field = NULL;

//! Base address for the synaptic matrix's direct rows
uint32_t direct_rows_base_address;

//! Base address for the synaptic matrix's indirect rows
uint32_t synaptic_rows_base_address;

//! The length of ::master_population_table
uint32_t master_population_table_length;

//! The master population table. This is sorted.
master_population_table_entry *master_population_table;

//! The array of information that points into the synaptic matrix
address_list_entry *address_list;

//! store of array dtcm blocks
synaptic_row_t** array_blocks;

//! store of binary search blocks
binary_search_top* binary_blocks;

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

//! \brief The number of cached look ups.
uint32_t n_master_pop_cached_look_ups = 0;

//! \brief The number of sdram look ups.
uint32_t n_master_pop_sdram_look_ups = 0;

//! \brief The number of direct matrix look ups.
uint32_t n_master_pop_direct_matrix_look_ups = 0;

//! \name Support functions
//! \{

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
#ifdef DEBUG
    uint32_t n_neurons = get_n_neurons(extra);
    if (local_neuron_id > n_neurons) {
        log_error("Spike %u is outside of expected neuron id range"
            "(neuron id %u of maximum %u)", spike, local_neuron_id, n_neurons);
        rt_error(RTE_SWERR);
    }
#endif
    return neuron_id;
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

#ifdef LOG_DEBUG
         // Sanity checking code; not needed in normal operation, and costs ITCM
         // With both things being in key order, this should never happen...
         if (bf_i < n_filters &&
                 filters[bf_i].key < master_population_table[mp_i].key) {
             log_error("Skipping bitfield %d for key 0x%08x", bf_i, filters[bf_i].key);
             rt_error(RTE_SWERR);
         }
#endif

         // While there is a match, keep track of the start and end; note this
         // may recheck the first entry, but there might not be a first entry if
         // we have already gone off the end of the bitfield array
         uint32_t start = bf_i;
         uint32_t n_words_total = 0;
         uint32_t useful = 0;
         log_debug("Starting with bit field %d with key 0x%08x", bf_i, filters[bf_i].key);
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

//! \brief locates the n atoms based off the filter
//! \param[in] key: master pop key.
//! \param[in] filter_region: base address of the bitfield region.
//! \param[out] atoms: the number of atoms, as defined by the filter.
//! \return bool stating if successful or not
static inline bool find_n_atoms(
        uint32_t key, filter_region_t *filter_region, uint32_t* atoms) {
    for (uint32_t filter_id = 0; filter_id < filter_region->n_filters;
            filter_id++) {
        if (filter_region->filters[filter_id].key == key) {
            *atoms = filter_region->filters[filter_id].n_atoms;
            return true;
        }
    }
    return false;
}

//! \brief caches into the array store
//! \param[in] atoms: the number of atoms in this block
//! \param[in] address_index: the index of this address
//! \param[in] key: the base routing key.
//! \param[in/out] array_index: the array index for this block
//! \return bool stating if successful or not.
static inline bool cached_in_array(
        uint32_t atoms, uint32_t address_index, uint32_t key,
        uint32_t* array_index) {
    log_debug(
        "caching address entry %d into array with atoms %d with base key %d",
        address_index, atoms, key);

    // malloc space for array
    synaptic_row_t* block = spin1_malloc(atoms * sizeof(synaptic_row_t));
    if (block == NULL) {
        log_error("failed to allocate DTCM for block with key %d", key);
    }

    // update and move marker
    array_blocks[*array_index] = block;

    // store
    for (uint32_t atom_id = 0; atom_id < atoms; atom_id ++) {
        // find row address
        spike_t spike = key + atom_id;
        synaptic_row_t row;
        uint32_t size_to_read;
        uint32_t representation;
        bool success = population_table_get_first_address(
            spike, &row, &size_to_read, &representation);
        if (!success) {
            log_error("failed to read first address");
            return false;
        }

        // find real row size
        uint32_t size_in_words = synapse_row_size_in_words(row);

        // if no data, nullify the holder
        if (size_in_words == N_SYNAPSE_ROW_HEADER_WORDS) {
            block[atom_id] = NULL;
            log_debug("no data for atom %d", atom_id);
        } else {
            // allocate dtcm for this row
            block[atom_id] = (synaptic_row_t) spin1_malloc(
                size_in_words * BYTE_TO_WORD_CONVERSION);
            if (array_blocks[*array_index] == NULL) {
                log_error(
                    "failed to malloc dtcm for block at index %d", address_index);
                return false;
            }

            // move the sdram into dtcm
            spin1_memcpy(
                block[atom_id], row, size_in_words * BYTE_TO_WORD_CONVERSION);
        }
    }
    return true;
}

//! \brief caches into the binary store
//! \param[in] atoms: the number of atoms in this block
//! \param[in] address_index: the index of this address
//! \param[in] key: the base routing key.
//! \param[in/out] binary_index: the binary index for this block
//! \return bool stating if successful or not.
static inline bool cached_in_binary_search(
        uint32_t atoms, uint32_t address_index, uint32_t key,
        uint32_t* binary_index) {
    log_debug("caching address entry %d into binary search", address_index);
    uint32_t elements_to_store = 0;

    // find elements total
    for (uint32_t atom_id = 0; atom_id < atoms; atom_id ++) {
        // find row address
        spike_t spike = key + atom_id;
        synaptic_row_t row;
        uint32_t size_to_read;
        uint32_t representation;
        bool success = population_table_get_first_address(
            spike, &row, &size_to_read, &representation);
        if (!success) {
            log_error("failed to read first address");
            return false;
        }

        // find real row size
        uint32_t size_in_words = synapse_row_size_in_words(row);

        if (size_in_words != N_SYNAPSE_ROW_HEADER_WORDS) {
            elements_to_store += 1;
        }
    }

    // malloc space for array
    binary_search_element * block = spin1_malloc(
        sizeof(binary_search_element) * elements_to_store);
    if (block == NULL) {
        log_error("failed to allocate DTCM for block with key %d", key);
    }

    // update trackers
    binary_blocks[*binary_index].elements = block;
    binary_blocks[*binary_index].len_of_array = elements_to_store;

    // store
    uint32_t binary_block_index = 0;
    for (uint32_t atom_id = 0; atom_id < atoms; atom_id ++) {
        // find row address
        spike_t spike = key + atom_id;
        synaptic_row_t row;
        uint32_t size_to_read;
        uint32_t representation;
        population_table_get_first_address(
            spike, &row, &size_to_read, &representation);

        // find real row size
        uint32_t size_in_words = synapse_row_size_in_words(row);

        if (size_in_words != N_SYNAPSE_ROW_HEADER_WORDS) {
            uint32_t size_in_bytes = size_in_words * BYTE_TO_WORD_CONVERSION;
            block[binary_block_index].src_neuron_id = atom_id;
            block[binary_block_index].row = spin1_malloc(size_in_bytes);

            if (block[binary_block_index].row == NULL) {
                log_error(
                    "failed to allocate DTCM for binary index %d for "
                    "block index %d of size %d as left over memory is %d",
                    *binary_index, binary_block_index, size_in_bytes,
                    sark_heap_max(sark.heap, 0));
                return false;
            }

            // move the sdram into dtcm
            spin1_memcpy(block[binary_block_index].row, row, size_in_bytes);
        }
    }
    return true;
}

//! \brief process a pop entry for caching in dtcm.
//! \param[in] pop_entry: the master pop entry
//! \param[in] filter_region: the bitfield region base address.
//! \param[in/out] array_index: the current index in the array store.
//! \param[in/out] binary_index: the current index in the binary store.
//! \return bool which states if successful or not.
static inline bool process_pop_entry_for_caching(
        master_population_table_entry pop_entry,
        filter_region_t * filter_region, uint32_t* array_index,
        uint32_t* binary_index) {

    // if an extra info flag is set, skip it as that is not cachable.
    uint32_t start = 0;
    uint32_t count = 0;
    bool success = population_table_set_start_and_count(
        pop_entry, &start, &count);
    if (!success) {
        log_error("failed to set start and count");
        return false;
    }

    // find size of block in terms of atoms
    uint32_t atoms = 0;
    success = find_n_atoms(pop_entry.key, filter_region, &atoms);
    if (!success) {
        log_error("failed to find the n atoms for key %d.", pop_entry.key);
        return false;
    }

    // search blocks and put in correct rep store
    for (uint32_t address_index = start; address_index < count + start;
            address_index ++) {

        // have to change rep here to default, to ensure get sdram address.
        // NOTE: needs to be changed back at the end of this.
        uint32_t correct_rep = address_list[address_index].addr.representation;
        address_list[address_index].addr.representation = DEFAULT;

        // process each rep correctly
        if (correct_rep == BINARY_SEARCH) {
            log_debug("binary cache");
            success = cached_in_binary_search(
                atoms, address_index, pop_entry.key, binary_index);
            if (success) {
                address_list[address_index].addr.address = *binary_index;
                *binary_index = *binary_index + 1;
                log_debug("success binary cache");
            }
        } else if (correct_rep == ARRAY) {
            log_debug("array cache");
            success = cached_in_array(
                atoms, address_index, pop_entry.key, array_index);
            if (success) {
                address_list[address_index].addr.address = *array_index;
                *array_index = *array_index + 1;
                log_debug("success array cache");
            }
        } else if (correct_rep == DEFAULT || correct_rep == DIRECT) {
            // ignore, as these are not cacheable
        } else {
            log_error("dont recognise the rep %d", correct_rep);
            return false;
        }

        // if it failed to cache return false
        if (!success) {
            return false;
        }

        // reset the representation to be whatever type it was.
        address_list[address_index].addr.representation = correct_rep;
    }

    // successfully cached all things
    return true;
}

//! \brief caches synaptic blocks into DTCM as required.
//! \param[in] table_address: master pop base address
//! \param[in] filter_region: bitfield region base address.
//! \return bool stating if successful or not
static inline bool cache_synaptic_blocks(
        address_t table_address, filter_region_t *filter_region) {
    // build stores.
    pop_table_config_t* store = (pop_table_config_t*) table_address;

    // safety check to bypass work
    if (store->n_array_blocks == 0 && store->n_binary_search_blocks == 0) {
        log_debug("no need to try to cache, nothing to cache");
        return true;
    }

    // try malloc array blocks
    if (store->n_array_blocks != 0) {
        array_blocks = spin1_malloc(sizeof(uint32_t*) * store->n_array_blocks);
        if (array_blocks == NULL) {
            log_error("failed to malloc array blocks");
            return false;
        }
    }

    // try to malloc binary blocks
    if (store->n_binary_search_blocks != 0) {
        binary_blocks = spin1_malloc(
            sizeof(binary_search_top) * store->n_binary_search_blocks);
        if (binary_blocks == NULL) {
            log_error("failed to malloc binary blocks");
            return false;
        }
    }

    // set params
    uint32_t array_index = 0;
    uint32_t binary_index = 0;

    // locate blocks to put into these blocks.
    for (uint32_t pop_entry_index = 0;
            pop_entry_index < master_population_table_length;
            pop_entry_index++) {
        master_population_table_entry pop_entry =
            population_table_entry(pop_entry_index);
        if (pop_entry.cache_in_dtcm) {
            log_debug("attempting to cach entry at %d", pop_entry_index);
            bool success = process_pop_entry_for_caching(
                pop_entry, filter_region, &array_index, &binary_index);
            if (!success) {
                log_error(
                    "failed to process entry with index %d with key %d",
                    pop_entry_index, pop_entry.key);
                return false;
            }
            log_debug("successfully cached entry at %d", pop_entry_index);
        }
    }
    log_debug("finish cache");
    return true;
}

//! \}

//! \name API functions
//! \{

bool population_table_initialise(
        address_t table_address, address_t synapse_rows_address,
        address_t direct_rows_address, filter_region_t *filter_region,
        uint32_t *row_max_n_words) {
    log_debug("Population_table_initialise: starting");
    pop_table_config_t *config = (pop_table_config_t *) table_address;

    master_population_table_length = config->table_length;
    // Store the base address
    log_debug("The stored synaptic matrix base address is located at: 0x%08x",
            synapse_rows_address);
    log_debug("The direct synaptic matrix base address is located at: 0x%08x",
            direct_rows_address);
    synaptic_rows_base_address = (uint32_t) synapse_rows_address;
    direct_rows_base_address = (uint32_t) direct_rows_address;

    // cast to correct store
    pop_table_config_t* store = (pop_table_config_t*) table_address;

    master_population_table_length = store->table_length;
    log_debug("Master pop table length is %d\n", master_population_table_length);
    log_debug("Master pop table entry size is %d\n",
            sizeof(master_population_table_entry));
    uint32_t n_master_pop_bytes =
            master_population_table_length * sizeof(master_population_table_entry);
    log_debug("Pop table size is %d\n", n_master_pop_bytes);
    log_debug("n cached array blocks = %d", store->n_array_blocks);
    log_debug("n cached binary blocks = %d", store->n_binary_search_blocks);

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
    spin1_memcpy(master_population_table, config->data,
            n_master_pop_bytes);
    spin1_memcpy(address_list, &config->data[master_population_table_length],
        n_address_list_bytes);

    // print to ensure every looks ok before caching
    print_master_population_table();

    // start the caching process.
    if (!cache_synaptic_blocks(table_address, filter_region)) {
        log_error("failed to cache into DTCM");
        return false;
    }

    //reset counters to reflect only execution lookups
    n_master_pop_cached_look_ups = 0;
    n_master_pop_sdram_look_ups = 0;
    n_master_pop_direct_matrix_look_ups = 0;

    *row_max_n_words = 0xFF + N_SYNAPSE_ROW_HEADER_WORDS;
    return true;
}

//! \brief search the dma cache for the correct element.
//! \param[in] binary_search_point: the top store for this block for searching.
//! \param[in] src_neuron_id: the src neuron id.
//! \return the synaptic row data as uint32_t*'s.
static inline synaptic_row_t binary_search_cache(
        binary_search_top binary_search_point, uint32_t src_neuron_id) {

    uint32_t imin = 0;
    uint32_t imax = binary_search_point.len_of_array;

    while (imin < imax) {
        uint32_t imid = (imax + imin) >> 1;
        binary_search_element entry = binary_search_point.elements[imid];
        if (src_neuron_id == entry.src_neuron_id) {
            return entry.row;
        } else if (entry.src_neuron_id < src_neuron_id) {

            // Entry must be in upper part of the table
            imin = imid + 1;
        } else {
            // Entry must be in lower part of the table
            imax = imid;
        }
    }
    return NULL;
}

bool population_table_get_first_address(
        spike_t spike, synaptic_row_t *row,
        size_t *n_bytes_to_transfer, uint32_t *representation) {
    // locate the position in the binary search / array
    log_debug("Searching for key %d", spike);

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
    log_debug("position = %d", position);

    master_population_table_entry entry = master_population_table[position];
    if (entry.count == 0) {
        log_debug("Spike %u (= %x): Population found in master population"
                "table but count is 0", spike, spike);
    }

    last_spike = spike;
    next_item = entry.start;
    items_to_go = entry.count;
    uint32_t bits_offset = 0;
    if (entry.extra_info_flag) {
        extra_info extra = address_list[next_item++].extra;
        bits_offset = get_core_index(extra, spike) * extra.n_words;
        last_neuron_id = get_extended_neuron_id(entry, extra, spike);
    } else {
        last_neuron_id = get_neuron_id(entry, spike);
    }

    // check we have a entry in the bit field for this (possible not to due to
    // DTCM limitations or router table compression). If not, go to DMA check.
    log_debug("Checking bit field");
    if (connectivity_bit_field != NULL &&
            connectivity_bit_field[position] != NULL) {
        log_debug("Can be checked, bitfield is allocated");
        // check that the bit flagged for this neuron id does hit a
        // neuron here. If not return false and avoid the DMA check.
        if (!bit_field_test(
                &connectivity_bit_field[position][bits_offset], last_neuron_id)) {
            log_debug("Tested and was not set");
            bit_field_filtered_packets += 1;
            return false;
        }
        log_debug("Was set, carrying on");
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
            &local_spike_id, row, n_bytes_to_transfer, representation);

    // tracks surplus DMAs
    if (!get_next) {
        log_debug("Found a entry which has a ghost entry for key %d", spike);
        ghost_pop_table_searches++;
    }
    return get_next;
}

bool population_table_get_next_address(
        spike_t *spike, synaptic_row_t *row,
        size_t *n_bytes_to_transfer, uint32_t* representation) {
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
            if (item.representation == DIRECT) {
                *row = (synaptic_row_t) (get_direct_address(item) +
                    (last_neuron_id * sizeof(uint32_t)));
                *n_bytes_to_transfer = 0;
                *representation = item.representation;
                is_valid = true;
                n_master_pop_direct_matrix_look_ups += 1;
            } else if (item.representation == ARRAY) {
                *n_bytes_to_transfer = 0;

                *row = array_blocks[item.address][last_neuron_id];
                if (*row == NULL) {
                    is_valid = false;
                } else {
                    is_valid = true;
                    *representation = item.representation;
                }
                n_master_pop_cached_look_ups += 1;
            }
            else if (item.representation == BINARY_SEARCH) {
                *n_bytes_to_transfer = 0;
                *row = binary_search_cache(
                    binary_blocks[item.address], last_neuron_id);
                if (*row == NULL) {
                    is_valid = false;
                } else {
                    is_valid = true;
                    *representation = item.representation;
                }
                n_master_pop_cached_look_ups += 1;
            } else if (item.representation == DEFAULT) {
                // sdram read needed
                uint32_t row_length = population_table_get_row_length(item);
                uint32_t block_address = population_table_get_address(item);
                uint32_t stride = (row_length + N_SYNAPSE_ROW_HEADER_WORDS);
                uint32_t neuron_offset = last_neuron_id * stride * sizeof(uint32_t);

                *row = (synaptic_row_t) (block_address + neuron_offset);
                *n_bytes_to_transfer = stride * sizeof(uint32_t);
                log_debug(
                    "neuron_id = %u, block_address = 0x%.8x,"
                    "row_length = %u, row = 0x%.8x, n_bytes = %u",
                    last_neuron_id, block_address, row_length, *row,
                    *n_bytes_to_transfer);
                *spike = last_spike;
                is_valid = true;
                *representation = item.representation;
                n_master_pop_sdram_look_ups += 1;
            } else {
                log_error(
                    "cant recognise the representation %d.",
                    item.representation);
                return false;
            }
        } else {
            log_debug("invalid address");
        }

        next_item++;
        items_to_go--;
    } while (!is_valid && (items_to_go > 0));

    return is_valid;
}

//! \}
