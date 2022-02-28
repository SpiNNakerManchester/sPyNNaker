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
#include "param_generator.h"
#include "rng.h"
#include "type_writers.h"

#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>
#include "common_mem.h"

#define REPEAT_PER_NEURON 0xFFFFFFFF

// Mask to work out MOD 4
#define MOD_4 0x3

// An array of how much to add to align data to 4-bytes
// indexed by [current offset % 4][size to write % 4].
// Note sizes are expected to be 1, 2, 4 or 8 (indices 1, 2, 0, 0)
// so other values are 0 (but indexing an array is quicker).
static const uint32_t ADD[4][3] = {
    {0, 0, 0},  // Offset 0 - anything goes
    {3, 0, 1},  // Offset 1 - needs shift for 2, 4 and 8 (indices 2, 0, 0)
    {2, 0, 0},  // Offset 2 - needs shift for 4 and 8 (indices 0, 0)
    {1, 0, 1}   // Offset 3 - needs shift for 2, 4 and 8 (indices 2, 0, 0)
};

static inline uint32_t align_offset(uint32_t offset, uint32_t size) {
    if (size == 0) {
        log_error("Size of 0!");
        rt_error(RTE_SWERR);
    }
    uint32_t size_mod = size & MOD_4;
    if (size_mod == 3) {
        log_error("Size %u unsupported!", size);
    }
    return ADD[offset & MOD_4][size & MOD_4];
}

typedef struct neuron_param_item {
    // The number of repeat calls to make of the generator
    uint32_t n_repeats;
    // The generator to use
    uint32_t generator;
} neuron_param_item_t;

typedef struct neuron_param {
    // The type of the parameter
    type param_type;
    // The number of "items" which are groups of values to be repeated
    uint32_t n_items;
    // The "items" to generate
    neuron_param_item_t item[];
} neuron_param_t;

//! The configuration of a struct
typedef struct neuron_params_struct {
    // How many bytes are needed for an aligned copy of the struct
    uint32_t bytes_per_repeat;
    // How many repeats will be made in total
    uint32_t n_repeats_total;
    // How many words in this struct including variable size data
    uint32_t struct_size_bytes;
    // How many parameters in the struct
    uint32_t n_params;
    // Each of the groups of parameters to generate
    neuron_param_t param[];
    // Following on from this are the data of each param_generator in order
    // of appearance in the above
} neuron_params_struct_t;

//! The configuration of the expander
__attribute__((aligned(4)))
typedef struct expander_config {
    uint32_t neuron_params_region;
    uint32_t neuron_recording_region;
    rng_t population_rng;
    rng_t core_rng;
    uint32_t n_structs;
    uint32_t n_neurons;
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
static bool read_struct_builder_region(void **region,
        void **neuron_params_region, uint32_t n_neurons) {

    // Get the config for the repeated struct and move on to the data after
    neuron_params_struct_t *config = *region;
    uint8_t *reg = *region;
    *region = &(reg[config->struct_size_bytes]);

    // Read items from SDRAM into variables for use later
    uint32_t n_params = config->n_params;
    uint32_t bytes_per_repeat = config->bytes_per_repeat;
    uint32_t n_repeats_total = config->n_repeats_total;
    if (n_repeats_total == REPEAT_PER_NEURON) {
        n_repeats_total = n_neurons;
    }
    log_debug("Reading %u params, %u bytes per neuron, %u neurons, "
            "%u bytes to end of struct", n_params, bytes_per_repeat,
            n_repeats_total, config->struct_size_bytes);

    // Get the current struct position
    uint8_t* struct_ptr = *neuron_params_region;
    *neuron_params_region = &(struct_ptr[bytes_per_repeat * n_repeats_total]);

    // Keep track of the offset of the param from the start of each struct
    uint32_t param_offset = 0;

    // Go through the params in the struct to be expanded
    neuron_param_t *param = &(config->param[0]);
    for (uint32_t p = 0; p < n_params; p++) {
        log_debug("    Param %u, type=%u, n_items=%u", p, param->param_type,
                param->n_items);

        // Get the writer for the parameter type
        type_info *writer = get_type_writer(param->param_type);

        // Align the offset for the size of parameter to be written
        param_offset += align_offset(param_offset, writer->size);
        log_debug("        Writing %u bytes each time to struct offset %u",
                writer->size, param_offset);

        // Go through the items and generate
        uint32_t n_items = param->n_items;
        uint32_t offset = 0;
        for (uint32_t i = 0; i < n_items; i++) {
            neuron_param_item_t item = param->item[i];
            log_debug("            Item %u, generator=%u, n_repeats=%u",
                    i, item.generator, item.n_repeats);

            param_generator_t gen = param_generator_init(item.generator, region);
            if (gen == NULL) {
                return false;
            }

            uint32_t n_repeats = item.n_repeats;
            if (n_repeats == REPEAT_PER_NEURON) {
                n_repeats = n_neurons;
                log_debug("            (Really only repeating %u times!)", n_repeats);
            }

            // Generate the requested number of times
            for (uint32_t r = 0; r < n_repeats; r++) {
                accum value = param_generator_generate(gen);
                uint32_t index = offset + param_offset;
                log_debug("                Writing %k to offset %u", value, index);
                writer->writer(&(struct_ptr[index]), value);
                offset += bytes_per_repeat;
            }

            // Finish with the generator
            param_generator_free(gen);
        }

        // After writing, add to the offset for the next parameter
        param_offset += writer->size;

        // Go to the next param
        param = (neuron_param_t *) &(param->item[n_items]);
    }

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
static bool run_neuron_expander(data_specification_metadata_t *ds_regions,
        void *params_address) {
    // Read in the global parameters
    expander_config_t *sdram_config = params_address;
    expander_config_t *config = spin1_malloc(sizeof(expander_config_t));
    fast_memcpy(config, sdram_config, sizeof(expander_config_t));
    log_info("Generating %u structs", config->n_structs);

    // Get the synaptic matrix region
    void *neuron_params_region = data_specification_get_region(
            config->neuron_params_region, ds_regions);

    // Store the RNGs
    population_rng = &(config->population_rng);
    core_rng = &(config->core_rng);

    log_info("Population RNG: %u %u %u %u", population_rng->seed[0],
            population_rng->seed[1], population_rng->seed[2],
            population_rng->seed[3]);

    log_info("Core RNG: %u %u %u %u", core_rng->seed[0],
            core_rng->seed[1], core_rng->seed[2], core_rng->seed[3]);


    // Go through each struct and generate
    void *address = &(sdram_config[1]);

    // Read the remaining structs
    for (uint32_t s = 0; s < config->n_structs; s++) {
        if (!read_struct_builder_region(&address, &neuron_params_region,
                config->n_neurons)) {
            return false;
        }
    }
    return true;
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
    if (!run_neuron_expander(ds_regions, params_address)) {
        log_info("!!!   Error reading SDRAM data   !!!");
        rt_error(RTE_ABORT);
    }

    log_info("Finished On Machine Connectors!");
}
