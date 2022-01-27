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

/*! \file
 *
 * \brief Connection Generator interface
 *
 */

#include <stdint.h>
#include <common-typedefs.h>

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
uint32_t connection_generator_generate(
        connection_generator_t generator, uint32_t pre_slice_start,
        uint32_t pre_slice_count, uint32_t pre_neuron_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        uint32_t max_row_length, uint16_t *indices);
