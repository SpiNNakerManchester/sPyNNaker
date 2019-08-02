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

enum {
    ONE_TO_ONE,
    ALL_TO_ALL,
    FIXED_PROBABILITY,
    FIXED_TOTAL,
    FIXED_PRE,
    FIXED_POST,
    KERNEL,
    /**
     *! \brief The number of known generators
     */
    N_CONNECTION_GENERATORS
};

/**
 *! \brief A "class" for connection generators
 */
typedef struct connection_generator_info {
    /**
     *! \brief The hash of the generator.
     *! For now, hash is just an index agreed between Python and here
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
     *! \brief Generate connections
     *! \param[in] data The data for the connection generator, returned by the
     *!                 initialise function
     *! \param[in] pre_slice_start The start of the slice of the pre-population
     *!                            being generated
     *! \param[in] pre_slice_count The number of neurons in the slice of the
     *!                            pre-population being generated
     *! \param[in] pre_neuron_index The index of the neuron in the
     *!                             pre-population being generated
     *! \param[in] post_slice_start The start of the slice of the
     *!                             post-population being generated
     *! \param[in] post_slice_count The number of neurons in the slice of the
     *!                             post-population being generated
     *! \param[in] max_row_length The maximum number of connections to generate
     *! \param[in/out] indices An array into which the core-relative
     *!                        post-indices should be placed.  This will be
     *!                        initialised to be max_row_length in size
     *! \return The number of connections generated
     */
    generate_connection_func *generate;

    /**
     *! \brief Free any data for the generator
     *! \param[in] data The data to free
     */
    free_func *free;
} connection_generator_info;

/**
 *! \brief The data for a connection generator
 */
struct connection_generator {
    const connection_generator_info *type;
    void *data;
};

/**
 *! \brief An Array of known generators
 */
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
            connection_generator_kernel_free}
};

connection_generator_t connection_generator_init(
        uint32_t hash, address_t *in_region) {
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

uint32_t connection_generator_generate(
        connection_generator_t generator, uint32_t pre_slice_start,
        uint32_t pre_slice_count, uint32_t pre_neuron_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        uint32_t max_row_length, uint16_t *indices) {
    return generator->type->generate(
            generator->data, pre_slice_start, pre_slice_count,
            pre_neuron_index, post_slice_start, post_slice_count,
            max_row_length, indices);
}

void connection_generator_free(connection_generator_t generator) {
    generator->type->free(generator->data);
    sark_free(generator);
}
