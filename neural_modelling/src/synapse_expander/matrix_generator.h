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
 * \brief Interface for matrix generation
 */
#include <common-typedefs.h>

#include "connection_generator.h"
#include "param_generator.h"

/**
 * \brief Data type for matrix generator
 */
typedef struct matrix_generator *matrix_generator_t;

/**
 * \brief Initialise a specific matrix generator
 * \param[in] hash: The identifier of the generator to initialise
 * \param[in,out] region: The address to read data from; updated to position
 *                        after data has been read
 * \return An initialised matrix generator that can be used with other
 *         functions, or NULL if it couldn't be initialised for any reason
 */
matrix_generator_t matrix_generator_init(uint32_t hash, void **region);

/**
 * \brief Finish with a matrix generator
 * \param[in] generator: The generator to free
 */
void matrix_generator_free(matrix_generator_t generator);

/**
 * \brief Generate a matrix with a matrix generator
 * \param[in] generator: The generator to use to generate the matrix
 * \param[in] synaptic_matrix: The address of the synaptic matrix to write to
 * \param[in] delayed_synaptic_matrix: The address of the synaptic matrix to
 *                                     write delayed connections to
 * \param[in] max_row_n_words: The maximum number of words in a normal row
 * \param[in] max_delayed_row_n_words: The maximum number of words in a delayed
 *                                     row
 * \param[in] max_row_n_synapses: The maximum number of synapses in a normal row
 * \param[in] max_delayed_row_n_synapses: The maximum number of synapses in a
 *                                        delayed row
 * \param[in] n_synapse_type_bits: The number of bits used for the synapse type
 * \param[in] n_synapse_index_bits: The number of bits used for the neuron id
 * \param[in] synapse_type: The synapse type of each connection
 * \param[in] weight_scales: An array of weight scales, one for each synapse
 *                           type
 * \param[in] post_slice_start: The start of the slice of the post-population
 *                              being generated
 * \param[in] post_slice_count: The number of neurons in the slice of the
 *                              post-population being generated
 * \param[in] pre_slice_start: The start of the slice of the pre-population
 *                             being generated
 * \param[in] pre_slice_count: The number of neurons in the slice of the
 *                             pre-population being generated
 * \param[in] connection_generator: The generator of connections
 * \param[in] delay_generator: The generator of delay values
 * \param[in] weight_generator: The generator of weight values
 * \param[in] max_stage: The maximum delay stage to support
 * \param[in] max_delay_per_stage: The delay per delay stage
 * \param[in] timestep_per_delay: The delay value multiplier to get to timesteps
 * \return The number of connections generated
 */
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
        uint32_t max_stage, uint32_t max_delay_per_stage,
        accum timestep_per_delay);
