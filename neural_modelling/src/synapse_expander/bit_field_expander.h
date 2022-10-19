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

static uint32_t master_pop_table_length;
static master_population_table_entry* master_pop_table;
static address_list_entry *address_list;

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
        uint32_t *n_atom_data, void *synaptic_matrix, void *structural_matrix,
        pre_pop_info_table_t *pre_info, synaptic_row_t row_data) {

    // Get the location just after the structs for the actual bit fields
    uint32_t *bit_field_words_location = (uint32_t *)
            &bitfield_filters->filters[master_pop_table_length];
    int position = 0;

     // iterate through the master pop entries
    log_info("Generating %u bitfields", master_pop_table_length);
    for (uint32_t i = 0; i < master_pop_table_length; i++) {

        // determine n_neurons and bit field size
        uint32_t n_neurons = n_atom_data[i];
        uint32_t n_words = get_bit_field_size(n_neurons);

        // Make and clear a bit field
        bit_field_t bit_field = bit_field_alloc(n_neurons);
        if (bit_field == NULL) {
            log_error("Could not allocate dtcm for bit field");
            return false;
        }
        clear_bit_field(bit_field, n_words);

        master_population_table_entry mp_entry = master_pop_table[i];

        if (structural_matrix != NULL) {

            // If this is a structural entry, set all the bits
            uint32_t dummy1 = 0, dummy2 = 0, dummy3 = 0, dummy4 = 0;
            if (sp_structs_find_by_spike(pre_info, mp_entry.key,
                    &dummy1, &dummy2, &dummy3, &dummy4)) {
            	for (uint32_t n = 0; n < n_neurons; n++) {
                    bit_field_set(bit_field, n);
                }
            }
        } else {

			// Go through the addresses of the master pop entry
			uint32_t pos = mp_entry.start;
			for (uint32_t j = mp_entry.count; j > 0; j--, pos++) {

				// Find the base address and row length of the address entry
				address_list_entry entry = address_list[pos];

				// Skip invalid addresses
				if (entry.address == INVALID_ADDRESS) {
					continue;
				}

				// Go through each neuron and check the row
				for (uint32_t n = 0; n < n_neurons; n++) {

					// If this neuron is already set, skip it this round
					if (bit_field_test(bit_field, n)) {
						continue;
					}

					synaptic_row_t row;
					uint32_t n_bytes_to_transfer;
					get_row_addr_and_size(entry, (uint32_t) synaptic_matrix,
					        n, &row, &n_bytes_to_transfer);

					// Check if the row is non-empty and if so set a bit
					if (do_sdram_read_and_test(row_data, row, n_bytes_to_transfer)) {
						bit_field_set(bit_field, n);
					}
				}
			}
        }

        // Copy details into SDRAM
        bitfield_filters->filters[i].key = mp_entry.key;
        bitfield_filters->filters[i].n_atoms = n_neurons;
        bitfield_filters->filters[i].n_atoms_per_core = mp_entry.n_neurons;
        bitfield_filters->filters[i].core_shift = mp_entry.mask_shift;
        spin1_memcpy(&bit_field_words_location[position], bit_field,
                n_words * sizeof(uint32_t));
        bitfield_filters->filters[i].data = &bit_field_words_location[position];

        // Move to the next location in SDRAM for bit fields
        position += n_words;

        // free dtcm of bitfield.
        log_debug("Freeing the bitfield dtcm");
        sark_free(bit_field);
    }

    // write how many entries (thus bitfields) have been generated into sdram
    bitfield_filters->n_filters = master_pop_table_length;
    return true;
}

//! Entry point
static bool do_bitfield_generation(
        uint32_t *n_atom_data_sdram, void *master_pop,
        void *synaptic_matrix, void *bitfield_filters, void *structural_matrix) {

	pop_table_config_t *config = (pop_table_config_t *) master_pop;
	master_pop_table_length = config->table_length;

    if (master_pop_table_length == 0) {
    	return true;
    }

    master_pop_table = &config->data[0];
    address_list = (address_list_entry *) &config->data[master_pop_table_length];

    uint32_t n_atom_bytes = master_pop_table_length * sizeof(uint32_t);
    uint32_t *n_atom_data = spin1_malloc(n_atom_bytes);
    if (n_atom_data == NULL) {
        log_error("Couldn't allocate memory for key_to_max_atoms");
        rt_error(RTE_SWERR);
    }
    spin1_memcpy(n_atom_data, n_atom_data_sdram, n_atom_bytes);


    uint32_t row_max_n_words = 0xFF + N_SYNAPSE_ROW_HEADER_WORDS;
    synaptic_row_t row_data = spin1_malloc(row_max_n_words * sizeof(uint32_t));
    if (row_data == NULL) {
        log_error("Could not allocate dtcm for the row data");
        return false;
    }

    rewiring_data_t rewiring_data;
    post_to_pre_entry *post_to_pre_table;
    pre_pop_info_table_t pre_info = {0, NULL};
    if (structural_matrix != NULL) {
        sp_structs_read_in_common(
            structural_matrix, &rewiring_data, &pre_info, &post_to_pre_table);
    }

    if (!generate_bit_field(bitfield_filters, n_atom_data, synaptic_matrix,
            structural_matrix, &pre_info, row_data)) {
        log_error("Failed to generate bit fields");
        return false;
    }
    determine_redundancy(bitfield_filters);
    return true;
}
