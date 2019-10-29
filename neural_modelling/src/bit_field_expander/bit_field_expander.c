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

#include <bit_field.h>
#include <utils.h>
#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>
#include <neuron/population_table/population_table.h>
#include <neuron/direct_synapses.h>
#include <neuron/synapse_row.h>

#include <filter_info.h>
#include <key_atom_map.h>

// byte to word conversion
#define BYTE_TO_WORD_CONVERSION 4

// does minimum neurons to sort out dtcm and get though the synapse init.
#define N_NEURONS 1

// does minimum synapse types to sort out dtcm and get though the synapse init.
#define N_SYNAPSE_TYPES 1

//! master pop address
address_t master_pop_base_address;

// synaptic matrix base address
address_t synaptic_matrix_base_address;

// bitfield base address
filter_region_t* bit_field_base_address;

// direct matrix base address
address_t direct_matrix_region_base_address;

// used to store the dtcm based master pop entries. (used during pop table
// init, and reading back synaptic rows).
address_t direct_synapses_address;

// used to store the max row size for dma reads (used when extracting a
// synapse row from sdram.
uint32_t row_max_n_words;

// storage location for the list of key to max atom maps
key_atom_data_t* keys_to_max_atoms;

// tracker for length of the key to max atoms map
uint32_t n_keys_to_max_atom_map = 0;

// the number of vertex regions to process
uint32_t n_vertex_regions = 0;

//! a fake bitfield holder. used to circumvent the need for a bitfield in the
//! master pop table, which we are trying to generate with the use of the
//! master pop table. chicken vs egg.
bit_field_t* fake_bit_fields;

//! \brief used to hold sdram read row
uint32_t * row_data;

//! \brief bool holder saying if we should run
bool can_run = true;

//! \brief struct for builder region
typedef struct builder_region_struct{
    int master_pop_region_id;
    int synaptic_matrix_region_id;
    int direct_matrix_region_id;
    int bit_field_region_id;
    int bit_field_key_map_region_id;
} builder_region_struct;


void fail_shut_down(void){
    vcpu_t *sark_virtual_processor_info = (vcpu_t *) SV_VCPU;
    uint core = spin1_get_core_id();
    sark_virtual_processor_info[core].user2 = 1;
    bit_field_base_address->n_filters = 0;
}


void success_shut_down(void){
    vcpu_t *sark_virtual_processor_info = (vcpu_t *) SV_VCPU;
    uint core = spin1_get_core_id();
    sark_virtual_processor_info[core].user2 = 0;
}


//! \brief reads in the vertex region addresses
void read_in_addresses(){

    // get the data (linked to sdram tag 2 and assume the app ids match)
    data_specification_metadata_t *core_address =
        data_specification_get_data_address();

    vcpu_t *sark_virtual_processor_info = (vcpu_t *) SV_VCPU;
    uint core = spin1_get_core_id();
    builder_region_struct *builder_base_address =
        (builder_region_struct*) sark_virtual_processor_info[core].user1;
    builder_region_struct builder_data;
    spin1_memcpy(
        &builder_data, builder_base_address, sizeof(builder_region_struct));

    master_pop_base_address = data_specification_get_region(
        builder_data.master_pop_region_id, core_address);
    synaptic_matrix_base_address = data_specification_get_region(
        builder_data.synaptic_matrix_region_id, core_address);
    bit_field_base_address = (filter_region_t*)
        data_specification_get_region(
            builder_data.bit_field_region_id, core_address);
    direct_matrix_region_base_address = data_specification_get_region(
        builder_data.direct_matrix_region_id, core_address);
    keys_to_max_atoms = (key_atom_data_t*) data_specification_get_region(
        builder_data.bit_field_key_map_region_id, core_address);

    // printer
    log_debug("master_pop_table_base_address = %0x", master_pop_base_address);
    log_debug(
        "synaptic_matrix_base_address = %0x", synaptic_matrix_base_address);
    log_debug("bit_field_base_address = %0x", bit_field_base_address);
    log_debug("direct_matrix_region_base_address = %0x",
              direct_matrix_region_base_address);
    log_info("finished reading in vertex data region addresses");
}


void _print_key_to_max_atom_map(){

    log_info("n items is %d", keys_to_max_atoms->n_pairs);

    // put map into dtcm
    for (int key_to_max_atom_index = 0;
            key_to_max_atom_index < keys_to_max_atoms->n_pairs;
            key_to_max_atom_index++){

        // print
        log_info("entry %d has key %x and n_atoms of %d",
            key_to_max_atom_index,
            keys_to_max_atoms->pairs[key_to_max_atom_index].key,
            keys_to_max_atoms->pairs[key_to_max_atom_index].n_atoms);
    }
}


//! \brief deduces n neurons from the key
//! \param[in] mask: the key to convert to n_neurons
//! \return the number of neurons from the key map based off this key
uint32_t _n_neurons_from_key(uint32_t key){
    int key_index = 0;
    log_debug("n pairs is %d", keys_to_max_atoms->n_pairs);
    while (key_index < keys_to_max_atoms->n_pairs){
        key_atom_pair_t entry = keys_to_max_atoms->pairs[key_index];
        if (entry.key == key){
            return entry.n_atoms;
        }
        key_index ++;
    }

    log_error("did not find the key %x in the map. WTF!", key);
    log_error("n pairs is %d", keys_to_max_atoms->n_pairs);
    for (int pair_id = 0; pair_id < keys_to_max_atoms->n_pairs; pair_id++) {
        key_atom_pair_t entry = keys_to_max_atoms->pairs[key_index];
        log_error(
            "key at index %d is %x and equal = %d",
            pair_id, entry.key, entry.key == key);
    }
    rt_error(RTE_SWERR);
    return NULL;
}

//! \brief creates a fake bitfield where every bit is set to 1.
//! \return bool, which states if the creation of the fake bitfield was
//!               successful or not.
bool _create_fake_bit_field(){
    fake_bit_fields = spin1_malloc(
        population_table_length() * sizeof(bit_field_t));
    if (fake_bit_fields == NULL){
        log_error("failed to alloc dtcm for the fake bitfield holders");
        return false;
    }

    // iterate through the master pop entries
    for (uint32_t master_pop_entry=0;
            master_pop_entry < population_table_length();
            master_pop_entry++){
        fake_bit_fields[master_pop_entry] = NULL;
    }
    log_info("finished fake bit field");
    return true;
}

//! \brief sets up the master pop table and synaptic matrix for the bit field
//!        processing
//! \return: bool that states if the init was successful or not.
bool initialise(){

    // init the synapses to get direct synapse address
    log_info("direct synapse init");
    if (!direct_synapses_initialise(
            direct_matrix_region_base_address, &direct_synapses_address)) {
        log_error("failed to init the synapses. failing");
        return false;
    }

    // init the master pop table
    log_info("pop table init");
    if (!population_table_initialise(
            master_pop_base_address, synaptic_matrix_base_address,
            direct_synapses_address, &row_max_n_words)) {
        log_error("failed to init the master pop table. failing");
        return false;
    }

    log_info(" elements in master pop table is %d \n and max rows is %d",
             population_table_length(), row_max_n_words);

    if (population_table_length() == 0){
         success_shut_down();
         log_info("successfully processed the bitfields as there wasnt any");
         can_run = false;
         return true;
    }

    // read in the correct key to max atom map
    //_print_key_to_max_atom_map();

    // set up a fake bitfield so that it always says there's something to read
    if (!_create_fake_bit_field()){
        log_error("failed to create fake bit field");
        return false;
    }

    // set up a sdram read for a row
    log_info("allocating dtcm for row data");
    row_data = spin1_malloc(row_max_n_words * sizeof(uint32_t));
    if (row_data == NULL){
        log_error("could not allocate dtcm for the row data");
        return false;
    }
    log_debug("finished dtcm for row data");
    // set up the fake connectivity lookup into the master pop table

    population_table_set_connectivity_bit_field(fake_bit_fields);
    log_info("finished pop table set connectivity lookup");

    return true;
}

//! \brief checks plastic and fixed elements to see if there is a target.
//! \param[in] row: the synaptic row
//! \return bool stating true if there is target, false if no target.
bool process_synaptic_row(synaptic_row_t row){
    // get address of plastic region from row
    if (synapse_row_plastic_size(row) > 0){
        log_debug("plastic row had entries, so cant be pruned");
        return true;
    }
    else{
        // Get address of non-plastic region from row
        address_t fixed_region_address = synapse_row_fixed_region(row);
        uint32_t fixed_synapse =
            synapse_row_num_fixed_synapses(fixed_region_address);
        if (fixed_synapse == 0){
            log_debug(
                "plastic and fixed do not have entries, so can be pruned");
            return false;
        }
        else{
            log_debug("fixed row has entries, so cant be pruned");
            return true;
        }
    }
}

//! \brief do sdram read to get synaptic row
//! \param[in] row_address: the sdram address to read
//! \param[in] n_bytes_to_transfer: how many bytes to read to get the
//!                                 synaptic row
//! \return bool which states true if there is target, false if no target.
bool _do_sdram_read_and_test(
        address_t row_address, uint32_t n_bytes_to_transfer){
    spin1_memcpy(row_data, row_address, n_bytes_to_transfer);
    log_debug("process synaptic row");
    return process_synaptic_row(row_data);
}

//! \brief creates the bitfield for this master pop table and synaptic matrix
//! \param[in] vertex_id: the index in the regions.
//! \return bool that states if it was successful at generating the bitfield
bool generate_bit_field(){

    // write how many entries (thus bitfields) are to be generated into sdram
    log_debug("update by pop length");
    bit_field_base_address->n_filters = population_table_length();

    // location where to dump the bitfields into (right after the filter structs
    address_t bit_field_words_location =
        (address_t) &bit_field_base_address->filters[
            bit_field_base_address->n_filters];
    log_info("words location is %x", bit_field_words_location);
    int position = 0;

    // iterate through the master pop entries
    log_debug("starting master pop entry bit field generation");
    for (uint32_t master_pop_entry=0;
            master_pop_entry < population_table_length();
            master_pop_entry++){

        // determine keys masks and n_neurons
        spike_t key = population_table_get_spike_for_index(master_pop_entry);
        uint32_t mask = population_table_get_mask_for_entry(master_pop_entry);
        uint32_t n_neurons = _n_neurons_from_key(key);

        // generate the bitfield for this master pop entry
        uint32_t n_words = get_bit_field_size(n_neurons);

        log_debug("pop entry %d, key = %d, mask = %0x, n_neurons = %d",
                  master_pop_entry, (uint32_t) key, mask, n_neurons);
        bit_field_t bit_field = bit_field_alloc(n_neurons);
        if (bit_field == NULL){
            log_error("could not allocate dtcm for bit field");
            return false;
        }

        // set the bitfield to 0. so assuming a miss on everything
        clear_bit_field(bit_field, n_words);
        log_debug("cleared bit field");

        // update sdram with size of this bitfield
        bit_field_base_address->filters[master_pop_entry].key = key;
        log_debug(
            "putting master pop key %d in entry %d",
            key, master_pop_entry);
        bit_field_base_address->filters[master_pop_entry].n_words = n_words;
        log_debug("putting n words %d in entry %d", n_words, master_pop_entry);

        // iterate through neurons and ask for rows from master pop table
        log_debug("searching neuron ids");
        for (uint32_t neuron_id=0; neuron_id < n_neurons; neuron_id++){

            // update key with neuron id
            spike_t new_key = (spike_t) (key + neuron_id);
            log_debug("new key for neurons %d is %0x", neuron_id, new_key);

            // holder for the bytes to transfer if we need to read sdram.
            size_t n_bytes_to_transfer;

            // used to store the row from the master pop / synaptic matrix,
            // not going to be used in reality.
            address_t row_address;
            bool bit_found = false;
            if (population_table_get_first_address(
                    new_key, &row_address, &n_bytes_to_transfer)){
                log_debug("%d", neuron_id);

                // This is a direct row to process, so will have 1 target, so
                // no need to go further
                if (n_bytes_to_transfer == 0) {
                    log_debug("direct synapse");
                    bit_found = true;
                } else {
                    // sdram read (faking dma transfer)
                    log_debug("dma read synapse");
                    bit_found = _do_sdram_read_and_test(
                        row_address, n_bytes_to_transfer);
                }

                while (!bit_found && population_table_get_next_address(
                        &new_key, &row_address, &n_bytes_to_transfer)){
                    log_debug("%d", neuron_id);

                    // This is a direct row to process, so will have 1 target,
                    // so no need to go further
                    if (n_bytes_to_transfer == 0) {
                        log_debug("direct synapse");
                        bit_found = true;
                    } else {
                        // sdram read (faking dma transfer)
                        log_debug("dma read synapse");
                        bit_found = _do_sdram_read_and_test(
                            row_address, n_bytes_to_transfer);
                    }
                }
            }

            // if returned false, then the bitfield should be set to 0.
            // Which its by default already set to. so do nothing. so no else.
            if (bit_found) {
                bit_field_set(bit_field, neuron_id);
            }
        }

        // write bitfield to sdram.
        log_debug("writing bitfield to sdram for core use");
        log_debug("writing to address %0x, %d words to write",
                  &bit_field_words_location[position], n_words);
        spin1_memcpy(
            &bit_field_words_location[position], bit_field,
            n_words * BYTE_TO_WORD_CONVERSION);

        // update pointer to correct place
        bit_field_base_address->filters[master_pop_entry].data =
            (bit_field_t) &bit_field_words_location[position];

        // update tracker
        position += n_words;

        // free dtcm of bitfield.
        log_debug("freeing the bitfield dtcm");
        sark_free(bit_field);
    }
    return true;
}

void c_main(void) {
    // set to running state
    sark_cpu_state(CPU_STATE_RUN);

    log_info("starting the bit field expander");

    // read in sdram data
    read_in_addresses();

    // generate bit field for each vertex regions
    if (!initialise()){
        log_error("failed to init the master pop and synaptic matrix");
        fail_shut_down();
    }
    if (can_run) {
        log_info("generating bit field");
        if (!generate_bit_field()){
            log_error("failed to generate bitfield");
            fail_shut_down();
        }
        else{
            success_shut_down();
            log_info("successfully processed the bitfield");
        }
    }
}
