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
 *! \file
 *! \brief The implementation of a parameter generator
 */
#include "param_generator.h"
#include <spin1_api.h>
#include <debug.h>
#include "generator_types.h"

#include "param_generators/param_generator_constant.h"
#include "param_generators/param_generator_uniform.h"
#include "param_generators/param_generator_normal.h"
#include "param_generators/param_generator_normal_clipped.h"
#include "param_generators/param_generator_normal_clipped_to_boundary.h"
#include "param_generators/param_generator_exponential.h"
#include "param_generators/param_generator_kernel.h"

enum {
    CONSTANT,
    UNIFORM,
    NORMAL,
    NORMAL_CLIPPED,
    NORMAL_CLIPPED_BOUNDARY,
    EXPONENTIAL,
    KERNEL,
    /**
     *! \brief The number of known generators
     */
    N_PARAM_GENERATORS = 7
};

/**
 *! \brief A "class" for parameter generators
 */
typedef struct param_generator_info {
    /**
     *! \brief The hash of the generator.
     *! For now, hash is just an index agreed between Python and here.
     */
    generator_hash_t hash;
    /**
     *! \brief Initialise the generator
     *! \param[in/out] region Region to read parameters from.  Should be updated
     *!                       to position just after parameters after calling.
     *! \return A data item to be passed in to other functions later on
     */
    initialize_func *initialize;
    /**
     *! \brief Generate values with a parameter generator
     *! \param[in] data The data for the parameter generator, returned by the
     *!                 initialise function
     *! \param[in] n_indices The number of values to generate
     *! \param[in] pre_neuron_index The index of the neuron in the pre-population
     *!                             being generated
     *! \param[in] indices The n_indices post-neuron indices for each connection
     *! \param[in/out] values An array into which to place the values; will be
     *!                       n_indices in size
     */
    generate_param_func *generate;
    /**
     *! \brief Free any data for the generator
     *! \param[in] data The data to free
     */
    free_func *free;
} param_generator_info;

/**
 *! \brief The data for a parameter generator
 */
struct param_generator {
    const param_generator_info *type;
    void *data;
};

/**
 *! \brief An Array of known generators
 */
static const struct param_generator_info param_generators[] = {
    {CONSTANT,
            param_generator_constant_initialize,
            param_generator_constant_generate,
            param_generator_constant_free},
    {UNIFORM,
            param_generator_uniform_initialize,
            param_generator_uniform_generate,
            param_generator_uniform_free},
    {NORMAL,
            param_generator_normal_initialize,
            param_generator_normal_generate,
            param_generator_normal_free},
    {NORMAL_CLIPPED,
            param_generator_normal_clipped_initialize,
            param_generator_normal_clipped_generate,
            param_generator_normal_clipped_free},
    {NORMAL_CLIPPED_BOUNDARY,
            param_generator_normal_clipped_boundary_initialize,
            param_generator_normal_clipped_boundary_generate,
            param_generator_normal_clipped_boundary_free},
    {EXPONENTIAL,
            param_generator_exponential_initialize,
            param_generator_exponential_generate,
            param_generator_exponential_free},
    {KERNEL,
            param_generator_kernel_initialize,
            param_generator_kernel_generate,
            param_generator_kernel_free},
};

param_generator_t param_generator_init(uint32_t hash, address_t *in_region) {
    // Look through the known generators
    for (uint32_t i = 0; i < N_PARAM_GENERATORS; i++) {
        const param_generator_info *type = &param_generators[i];

        // If the hash requested matches the hash of the generator, use it
        if (hash == type->hash) {
            // Prepare a space for the data
            struct param_generator *generator =
                    spin1_malloc(sizeof(struct param_generator));
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
    log_error("Param generator with hash %u not found", hash);
    return NULL;
}

void param_generator_generate(
        param_generator_t generator, uint32_t n_indices,
        uint32_t pre_neuron_index, uint16_t *indices, accum *values) {
    generator->type->generate(
            generator->data, n_indices, pre_neuron_index, indices, values);
}

void param_generator_free(param_generator_t generator) {
    generator->type->free(generator->data);
    sark_free(generator);
}
