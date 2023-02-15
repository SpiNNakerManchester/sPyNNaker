/*
 * Copyright (c) 2017 The University of Manchester
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

/*! \file
 *
 * \brief Connection Generator interface
 *
 */

#include <stdint.h>
#include <common-typedefs.h>

#include "param_generator.h"
#include "matrix_generator.h"

/**
 * \brief Connection generator "object"
 */
typedef struct connection_generator *connection_generator_t;

/**
 * \brief Initialise a specific connection generator
 * \param[in] hash: The identifier of the generator to initialise
 * \param[in,out] region: The address to read data from; updated to position
 *                        after data has been read
 * \return An initialised connection generator that can be used with other
 *         functions, or NULL if it couldn't be initialised for any reason
 */
connection_generator_t connection_generator_init(
        uint32_t hash, void **region);

/**
 * \brief Finish with a connection generator
 * \param[in] generator: The generator to free
 */
void connection_generator_free(connection_generator_t generator);

/**
 * \brief Generate connections with a connection generator
 * \param[in] generator: The generator to use to generate connections
 * \param[in] pre_slice_start: The start of the slice of the pre-population
 *                             being generated
 * \param[in] pre_slice_count: The number of neurons in the slice of the
 *                             pre-population being generated
 * \param[in] pre_neuron_index: The index of the neuron in the pre-population
 *                              being generated
 * \param[in] post_slice_start: The start of the slice of the post-population
 *                              being generated
 * \param[in] post_slice_count: The number of neurons in the slice of the
 *                              post-population being generated
 * \param[in] max_row_length: The maximum number of connections to generate
 * \param[in,out] indices: An array into which the core-relative post-indices
 *                         should be placed.  This will be initialised to be
 *                         max_row_length in size
 * \return The number of connections generated
 */
bool connection_generator_generate(
        connection_generator_t generator, uint32_t pre_lo, uint32_t pre_hi,
        uint32_t post_lo, uint32_t post_hi, uint32_t post_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        unsigned long accum weight_scale, accum timestep_per_delay,
        param_generator_t weight_generator, param_generator_t delay_generator,
        matrix_generator_t matrix_generator);
