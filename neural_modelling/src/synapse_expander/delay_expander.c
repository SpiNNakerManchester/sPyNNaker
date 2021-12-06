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
 * \file
 * \brief Generate data for delay extensions
 */
#include "connection_generator.h"
#include "param_generator.h"
#include "matrix_generators/matrix_generator_common.h"
#include "common_mem.h"

#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>
#include <delay_extension/delay_extension.h>
#include <bit_field.h>

//! The configuration of the delay builder
struct delay_builder_config {
    // the parameters
    uint32_t max_row_n_synapses;
    uint32_t max_delayed_row_n_synapses;
    uint32_t post_slice_start;
    uint32_t post_slice_count;
    uint32_t max_stage;
    uint32_t max_delay_per_stage;
    accum timestep_per_delay;
    // the connector and delay parameter generators
    uint32_t connector_type;
    uint32_t delay_type;
};

/**
 * \brief Generate the data for a single connector
 * \param[in,out] in_region:
 *      The address to read the parameters from.  Should be updated to the
 *      position just after the parameters after calling.
 * \param[in,out] neuron_delay_stage_config:
 *      Bit fields into which to write the delay information
 * \param[in] pre_slice_start:
 *      The start of the slice of the delay extension to generate for
 * \param[in] pre_slice_count:
 *      The number of neurons of the delay extension to generate for
 * \return True if the region was correctly generated, False if there was an
 *         error
 */
static bool read_delay_builder_region(address_t *in_region,
        bit_field_t *neuron_delay_stage_config, uint32_t pre_slice_start,
        uint32_t pre_slice_count) {
    // Get the parameters
    address_t region = *in_region;
    struct delay_builder_config config;
    fast_memcpy(&config, region, sizeof(config));
    region += sizeof(config) / sizeof(uint32_t);
    // Get the connector and delay parameter generators
    connection_generator_t connection_generator =
            connection_generator_init(config.connector_type, &region);
    param_generator_t delay_generator =
            param_generator_init(config.delay_type, &region);
    *in_region = region;

    // If any components couldn't be created return false
    if (connection_generator == NULL || delay_generator == NULL) {
        return false;
    }

    // For each pre-neuron, generate the connections
    uint32_t pre_slice_end = pre_slice_start + pre_slice_count;
    for (uint32_t pre_neuron_index = pre_slice_start;
            pre_neuron_index < pre_slice_end; pre_neuron_index++) {
        // Generate the connections
        uint32_t max_n_synapses =
                config.max_row_n_synapses + config.max_delayed_row_n_synapses;
        uint16_t indices[max_n_synapses];
        uint32_t n_indices = connection_generator_generate(
                connection_generator, pre_slice_start, pre_slice_count,
                pre_neuron_index, config.post_slice_start, config.post_slice_count,
                max_n_synapses, indices);
        log_debug("Generated %u synapses", n_indices);

        // Generate delays for each index
        accum delay_params[n_indices];
        param_generator_generate(
                delay_generator, n_indices, pre_neuron_index, indices,
                delay_params);

        // Go through the delays
        for (uint32_t i = 0; i < n_indices; i++) {
            // Get the delay in timesteps
            accum delay = delay_params[i] * config.timestep_per_delay;
            if (delay < 0) {
                delay = 1;
            }

            // Round down to an integer number of timesteps
            uint16_t rounded_delay = (uint16_t) delay;
            if (delay != rounded_delay) {
                log_debug("Rounded delay %k to %u", delay, rounded_delay);
            }

            // Get the delay stage and update the data
            struct delay_value delay_value = get_delay(
                rounded_delay, config.max_stage, config.max_delay_per_stage);
            if (delay_value.stage > 0) {
                bit_field_set(neuron_delay_stage_config[delay_value.stage - 1],
                        pre_neuron_index - pre_slice_start);
            }
        }
    }

    // Finish with the generators
    connection_generator_free(connection_generator);
    param_generator_free(delay_generator);

    return true;
}

/**
 * \brief Read the data for the generator
 * \param[in] delay_params_address: The address of the delay extension
 *                                  parameters
 * \param[in] params_address: The address of the expander parameters
 * \return True if the expander finished correctly, False if there was an
 *         error
 */
static bool run_delay_expander(
        void *delay_params_address, address_t params_address) {
    // Read the global parameters from the delay extension
    struct delay_parameters *delay_params = delay_params_address;
    uint32_t num_neurons = delay_params->n_atoms;
    uint32_t neuron_bit_field_words = get_bit_field_size(num_neurons);
    uint32_t n_stages = delay_params->n_delay_stages;

    // Set up the bit fields
    bit_field_t *neuron_delay_stage_config =
            spin1_malloc(n_stages * sizeof(bit_field_t));
    for (uint32_t d = 0; d < n_stages; d++) {
        neuron_delay_stage_config[d] =
                &delay_params->delay_blocks[d * neuron_bit_field_words];
        clear_bit_field(neuron_delay_stage_config[d], neuron_bit_field_words);
    }

    // Read the global parameters from the expander region
    uint32_t n_out_edges = *params_address++;
    uint32_t pre_slice_start = *params_address++;
    uint32_t pre_slice_count = *params_address++;

    log_info("Generating %u delay edges for %u atoms starting at %u",
            n_out_edges, pre_slice_count, pre_slice_start);

    // Go through each connector and make the delay data
    for (uint32_t edge = 0; edge < n_out_edges; edge++) {
        if (!read_delay_builder_region(
                &params_address, neuron_delay_stage_config,
                pre_slice_start, pre_slice_count)) {
            return false;
        }
    }

    return true;
}

//! Entry point
void c_main(void) {
    sark_cpu_state(CPU_STATE_RUN);

    // Get the addresses of the regions
    log_info("Starting To Build Delays");
    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();
    address_t delay_params_address = data_specification_get_region(
            DELAY_PARAMS, ds_regions);
    address_t params_address = data_specification_get_region(
            EXPANDER_REGION, ds_regions);
    log_info("\tReading SDRAM delay params at 0x%08x,"
            " expander params at 0x%08x",
            delay_params_address, params_address);

    // Run the expander
    if (!run_delay_expander(
            (address_t) delay_params_address, (address_t) params_address)) {
        log_info("!!!   Error reading SDRAM data   !!!");
        rt_error(RTE_ABORT);
    }

    log_info("Finished On-Machine Delays!");
}
