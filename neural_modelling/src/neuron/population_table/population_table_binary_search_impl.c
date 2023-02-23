/*
 * Copyright (c) 2016 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Master population table implementation that uses binary search
#include "population_table.h"
#include <neuron/synapse_row.h>
#include <debug.h>
#include <stdbool.h>


//! The master population table. This is sorted.
static master_population_table_entry *master_population_table;

//! The length of ::master_population_table
static uint32_t master_population_table_length;

//! The array of information that points into the synaptic matrix
static address_list_entry *address_list;

//! Base address for the synaptic matrix's indirect rows
static uint32_t synaptic_rows_base_address;

//! \brief The last spike received
static spike_t last_spike = 0;

//! \brief The last colour received
static uint32_t last_colour = 0;

//! \brief The last colour mask used
static uint32_t last_colour_mask = 0;

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

//! \brief Prints the master pop table.
//! \details For debugging
static inline void print_master_population_table(void) {
#if LOG_LEVEL >= LOG_DEBUG
    log_info("Master_population\n");
    for (uint32_t i = 0; i < master_population_table_length; i++) {
        master_population_table_entry entry = master_population_table[i];
        log_info("key: 0x%08x, mask: 0x%08x", entry.key, entry.mask);
        int count = entry.count;
        int start = entry.start;
		log_info("    core_mask: 0x%08x, core_shift: %u, n_neurons: %u, n_words: %u, n_colour_bits: %u",
				entry.core_mask, entry.mask_shift, entry.n_neurons, entry.n_words, entry.n_colour_bits);
        for (uint16_t j = start; j < (start + count); j++) {
            address_list_entry addr = address_list[j];
            if (addr.address == INVALID_ADDRESS) {
                log_info("    index %d: INVALID", j);
            } else {
                log_info("    index %d: offset: %u, address: 0x%08x, row_length: %u",
                    j, get_offset(addr), get_address(addr, synaptic_rows_base_address),
                    get_row_length(addr));
            }
        }
    }
    log_info("Population table has %u entries", master_population_table_length);
#endif
}

//! \brief Print bitfields for debugging
//! \param[in] mp_i: The master population table entry index
//! \param[in] filters: The bitfields to print
static inline void print_bitfields(uint32_t mp_i, filter_info_t *filters) {
#if LOG_LEVEL >= LOG_DEBUG
    // print out the bit field for debug purposes
    uint32_t n_words = get_bit_field_size(filters[mp_i].n_atoms);
    log_info("Bit field(s) for key 0x%08x, %u words for %u atoms:",
            master_population_table[mp_i].key, n_words, filters[mp_i].n_atoms);
    for (uint32_t i = 0; i < n_words; i++) {
        log_info("0x%08x", connectivity_bit_field[mp_i][i]);
    }
#else
    use(mp_i);
    use(filters);
#endif
}

bool population_table_load_bitfields(filter_region_t *filter_region) {

    if (master_population_table_length == 0) {
        return true;
    }
    // No filters = nothing to load
    if (filter_region->n_filters == 0) {
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
        failed_bit_field_reads += filter_region->n_filters;
        return true;
    }

    // Go through the population table, and the relevant bitfield list, both
    // of which are ordered by key...
    if (filter_region->n_filters != master_population_table_length) {
        log_error("The number of filters doesn't match the population table");
        return false;
    }
    filter_info_t* filters = filter_region->filters;
    for (uint32_t mp_i = 0; mp_i < master_population_table_length; mp_i++) {
         connectivity_bit_field[mp_i] = NULL;

         // Fail if the key doesn't match
         if (master_population_table[mp_i].key != filters[mp_i].key) {
             log_error("Bitfield for %u keys do not match: bf=0x%08x vs mp=0x%08x",
                     mp_i, filters[mp_i].key, master_population_table[mp_i].key);
             return false;
         }
         uint32_t useful = !(filters[mp_i].merged || filters[mp_i].all_ones);
         if (useful) {
             // Try to allocate all the bitfields for this entry
             uint32_t n_words = get_bit_field_size(filters[mp_i].n_atoms);
             uint32_t size = sizeof(bit_field_t) * n_words;
             connectivity_bit_field[mp_i] = spin1_malloc(size);
             if (connectivity_bit_field[mp_i] == NULL) {
                 // There might be more than one that has failed
                 failed_bit_field_reads += 1;
             } else {
                 spin1_memcpy(connectivity_bit_field[mp_i], filters[mp_i].data, size);
                 print_bitfields(mp_i, filters);
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

bool population_table_setup(address_t table_address, uint32_t *row_max_n_words,
        uint32_t *master_pop_table_length,
        master_population_table_entry **master_pop_table,
        address_list_entry **address_list) {
    pop_table_config_t *config = (pop_table_config_t *) table_address;

    *master_pop_table_length = config->table_length;

    if (*master_pop_table_length == 0) {
        return true;
    }

    uint32_t n_master_pop_bytes =
            *master_pop_table_length * sizeof(master_population_table_entry);

    // only try to malloc if there's stuff to malloc.
    *master_pop_table = spin1_malloc(n_master_pop_bytes);
    if (*master_pop_table == NULL) {
        log_error("Could not allocate master population table of %u bytes",
                n_master_pop_bytes);
        return false;
    }

    uint32_t address_list_length = config->addr_list_length;
    uint32_t n_address_list_bytes =
            address_list_length * sizeof(address_list_entry);

    *address_list = spin1_malloc(n_address_list_bytes);
    if (*address_list == NULL) {
        log_error("Could not allocate master population address list of %u bytes",
                n_address_list_bytes);
        return false;
    }

    // Copy the master population table
    spin1_memcpy(*master_pop_table, config->data, n_master_pop_bytes);
    spin1_memcpy(*address_list, &config->data[*master_pop_table_length],
            n_address_list_bytes);

    *row_max_n_words = 0xFF + N_SYNAPSE_ROW_HEADER_WORDS;
    return true;
}
//! \}

//! \name API functions
//! \{

bool population_table_initialise(
        address_t table_address, address_t synapse_rows_address,
        uint32_t *row_max_n_words) {
    population_table_setup(table_address, row_max_n_words,
            &master_population_table_length,
            &master_population_table, &address_list);

    // Store the base address
    synaptic_rows_base_address = (uint32_t) synapse_rows_address;

    print_master_population_table();
    return true;
}

bool population_table_get_first_address(spike_t spike, pop_table_lookup_result_t *result) {

    // check we don't have a complete miss
    uint32_t position;
    if (!population_table_position_in_the_master_pop_array(spike, &position)) {
        invalid_master_pop_hits++;
        return false;
    }

    master_population_table_entry entry = master_population_table[position];

    last_spike = spike;
    next_item = entry.start;
    items_to_go = entry.count;
	uint32_t local_neuron_id = get_local_neuron_id(entry, spike);
	if (entry.n_colour_bits) {
		last_colour_mask = (1 << entry.n_colour_bits) - 1;
	    last_colour = local_neuron_id & last_colour_mask;
	    last_neuron_id = (local_neuron_id >> entry.n_colour_bits) + get_core_sum(entry, spike);
	} else {
		last_colour = 0;
		last_colour_mask = 0;
		last_neuron_id = local_neuron_id + get_core_sum(entry, spike);
	}

    // check we have a entry in the bit field for this (possible not to due to
    // DTCM limitations or router table compression). If not, go to DMA check.
    if (connectivity_bit_field != NULL &&
            connectivity_bit_field[position] != NULL) {
        // check that the bit flagged for this neuron id does hit a
        // neuron here. If not return false and avoid the DMA check.
        if (!bit_field_test(
                connectivity_bit_field[position], last_neuron_id)) {
            bit_field_filtered_packets += 1;
            items_to_go = 0;
            return false;
        }
    }

    // A local address is used here as the interface requires something
    // to be passed in but using the address of an argument is odd!
    uint32_t local_spike_id;
    bool get_next = population_table_get_next_address(&local_spike_id, result);

    // tracks surplus DMAs
    if (!get_next) {
        ghost_pop_table_searches++;
    }
    return get_next;
}

bool population_table_get_next_address(spike_t *spike, pop_table_lookup_result_t *result) {
    // If there are no more items in the list, return false
    if (items_to_go == 0) {
        return false;
    }

    bool is_valid = false;
    do {
        address_list_entry item = address_list[next_item];
        if (item.address != INVALID_ADDRESS) {

        	get_row_addr_and_size(item, synaptic_rows_base_address,
        			last_neuron_id, result);
            *spike = last_spike;
            result->colour = last_colour;
            result->colour_mask = last_colour_mask;
            is_valid = true;
        }

        next_item++;
        items_to_go--;
    } while (!is_valid && (items_to_go > 0));

    return is_valid;
}
