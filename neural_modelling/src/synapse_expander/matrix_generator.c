/*
 * Copyright (c) 2017 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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
#include "matrix_generators/matrix_generator_neuromodulation.h"
#include "matrix_generators/matrix_generator_weight_changer.h"
#include <delay_extension/delay_extension.h>

//! The "hashes" for synaptic matrix generators
enum {
    //! Generate a pure static synaptic matrix
    STATIC_MATRIX_GENERATOR,
    //! Generate a synaptic matrix with STDP
    PLASTIC_MATRIX_GENERATOR,
    //! Generate a synaptic matrix for Neuromodulation
    NEUROMODULATION_MATRIX_GENERATOR,
	//! Generate a synaptic matrix for weight change
	WEIGHT_CHANGER_MATRIX_GENERATOR,
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
    initialize_matrix_func *initialize;

    //! Generate a row of a matrix with a matrix generator
    write_synapse_func *write_synapse;

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
            matrix_generator_static_write_synapse,
            matrix_generator_static_free},
    {PLASTIC_MATRIX_GENERATOR,
            matrix_generator_stdp_initialize,
            matrix_generator_stdp_write_synapse,
            matrix_generator_stdp_free},
    {NEUROMODULATION_MATRIX_GENERATOR,
            matrix_generator_neuromodulation_initialize,
            matrix_generator_neuromodulation_write_synapse,
            matrix_generator_neuromodulation_free},
    {WEIGHT_CHANGER_MATRIX_GENERATOR,
		matrix_generator_changer_initialize,
		matrix_generator_changer_write_synapse,
		matrix_generator_changer_free}
};

matrix_generator_t matrix_generator_init(uint32_t hash, void **in_region,
        void *synaptic_matrix) {
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
            generator->data = type->initialize(in_region, synaptic_matrix);
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


bool matrix_generator_write_synapse(
        matrix_generator_t generator,
        uint32_t pre_index, uint16_t post_index, accum weight, uint16_t delay,
		unsigned long accum weight_scale) {
    return generator->type->write_synapse(
            generator->data, pre_index, post_index, weight, delay, weight_scale);
}
