/*
 * Copyright (c) 2019-2020 The University of Manchester
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
//! \brief Expands bitfields on SpiNNaker to reduce data transfer times
#include <bit_field.h>
#include <utils.h>
#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>
#include <common/bit_field_common.h>
#include <neuron/synapse_row.h>
#include <neuron/direct_synapses.h>
#include <neuron/population_table/population_table.h>

// stuff needed for the structural stuff to work
#include <neuron/structural_plasticity/synaptogenesis/sp_structs.h>

#include <filter_info.h>
#include <key_atom_map.h>

//! Byte to word conversion
#define BYTE_TO_WORD_CONVERSION 4

//! The minimum neurons to sort out DTCM and get though the synapse init.
#define N_NEURONS       1

//! The minimum synapse types to sort out DTCM and get though the synapse init
#define N_SYNAPSE_TYPES 1

//! key rep for using bianry
#define USE_BINARY 0

//! key rep for using array
#define USE_ARRAY 1

//! random number for malloc cost calc
#define ALANS_RANDOM 4

//! Magic flag for if the region id is not setup
int FAILED_REGION_ID = 0xFFFFFFFF;

//! \brief tracker for not redundant
typedef struct not_redundant_tracker_t {
    // not redundant count
    uint32_t not_redundant_count;
    // filter pointer
    filter_info_t *filter;
} not_redundant_tracker_t;

//! Master population table base address
address_t master_pop_base_address;

//! Synaptic matrix base address
address_t synaptic_matrix_base_address;

//! Bitfield base address
filter_region_t* bit_field_base_address;

//! Direct matrix base address
address_t direct_matrix_region_base_address;

//! Structural matrix region base address
address_t structural_matrix_region_base_address = NULL;

//! \brief Stores the DMA based master pop entries.
//! \details Used during pop table init, and reading back synaptic rows.
address_t direct_synapses_address;

//! \brief Stores the max row size for DMA reads (used when extracting a
//!     synapse row from sdram.
uint32_t row_max_n_words;

//! Holds SDRAM read row
uint32_t * row_data;

//! Says if we should run
bool can_run = true;

//! dtcm tracker from the core in question
int dtcm_to_use = 0;

//! malloc cost
int malloc_cost = 0;

/*****************************stuff needed for structural stuff to work*/

//! The instantiation of the rewiring data
rewiring_data_t rewiring_data;

//! Inverse of synaptic matrix
static post_to_pre_entry *post_to_pre_table;

//! Pre-population information table
pre_pop_info_table_t pre_info;

static not_redundant_tracker_t* not_redundant_tracker = NULL;

/***************************************************************/

//! \brief checks if the synapses in the block are plastic or structural or
//! not. If plastic then currently they wont be cached in the first impl.
//! \param[in] bit_field_index: index in bitfields.
//! \param[in] entry: the address list entry.
//! \return: bool stating if the block contains plastic synapses.
static inline bool synapses_are_plastic_or_structural(
        uint32_t bit_field_index, address_list_entry entry) {
    uint32_t address = population_table_get_address(entry.addr);
    uint32_t row_length = population_table_get_row_length(entry.addr);
    uint32_t stride = (row_length + N_SYNAPSE_ROW_HEADER_WORDS);

    uint32_t n_atoms = not_redundant_tracker->filter[bit_field_index].n_atoms;

    // cycle through atoms looking for plastic and struct synapses
    for (uint32_t atom_id = 0; atom_id < n_atoms; atom_id++) {
        uint32_t atom_offset = atom_id * stride * sizeof(uint32_t);
        address_t row_address = (address_t) (address + atom_offset);
        synaptic_row_t row = (synaptic_row_t) row_address;

        // plastic
        if (synapse_row_plastic_size(row) > 0) {
            return true;
        }

        // struct synapses
        bool bit_found = false;
        if (structural_matrix_region_base_address != NULL) {
            uint32_t new_key =
                not_redundant_tracker->filter[bit_field_index].key + atom_id;
            uint32_t dummy1 = 0, dummy2 = 0, dummy3 = 0, dummy4 = 0;
            bit_found = sp_structs_find_by_spike(&pre_info, new_key,
                    &dummy1, &dummy2, &dummy3, &dummy4);
        }
        if (bit_found) {
            return true;
        }
    }

    return false;
}

//! \brief returns the size of dtcm needed when using binary search rep
//! \param[in] bit_field_index: index in bitfields.
//! \param[in] entry: the address list entry.
//! \return: the size in bytes used by dtcm.
static inline int calculate_binary_search_size(
        uint32_t bit_field_index, address_list_entry entry) {
    // build stores
    uint32_t dtcm_used = 0;
    uint32_t n_atoms =
        not_redundant_tracker->filter[bit_field_index].n_atoms;
    uint32_t n_valid_entries = 0;

    uint32_t address = population_table_get_address(entry.addr);
    uint32_t row_length = population_table_get_row_length(entry.addr);
    uint32_t stride = (row_length + N_SYNAPSE_ROW_HEADER_WORDS);

    // populate stores
    for (uint32_t atom_id = 0; atom_id < n_atoms; atom_id++) {
        uint32_t atom_offset = atom_id * stride * sizeof(uint32_t);
        address_t row_address = (address_t) (address + atom_offset);
        // process static synapses
        uint32_t n_targets_in_words = synapse_row_num_fixed_synapses(
            synapse_row_fixed_region(row_address));

        if (n_targets_in_words != 0) {
            // TODO FIX WHEN STAGE 2.5 HAS HAPPENED
            uint32_t overall_bytes =
                (N_SYNAPSE_ROW_HEADER_WORDS + n_targets_in_words) *
                BYTE_TO_WORD_CONVERSION;
            dtcm_used += overall_bytes + malloc_cost;
            n_valid_entries += 1;
        } else {
            log_debug(
                "row for atom %d has no targets, so not caching", atom_id);
        }
    }

    // accum size of binary search array
    dtcm_used += sizeof(binary_search_top) + malloc_cost;
    dtcm_used +=
        n_valid_entries * sizeof(binary_search_element*) + malloc_cost;

    // return dtcm used
    return dtcm_used;
}

//! \brief returns the size of dtcm needed when using array search rep
//! \param[in] bit_field_index: index in bitfields.
//! \param[in] entry: the address list entry.
//! \return: the size in bytes used by dtcm.
static inline uint32_t calculate_array_search_size(
        uint32_t bit_field_index, address_list_entry entry) {
    // build stores
    uint32_t dtcm_used = 0;
    uint32_t n_atoms =
        not_redundant_tracker->filter[bit_field_index].n_atoms;
    dtcm_used += n_atoms * sizeof(uint32_t*) + malloc_cost;

    uint32_t address = population_table_get_address(entry.addr);
    uint32_t row_length = population_table_get_row_length(entry.addr);
    uint32_t stride = (row_length + N_SYNAPSE_ROW_HEADER_WORDS);

    // populate stores
    for (uint32_t atom_id = 0; atom_id < n_atoms; atom_id++) {
        uint32_t atom_offset = atom_id * stride * sizeof(uint32_t);
        address_t row_address = (address_t) (address + atom_offset);
        // process static synapses
        uint32_t n_targets_in_words = synapse_row_num_fixed_synapses(
            synapse_row_fixed_region(row_address));

        if (n_targets_in_words != 0) {
            // TODO FIX WHEN STAGE 2.5 HAS HAPPENED
            uint32_t overall_bytes =
                (N_SYNAPSE_ROW_HEADER_WORDS + n_targets_in_words) *
                BYTE_TO_WORD_CONVERSION;
            dtcm_used += overall_bytes + malloc_cost;
        } else {
            log_debug(
                "row for atom %d has no targets, so not caching", atom_id);
        }
    }

    // return dtcm used
    return dtcm_used;
}


//! \brief Mark this process as failed.
static void fail_shut_down(void) {
    vcpu()->user2 = 1;
}

//! \brief Mark this process as succeeded.
static inline void success_shut_down(void) {
    vcpu()->user2 = 0;
}

//! \brief Determine how many bits are not set in a bit field
//! \param[in] filter: The bitfield to look for redundancy in
//! \return How many not redundant packets there are
static uint32_t n_not_redundant(filter_info_t filter) {
    uint32_t n_atoms = filter.n_atoms;
    uint32_t n_words = get_bit_field_size(n_atoms);
    return count_bit_field(filter.data, n_words);
}

//! \brief Read in the vertex region addresses
static inline void read_in_addresses(void) {
    // get the data (linked to sdram tag 2 and assume the app ids match)
    data_specification_metadata_t *dsg_metadata =
            data_specification_get_data_address();
    const builder_region_struct *builder_data =
            (builder_region_struct *) vcpu()->user1;

    master_pop_base_address = data_specification_get_region(
            builder_data->master_pop_region_id, dsg_metadata);
    synaptic_matrix_base_address = data_specification_get_region(
            builder_data->synaptic_matrix_region_id, dsg_metadata);
    bit_field_base_address = data_specification_get_region(
            builder_data->bit_field_region_id, dsg_metadata);

    // fill in size zero in case population table never read in
    direct_matrix_region_base_address = data_specification_get_region(
            builder_data->direct_matrix_region_id, dsg_metadata);

    log_info("structural matrix region id = %d",
            builder_data->structural_matrix_region_id);
    if (builder_data->structural_matrix_region_id != FAILED_REGION_ID) {
        structural_matrix_region_base_address = data_specification_get_region(
                builder_data->structural_matrix_region_id, dsg_metadata);
    }

    // printer
    log_debug("master_pop_table_base_address = %0x", master_pop_base_address);
    log_debug("synaptic_matrix_base_address = %0x",
            synaptic_matrix_base_address);
    log_debug("bit_field_base_address = %0x", bit_field_base_address);
    log_debug("direct_matrix_region_base_address = %0x",
            direct_matrix_region_base_address);
    log_debug("Structural matrix region base address = %0x",
            structural_matrix_region_base_address);
    log_info("Finished reading in vertex data region addresses");

    // read user 2 into store
    dtcm_to_use = vcpu()->user2;
}

//! \brief Set up the master pop table and synaptic matrix for the bit field
//!        processing.
//! \return whether the init was successful.
static inline bool initialise(void) {

    // set up malloc cost
    uint dtcm_available = sark_heap_max(sark.heap, 0);
    uint32_t* holder = sark_alloc(ALANS_RANDOM * sizeof(uint32_t), 1);
    if (holder == NULL) {
        log_error("failed to alloc base checker");
        return false;
    }
    uint dtcm_used = dtcm_available - sark_heap_max(sark.heap, 0);
    malloc_cost = dtcm_used - (ALANS_RANDOM * sizeof(uint32_t));
    log_info("malloc cost is %d", malloc_cost);


    // init the synapses to get direct synapse address
    log_info("Direct synapse init");
    if (!direct_synapses_initialise(
            direct_matrix_region_base_address, &direct_synapses_address)) {
        log_error("Failed to init the synapses. failing");
        return false;
    }

    // init the master pop table
    log_info("Pop table init");
    if (!population_table_initialise(
            master_pop_base_address, synaptic_matrix_base_address,
            direct_synapses_address, &row_max_n_words)) {
        log_error("Failed to init the master pop table. failing");
        return false;
    }

    log_info("Structural plastic if needed");
    if (structural_matrix_region_base_address != NULL) {
        if (! sp_structs_read_in_common(
                structural_matrix_region_base_address, &rewiring_data,
                &pre_info, &post_to_pre_table)) {
            log_error("Failed to init the synaptogenesis");
            return false;
        }
    }

    // set up a sdram read for a row
    log_debug("Allocating dtcm for row data");
    row_data = sark_xalloc(
        sv->sdram_heap, row_max_n_words * sizeof(uint32_t), 0, ALLOC_LOCK);
    if (row_data == NULL) {
        log_error("Could not allocate dtcm for the row data");
        return false;
    }
    log_debug("Finished pop table set connectivity lookup");

    // sort out user 2 to see if we have anything to do
    if (dtcm_to_use == 0) {
        can_run = false;
    }

    return true;
}

//! \brief prints the store
static void print_store(void) {
    // print for debug purposes
    for (uint32_t bit_field = 0; bit_field < bit_field_base_address->n_filters;
            bit_field++) {
        log_info(
            "bitfield with index %d has key %d and has none redundant count of %d",
            bit_field, not_redundant_tracker[bit_field].filter->key,
            not_redundant_tracker[bit_field].not_redundant_count);
    }
    log_info("fin");
}

//! \brief reads in the bitfields
static inline bool read_in_bitfields(void) {
    // get the bitfields in a copy form
    not_redundant_tracker = sark_xalloc(
        sv->sdram_heap,
        sizeof(not_redundant_tracker_t) * bit_field_base_address->n_filters,
        0, ALLOC_LOCK);

    if (not_redundant_tracker == NULL) {
        log_error("failed to malloc the main array");
        return false;
    }

    // store filter info
    for (uint32_t bit_field = 0; bit_field < bit_field_base_address->n_filters;
            bit_field++) {
        not_redundant_tracker[bit_field].filter =
            &bit_field_base_address->filters[bit_field];

        // deduce redundancy
        not_redundant_tracker[bit_field].not_redundant_count = n_not_redundant(
            bit_field_base_address->filters[bit_field]);
    }
    return true;
}

//! \brief sorts so that bitfields with most none redundant at front
static inline void sort(void) {
    log_info("s");
    for (uint32_t i = 1; i < bit_field_base_address->n_filters; i++) {
        const not_redundant_tracker_t temp = not_redundant_tracker[i];

        uint32_t j;
        for (j = i; j > 0 &&
                not_redundant_tracker[j - 1].not_redundant_count <=
                temp.not_redundant_count; j--) {
            not_redundant_tracker[j] = not_redundant_tracker[j - 1];
        }
        log_info("stt");
        not_redundant_tracker[j] = temp;
    }
    log_info("st");
}

//! \brief sorts out bitfields for most important
static inline bool sort_out_bitfields(void) {
    // read in the stuff
    bool success = read_in_bitfields();
    if (!success) {
        log_error("failed to read in bitfields");
        return false;
    }
    // debug
    log_info("A");
    print_store();
    log_info("B");

    // sort so that most not redundant at front
    sort();

    log_info("after sort");
    print_store();
    return true;
}

static inline master_population_table_entry find_master_pop_entry(
        uint32_t bit_field_index) {
    uint32_t position = 0;
    bool success  = population_table_position_in_the_master_pop_array(
        not_redundant_tracker[bit_field_index].filter->key, &position);
    if (!success) {
        log_error(
            "failed to find a master pop table position for key %d.",
            not_redundant_tracker[bit_field_index].filter->key);
    }
    return population_table_entry(position);
}

//! \brief sets master pop entry in sdram to cache mode.
static bool set_master_pop_sdram_entry_to_cache(uint32_t bit_field_index) {
    // position in the array table.
    uint32_t position;
    bool success  = population_table_position_in_the_master_pop_array(
        not_redundant_tracker[bit_field_index].filter->key, &position);
    if (!success) {
        log_error("failed to read master pop entry");
        return false;
    }

    // set to cache in sdram
    master_population_table_entry* entry =
        population_table_get_master_pop_entry_from_sdram(
            master_pop_base_address, position);
    entry->cache_in_dtcm = 1;
    return true;
}

//! \brief sets sdram address to a different rep
static inline void set_address_to_cache_reps(
        uint32_t address_entry_index, uint32_t rep) {
    address_list_entry* entry =
        population_table_get_address_entry_from_sdram(
            master_pop_base_address, address_entry_index);
    entry->addr.representation = rep;
}

//! \brief determines which blocks can be DTCM'ed.
static inline bool cache_blocks(void) {
    log_info("plan to fill %d bytes of DTCM", dtcm_to_use);
    bool added_binary_base_cost = false;
    bool added_array_base_cost = false;
    bool used_binary_rep = false;
    bool used_array_rep = false;

    // search all the bitfields.
    for (uint32_t bit_field_index = 0;
            bit_field_index < bit_field_base_address->n_filters;
            bit_field_index++) {
        master_population_table_entry master_entry =
            find_master_pop_entry(bit_field_index);

        // trackers
        bool cache = true;
        int dtcm_to_use_tmp = dtcm_to_use;
        uint32_t * reps = sark_xalloc(
            sv->sdram_heap, sizeof(uint32_t) * master_entry.count, 0, ALLOC_LOCK);
        if (reps == NULL) {
            log_error("cannot allocate sdram for the reps.");
            return false;
        }

        // if an extra info flag is set, skip it as that is not cachable.
        uint32_t start = master_entry.start;
        uint32_t count = master_entry.count;
        if (master_entry.extra_info_flag) {
            start += 1;
            count -= 1;
        }

        // test all the blocks. all or nothing due to bitfield
        for (uint32_t address_index = start; address_index < count;
                address_index ++) {
            address_list_entry address_entry =
                population_table_get_address_entry(address_index);

            // if plastic or struct, wont cache during this impl.
            if (synapses_are_plastic_or_structural(
                    bit_field_index, address_entry)) {
                cache = false;
            }
            else {
                // test memory requirements of the 2 reps.
                int binary_search_size = calculate_binary_search_size(
                    bit_field_index, address_entry);
                int array_search_size = calculate_array_search_size(
                    bit_field_index, address_entry);

                // if binary better memory. see if we can cache with that rep.
                if (binary_search_size < array_search_size) {
                    // check if can be cached
                    if (dtcm_to_use_tmp - binary_search_size > 0) {
                        reps[address_index - start] = USE_BINARY;
                        dtcm_to_use_tmp =- binary_search_size;
                        used_binary_rep = true;
                    }
                    else {
                        cache = false;
                    }
                }
                else{  // array rep better. check if can be cached
                    if(dtcm_to_use_tmp - array_search_size > 0) {
                        reps[address_index - start] = USE_ARRAY;
                        dtcm_to_use_tmp =- binary_search_size;
                        used_array_rep = true;
                    }
                    else {
                        cache = false;
                    }
                }

                // add base costs if not done already
                if (used_binary_rep && !added_binary_base_cost) {
                    dtcm_to_use_tmp -= malloc_cost;
                    added_binary_base_cost = true;
                }
                if (used_array_rep && !added_array_base_cost) {
                    dtcm_to_use_tmp -= malloc_cost;
                    added_array_base_cost = true;
                }

                // final check before caching.
                if(dtcm_to_use_tmp <= 0) {
                    cache = false;
                }
            }
        }

        // update data structs to reflect caching
        if (cache) {
            // set master pop table to cache. and remove dtcm usage.
            bool success = set_master_pop_sdram_entry_to_cache(bit_field_index);
            if (!success) {
                return false;
            }

            for (uint32_t address_index = 0; address_index < count;
                    address_index ++) {
                // set addresses to cached reps.
                set_address_to_cache_reps(
                    address_index + start, reps[address_index]);
            }
            dtcm_to_use -= dtcm_to_use_tmp;
        }
    }
    return true;
}

//! Entry point
void c_main(void) {
    // set to running state
    sark_cpu_state(CPU_STATE_RUN);

    log_info("Starting the synaptic block cacher");

    // read in sdram data
    read_in_addresses();

    // set up stores etc
    if (!initialise()) {
        log_error("Failed to init the master pop and synaptic matrix");
        fail_shut_down();
    }

    if (can_run) {
        bool success = sort_out_bitfields();
        if (!success) {
            fail_shut_down();
        }
        success = cache_blocks();
        if (!success) {
            fail_shut_down();
        }
    }
    success_shut_down();
}
