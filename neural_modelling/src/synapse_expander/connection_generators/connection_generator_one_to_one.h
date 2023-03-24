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

/**
 * \file
 * \brief One-to-One Connection generator implementation
 */

#include <synapse_expander/generator_types.h>

/**
 * \brief Initialise the one-to-one connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *connection_generator_one_to_one_initialise(UNUSED void **region) {

    log_debug("One to one connector");

    return NULL;
}

/**
 * \brief Free the one-to-one connection generator
 * \param[in] generator: The generator to free
 */
static void connection_generator_one_to_one_free(UNUSED void *generator) {
    // Nothing to do
}

/**
 * \brief Generate connections with the one-to-one connection generator
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
 *                         \p max_row_length in size
 * \return The number of connections generated
 */
static bool connection_generator_one_to_one_generate(
        UNUSED void *generator, uint32_t pre_lo, uint32_t pre_hi,
        uint32_t post_lo, uint32_t post_hi, UNUSED uint32_t post_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        unsigned long accum weight_scale, accum timestep_per_delay,
        param_generator_t weight_generator, param_generator_t delay_generator,
        matrix_generator_t matrix_generator) {

	// First check if any of the range to generate is on this slice
	uint32_t post_slice_end = post_slice_start + post_slice_count - 1;
	if (post_lo > post_slice_end || post_hi < post_slice_start) {
		return true;
	}

	// Find the start and end on the current slice
	uint32_t post_start = max(post_slice_start, post_lo);
	uint32_t post_end = min(post_slice_end, post_hi);

	// Find the offset and length on the current slice
	uint32_t offset = post_start - post_lo;
	uint32_t length = post_end - post_start;

	// Work out the pre start and end to be generated
	uint32_t pre_start = pre_lo + offset;
	uint32_t pre_end = min(pre_start + length, pre_hi);

    for (uint32_t pre = pre_start, post = post_start; pre <= pre_end; pre++, post++) {
        uint32_t local_post = post - post_slice_start;
        accum weight = param_generator_generate(weight_generator);
        uint16_t delay = rescale_delay(
                param_generator_generate(delay_generator), timestep_per_delay);
        if (!matrix_generator_write_synapse(matrix_generator, pre, local_post,
                weight, delay, weight_scale)) {
            log_error("Matrix size is wrong!");
            return false;
        }
    }
    return true;
}
