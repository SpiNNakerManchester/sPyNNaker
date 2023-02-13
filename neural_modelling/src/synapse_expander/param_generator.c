/*
 * Copyright (c) 2017-2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * \file
 * \brief The implementation of a parameter generator
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

//! The "hashes" for parameter generators
enum {
    //! A parameter that is a constant
    CONSTANT,
    //! A parameter that is a uniformly-distributed random variable
    UNIFORM,
    //! A parameter that is a normally-distributed random variable
    NORMAL,
    //! A parameter that is a clipped-normally-distributed random variable
    NORMAL_CLIPPED,
    //! A parameter that is a clamped-normally-distributed random variable
    NORMAL_CLIPPED_BOUNDARY,
    //! A parameter that is an exponentially-distributed random variable
    EXPONENTIAL,
    //! The number of known generators
    N_PARAM_GENERATORS
};

/**
 *! \brief A "class" for parameter generators
 */
typedef struct param_generator_info {
    /**
     * \brief The hash of the generator.
     *
     * For now, hash is just an index agreed between Python and here.
     */
    generator_hash_t hash;
    //! Initialise the generator
    initialize_param_func *initialize;
    //! Generate values with a parameter generator
    generate_param_func *generate;
    //! Free any data for the generator
    free_func *free;
} param_generator_info;

/**
 * \brief The data for a parameter generator
 */
struct param_generator {
    const param_generator_info *type;
    void *data;
};

/**
 * \brief An Array of known generators
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
            param_generator_exponential_free}
};

param_generator_t param_generator_init(uint32_t hash, void **in_region) {
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

accum param_generator_generate(param_generator_t generator) {
    return generator->type->generate(generator->data);
}

void param_generator_free(param_generator_t generator) {
    generator->type->free(generator->data);
    sark_free(generator);
}
