/**
 *! \file
 *! \brief The synapse expander for neuron cores
 */
#include <neuron/regions.h>
#include "matrix_generator.h"
#include "connection_generator.h"
#include "param_generator.h"

#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>

#define _unused(x) ((void)(x))

struct expander_config_t {
    // the global parameters
    uint32_t n_in_edges;
    uint32_t post_slice_start;
    uint32_t post_slice_count;
    uint32_t n_synapse_types;
    uint32_t n_synapse_type_bits;
    uint32_t n_synapse_index_bits;
    // the weight scales, followed by connection builder configs
    uint32_t config_data[];
};

struct connection_builder_region_t {
    // the per-connector parameters
    uint32_t synaptic_matrix_offset;
    uint32_t delayed_synaptic_matrix_offset;
    uint32_t max_row_n_words;
    uint32_t max_delayed_row_n_words;
    uint32_t max_row_n_synapses;
    uint32_t max_delayed_row_n_synapses;
    uint32_t pre_slice_start;
    uint32_t pre_slice_count;
    uint32_t max_stage;
    accum timestep_per_delay;
    uint32_t synapse_type;
    // the types of the various components and their configs
    uint32_t matrix_type_hash;
    uint32_t connector_type_hash;
    uint32_t weight_type_hash;
    uint32_t delay_type_hash;
    uint32_t component_config[];
};

/**
 *! \brief Generate the synapses for a single connector
 *! \param[in/out] in_region The address to read the parameters from.  Should be
 *!                          updated to the position just after the parameters
 *!                          after calling.
 *! \param[in] synaptic_matrix_region The address of the synaptic matrices
 *! \param[in] post_slice_start The start of the slice of the post-population to
 *!                             generate for
 *! \param[in] post_slice_count The number of neurons to generate for
 *! \param[in] n_synapse_type_bits The number of bits in the synapse type
 *! \param[in] n_synapse_index_bits The number of bits for the neuron index id
 *! \param[in] weight_scales An array of weight scales, one for each synapse
 *!                          type
 */
static bool run_connection_builder_region(void **in_region,
        address_t synaptic_matrix_region, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t n_synapse_type_bits,
        uint32_t n_synapse_index_bits, uint32_t *weight_scales) {
    struct connection_builder_region_t *config = *in_region;

    // Get the matrix, connector, weight and delay parameter generators
    address_t region = config->component_config;
    matrix_generator_t matrix_generator =
            matrix_generator_init(config->matrix_type_hash, &region);
    connection_generator_t connection_generator =
            connection_generator_init(config->connector_type_hash, &region);
    param_generator_t weight_generator =
            param_generator_init(config->weight_type_hash, &region);
    param_generator_t delay_generator =
            param_generator_init(config->delay_type_hash, &region);
    *in_region = region;

    // If any components couldn't be created return false
    if (matrix_generator == NULL || connection_generator == NULL
            || delay_generator == NULL || weight_generator == NULL) {
        return false;
    }

    log_debug("Synaptic matrix offset = %u, delayed offset = %u",
            config->synaptic_matrix_offset, config->delayed_synaptic_matrix_offset);
    log_debug("Max row synapses = %u, max delayed row synapses = %u",
            config->max_row_n_synapses, config->max_delayed_row_n_synapses);

    // Get the positions to which the data should be written in the matrix
    address_t synaptic_matrix = NULL;
    if (config->synaptic_matrix_offset != 0xFFFFFFFF) {
        synaptic_matrix = &synaptic_matrix_region[config->synaptic_matrix_offset];
    }
    address_t delayed_synaptic_matrix = NULL;
    if (config->delayed_synaptic_matrix_offset != 0xFFFFFFFF) {
        delayed_synaptic_matrix =
                &synaptic_matrix_region[config->delayed_synaptic_matrix_offset];
    }
    log_debug("Generating matrix at 0x%08x, delayed at 0x%08x",
            synaptic_matrix, delayed_synaptic_matrix);

    // Do the generation
    bool status = matrix_generator_generate(
            matrix_generator, synaptic_matrix, delayed_synaptic_matrix,
            config->max_row_n_words, config->max_delayed_row_n_words,
            config->max_row_n_synapses, config->max_delayed_row_n_synapses,
            n_synapse_type_bits, n_synapse_index_bits, config->synapse_type,
            weight_scales, post_slice_start, post_slice_count,
            config->pre_slice_start, config->pre_slice_count,
            connection_generator, delay_generator, weight_generator,
            config->max_stage, config->timestep_per_delay);

    // Free the neuron four!
    matrix_generator_free(matrix_generator);
    connection_generator_free(connection_generator);
    param_generator_free(weight_generator);
    param_generator_free(delay_generator);

    // If failed, log error
    if (!status) {
        log_error("\tMatrix generation failed");
        return false;
    }

    // Return success!
    return true;
}

/**
 *! \brief Read the data for the expander and execute what was found
 *! \param[in] params_address The address of the expander parameters
 *! \param[in] synaptic_matrix_region The address of the synaptic matrices
 *! \return True if the expander finished correctly, False if there was an
 *!         error
 */
static bool run_expander(
        void *params_address, address_t synaptic_matrix_region) {
    struct expander_config_t *config = params_address;
    log_info("Generating %u edges for %u atoms starting at %u",
            config->n_in_edges, config->post_slice_count,
            config->post_slice_start);

    // Read in the weight scales, one per synapse type
    uint32_t weight_scales[config->n_synapse_types];
    for (uint32_t i = 0; i < config->n_synapse_types; i++) {
        weight_scales[i] = config->config_data[i];
    }

    // Go through each connector and generate
    void *params = &config->config_data[config->n_synapse_types];
    for (uint32_t edge = 0; edge < config->n_in_edges; edge++) {
        if (!run_connection_builder_region(
                &params, synaptic_matrix_region,
                config->post_slice_start, config->post_slice_count,
                config->n_synapse_type_bits, config->n_synapse_index_bits,
                weight_scales)) {
            return false;
        }
    }

    return true;
}

void c_main(void) {
    sark_cpu_state(CPU_STATE_RUN);

    // Get the addresses of the regions
    log_info("Starting To Build Connectors");
    address_t core_address = data_specification_get_data_address();
    address_t params_address = data_specification_get_region(
            CONNECTOR_BUILDER_REGION, core_address);
    address_t syn_mtx_addr = data_specification_get_region(
            SYNAPTIC_MATRIX_REGION, core_address);
    log_info("\tReading SDRAM at 0x%08x, writing to matrix at 0x%08x",
            params_address, syn_mtx_addr);

    // Run the expander
    if (!run_expander(params_address, syn_mtx_addr)) {
        log_info("!!!   Error reading SDRAM data   !!!");
        rt_error(RTE_ABORT);
    }

    log_info("Finished On Machine Connectors!");
}
