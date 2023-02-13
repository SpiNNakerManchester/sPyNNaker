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
		unsigned long accum weight_scale);
