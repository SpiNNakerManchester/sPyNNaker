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

/**
 * \brief Data type for matrix generator
 */
typedef struct matrix_generator *matrix_generator_t;

/**
 * \brief Initialise a specific matrix generator
 * \param[in] hash: The identifier of the generator to initialise
 * \param[in,out] region: The address to read data from; updated to position
 *                        after data has been read
 * \param[in] synaptic_matrix: The address of the base of the synaptic matrix
 * \return An initialised matrix generator that can be used with other
 *         functions, or NULL if it couldn't be initialised for any reason
 */
matrix_generator_t matrix_generator_init(uint32_t hash, void **region,
        void *synaptic_matrix);

/**
 * \brief Finish with a matrix generator
 * \param[in] generator: The generator to free
 */
void matrix_generator_free(matrix_generator_t generator);

/**
 * \brief Write a synapse with a matrix generator
 * \param[in] generator: The generator to use to generate the matrix
 * \param[in] pre_index: The index of the pre-neuron relative to the start of
 *                       the matrix
 * \param[in] post_index: The index of the post-neuron on this core
 * \param[in] weight: The weight of the synapse in raw form
 * \param[in] delay: The delay of the synapse in time steps
 * \param[in] weight_scale: The scale to apply to the weight if needed
 */
bool matrix_generator_write_synapse(matrix_generator_t generator,
        uint32_t pre_index, uint16_t post_index, accum weight, uint16_t delay,
		accum weight_scale);
