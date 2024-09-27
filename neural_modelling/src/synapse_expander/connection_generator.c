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
 * \brief The implementation of the functions in connection_generator.h
 */

#include "connection_generator.h"
#include <spin1_api.h>
#include <debug.h>
#include "generator_types.h"

#include "connection_generators/connection_generator_one_to_one.h"
#include "connection_generators/connection_generator_all_to_all.h"
#include "connection_generators/connection_generator_fixed_prob.h"
#include "connection_generators/connection_generator_fixed_total.h"
#include "connection_generators/connection_generator_fixed_pre.h"
#include "connection_generators/connection_generator_fixed_post.h"
#include "connection_generators/connection_generator_kernel.h"
#include "connection_generators/connection_generator_all_but_me.h"
#include "connection_generators/connection_generator_shift.h"

//! \brief Known "hashes" of connection generators
//!
//! For now, hash is just an index agreed between Python and here
enum {
    ONE_TO_ONE,            //!< One-to-one connection generator
    ALL_TO_ALL,            //!< All-to-all connection generator
    FIXED_PROBABILITY,     //!< Fixed probability connection generator
    FIXED_TOTAL,           //!< Fixed total connections connection generator
    FIXED_PRE,             //!< Fixed pre-size connection generator
    FIXED_POST,            //!< Fixed post-size connection generator
    KERNEL,                //!< Convolution kernel connection generator
	ALL_BUT_ME,            //!< AllButMe connection generator
	SHIFT,                 //!< Shift connection generator
    N_CONNECTION_GENERATORS//!< The number of known generators
};

//! \brief A "class" for connection generators
typedef struct connection_generator_info {
    //! The hash of the generator.
    generator_hash_t hash;

    //! \brief Initialises the generator
    initialize_connector_func *initialize;

    //! \brief Generate connections
    generate_connection_func *generate;

    //! \brief Frees any data for the generator
    free_func *free;
} connection_generator_info;

//! \brief The data for a connection generator
struct connection_generator {
    const connection_generator_info *type;
    void *data;
};

//! \brief An Array of known generators
static const connection_generator_info connection_generators[] = {
    {ONE_TO_ONE,
            connection_generator_one_to_one_initialise,
            connection_generator_one_to_one_generate,
            connection_generator_one_to_one_free},
    {ALL_TO_ALL,
            connection_generator_all_to_all_initialise,
            connection_generator_all_to_all_generate,
            connection_generator_all_to_all_free},
    {FIXED_PROBABILITY,
            connection_generator_fixed_prob_initialise,
            connection_generator_fixed_prob_generate,
            connection_generator_fixed_prob_free},
    {FIXED_TOTAL,
            connection_generator_fixed_total_initialise,
            connection_generator_fixed_total_generate,
            connection_generator_fixed_total_free},
    {FIXED_PRE,
            connection_generator_fixed_pre_initialise,
            connection_generator_fixed_pre_generate,
            connection_generator_fixed_pre_free},
    {FIXED_POST,
            connection_generator_fixed_post_initialise,
            connection_generator_fixed_post_generate,
            connection_generator_fixed_post_free},
    {KERNEL,
            connection_generator_kernel_initialise,
            connection_generator_kernel_generate,
            connection_generator_kernel_free},
    {ALL_BUT_ME,
			connection_generator_all_but_me_initialise,
			connection_generator_all_but_me_generate,
			connection_generator_all_but_me_free},
	{SHIFT,
			connection_generator_shift_initialise,
			connection_generator_shift_generate,
			connection_generator_shift_free}
};

connection_generator_t connection_generator_init(
        uint32_t hash, void **in_region) {
    // Look through the known generators
    for (uint32_t i = 0; i < N_CONNECTION_GENERATORS; i++) {
        const connection_generator_info *type = &connection_generators[i];

        // If the hash requested matches the hash of the generator, use it
        if (hash == type->hash) {
            // Prepare a space for the data
            struct connection_generator *generator =
                    spin1_malloc(sizeof(struct connection_generator));
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
    log_error("Connection generator with hash %u not found", hash);
    return NULL;
}

bool connection_generator_generate(
        connection_generator_t generator, uint32_t pre_lo, uint32_t pre_hi,
        uint32_t post_lo, uint32_t post_hi, uint32_t post_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        unsigned long accum weight_scale, accum timestep_per_delay,
        param_generator_t weight_generator, param_generator_t delay_generator,
        matrix_generator_t matrix_generator) {
    return generator->type->generate(
            generator->data, pre_lo, pre_hi, post_lo, post_hi, post_index,
            post_slice_start, post_slice_count, weight_scale, timestep_per_delay,
            weight_generator, delay_generator, matrix_generator);
}

void connection_generator_free(connection_generator_t generator) {
    generator->type->free(generator->data);
    sark_free(generator);
}
