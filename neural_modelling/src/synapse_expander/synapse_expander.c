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

/**
 * \dir
 * \brief Implementation of the synapse expander and delay expander
 * \file
 * \brief The synapse expander for neuron cores
 */
#include "matrix_generator.h"
#include "connection_generator.h"
#include "param_generator.h"
#include "rng.h"

#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>
#include <key_atom_map.h>
#include "common_mem.h"
#include "bit_field_expander.h"

#define INVALID_REGION_ID 0xFFFFFFFF

//! The configuration of the connection builder
typedef struct connection_builder_config {
    // the per-connector parameters
    uint32_t pre_lo;
    uint32_t pre_hi;
    uint32_t post_lo;
    uint32_t post_hi;
    uint32_t synapse_type;
    // The types of the various components
    uint32_t matrix_type;
    uint32_t connector_type;
    uint32_t weight_type;
    uint32_t delay_type;
} connection_builder_config_t;

//! The configuration of the synapse expander
__attribute__((aligned(4)))
typedef struct expander_config {
    uint32_t synaptic_matrix_region;
    uint32_t master_pop_region;
    uint32_t bitfield_filter_region;
    uint32_t structural_region;
    uint32_t n_in_edges;
    uint32_t post_slice_start;
    uint32_t post_slice_count;
    uint32_t post_index;
    uint32_t n_synapse_types;
    accum timestep_per_delay;
    rng_t population_rng;
    rng_t core_rng;
    unsigned long accum weight_scales[];
} expander_config_t;

rng_t *population_rng;
rng_t *core_rng;

/**
 * \brief Generate the synapses for a single connector
 * \param[in,out] in_region: The address to read the parameters from. Should be
 *                           updated to the position just after the parameters
 *                           after calling.
 * \param[in] synaptic_matrix_region: The address of the synaptic matrices
 * \param[in] post_slice_start: The start of the slice of the post-population to
 *                              generate for
 * \param[in] post_slice_count: The number of neurons to generate for
 * \param[in] n_synapse_type_bits: The number of bits in the synapse type
 * \param[in] n_synapse_index_bits: The number of bits for the neuron index id
 * \param[in] weight_scales: An array of weight scales, one for each synapse
 *                           type
 * \return true on success, false on failure
 */
static bool read_connection_builder_region(void **region,
        void *synaptic_matrix, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t post_index,
        unsigned long accum *weight_scales, accum timestep_per_delay) {
    connection_builder_config_t *sdram_config = *region;
    connection_builder_config_t config = *sdram_config;
    *region = &sdram_config[1];

    // Get the matrix, connector, weight and delay parameter generators
    matrix_generator_t matrix_generator =
            matrix_generator_init(config.matrix_type, region, synaptic_matrix);
    connection_generator_t connection_generator =
            connection_generator_init(config.connector_type, region);
    param_generator_t weight_generator =
            param_generator_init(config.weight_type, region);
    param_generator_t delay_generator =
            param_generator_init(config.delay_type, region);

    // If any components couldn't be created return false
    if (matrix_generator == NULL || connection_generator == NULL
            || delay_generator == NULL || weight_generator == NULL) {
        return false;
    }

    if (!connection_generator_generate(
            connection_generator, config.pre_lo, config.pre_hi, config.post_lo,
            config.post_hi, post_index, post_slice_start, post_slice_count,
            weight_scales[config.synapse_type], timestep_per_delay,
            weight_generator, delay_generator, matrix_generator)) {
        return false;
    }

    // Free the neuron four!
    matrix_generator_free(matrix_generator);
    connection_generator_free(connection_generator);
    param_generator_free(weight_generator);
    param_generator_free(delay_generator);

    // Return success!
    return true;
}

/**
 * \brief Read the data for the expander
 * \param[in] ds_regions: The data specification regions
 * \param[in] params_address: The address of the expander parameters
 * \return True if the expander finished correctly, False if there was an
 *         error
 */
static bool run_synapse_expander(data_specification_metadata_t *ds_regions,
        void *params_address) {
    // Read in the global parameters
    expander_config_t *sdram_config = params_address;
    uint32_t data_size = sizeof(expander_config_t)
            + (sizeof(long accum) * sdram_config->n_synapse_types);
    expander_config_t *config = spin1_malloc(data_size);
    fast_memcpy(config, sdram_config, data_size);
    log_info("Generating %u edges for %u atoms starting at %u",
            config->n_in_edges, config->post_slice_count, config->post_slice_start);

    // Get the synaptic matrix region
    void *synaptic_matrix = data_specification_get_region(
            config->synaptic_matrix_region, ds_regions);

    // We are changing this region, so void the checksum
    ds_regions->regions[config->synaptic_matrix_region].n_words = 0;
    ds_regions->regions[config->synaptic_matrix_region].checksum = 0;

    // Store the RNGs
    population_rng = &(config->population_rng);
    core_rng = &(config->core_rng);

    log_info("Population RNG: %u %u %u %u", population_rng->seed[0],
            population_rng->seed[1], population_rng->seed[2],
            population_rng->seed[3]);

    log_info("Core RNG: %u %u %u %u", core_rng->seed[0],
            core_rng->seed[1], core_rng->seed[2], core_rng->seed[3]);


    // Go through each connector and generate
    void *address = &(sdram_config->weight_scales[config->n_synapse_types]);
    for (uint32_t edge = 0; edge < config->n_in_edges; edge++) {
        if (!read_connection_builder_region(
                &address, synaptic_matrix, config->post_slice_start,
                config->post_slice_count, config->post_index,
                config->weight_scales, config->timestep_per_delay)) {
            return false;
        }
    }

    // Do bitfield generation on the whole matrix
    uint32_t *n_atom_data_sdram = address;
    void *master_pop = data_specification_get_region(
            config->master_pop_region, ds_regions);
    void *bitfield_filter = data_specification_get_region(
            config->bitfield_filter_region, ds_regions);
    void *structural_matrix = NULL;
    if (config->structural_region != INVALID_REGION_ID) {
        structural_matrix = data_specification_get_region(
            config->structural_region, ds_regions);
    }

    // We are changing this region, so void the checksum
    ds_regions->regions[config->bitfield_filter_region].n_words = 0;
    ds_regions->regions[config->bitfield_filter_region].checksum = 0;
    log_info("Region %u set to 0 at 0x%08x and 0x%08x",
    		config->bitfield_filter_region,
			&(ds_regions->regions[config->bitfield_filter_region].n_words),
			&(ds_regions->regions[config->bitfield_filter_region].checksum));
    return do_bitfield_generation(n_atom_data_sdram, master_pop,
            synaptic_matrix, bitfield_filter, structural_matrix);
}

//! Entry point
void c_main(void) {
    sark_cpu_state(CPU_STATE_RUN);

    log_info("Starting To Build Connectors");

    // Get pointer to 1st virtual processor info struct in SRAM and get USER1;
    // This is the ID of the connection builder region from which to read the
    // rest of the data
    vcpu_t *virtual_processor_table = (vcpu_t*) SV_VCPU;
    uint user1 = virtual_processor_table[spin1_get_core_id()].user1;

    // Get the addresses of the regions
    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();
    void *params_address = data_specification_get_region(user1, ds_regions);
    log_info("\tReading SDRAM at 0x%08x", params_address);

    // Run the expander
    if (!run_synapse_expander(ds_regions, params_address)) {
        log_info("!!!   Error reading SDRAM data   !!!");
        rt_error(RTE_ABORT);
    }

    log_info("Finished On Machine Connectors!");
}
