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
#include "matrix_generators/matrix_generator_neuromodulation.h"
#include <delay_extension/delay_extension.h>

//! The "hashes" for synaptic matrix generators
enum {
    //! Generate a pure static synaptic matrix
    STATIC_MATRIX_GENERATOR,
    //! Generate a synaptic matrix with STDP
    PLASTIC_MATRIX_GENERATOR,
    //! Generate a synaptic matrix for Neuromodulation
    NEUROMODULATION_MATRIX_GENERATOR,
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
            matrix_generator_neuromodulation_free}
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


void matrix_generator_write_synapse(
        matrix_generator_t generator,
        uint32_t pre_index, uint16_t post_index, uint16_t weight, uint16_t delay) {
    generator->type->write_synapse(
            generator->data, pre_index, post_index, weight, delay);
}
