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

//! Magic flag for if the region id is not setup
int FAILED_REGION_ID = 0xFFFFFFFF;

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

//! The list of key to max atom maps
key_atom_data_t* keys_to_max_atoms;

//! Tracker for length of the key to max atoms map
uint32_t n_keys_to_max_atom_map = 0;

//! The number of vertex regions to process
uint32_t n_vertex_regions = 0;

//! \brief Fake bitfield holder.
//! \details This is used to circumvent the need for a bitfield in the
//!     master pop table, which we are trying to generate with the use of the
//!     master pop table. chicken vs egg.
bit_field_t* fake_bit_fields;

//! Holds SDRAM read row
synaptic_row_t row_data;

//! Says if we should run
bool can_run = true;

/*****************************stuff needed for structural stuff to work*/

//! The instantiation of the rewiring data
rewiring_data_t rewiring_data;

//! Inverse of synaptic matrix
static post_to_pre_entry *post_to_pre_table;

//! Pre-population information table
pre_pop_info_table_t pre_info;

/***************************************************************/

//! \brief Format of the builder region in SDRAM
typedef struct builder_region_struct {
    //! What region to find master population table in
    int master_pop_region_id;
    //! What region to find the synaptic matrix in
    int synaptic_matrix_region_id;
    //! What region to find the direct matrix in
    int direct_matrix_region_id;
    //! What region to find bitfield region information in
    int bit_field_region_id;
    //! What region to find bitfield key map information in
    int bit_field_key_map_region_id;
    //! What region to find structural plasticity information in
    int structural_matrix_region_id;
} builder_region_struct;

/***************************************************************/

//! \brief Get this processor's virtual CPU control table in SRAM.
//! \return a pointer to the virtual control table
static inline vcpu_t *vcpu(void) {
    vcpu_t *sark_virtual_processor_info = (vcpu_t *) SV_VCPU;
    uint core = spin1_get_core_id();
    return &sark_virtual_processor_info[core];
}

//! \brief Mark this process as failed.
static inline void fail_shut_down(void) {
    vcpu()->user2 = 1;
    bit_field_base_address->n_filters = 0;
}

//! \brief Mark this process as succeeded.
static inline void success_shut_down(void) {
    vcpu()->user2 = 0;
}

//! \brief Read in the vertex region addresses
void read_in_addresses(void) {
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

    dsg_metadata->regions[builder_data->bit_field_region_id].checksum = 0;
    dsg_metadata->regions[builder_data->bit_field_region_id].n_words = 0;

    // fill in size zero in case population table never read in
    bit_field_base_address->n_filters = 0;
    direct_matrix_region_base_address = data_specification_get_region(
            builder_data->direct_matrix_region_id, dsg_metadata);

    log_info("structural matrix region id = %d",
            builder_data->structural_matrix_region_id);
    if (builder_data->structural_matrix_region_id != FAILED_REGION_ID) {
        structural_matrix_region_base_address = data_specification_get_region(
                builder_data->structural_matrix_region_id, dsg_metadata);
    }
    key_atom_data_t *keys_to_max_atoms_sdram = data_specification_get_region(
            builder_data->bit_field_key_map_region_id, dsg_metadata);
    uint32_t pair_size = sizeof(key_atom_data_t) +
            (keys_to_max_atoms_sdram->n_pairs * sizeof(key_atom_pair_t));
    keys_to_max_atoms = spin1_malloc(pair_size);
    if (keys_to_max_atoms == NULL) {
        log_error("Couldn't allocate memory for key_to_max_atoms");
        rt_error(RTE_SWERR);
    }
    spin1_memcpy(keys_to_max_atoms, keys_to_max_atoms_sdram, pair_size);

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
}

#ifdef __PRINT_KEY_ATOM_MAP__
//! Debugging: print the map
static void print_key_to_max_atom_map(void) {
    log_info("Number of items is %d", keys_to_max_atoms->n_pairs);

    // put map into dtcm
    for (int key_to_max_atom_index = 0;
            key_to_max_atom_index < keys_to_max_atoms->n_pairs;
            key_to_max_atom_index++) {
        // print
        log_info("Entry %d has key %x and n_atoms of %d",
                key_to_max_atom_index,
                keys_to_max_atoms->pairs[key_to_max_atom_index].key,
                keys_to_max_atoms->pairs[key_to_max_atom_index].n_atoms);
    }
}
#endif

//! \brief Set up the master pop table and synaptic matrix for the bit field
//!        processing.
//! \return whether the init was successful.
bool initialise(void) {
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

    if (keys_to_max_atoms->n_pairs == 0) {
         success_shut_down();
         log_info("There were no bitfields to process.");
         can_run = false;
         return true;
    }

    // read in the correct key to max atom map
#ifdef __PRINT_KEY_ATOM_MAP__
    print_key_to_max_atom_map();
#endif

    // set up a sdram read for a row
    log_debug("Allocating dtcm for row data");
    row_data = spin1_malloc(row_max_n_words * sizeof(uint32_t));
    if (row_data == NULL) {
        log_error("Could not allocate dtcm for the row data");
        return false;
    }
    log_debug("Finished pop table set connectivity lookup");

    return true;
}

//! \brief Check plastic and fixed elements to see if there is a target.
//! \param[in] row: the synaptic row
//! \return Whether there is target.
bool process_synaptic_row(synaptic_row_t row) {
    // get address of plastic region from row
    if (synapse_row_plastic_size(row) > 0) {
        log_debug("Plastic row had entries, so cant be pruned");
        return true;
    }

    // Get address of non-plastic region from row
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    uint32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region);
    if (fixed_synapse == 0) {
        log_debug("Plastic and fixed do not have entries, so can be pruned");
        return false;
    } else {
        log_debug("Fixed row has entries, so cant be pruned");
        return true;
    }
}

//! \brief Do an SDRAM read to get synaptic row.
//! \param[in] row: the SDRAM address to read
//! \param[in] n_bytes_to_transfer:
//!     how many bytes to read to get the synaptic row
//! \return Whether there is target
static bool do_sdram_read_and_test(
        synaptic_row_t row, uint32_t n_bytes_to_transfer) {
    spin1_memcpy(row_data, row, n_bytes_to_transfer);
    log_debug("Process synaptic row");
    return process_synaptic_row(row_data);
}

//! \brief Sort filters by key
static inline void sort_by_key(void) {
    filter_info_t *filters = bit_field_base_address->filters;
    for (uint32_t i = 1; i < bit_field_base_address->n_filters; i++) {
        const filter_info_t temp = filters[i];

        uint32_t j;
        for (j = i; j > 0 && filters[j - 1].key > temp.key; j--) {
            filters[j] = filters[j - 1];
        }
        filters[j] = temp;
    }
}

//! Determine which bit fields are redundant
static void determine_redundancy(void) {
    // Semantic sugar to keep the code a little shorter
    filter_info_t *filters = bit_field_base_address->filters;
    for (uint32_t i = 0; i < bit_field_base_address->n_filters; i++) {
        filters[i].merged = 0;
        filters[i].all_ones = 0;
        int i_atoms = filters[i].n_atoms;
        int i_words = get_bit_field_size(i_atoms);
        if (i_atoms == count_bit_field(filters[i].data, i_words)) {
            filters[i].all_ones = 1;
        }
    }

    for (uint32_t i = 0; i < bit_field_base_address->n_filters; i++) {
        log_info("    Key: 0x%08x, Filter:", filters[i].key);
        uint32_t n_words = get_bit_field_size(filters[i].n_atoms);
        for (uint32_t j = 0; j < n_words; j++) {
            log_info("        0x%08x", filters[i].data[j]);
        }
    }
}

//! \brief Create the bitfield for this master pop table and synaptic matrix.
//! \return Whether it was successful at generating the bitfield
bool generate_bit_field(void) {
    // write how many entries (thus bitfields) are to be generated into sdram
    log_debug("Update by pop length");
    bit_field_base_address->n_filters = keys_to_max_atoms->n_pairs;

    // location where to dump the bitfields into (right after the filter structs
    address_t bit_field_words_location = (address_t)
            &bit_field_base_address->filters[bit_field_base_address->n_filters];
    log_debug("bit_field_words_location is %x", bit_field_words_location);
    int position = 0;

     // iterate through the master pop entries
    log_debug("Starting master pop entry bit field generation");
    for (uint32_t i = 0; i < keys_to_max_atoms->n_pairs; i++) {

        // Make a filter locally for now
        uint32_t n_neurons = keys_to_max_atoms->pairs[i].n_atoms;
        filter_info_t filter;
        filter.key = keys_to_max_atoms->pairs[i].key;
        filter.n_atoms = n_neurons;
        filter.core_shift = keys_to_max_atoms->pairs[i].core_shift;
        filter.n_atoms_per_core = keys_to_max_atoms->pairs[i].n_atoms_per_core;

        // generate the bitfield for this master pop entry
        uint32_t n_words = get_bit_field_size(n_neurons);

        log_debug("Bitfield %d, key = %d, n_neurons = %d",
                i, filter.key, n_neurons);
        bit_field_t bit_field = bit_field_alloc(n_neurons);
        if (bit_field == NULL) {
            log_error("Could not allocate dtcm for bit field");
            return false;
        }

        // set the bitfield to 0. so assuming a miss on everything
        clear_bit_field(bit_field, n_words);

        // iterate through neurons and ask for rows from master pop table
        log_debug("Searching neuron ids");
        struct core_atom core_atom = {0, 0};
        for (uint32_t neuron_id=0; neuron_id < n_neurons; neuron_id++) {
            // update key with neuron id
            spike_t new_key = get_bf_key(&filter, &core_atom);
            log_debug("New key for neurons %d is %0x", neuron_id, new_key);

            // check if this is governed by the structural stuff. if so,
            // avoid filtering as it could change over time
            bool bit_found = false;
            if (structural_matrix_region_base_address != NULL) {
                uint32_t dummy1 = 0, dummy2 = 0, dummy3 = 0, dummy4 = 0;
                bit_found = sp_structs_find_by_spike(&pre_info, new_key,
                        &dummy1, &dummy2, &dummy3, &dummy4);
            }

            // holder for the bytes to transfer if we need to read SDRAM.
            size_t n_bytes_to_transfer;

            // used to store the row from the master pop / synaptic matrix,
            // not going to be used in reality.
            synaptic_row_t row;
            if (!bit_found) {
                if (population_table_get_first_address(
                        new_key, &row, &n_bytes_to_transfer)) {
                    log_debug("%d", neuron_id);

                    // This is a direct row to process, so will have 1 target,
                    // so no need to go further
                    if (n_bytes_to_transfer == 0) {
                        log_debug("Direct synapse");
                        bit_found = true;
                    } else {
                        // sdram read (faking dma transfer)
                        log_debug("DMA read synapse");
                        bit_found = do_sdram_read_and_test(
                                row, n_bytes_to_transfer);
                    }

                    while (!bit_found && population_table_get_next_address(
                            &new_key, &row, &n_bytes_to_transfer)){
                        log_debug("%d", neuron_id);

                        // This is a direct row to process, so will have 1
                        // target, so no need to go further
                        if (n_bytes_to_transfer == 0) {
                            log_debug("Direct synapse");
                            bit_found = true;
                        } else {
                            // sdram read (faking dma transfer)
                            log_debug("DMA read synapse");
                            bit_found = do_sdram_read_and_test(
                                    row, n_bytes_to_transfer);
                        }
                    }
                }
            }

            // if returned false, then the bitfield should be set to 0.
            // Which its by default already set to. so do nothing. so no else.
            log_debug("bit_found %d", bit_found);
            if (bit_found) {
                bit_field_set(bit_field, neuron_id);
            }
            next_core_atom(&filter, &core_atom);
        }

        log_debug("Writing bitfield to sdram for core use");
        bit_field_base_address->filters[i].key = filter.key;
        log_debug("Putting master pop key %d in entry %d", filter.key, i);
        bit_field_base_address->filters[i].n_atoms = n_neurons;
        log_debug("Putting n_atom %d in entry %d", n_neurons, i);
        bit_field_base_address->filters[i].core_shift = filter.core_shift;
        bit_field_base_address->filters[i].n_atoms_per_core = filter.n_atoms_per_core;

        // write bitfield to sdram.
        log_debug("Writing to address %0x, %d words to write",
                &bit_field_words_location[position], n_words);
        spin1_memcpy(&bit_field_words_location[position], bit_field,
                n_words * BYTE_TO_WORD_CONVERSION);
        // update pointer to correct place
        bit_field_base_address->filters[i].data =
                (bit_field_t) &bit_field_words_location[position];

        // update tracker
        position += n_words;

        // free dtcm of bitfield.
        log_debug("Freeing the bitfield dtcm");
        sark_free(bit_field);
    }
    determine_redundancy();
    sort_by_key();
    return true;
}

//! Entry point
void c_main(void) {
    // set to running state
    sark_cpu_state(CPU_STATE_RUN);

    log_info("Starting the bit field expander");

    // read in sdram data
    read_in_addresses();

    // generate bit field for each vertex regions
    if (!initialise()) {
        log_error("Failed to init the master pop and synaptic matrix");
        fail_shut_down();
    }

    if (can_run) {
        log_info("Generating bit field");
        if (!generate_bit_field()) {
            log_error("Failed to generate bitfield");
            fail_shut_down();
        } else {
            success_shut_down();
            log_info("Successfully processed the bitfield");
        }
    }
}
