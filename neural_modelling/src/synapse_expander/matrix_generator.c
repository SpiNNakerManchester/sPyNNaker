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
 * \brief The implementation of the matrix generator
 */
#include "matrix_generator.h"
#include <spin1_api.h>
#include <debug.h>
#include "generator_types.h"

#include "matrix_generators/matrix_generator_static.h"
#include "matrix_generators/matrix_generator_stdp.h"
#include <delay_extension/delay_extension.h>

//! The "hashes" for synaptic matrix generators
enum {
    //! Generate a pure static synaptic matrix
    STATIC_MATRIX_GENERATOR,
    //! Generate a synaptic matrix with STDP
    PLASTIC_MATRIX_GENERATOR,
    /**
     * \brief The number of known generators
     */
    N_MATRIX_GENERATORS
};

/**
 * \brief A "class" for matrix generators
 */
typedef struct matrix_generator_info {
    /**
     * \brief The hash of the generator
     *
     * For now, hash is just an index agreed between Python and here.
     */
    generator_hash_t hash;

    //! Initialise the generator
    initialize_func *initialize;

    //! Generate a row of a matrix with a matrix generator
    generate_row_func *write_row;

    //! Free any data for the generator
    free_func *free;
} matrix_generator_info;

/**
 * \brief The data for a matrix generator
 */
struct matrix_generator {
    const matrix_generator_info *type;
    void *data;
};

/**
 * \brief An Array of known generators
 */
static const struct matrix_generator_info matrix_generators[] = {
    {STATIC_MATRIX_GENERATOR,
            matrix_generator_static_initialize,
            matrix_generator_static_write_row,
            matrix_generator_static_free},
    {PLASTIC_MATRIX_GENERATOR,
            matrix_generator_stdp_initialize,
            matrix_generator_stdp_write_row,
            matrix_generator_stdp_free}
};

matrix_generator_t matrix_generator_init(uint32_t hash, address_t *in_region) {
    // Look through the known generators
    for (uint32_t i = 0; i < N_MATRIX_GENERATORS; i++) {
        const matrix_generator_info *type = &matrix_generators[i];

        // If the hash requested matches the hash of the generator, use it
        if (hash == type->hash) {
            // Prepare a space for the data
            struct matrix_generator *generator =
                    spin1_malloc(sizeof(struct matrix_generator));
            if (generator == NULL) {
                log_error("Could not create generator");
                return NULL;
            }

            // Store the index
            generator->type = type;

            // Initialise the generator and store the data
            generator->data = type->initialize(in_region);
            return generator;
        }
    }
    log_error("Matrix generator with hash %u not found", hash);
    return NULL;
}

void matrix_generator_free(matrix_generator_t generator) {
    generator->type->free(generator->data);
    sark_free(generator);
}

/**
 * \brief Generate a row of a synaptic matrix
 * \param[in] generator: The matrix generator
 * \param[out] synaptic_matrix: The address of the synaptic matrix to write to
 * \param[out] delayed_synaptic_matrix: The address of the synaptic matrix to
 *                                      write delayed connections to
 * \param[in] n_pre_neurons: The number of pre neurons to generate for
 * \param[in] pre_neuron_index: The index of the first pre neuron
 * \param[in] max_row_n_words: The maximum number of words in a normal row
 * \param[in] max_delayed_row_n_words: The maximum number of words in a
 *                                     delayed row
 * \param[in] n_synapse_type_bits: The number of bits used for the synapse type
 * \param[in] n_synapse_index_bits: The number of bits used for the neuron id
 * \param[in] synapse_type: The synapse type of each connection
 * \param[in] n_synapses: The number of synapses
 * \param[in] indices: Pointer to table of indices
 * \param[in] delays: Pointer to table of delays
 * \param[in] weights: Pointer to table of weights
 * \param[in] max_stage: The maximum delay stage to support
 * \param[in] max_delay_per_stage: max delay ina  given delay stage
 */
static void matrix_generator_write_row(
        matrix_generator_t generator,
        address_t synaptic_matrix, address_t delayed_synaptic_matrix,
        uint32_t n_pre_neurons, uint32_t pre_neuron_index,
        uint32_t max_row_n_words, uint32_t max_delayed_row_n_words,
        uint32_t n_synapse_type_bits, uint32_t n_synapse_index_bits,
        uint32_t synapse_type, uint32_t n_synapses,
        uint16_t *indices, uint16_t *delays, uint16_t *weights,
        uint32_t max_stage, uint32_t max_delay_per_stage) {
    generator->type->write_row(
            generator->data, synaptic_matrix, delayed_synaptic_matrix,
            n_pre_neurons, pre_neuron_index, max_row_n_words,
            max_delayed_row_n_words, n_synapse_type_bits, n_synapse_index_bits,
            synapse_type, n_synapses, indices, delays, weights, max_stage,
            max_delay_per_stage);
}

// ---------------------------------------------------------------------

//! \brief Rescales a delay to account for timesteps and type-converts it
//! \param[in] delay: the delay to rescale
//! \param[in] timestep_per_delay: The timestep unit
//! \return the rescaled delay
static inline uint16_t rescale_delay(accum delay, accum timestep_per_delay) {
    delay = delay * timestep_per_delay;
    if (delay < 0) {
        delay = 1;
    }
    uint16_t delay_int = (uint16_t) delay;
    if (delay != delay_int) {
        log_debug("Rounded delay %k to %u", delay, delay_int);
    }
    return delay_int;
}

//! \brief Rescales a weight to account for weight granularity and
//!     type-converts it
//! \param[in] weight: the weight to rescale
//! \param[in] weight_scale: The weight scaling factor
//! \return the rescaled weight
static inline uint16_t rescale_weight(accum weight, unsigned long accum weight_scale) {
    if (weight < 0) {
        weight = -weight;
    }
    accum weight_scaled = weight * weight_scale;
    uint16_t weight_int = (uint16_t) weight_scaled;
    if (weight_scaled != weight_int) {
        log_debug("Rounded weight %k to %u (scale is %k)",
                weight_scaled, weight_int, weight_scale);
    }
    return weight_int;
}

bool matrix_generator_generate(
        matrix_generator_t generator,
        address_t synaptic_matrix, address_t delayed_synaptic_matrix,
        uint32_t max_row_n_words, uint32_t max_delayed_row_n_words,
        uint32_t max_row_n_synapses, uint32_t max_delayed_row_n_synapses,
        uint32_t n_synapse_type_bits, uint32_t n_synapse_index_bits,
        uint32_t synapse_type, unsigned long accum *weight_scales,
        uint32_t post_slice_start, uint32_t post_slice_count,
        uint32_t pre_slice_start, uint32_t pre_slice_count,
        connection_generator_t connection_generator,
        param_generator_t delay_generator, param_generator_t weight_generator,
        uint32_t max_stage, uint32_t max_delay_in_a_stage,
        accum timestep_per_delay) {
    // Go through and generate connections for each pre-neuron
    uint32_t n_connections = 0;
    for (uint32_t i = 0; i < pre_slice_count; i++) {
        uint32_t pre_neuron_index = pre_slice_start + i;

        // Get up to a maximum number of synapses
        uint32_t max_n_synapses =
                max_row_n_synapses + max_delayed_row_n_synapses;
        uint16_t indices[max_n_synapses];
        uint32_t n_indices = connection_generator_generate(
                connection_generator, pre_slice_start, pre_slice_count,
                pre_neuron_index, post_slice_start, post_slice_count,
                max_n_synapses, indices);
        log_debug("Generated %u synapses", n_indices);

        for (uint32_t j = 0; j < n_indices; j++) {
            if (indices[j] >= post_slice_count) {
                log_error("Index %u out of bounds for %u neurons", indices[j], post_slice_count);
                rt_error(RTE_SWERR);
            }
        }

        accum delay_params[n_indices], weight_params[n_indices];
        uint16_t delays[n_indices], weights[n_indices];

        // Generate delays for each index
        param_generator_generate(
                delay_generator, n_indices, pre_neuron_index, indices, delay_params);
        for (uint32_t j = 0; j < n_indices; j++) {
            delays[j] = rescale_delay(delay_params[j], timestep_per_delay);
        }

        // Generate weights for each index
        param_generator_generate(
                weight_generator, n_indices, pre_neuron_index, indices, weight_params);
        for (uint32_t j = 0; j < n_indices; j++) {
            weights[j] = rescale_weight(weight_params[j], weight_scales[synapse_type]);
        }

        // Write row
        matrix_generator_write_row(
                generator, synaptic_matrix, delayed_synaptic_matrix,
                pre_slice_count, pre_neuron_index - pre_slice_start,
                max_row_n_words, max_delayed_row_n_words,
                n_synapse_type_bits, n_synapse_index_bits,
                synapse_type, n_indices, indices, delays, weights, max_stage,
                max_delay_in_a_stage);

        n_connections += n_indices;
    }
    log_debug("\t\tTotal synapses generated = %u. Done!", n_connections);

    return true;
}
