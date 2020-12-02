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
#include <malloc_extras.h>

// stuff needed for the structural stuff to work
#include <neuron/structural_plasticity/synaptogenesis/sp_structs.h>

#include <filter_info.h>
#include <key_atom_map.h>

typedef struct not_redundant_tracker_t {
    // not redundant count
    uint32_t not_redundant_count;
    // filter pointer
    filter_info_t *filter;
} not_redundant_tracker_t;

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

//! Holds SDRAM read row
uint32_t * row_data;

//! Says if we should run
bool can_run = true;

//! dtcm tracker from the core in question
int dtcm_to_use = 0;

/*****************************stuff needed for structural stuff to work*/

//! The instantiation of the rewiring data
rewiring_data_t rewiring_data;

//! Inverse of synaptic matrix
static post_to_pre_entry *post_to_pre_table;

//! Pre-population information table
pre_pop_info_table_t pre_info;

static not_redundant_tracker_t* not_redundant_tracker = NULL;

/***************************************************************/


//! \brief Mark this process as failed.
static inline void fail_shut_down(void) {
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

    // set up a sdram read for a row
    log_debug("Allocating dtcm for row data");
    row_data = MALLOC(row_max_n_words * sizeof(uint32_t));
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

//! \brief sorts out bitfields for most important
bool sort_out_bitfields(void) {
    // get the bitfields in a copy form
    log_info("%d", population_table_get_length());
    not_redundant_tracker = MALLOC(
        sizeof(not_redundant_tracker_t) * bit_field_base_address->n_filters);

    if (not_redundant_tracker == NULL) {
        log_error("failed to malloc the main array");
        return false;
    }

    // store filter info
    for (uint32_t bit_field = 0; bit_field < bit_field_base_address->n_filters;
            bit_field++) {
        spin1_memcpy(
            not_redundant_tracker[bit_field].filter,
            &bit_field_base_address->filters[bit_field], sizeof(filter_info_t));

        // deduce redundancy
        not_redundant_tracker[bit_field].not_redundant_count = n_not_redundant(
            bit_field_base_address->filters[bit_field]);
    }

    // print for debug purposes
    for (uint32_t bit_field = 0; bit_field < bit_field_base_address->n_filters;
            bit_field++) {
        log_info(
            "bitfield with index %d has key %d and has redundant count of %d",
            bit_field, not_redundant_tracker[bit_field].filter->key,
            not_redundant_tracker[bit_field].not_redundant_count);
    }

    // sort so that most not redundant at front




}

//! \brief determines which blocks can be DTCM'ed.
bool cache_blocks(void) {
    log_info("plan to fill %d bytes of DTCM", dtcm_to_use);
    return true;
}

//! Entry point
void c_main(void) {
    // set to running state
    sark_cpu_state(CPU_STATE_RUN);

    log_info("Starting the synaptic block cacher");

    // set up the dtcm/sdram malloc system.
    malloc_extras_turn_off_safety();
    malloc_extras_initialise_no_fake_heap_data();

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
