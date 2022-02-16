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
#include <neuron/synapse_row.h>
#include <neuron/population_table/population_table.h>
#include <neuron/structural_plasticity/synaptogenesis/sp_structs.h>
#include <filter_info.h>
#include <key_atom_map.h>

/***************************************************************/

//! \brief Read row and test if there are any synapses
//! \param[in] row_data: The DTCM address to read into
//! \param[in] row: the SDRAM address to read
//! \param[in] n_bytes_to_transfer:
//!     how many bytes to read to get the synaptic row
//! \return Whether there is target
static bool do_sdram_read_and_test(
        synaptic_row_t row_data, synaptic_row_t row,
        uint32_t n_bytes_to_transfer) {
    spin1_memcpy(row_data, row, n_bytes_to_transfer);
    log_debug("Process synaptic row");

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

//! \brief Sort filters by key
static inline void sort_by_key(filter_region_t *bitfield_filters) {
    filter_info_t *filters = bitfield_filters->filters;
    for (uint32_t i = 1; i < bitfield_filters->n_filters; i++) {
        const filter_info_t temp = filters[i];

        uint32_t j;
        for (j = i; j > 0 && filters[j - 1].key > temp.key; j--) {
            filters[j] = filters[j - 1];
        }
        filters[j] = temp;
    }
}

//! Determine which bit fields are redundant
static inline void determine_redundancy(filter_region_t *bitfield_filters) {
    // Semantic sugar to keep the code a little shorter
    filter_info_t *filters = bitfield_filters->filters;
    for (uint32_t i = 0; i < bitfield_filters->n_filters; i++) {
        filters[i].merged = 0;
        filters[i].all_ones = 0;
        int i_atoms = filters[i].n_atoms;
        int i_words = get_bit_field_size(i_atoms);
        if (i_atoms == count_bit_field(filters[i].data, i_words)) {
            filters[i].all_ones = 1;
        }
    }
}

//! \brief Create the bitfield for this master pop table and synaptic matrix.
//! \return Whether it was successful at generating the bitfield
static inline bool generate_bit_field(filter_region_t *bitfield_filters,
        key_atom_data_t *key_atom_data, void *structural_matrix,
        pre_pop_info_table_t *pre_info, synaptic_row_t row_data) {
    // write how many entries (thus bitfields) are to be generated into sdram
    bitfield_filters->n_filters = key_atom_data->n_pairs;

    // location where to dump the bitfields into (right after the filter structs
    address_t bit_field_words_location = (address_t)
            &bitfield_filters->filters[bitfield_filters->n_filters];
    int position = 0;

     // iterate through the master pop entries
    log_info("Generating %u pairs", key_atom_data->n_pairs);
    for (uint32_t i = 0; i < key_atom_data->n_pairs; i++) {

        // determine keys masks and n_neurons
        spike_t key = key_atom_data->pairs[i].key;
        uint32_t n_neurons = key_atom_data->pairs[i].n_atoms;

        // generate the bitfield for this master pop entry
        uint32_t n_words = get_bit_field_size(n_neurons);

        log_debug("Bitfield %d, key = %d, n_neurons = %d", i, key, n_neurons);
        bit_field_t bit_field = bit_field_alloc(n_neurons);
        if (bit_field == NULL) {
            log_error("Could not allocate dtcm for bit field");
            return false;
        }

        // set the bitfield to 0. so assuming a miss on everything
        clear_bit_field(bit_field, n_words);

        // iterate through neurons and ask for rows from master pop table
        log_debug("Searching neuron ids");
        for (uint32_t neuron_id=0; neuron_id < n_neurons; neuron_id++) {
            // update key with neuron id
            spike_t new_key = (spike_t) (key + neuron_id);
            log_debug("New key for neurons %d is %0x", neuron_id, new_key);

            // check if this is governed by the structural stuff. if so,
            // avoid filtering as it could change over time
            bool bit_found = false;
            if (structural_matrix != NULL) {
                uint32_t dummy1 = 0, dummy2 = 0, dummy3 = 0, dummy4 = 0;
                bit_found = sp_structs_find_by_spike(pre_info, new_key,
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
                                row_data, row, n_bytes_to_transfer);
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
                                    row_data, row, n_bytes_to_transfer);
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
        }

        log_debug("Writing bitfield to sdram for core use");
        bitfield_filters->filters[i].key = key;
        log_debug("Putting master pop key %d in entry %d", key, i);
        bitfield_filters->filters[i].n_atoms = n_neurons;
        log_debug("Putting n_atom %d in entry %d", n_neurons, i);
        // write bitfield to sdram.
        log_debug("Writing to address %0x, %d words to write",
                &bit_field_words_location[position], n_words);
        spin1_memcpy(&bit_field_words_location[position], bit_field,
                n_words * sizeof(uint32_t));
        // update pointer to correct place
        bitfield_filters->filters[i].data =
                (bit_field_t) &bit_field_words_location[position];

        // update tracker
        position += n_words;

        // free dtcm of bitfield.
        log_debug("Freeing the bitfield dtcm");
        sark_free(bit_field);
    }
    return true;
}

//! Entry point
static bool do_bitfield_generation(
        key_atom_data_t *key_atom_data_sdram, void *master_pop,
        void *synaptic_matrix, void *bitfield_filters, void *structural_matrix) {

    uint32_t pair_size = sizeof(key_atom_data_t) +
                (key_atom_data_sdram->n_pairs * sizeof(key_atom_pair_t));
    key_atom_data_t *key_atom_data = spin1_malloc(pair_size);
    if (key_atom_data == NULL) {
        log_error("Couldn't allocate memory for key_to_max_atoms");
        rt_error(RTE_SWERR);
    }
    spin1_memcpy(key_atom_data, key_atom_data_sdram, pair_size);

    uint32_t row_max_n_words;
    if (!population_table_initialise(master_pop, synaptic_matrix,
            &row_max_n_words)) {
        log_error("Failed to init the master pop table. failing");
        return false;
    }
    synaptic_row_t row_data = spin1_malloc(row_max_n_words * sizeof(uint32_t));
    if (row_data == NULL) {
        log_error("Could not allocate dtcm for the row data");
        return false;
    }

    rewiring_data_t rewiring_data;
    post_to_pre_entry *post_to_pre_table;
    pre_pop_info_table_t pre_info = {0, NULL};
    if (structural_matrix != NULL) {
        if (!sp_structs_read_in_common(
                structural_matrix, &rewiring_data, &pre_info, &post_to_pre_table)) {
            log_error("Failed to init the synaptogenesis");
            return false;
        }
    }

    if (!generate_bit_field(bitfield_filters, key_atom_data, structural_matrix,
            &pre_info, row_data)) {
        log_error("Failed to generate bit fields");
        return false;
    }
    determine_redundancy(bitfield_filters);
    sort_by_key(bitfield_filters);
    return true;
}
